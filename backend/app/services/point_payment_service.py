"""积分订单支付服务 - 混合支付系统"""
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, NotFoundException, ValidationException
from app.models.point_order import PointOrder
from app.models.point_payment import PointPayment
from app.models.point_payment_notify import PointPaymentNotify
from app.models.point_product import PointProduct
from app.models.point_sku import PointProductSKU
from app.services.ability_points_service import spend_points, add_points
from app.utils.wechat_pay import create_mini_program_payment
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_out_trade_no() -> str:
    """生成商户订单号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = secrets.token_hex(8).upper()
    return f"PP{timestamp}{random_str}"


async def create_point_payment(
    db: AsyncSession,
    order_id: str,
    user_id: str,
    openid: str,
    client_ip: str = "127.0.0.1",
    idempotency_key: Optional[str] = None,
) -> Tuple[PointPayment, Dict]:
    """
    创建积分订单支付

    Args:
        db: 数据库会话
        order_id: 订单ID
        user_id: 用户ID
        openid: 用户微信 openid
        client_ip: 客户端真实 IP
        idempotency_key: 幂等性键

    Returns:
        (支付流水, 小程序支付参数)

    Raises:
        NotFoundException: 订单不存在
        BusinessException: 业务逻辑错误
    """
    # 1. 查询订单并加锁
    result = await db.execute(
        select(PointOrder)
        .where(PointOrder.id == order_id)
        .with_for_update()
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在", code="ORDER_NOT_FOUND")

    if order.user_id != user_id:
        raise BusinessException("无权操作此订单", code="PERMISSION_DENIED")

    if order.payment_status not in ["unpaid"]:
        raise BusinessException("订单支付状态不正确", code="INVALID_PAYMENT_STATUS")

    if not order.cash_amount or order.cash_amount <= 0:
        raise BusinessException("订单无需支付现金", code="NO_PAYMENT_REQUIRED")

    # 2. 检查幂等性（如果提供了幂等性键）
    if idempotency_key:
        existing_payment = await db.execute(
            select(PointPayment)
            .where(PointPayment.idempotency_key == idempotency_key)
        )
        if existing_payment.scalar_one_or_none():
            raise BusinessException("重复的支付请求", code="DUPLICATE_PAYMENT")

    # 3. 检查是否已有进行中的支付
    existing_payment = await db.execute(
        select(PointPayment)
        .where(
            PointPayment.order_id == order_id,
            PointPayment.status.in_(["created", "paying"])
        )
    )
    existing = existing_payment.scalar_one_or_none()
    if existing:
        # 返回现有的支付流水
        if existing.prepay_id:
            # 重新生成支付参数
            from app.core.config import settings
            from app.utils.wechat_pay import generate_pay_sign

            pay_sign_result = generate_pay_sign(
                prepay_id=existing.prepay_id,
                appid=settings.wechat_app_id,
            )
            payment_params = {
                "timeStamp": pay_sign_result["timeStamp"],
                "nonceStr": pay_sign_result["nonceStr"],
                "package": pay_sign_result["package"],
                "signType": pay_sign_result["signType"],
                "paySign": pay_sign_result["paySign"],
            }
            return existing, payment_params
        else:
            raise BusinessException("已有进行中的支付", code="PAYMENT_IN_PROGRESS")

    # 4. 生成商户订单号
    out_trade_no = generate_out_trade_no()

    # 5. 创建支付流水
    payment = PointPayment(
        order_id=order_id,
        user_id=user_id,
        out_trade_no=out_trade_no,
        total_amount=order.cash_amount,
        cash_amount=order.cash_amount,
        points_amount=order.points_cost if order.payment_mode == "mixed" else 0,
        status="created",
        payment_method="wechat",
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    await db.flush()

    # 6. 调用微信支付统一下单接口
    try:
        payment_params = await create_mini_program_payment(
            out_trade_no=out_trade_no,
            total_fee=order.cash_amount,
            body=f"积分商城-{order.product_name}",
            openid=openid,
            client_ip=client_ip,
        )

        # 7. 更新支付流水
        payment.prepay_id = payment_params.get("prepay_id", "").replace("prepay_id=", "")
        payment.status = "paying"
        payment.expired_at = datetime.utcnow() + timedelta(minutes=30)
        payment.request_snapshot = json.dumps({
            "out_trade_no": out_trade_no,
            "total_fee": order.cash_amount,
            "openid": openid,
            "client_ip": client_ip,
        })

        await db.commit()
        await db.refresh(payment)

        return payment, payment_params

    except Exception as e:
        logger.error(f"Failed to create wechat payment: {e}")
        payment.status = "failed"
        payment.fail_code = "WECHAT_ERROR"
        payment.fail_message = str(e)
        await db.commit()
        raise BusinessException("创建支付失败，请重试", code="PAYMENT_CREATE_FAILED")


async def handle_point_payment_notify(
    db: AsyncSession,
    notify_data: dict,
) -> bool:
    """
    处理积分订单支付回调通知

    核心逻辑：
    1. 验证签名（在调用前完成）
    2. 查询支付流水并加锁
    3. 验证金额
    4. 更新支付状态
    5. 更新订单状态
    6. 扣除积分（如果是混合支付）
    7. 记录回调通知

    Args:
        db: 数据库会话
        notify_data: 解析后的通知数据

    Returns:
        处理是否成功
    """
    from sqlalchemy.exc import IntegrityError

    out_trade_no = notify_data.get("out_trade_no")
    transaction_id = notify_data.get("transaction_id")
    total_fee = notify_data.get("total_fee")
    time_end = notify_data.get("time_end")
    result_code = notify_data.get("result_code")

    if not out_trade_no or not transaction_id:
        logger.warning(f"Missing required fields in notify_data: {notify_data.keys()}")
        return False

    # 验证支付结果
    if result_code != "SUCCESS":
        logger.warning(f"Payment failed: result_code={result_code}")
        return False

    # SECURITY: 验证时间戳，防止重放攻击
    if time_end:
        try:
            notify_time = datetime.strptime(time_end, "%Y%m%d%H%M%S")
            current_time = datetime.utcnow()
            max_delay = timedelta(minutes=5)
            time_diff = abs((current_time - notify_time).total_seconds())

            if time_diff > max_delay.total_seconds():
                logger.warning(f"Payment notification expired: {time_end}, diff={time_diff}s")
                return False
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid time_end format: {time_end}, error={e}")

    # SECURITY: 使用 nonce 检查防止重放攻击
    from app.core.cache import get_redis_client
    redis = await get_redis_client()
    if redis:
        try:
            nonce_key = f"point_payment_nonce:{transaction_id}"
            if await redis.exists(nonce_key):
                logger.warning(f"Replay attack detected: transaction_id={transaction_id}")
                # 检查支付状态
                result = await db.execute(
                    select(PointPayment).where(PointPayment.transaction_id == transaction_id)
                )
                payment = result.scalar_one_or_none()
                return payment and payment.status == "success"
            await redis.setex(nonce_key, 3600, "1")
        except Exception as e:
            logger.error(f"Failed to check payment nonce: {e}")

    try:
        # 查询支付流水并加锁
        result = await db.execute(
            select(PointPayment)
            .where(PointPayment.out_trade_no == out_trade_no)
            .with_for_update(skip_locked=True)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            logger.warning(f"Payment not found: {out_trade_no}")
            return False

        # 幂等性检查
        if payment.status == "success":
            logger.info(f"Payment already processed: {out_trade_no}")
            return True

        # 验证金额
        try:
            fee_amount = int(total_fee)
            if fee_amount != payment.cash_amount:
                logger.warning(f"Amount mismatch: expected={payment.cash_amount}, got={fee_amount}")
                return False
        except (ValueError, TypeError):
            return False

        # 查询订单并加锁
        order_result = await db.execute(
            select(PointOrder)
            .where(PointOrder.id == payment.order_id)
            .with_for_update()
        )
        order = order_result.scalar_one_or_none()

        if not order:
            logger.warning(f"Order not found: {payment.order_id}")
            return False

        # 更新支付状态
        payment.status = "success"
        payment.transaction_id = transaction_id
        payment.paid_at = datetime.utcnow()
        payment.response_snapshot = json.dumps(notify_data)

        # 如果是混合支付，确认扣除锁定的积分
        if order.payment_mode == "mixed" and not order.points_deducted and order.points_cost > 0:
            from app.services.ability_points_service import confirm_locked_points
            await confirm_locked_points(
                db,
                order.user_id,
                order.points_cost,
                reference_id=order.id,
                reference_type="point_order",
                description=f"购买商品: {order.product_name}"
            )
            order.points_deducted = True

        # 更新订单状态
        order.payment_status = "paid"
        order.transaction_id = transaction_id
        order.payment_method = "wechat"

        # 记录回调通知
        notify_record = PointPaymentNotify(
            payment_id=payment.id,
            transaction_id=transaction_id,
            out_trade_no=out_trade_no,
            notify_type="payment",
            raw_data=json.dumps(notify_data),
            parsed_data=json.dumps(notify_data),
            process_status="success",
            notified_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
        )
        db.add(notify_record)

        await db.commit()
        logger.info(f"Payment processed successfully: {out_trade_no}")
        return True

    except IntegrityError as e:
        logger.error(f"Integrity error in payment notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing payment notification: {e}")
        return False


async def query_payment_status(
    db: AsyncSession,
    payment_id: str,
    user_id: str,
) -> Optional[PointPayment]:
    """
    查询支付状态

    Args:
        db: 数据库会话
        payment_id: 支付ID
        user_id: 用户ID

    Returns:
        支付流水
    """
    result = await db.execute(
        select(PointPayment).where(
            PointPayment.id == payment_id,
            PointPayment.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def close_payment(
    db: AsyncSession,
    payment_id: str,
    user_id: str,
    reason: Optional[str] = None,
) -> bool:
    """
    关闭支付

    Args:
        db: 数据库会话
        payment_id: 支付ID
        user_id: 用户ID
        reason: 关闭原因

    Returns:
        是否成功
    """
    result = await db.execute(
        select(PointPayment)
        .where(
            PointPayment.id == payment_id,
            PointPayment.user_id == user_id,
        )
        .with_for_update()
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise NotFoundException("支付记录不存在", code="PAYMENT_NOT_FOUND")

    if payment.status not in ["created", "paying"]:
        raise BusinessException("支付状态不允许关闭", code="INVALID_PAYMENT_STATUS")

    # 查询关联订单
    order_result = await db.execute(
        select(PointOrder)
        .where(PointOrder.id == payment.order_id)
        .with_for_update()
    )
    order = order_result.scalar_one_or_none()

    # 如果是混合支付且订单存在，解锁积分
    if order and order.payment_mode == "mixed" and not order.points_deducted and order.points_cost > 0:
        from app.services.ability_points_service import unlock_points
        await unlock_points(
            db,
            order.user_id,
            order.points_cost,
            reference_id=order.id,
            reference_type="point_order",
            description=f"支付取消，解锁积分: {order.product_name}"
        )
        order.points_deducted = False  # 标记积分未扣除（已解锁）

    # 更新支付状态
    payment.status = "closed"
    payment.closed_at = datetime.utcnow()
    payment.fail_message = reason or "用户取消支付"

    await db.commit()
    return True


def generate_payment_response(return_code: str, return_msg: str = "OK") -> str:
    """
    生成支付回调响应

    Args:
        return_code: 返回码
        return_msg: 返回信息

    Returns:
        XML 格式的响应
    """
    from app.utils.wechat_pay import dict_to_xml

    return dict_to_xml({
        "return_code": return_code,
        "return_msg": return_msg,
    })
