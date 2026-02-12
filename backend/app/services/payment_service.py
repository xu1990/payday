"""
支付服务 - 处理支付业务逻辑
"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import MembershipOrder
from app.utils.wechat_pay import (
    create_mini_program_payment,
    parse_payment_notify,
)
from app.core.exceptions import BusinessException, NotFoundException


async def create_membership_payment(
    db: AsyncSession,
    order_id: str,
    openid: str,
) -> dict:
    """
    创建会员订单支付

    Args:
        db: 数据库会话
        order_id: 订单ID
        openid: 用户微信 openid

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

    # 调用微信支付统一下单接口
    payment_params = await create_mini_program_payment(
        out_trade_no=order_id,
        total_fee=order.amount,
        body=f"{order.membership_name or '会员套餐'}",
        openid=openid,
    )

    return payment_params


async def handle_payment_notify(
    db: AsyncSession,
    notify_data: dict,
) -> bool:
    """
    处理支付回调通知 - 优化并发安全

    支持幂等性：同一笔交易的重复通知会被安全处理
    使用数据库行锁 + 唯一约束防止并发问题

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
    time_end = notify_data.get("time_end")  # 微信支付完成时间

    if not out_trade_no or not transaction_id:
        return False

    try:
        async with db.begin():
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

            # 验证金额（防止篡改）
            try:
                fee_amount = int(total_fee)
            except (ValueError, TypeError):
                return False

            if fee_amount != int(order.amount * 100):  # 转换为分
                return False

            # 幂等性：检查交易ID是否已使用
            if order.transaction_id and order.transaction_id != transaction_id:
                return False  # 不同的交易ID，异常情况

            # 如果已支付且交易ID相同，直接返回成功（重复通知）
            if order.status == "paid" and order.transaction_id == transaction_id:
                return True

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
                order.end_date = order.start_date + timedelta(days=order.membership.duration_days)
            except (ValueError, TypeError):
                pass  # 时间解析失败，使用数据库默认值

        return True

    except IntegrityError:
        # 并发插入导致的唯一约束冲突
        return False
    except Exception:
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
