"""
工资金额加密 - 技术方案 2.2.3
"""
import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import get_settings


def _get_cipher():
    settings = get_settings()
    key = hashlib.sha256(settings.encryption_secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_amount(amount: float) -> str:
    """加密工资金额"""
    return _get_cipher().encrypt(str(amount).encode()).decode()


def decrypt_amount(encrypted: str) -> float:
    """解密工资金额"""
    decrypted = _get_cipher().decrypt(encrypted.encode()).decode()
    return float(decrypted)
