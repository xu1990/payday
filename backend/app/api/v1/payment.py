"""
支付 API - 处理支付相关请求
"""
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentErrorResponse,
)
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.payment_service import (
    create_membership_payment,
    generate_payment_response,
    handle_payment_notify,
)
from app.utils.wechat_pay import parse_payment_notify

router = APIRouter(prefix="/payment", tags=["payment"])


@router.post("/create", response_model=CreatePaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建支付订单

    Args:
        data: 支付请求参数
        current_user: 当前用户
        db: 数据库会话

    Returns:
        小程序支付参数
    """
    # 获取用户的 openid
    openid = current_user.openid
    if not openid:
        return PaymentErrorResponse(
            success=False,
            message="用户未绑定微信",
        )

    try:
        payment_params = await create_membership_payment(
            db=db,
            order_id=data.order_id,
            openid=openid,
        )

        return CreatePaymentResponse(
            success=True,
            data=payment_params,
            message="支付参数生成成功",
        )

    except ValueError as e:
        # 业务逻辑错误（如订单不存在、状态不对）
        return PaymentErrorResponse(
            success=False,
            message=str(e),
        )
    except Exception:
        # 其他未知错误，不暴露详细信息
        return PaymentErrorResponse(
            success=False,
            message="创建支付失败，请稍后重试",
        )


@router.post("/notify/wechat")
async def wechat_payment_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    微信支付回调通知

    Args:
        request: FastAPI 请求对象
        db: 数据库会话

    Returns:
        XML 格式的响应
    """
    # 读取原始 XML 数据
    xml_data = await request.body()

    try:
        # 解析通知数据
        notify_data = parse_payment_notify(xml_data.decode("utf-8"))

        # 处理支付结果
        success = await handle_payment_notify(
            db=db,
            notify_data=notify_data,
        )

        if success:
            return generate_payment_response("SUCCESS", "OK")
        else:
            return generate_payment_response("FAIL", "处理失败")

    except Exception as e:
        return generate_payment_response("FAIL", str(e))
