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


def _get_client_ip(request: Request) -> str:
    """
    从请求中获取客户端真实 IP

    优先级: client > X-Real-IP > X-Forwarded-For (最右侧)

    SECURITY:
    - 使用 ipaddress 模块严格验证 IP 格式
    - 拒绝私有 IP 地址（除非是直连）
    - X-Forwarded-For 可被客户端伪造，只信任最右侧的 IP（第一个代理）
    """
    import ipaddress

    def is_valid_public_ip(ip_str: str) -> bool:
        """验证 IP 地址格式且为公网地址"""
        try:
            ip = ipaddress.ip_address(ip_str)
            # 拒绝私有、本地、链路本地地址
            return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
        except ValueError:
            return False

    # 首先尝试直接连接的 IP（最可靠，即使是私有 IP 也接受）
    if request.client and request.client.host:
        direct_ip = request.client.host
        try:
            # 验证 IP 格式（包括私有 IP，因为是直连）
            ipaddress.ip_address(direct_ip)
            return direct_ip
        except ValueError:
            pass

    # X-Real-IP: 通常由反向代理设置，相对可信
    # 但仍然需要验证 IP 格式和公网地址
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        ip = real_ip.strip()
        if is_valid_public_ip(ip):
            return ip

    # X-Forwarded-For: 可能包含多个 IP，格式: client, proxy1, proxy2
    # 只信任最右侧的 IP（第一个代理看到的真实 IP）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ips = [ip.strip() for ip in forwarded_for.split(",")]
        # 从右向左查找第一个有效的公网 IP
        for ip in reversed(ips):
            if is_valid_public_ip(ip):
                return ip

    # 如果所有方法都失败，返回默认值
    return "0.0.0.0"  # 表示无法确定真实IP


@router.post("/create", response_model=CreatePaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建支付订单

    Args:
        data: 支付请求参数
        request: FastAPI 请求对象
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

    # 获取客户端真实 IP
    client_ip = _get_client_ip(request)

    try:
        payment_params = await create_membership_payment(
            db=db,
            order_id=data.order_id,
            openid=openid,
            client_ip=client_ip,
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
    # 验证 Content-Type，确保只接受 XML 数据
    content_type = request.headers.get("content-type", "")
    if "application/xml" not in content_type and "text/xml" not in content_type:
        # 返回错误响应，但不暴露详细信息
        return generate_payment_response("FAIL", "Unsupported Media Type")

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
