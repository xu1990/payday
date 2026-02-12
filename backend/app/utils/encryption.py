"""
工资金额加密 - 增强密钥派生
使用 HKDF (HMAC-based Extract-and-Expand Key Derivation)
支持每条记录独立的随机 salt
"""
import base64
import os
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
from app.core.config import get_settings
from typing import Tuple

# 密钥版本（支持密钥轮换）
CURRENT_KEY_VERSION = 2


def _derive_key(secret_key: str, salt: bytes, info: bytes = b"payday-salary-encryption") -> bytes:
    """
    使用 HKDF 从密钥派生加密密钥

    Args:
        secret_key: 原始密钥
        salt: 盐值
        info: 上下文信息
    """
    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    )
    return kdf.derive(secret_key.encode())


def _get_cipher(salt: bytes) -> Fernet:
    """
    使用指定 salt 获取加密器

    Args:
        salt: 加密使用的盐值
    """
    settings = get_settings()
    key = _derive_key(settings.encryption_secret_key, salt)
    return Fernet(base64.urlsafe_b64encode(key))


def _generate_salt() -> bytes:
    """
    生成随机 salt（32字节）

    Returns:
        随机生成的 salt
    """
    return os.urandom(32)


def encrypt_amount(amount: float) -> Tuple[str, str]:
    """
    加密工资金额 - 每次使用独立随机 salt

    Args:
        amount: 待加密的金额

    Returns:
        (encrypted_text, salt_base64): 加密后的文本和 base64 编码的 salt
    """
    salt = _generate_salt()
    cipher = _get_cipher(salt)
    encrypted = cipher.encrypt(str(amount).encode()).decode()
    salt_b64 = base64.urlsafe_b64encode(salt).decode()
    return encrypted, salt_b64


def decrypt_amount(encrypted: str, salt_b64: str) -> float:
    """
    解密工资金额 - 使用记录的 salt

    Args:
        encrypted: 加密的金额文本
        salt_b64: base64 编码的 salt

    Returns:
        解密后的金额
    """
    salt = base64.urlsafe_b64decode(salt_b64.encode())
    cipher = _get_cipher(salt)
    decrypted = cipher.decrypt(encrypted.encode()).decode()
    return float(decrypted)
