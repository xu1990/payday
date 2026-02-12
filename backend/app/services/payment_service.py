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
        raise ValueError("订单不存在")

    if order.status != "pending":
        raise ValueError("订单状态不正确")

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
    处理支付回调通知

    支持幂等性：同一笔交易的重复通知会被安全处理
    使用数据库事务确保数据一致性

    Args:
        db: 数据库会话
        notify_data: 解析后的通知数据

    Returns:
        处理是否成功
    """
    from sqlalchemy.exc import SQLAlchemyError

    out_trade_no = notify_data.get("out_trade_no")
    transaction_id = notify_data.get("transaction_id")
    total_fee = notify_data.get("total_fee")

    if not out_trade_no or not transaction_id:
        return False

    try:
        # 使用数据库事务确保原子性
        async with db.begin():
            # 查询订单并加锁（防止并发修改）
            result = await db.execute(
                select(MembershipOrder)
                .where(MembershipOrder.id == out_trade_no)
                .with_for_update()  # 行级锁
            )
            order = result.scalar_one_or_none()

            if not order:
                return False

            # 检查订单金额是否匹配（安全校验）
            if int(total_fee) != order.amount:
                return False

            # 幂等性检查：如果订单已支付且交易ID相同，直接返回成功
            if order.status == "paid" and order.transaction_id == transaction_id:
                return True  # 重复通知，安全处理

            # 如果订单已支付但交易ID不同，可能是异常情况
            if order.status == "paid":
                return False

            # 更新订单状态为已支付
            await db.execute(
                update(MembershipOrder)
                .where(MembershipOrder.id == out_trade_no)
                .values(
                    status="paid",
                    payment_method="wechat",
                    transaction_id=transaction_id,
                )
            )

        return True

    except SQLAlchemyError:
        # 数据库错误，回滚事务（自动由 with 块处理）
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
