"""加密工具测试"""
import pytest
import base64

from app.utils.encryption import (
    encrypt_amount,
    decrypt_amount,
    _generate_salt,
    _derive_key,
    _get_cipher,
)


class TestGenerateSalt:
    """测试salt生成"""

    def test_generate_salt_length(self):
        """测试生成32字节salt"""
        salt = _generate_salt()
        assert len(salt) == 32

    def test_generate_salt_randomness(self):
        """测试每次生成不同的salt"""
        salt1 = _generate_salt()
        salt2 = _generate_salt()
        assert salt1 != salt2

    def test_generate_salt_bytes(self):
        """测试生成字节类型"""
        salt = _generate_salt()
        assert isinstance(salt, bytes)


class TestDeriveKey:
    """测试密钥派生"""

    def test_derive_key_same_input_same_output(self):
        """测试相同输入产生相同密钥"""
        salt = b"test_salt"
        key1 = _derive_key("test_secret", salt)
        key2 = _derive_key("test_secret", salt)
        assert key1 == key2

    def test_derive_key_different_secret(self):
        """测试不同密钥产生不同结果"""
        salt = b"test_salt"
        key1 = _derive_key("secret1", salt)
        key2 = _derive_key("secret2", salt)
        assert key1 != key2

    def test_derive_key_different_salt(self):
        """测试不同salt产生不同结果"""
        key1 = _derive_key("test_secret", b"salt1")
        key2 = _derive_key("test_secret", b"salt2")
        assert key1 != key2

    def test_derive_key_length(self):
        """测试派生密钥长度为32字节"""
        salt = b"test_salt"
        key = _derive_key("test_secret", salt)
        assert len(key) == 32


class TestGetCipher:
    """测试获取加密器"""

    def test_get_cipher_returns_fernet(self):
        """测试返回Fernet实例"""
        from cryptography.fernet import Fernet

        salt = b"test_salt_32_bytes_____________"
        cipher = _get_cipher(salt)
        assert isinstance(cipher, Fernet)

    def test_get_cipher_same_salt_same_key(self):
        """测试相同salt产生相同密钥"""
        salt = b"test_salt_32_bytes_____________"
        cipher1 = _get_cipher(salt)
        cipher2 = _get_cipher(salt)
        # 相同的salt应该产生相同的Fernet实例（密钥相同）
        assert cipher1._signing_key == cipher2._signing_key


class TestEncryptAmount:
    """测试金额加密"""

    def test_encrypt_integer_amount(self):
        """测试加密整数金额"""
        encrypted, salt = encrypt_amount(10000)

        assert encrypted is not None
        assert salt is not None
        assert isinstance(encrypted, str)
        assert isinstance(salt, str)
        assert len(encrypted) > 0
        assert len(salt) > 0

    def test_encrypt_float_amount(self):
        """测试加密浮点数金额"""
        encrypted, salt = encrypt_amount(10000.50)

        assert encrypted is not None
        assert salt is not None

    def test_encrypt_zero_amount(self):
        """测试加密0金额"""
        encrypted, salt = encrypt_amount(0)

        assert encrypted is not None
        assert salt is not None

    def test_encrypt_negative_amount(self):
        """测试加密负数金额"""
        encrypted, salt = encrypt_amount(-5000)

        assert encrypted is not None
        assert salt is not None

    def test_encrypt_large_amount(self):
        """测试加密大额金额"""
        encrypted, salt = encrypt_amount(999999.99)

        assert encrypted is not None
        assert salt is not None

    def test_encrypt_different_amounts_different_cipher(self):
        """测试不同金额产生不同密文（因为salt不同）"""
        encrypted1, salt1 = encrypt_amount(10000)
        encrypted2, salt2 = encrypt_amount(10000)

        # 相同金额，不同salt，密文应该不同
        assert encrypted1 != encrypted2
        assert salt1 != salt2

    def test_encrypt_salt_is_base64(self):
        """测试salt是有效的base64编码"""
        encrypted, salt = encrypt_amount(10000)

        # 应该能够解码base64
        try:
            decoded = base64.urlsafe_b64decode(salt)
            assert len(decoded) == 32  # salt应该是32字节
        except Exception:
            pytest.fail("Salt should be valid base64")


class TestDecryptAmount:
    """测试金额解密"""

    def test_decrypt_integer_amount(self):
        """测试解密整数金额"""
        original = 10000
        encrypted, salt = encrypt_amount(original)

        decrypted = decrypt_amount(encrypted, salt)

        assert decrypted == original

    def test_decrypt_float_amount(self):
        """测试解密浮点数金额"""
        original = 10000.50
        encrypted, salt = encrypt_amount(original)

        decrypted = decrypt_amount(encrypted, salt)

        assert decrypted == original

    def test_decrypt_zero_amount(self):
        """测试解密0金额"""
        original = 0
        encrypted, salt = encrypt_amount(original)

        decrypted = decrypt_amount(encrypted, salt)

        assert decrypted == original

    def test_decrypt_negative_amount(self):
        """测试解密负数金额"""
        original = -5000
        encrypted, salt = encrypt_amount(original)

        decrypted = decrypt_amount(encrypted, salt)

        assert decrypted == original

    def test_decrypt_large_amount(self):
        """测试解密大额金额"""
        original = 999999.99
        encrypted, salt = encrypt_amount(original)

        decrypted = decrypt_amount(encrypted, salt)

        assert decrypted == original

    def test_decrypt_precision_preserved(self):
        """测试解密保持精度"""
        original = 12345.67
        encrypted, salt = encrypt_amount(original)

        decrypted = decrypt_amount(encrypted, salt)

        assert abs(decrypted - original) < 0.01

    def test_decrypt_wrong_salt_fails(self):
        """测试错误的salt导致解密失败"""
        original = 10000
        encrypted, salt = encrypt_amount(original)

        # 使用不同的salt
        wrong_salt = base64.urlsafe_b64encode(b"wrong_salt_32_bytes___________").decode()

        with pytest.raises(Exception):
            decrypt_amount(encrypted, wrong_salt)

    def test_decrypt_wrong_cipher_fails(self):
        """测试错误的密文导致解密失败"""
        original = 10000
        encrypted, salt = encrypt_amount(original)

        # 篡改密文
        wrong_cipher = encrypted[:-5] + "wrong"

        with pytest.raises(Exception):
            decrypt_amount(wrong_cipher, salt)

    def test_decrypt_empty_strings_fails(self):
        """测试空字符串解密失败"""
        with pytest.raises(Exception):
            decrypt_amount("", "")

    def test_roundtrip_multiple_amounts(self):
        """测试多个金额的加密解密往返"""
        amounts = [0, 1, 100, 1000.50, 10000, 99999.99, -5000]

        for amount in amounts:
            encrypted, salt = encrypt_amount(amount)
            decrypted = decrypt_amount(encrypted, salt)
            assert decrypted == amount, f"Failed for amount: {amount}"


class TestEncryptionDecryptionIntegration:
    """加密解密集成测试"""

    def test_full_cycle_multiple_times(self):
        """测试多次加密解密循环"""
        amounts = [5000, 8000, 12000, 15000.50]

        results = []
        for amount in amounts:
            encrypted, salt = encrypt_amount(amount)
            decrypted = decrypt_amount(encrypted, salt)
            results.append((amount, decrypted))

        for original, decrypted in results:
            assert original == decrypted

    def test_same_amount_different_salts_different_ciphers(self):
        """测试相同金额使用不同salt产生不同密文"""
        amount = 10000

        encrypted1, salt1 = encrypt_amount(amount)
        encrypted2, salt2 = encrypt_amount(amount)

        # 密文和salt都应该不同
        assert encrypted1 != encrypted2
        assert salt1 != salt2

        # 但都能正确解密
        assert decrypt_amount(encrypted1, salt1) == amount
        assert decrypt_amount(encrypted2, salt2) == amount
