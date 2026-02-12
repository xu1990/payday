"""
HTTP 请求工具函数
"""
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    从请求中获取客户端 IP 地址

    优先级: X-Forwarded-For > X-Real-IP > client.host
    """
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"
