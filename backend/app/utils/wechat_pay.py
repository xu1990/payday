"""
微信支付工具 - 小程序支付
参考文档: https://pay.weixin.qq.com/wiki/doc/apiv3/open/pay/chapter2_7_2.shtml
"""
import hashlib
import random
import string
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()


def generate_nonce_str() -> str:
    """生成随机字符串"""
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))


def dict_to_xml(data: dict[str, Any]) -> str:
    """将字典转换为 XML 格式"""
    xml = ["<xml>"]
    for k, v in data.items():
        xml.append(f"<{k}>{v}</{k}>")
    xml.append("</xml>")
    return "".join(xml)


def xml_to_dict(xml_str: str) -> dict[str, Any]:
    """将 XML 转换为字典 - 防止 XXE 攻击"""
    # 禁用 DTD 和实体解析，防止 XXE 攻击
    parser = ET.XMLParser(resolve_entities=False, forbid_dtd=True)
    root = ET.fromstring(xml_str, parser=parser)
    data = {}
    for child in root:
        data[child.tag] = child.text
    return data


def sign_md5(data: dict[str, Any], api_key: str) -> str:
    """生成 MD5 签名"""
    # 过滤空值和 sign 字段，按 key 排序
    filtered = {k: v for k, v in data.items() if v != "" and k != "sign"}
    sorted_items = sorted(filtered.items())
    # 拼接字符串
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_items])
    sign_str += f"&key={api_key}"
    # MD5 加密并转大写
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()


def verify_sign(data: dict[str, Any], api_key: str) -> bool:
    """验证签名"""
    received_sign = data.get("sign", "")
    calculated_sign = sign_md5(data, api_key)
    return received_sign == calculated_sign


async def create_mini_program_payment(
    out_trade_no: str,
    total_fee: int,
    body: str,
    openid: str,
    client_ip: str = "127.0.0.1",
) -> dict[str, Any]:
    """
    创建小程序支付订单

    Args:
        out_trade_no: 商户订单号
        total_fee: 总金额（分）
        body: 商品描述
        openid: 用户 openid
        client_ip: 客户端真实 IP（从请求中获取）

    Returns:
        包含 prepay_id 的字典，用于小程序调起支付
    """
    url = "https://api.mch.weixin.qq.com/pay/unifiedorder"

    data = {
        "appid": settings.wechat_app_id,
        "mch_id": settings.wechat_mch_id,
        "nonce_str": generate_nonce_str(),
        "body": body,
        "out_trade_no": out_trade_no,
        "total_fee": total_fee,
        "spbill_create_ip": client_ip,
        "notify_url": settings.wechat_pay_notify_url,
        "trade_type": "JSAPI",
        "openid": openid,
    }

    # 生成签名
    data["sign"] = sign_md5(data, settings.wechat_pay_api_key)

    # 转换为 XML
    xml_data = dict_to_xml(data)

    # 发送请求
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, content=xml_data.encode("utf-8"), headers={"Content-Type": "application/xml"})

    # 解析响应
    resp_data = xml_to_dict(response.text)

    if resp_data.get("return_code") != "SUCCESS":
        raise Exception(f"微信支付接口错误: {resp_data.get('return_msg')}")

    if resp_data.get("result_code") != "SUCCESS":
        raise Exception(f"微信支付业务错误: {resp_data.get('err_code_des')}")

    # 生成小程序支付参数
    prepay_id = resp_data.get("prepay_id")
    timestamp = str(int(time.time()))
    nonce_str = generate_nonce_str()

    package = f"prepay_id={prepay_id}"

    # 生成小程序支付签名
    pay_sign_data = {
        "appId": settings.wechat_app_id,
        "timeStamp": timestamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "MD5",
    }
    pay_sign = sign_md5(pay_sign_data, settings.wechat_pay_api_key)

    return {
        "timeStamp": timestamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "MD5",
        "paySign": pay_sign,
        "out_trade_no": out_trade_no,
    }


def parse_payment_notify(xml_data: str) -> dict[str, Any]:
    """
    解析支付回调通知 - 增强安全验证

    Args:
        xml_data: 微信支付回调的 XML 数据

    Returns:
        解析后的字典数据

    Raises:
        Exception: 签名验证失败或缺少必需字段
    """
    data = xml_to_dict(xml_data)

    # 验证签名
    if not verify_sign(data, settings.wechat_pay_api_key):
        raise Exception("Invalid signature")

    # 验证必需字段
    required_fields = ["return_code", "result_code", "out_trade_no",
                     "transaction_id", "total_fee", "time_end"]
    missing_fields = [f for f in required_fields if not data.get(f)]
    if missing_fields:
        raise Exception(f"Missing required fields: {', '.join(missing_fields)}")

    # 验证业务状态
    if data.get("return_code") != "SUCCESS" or data.get("result_code") != "SUCCESS":
        raise Exception(f"Payment failed: {data.get('err_code_des', 'Unknown error')}")

    return data
