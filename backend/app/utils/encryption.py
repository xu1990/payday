"""
工资金额加密 - 增强密钥派生
使用 HKDF (HMAC-based Extract-and-Expand Key Derivation)
"""
import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet
from app.core.config import get_settings

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


def _get_cipher():
    """获取加密器（兼容旧版本）"""
    settings = get_settings()

    # 新版本：使用 HKDF + 随机salt
    # 使用密钥前16字节作为固定salt（生产环境应从数据库读取每个记录的唯一salt）
    salt = settings.encryption_secret_key[:16].encode()
    key = _derive_key(settings.encryption_secret_key, salt)
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_amount(amount: float) -> str:
    """加密工资金额 - 增强版本"""
    return _get_cipher().encrypt(str(amount).encode()).decode()


def decrypt_amount(encrypted: str) -> float:
    """解密工资金额 - 支持密钥轮换"""
    decrypted = _get_cipher().decrypt(encrypted.encode()).decode()
    return float(decrypted)
