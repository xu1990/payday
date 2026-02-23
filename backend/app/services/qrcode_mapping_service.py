"""
二维码参数映射服务
"""
import string
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.qrcode_mapping import QRCodeMapping
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 可用于生成短码的字符（去掉易混淆的字符：0OIl）
CHARS = string.ascii_letters + string.digits
CHARS = CHARS.replace('0', '').replace('O', '').replace('I', '').replace('l', '')


def generate_short_code(length: int = 8) -> str:
    """
    生成随机短码
    使用62进制字符（去除易混淆字符）
    """
    return ''.join(random.choices(CHARS, k=length))


async def create_qrcode_mapping(
    db: AsyncSession,
    page: str,
    params: Dict[str, Any],
    expires_days: Optional[int] = None
) -> QRCodeMapping:
    """
    创建二维码参数映射

    Args:
        db: 数据库会话
        page: 小程序页面路径
        params: 自定义参数
        expires_days: 过期天数（可选）

    Returns:
        QRCodeMapping 对象
    """
    import uuid

    # 生成唯一短码（最多尝试10次）
    short_code = None
    for _ in range(10):
        code = generate_short_code(8)
        # 检查是否已存在
        existing = await db.execute(
            select(QRCodeMapping).where(QRCodeMapping.short_code == code)
        )
        if not existing.scalar_one_or_none():
            short_code = code
            break

    if not short_code:
        raise Exception("Failed to generate unique short code")

    # 计算过期时间
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    # 创建记录
    mapping = QRCodeMapping(
        id=str(uuid.uuid4()),
        short_code=short_code,
        page=page,
        params=params,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        scan_count=0
    )

    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    logger.info(f"Created QR code mapping: {short_code} -> {page} {params}")
    return mapping


async def get_qrcode_mapping(
    db: AsyncSession,
    short_code: str,
    increment_scan: bool = True
) -> Optional[QRCodeMapping]:
    """
    获取二维码参数映射

    Args:
        db: 数据库会话
        short_code: 短码
        increment_scan: 是否增加扫描次数

    Returns:
        QRCodeMapping 对象，不存在或已过期返回 None
    """
    result = await db.execute(
        select(QRCodeMapping).where(QRCodeMapping.short_code == short_code)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        return None

    # 检查是否过期
    if mapping.expires_at and mapping.expires_at < datetime.utcnow():
        logger.warning(f"QR code mapping expired: {short_code}")
        return None

    # 增加扫描次数
    if increment_scan:
        mapping.scan_count += 1
        await db.commit()
        logger.info(f"QR code {short_code} scanned, count: {mapping.scan_count}")

    return mapping


async def batch_get_qrcode_mappings(
    db: AsyncSession,
    short_codes: list[str],
    increment_scan: bool = True
) -> Dict[str, Dict[str, Any]]:
    """
    批量获取二维码参数映射

    Args:
        db: 数据库会话
        short_codes: 短码列表
        increment_scan: 是否增加扫描次数

    Returns:
        短码到参数的映射字典
    """
    if not short_codes:
        return {}

    result = await db.execute(
        select(QRCodeMapping).where(QRCodeMapping.short_code.in_(short_codes))
    )
    mappings = result.scalars().all()

    output = {}
    for mapping in mappings:
        # 检查是否过期
        if mapping.expires_at and mapping.expires_at < datetime.utcnow():
            continue

        # 增加扫描次数
        if increment_scan:
            mapping.scan_count += 1

        output[mapping.short_code] = {
            "page": mapping.page,
            "params": mapping.params,
            "scan_count": mapping.scan_count
        }

    if increment_scan and mappings:
        await db.commit()

    return output
