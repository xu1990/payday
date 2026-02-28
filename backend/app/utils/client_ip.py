"""客户端IP获取工具"""
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址

    优先级：
    1. X-Forwarded-For 头（取第一个IP）
    2. X-Real-IP 头
    3. request.client.host

    Args:
        request: FastAPI Request 对象

    Returns:
        客户端IP地址字符串
    """
    # 优先检查 X-Forwarded-For 头（代理/负载均衡场景）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个IP，取第一个（原始客户端IP）
        return forwarded_for.split(",")[0].strip()

    # 检查 X-Real-IP 头（Nginx等代理常用）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # 最后使用直接连接的客户端地址
    if request.client and request.client.host:
        return request.client.host

    # 兜底返回
    return "127.0.0.1"
