"""测试加密工具"""
import pytest
from app.utils.encryption import encrypt_amount, decrypt_amount


class TestEncryptAmount:
    """测试金额加密"""

    def test_encrypt_amount_returns_tuple(self):
        """测试加密返回元组"""
        result = encrypt_amount(10000)
        assert isinstance(result, tuple)
        assert len(result) == 2
        encrypted, salt = result
        assert isinstance(encrypted, str)  # 加密结果是base64字符串
        assert isinstance(salt, str)  # salt也是base64字符串

    def test_encrypt_amount_same_amount_different_result(self):
        """测试相同金额加密后结果不同（因为随机salt）"""
        result1 = encrypt_amount(10000)
        result2 = encrypt_amount(10000)
        assert result1[0] != result2[0]  # 加密结果不同
        assert result1[1] != result2[1]  # salt不同


class TestDecryptAmount:
    """测试金额解密"""

    def test_decrypt_amount_roundtrip(self):
        """测试加密解密往返"""
        original = 10000
        encrypted, salt = encrypt_amount(original)
        decrypted = decrypt_amount(encrypted, salt)
        assert decrypted == original

    def test_decrypt_amount_different_values(self):
        """测试不同金额的加密解密"""
        amounts = [0, 1, 100, 10000, 999999, 10000000]
        for amount in amounts:
            encrypted, salt = encrypt_amount(amount)
            decrypted = decrypt_amount(encrypted, salt)
            assert decrypted == amount

    def test_decrypt_amount_negative(self):
        """测试负数金额"""
        original = -5000
        encrypted, salt = encrypt_amount(original)
        decrypted = decrypt_amount(encrypted, salt)
        assert decrypted == original


class TestEdgeCases:
    """测试边界情况"""

    def test_zero_amount(self):
        """测试0金额"""
        encrypted, salt = encrypt_amount(0)
        decrypted = decrypt_amount(encrypted, salt)
        assert decrypted == 0

    def test_large_amount(self):
        """测试大金额"""
        original = 999999999
        encrypted, salt = encrypt_amount(original)
        decrypted = decrypt_amount(encrypted, salt)
        assert decrypted == original
