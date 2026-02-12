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
    """
    # 查询订单
    result = await db.execute(
        select(MembershipOrder).where(MembershipOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise Exception("订单不存在")

    if order.status != "pending":
        raise Exception("订单状态不正确")

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

    Args:
        db: 数据库会话
        notify_data: 解析后的通知数据

    Returns:
        处理是否成功
    """
    out_trade_no = notify_data.get("out_trade_no")
    transaction_id = notify_data.get("transaction_id")
    total_fee = notify_data.get("total_fee")

    if not out_trade_no or not transaction_id:
        return False

    # 查询订单
    result = await db.execute(
        select(MembershipOrder).where(MembershipOrder.id == out_trade_no)
    )
    order = result.scalar_one_or_none()

    if not order:
        return False

    # 检查订单金额是否匹配
    if int(total_fee) != order.amount:
        return False

    # 更新订单状态
    if order.status == "pending":
        await db.execute(
            update(MembershipOrder)
            .where(MembershipOrder.id == out_trade_no)
            .values(
                status="paid",
                payment_method="wechat",
                transaction_id=transaction_id,
            )
        )
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
