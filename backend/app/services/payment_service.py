"""
支付服务 - 处理支付业务逻辑
"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from app.models.membership import MembershipOrder, Membership
from app.utils.wechat_pay import (
    create_mini_program_payment,
    parse_payment_notify,
)
from app.core.exceptions import BusinessException, NotFoundException


async def create_membership_payment(
    db: AsyncSession,
    order_id: str,
    openid: str,
    client_ip: str = "127.0.0.1",
) -> dict:
    """
    创建会员订单支付

    Args:
        db: 数据库会话
        order_id: 订单ID
        openid: 用户微信 openid
        client_ip: 客户端真实 IP

    Returns:
        小程序支付参数

    Raises:
        ValueError: 业务逻辑错误（订单不存在、状态不对等）
    """
    # 查询订单
    result = await db.execute(
        select(MembershipOrder).where(MembershipOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise NotFoundException("订单不存在")

    if order.status != "pending":
        raise BusinessException("订单状态不正确，仅待支付订单可创建支付")

    # 查询会员套餐信息以获取名称
    membership_result = await db.execute(
        select(Membership).where(Membership.id == order.membership_id)
    )
    membership = membership_result.scalar_one_or_none()
    membership_name = membership.name if membership else "会员套餐"

    # 调用微信支付统一下单接口
    payment_params = await create_mini_program_payment(
        out_trade_no=order_id,
        total_fee=int(order.amount),
        body=membership_name,
        openid=openid,
        client_ip=client_ip,
    )

    return payment_params


async def handle_payment_notify(
    db: AsyncSession,
    notify_data: dict,
) -> bool:
    """
    处理支付回调通知 - 优化并发安全 + 重放攻击防护

    支持幂等性：同一笔交易的重复通知会被安全处理
    使用数据库行锁 + 唯一约束防止并发问题

    SECURITY:
    - 时间戳验证：通知时间必须在可接受范围内（5分钟）
    - Nonce检查：使用Redis检测重放攻击
    - 金额验证：防止金额篡改

    Args:
        db: 数据库会话
        notify_data: 解析后的通知数据

    Returns:
        处理是否成功
    """
    from datetime import datetime, timedelta
    from sqlalchemy.exc import IntegrityError

    out_trade_no = notify_data.get("out_trade_no")
    transaction_id = notify_data.get("transaction_id")
    total_fee = notify_data.get("total_fee")
    time_end = notify_data.get("time_end")  # 微信支付完成时间

    if not out_trade_no or not transaction_id:
        return False

    # SECURITY: 验证时间戳，防止重放攻击
    if time_end:
        try:
            # 解析微信时间格式：yyyyMMddHHmmss
            from app.utils.logger import get_logger
            logger = get_logger(__name__)

            notify_time = datetime.strptime(time_end, "%Y%m%d%H%M%S")
            current_time = datetime.utcnow()

            # SECURITY: 检查通知时间是否在合理范围内（5分钟内）
            # 注意：微信服务器可能有时间偏差，给予一定容错空间
            max_acceptable_delay = timedelta(minutes=5)
            time_diff = (current_time - notify_time).total_seconds()

            # 如果通知时间超过当前时间5分钟以上，拒绝
            if abs(time_diff) > max_acceptable_delay.total_seconds():
                logger.warning(
                    f"Payment notification time validation failed: {time_end}, "
                    f"diff={time_diff}s"
                )
                return False

        except (ValueError, TypeError) as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Invalid time_end format: {time_end}, error={e}")
            # 不暴露具体的格式错误信息
            return False

    # SECURITY: 使用 nonce 检查防止重放攻击
    from app.core.cache import get_redis_client
    redis = await get_redis_client()
    if redis:
        try:
            nonce_key = f"payment_nonce:{transaction_id}"
            # 检查是否已存在相同的 transaction_id（重放检测）
            if await redis.exists(nonce_key):
                from app.utils.logger import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Replay attack detected: transaction_id={transaction_id}")
                # 已处理过的通知，返回True避免微信重复通知
                # 但需要验证订单状态
                result = await db.execute(
                    select(MembershipOrder).where(MembershipOrder.id == out_trade_no)
                )
                order = result.scalar_one_or_none()
                return order and order.status == "paid"

            # 存储 nonce，有效期1小时
            await redis.setex(nonce_key, 3600, "1")
        except Exception as e:
            # SECURITY: 不暴露详细的错误信息
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to check payment nonce")
            # nonce检查失败不应阻止支付流程，继续处理

    try:
        # 查询订单并加锁（SKIP LOCKED 避免长时间等待）
        result = await db.execute(
            select(MembershipOrder)
            .where(MembershipOrder.id == out_trade_no)
            .with_for_update(skip_locked=True)  # 如果被锁定则返回None
        )
        order = result.scalar_one_or_none()

        if not order:
            # 可能被其他进程处理中，返回False让微信重试
            return False

        # 验证金额（防止篡改） - 使用 Decimal 避免浮点精度问题
        try:
            fee_amount = int(total_fee)
        except (ValueError, TypeError):
            return False

        # 使用 Decimal 进行精确的金额计算和比较
        # order.amount 存储的是浮点数，需要转换为 Decimal 进行精确计算
        try:
            expected_amount = Decimal(str(order.amount)) * Decimal(100)
            # SECURITY: 使用Decimal('0.01')保留分位精度（2位小数）
            # 避免round(Decimal('1'))四舍五入取整导致的精度损失
            expected_amount = expected_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if fee_amount != int(expected_amount):  # 转换为分比较
                return False
        except (InvalidOperation, ValueError):
            return False

        # 幂等性：检查交易ID是否已使用
        if order.transaction_id and order.transaction_id != transaction_id:
            return False  # 不同的交易ID，异常情况

        # 如果已支付且交易ID相同，直接返回成功（重复通知）
        if order.status == "paid" and order.transaction_id == transaction_id:
            return True

        # 查询会员套餐信息
        membership_result = await db.execute(
            select(Membership).where(Membership.id == order.membership_id)
        )
        membership = membership_result.scalar_one_or_none()

        # 更新订单状态
        order.status = "paid"
        order.payment_method = "wechat"
        order.transaction_id = transaction_id
        # 使用微信支付时间作为开始时间
        from datetime import datetime, timedelta
        try:
            # 解析微信时间格式：yyyyMMddHHmmss
            pay_time = datetime.strptime(time_end, "%Y%m%d%H%M%S")
            order.start_date = pay_time
            duration_days = membership.duration_days if membership else 30
            order.end_date = order.start_date + timedelta(days=duration_days)
        except (ValueError, TypeError):
            pass  # 时间解析失败，使用数据库默认值

        await db.commit()
        return True

    except IntegrityError:
        # 并发插入导致的唯一约束冲突
        return False
    except (ValueError, TypeError, InvalidOperation) as e:
        # 捕获具体的异常类型，提供更好的调试信息
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Payment notification processing error: {e}, type={type(e).__name__}")
        return False
    except Exception as e:
        # 捕获所有其他异常
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Unexpected error in payment notification: {e}")
        return False


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
