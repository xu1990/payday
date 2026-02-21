"""
Test phone number encryption and masking utilities
"""
import pytest
from app.utils.encryption import encrypt_amount, decrypt_amount


def test_encrypt_phone_number():
    """Test encrypting a phone number using existing encryption service"""
    phone = "13800138000"
    # Reuse salary encryption for phone numbers
    encrypted, salt = encrypt_amount(phone)
    assert encrypted != phone
    assert len(encrypted) > 0
    assert len(salt) > 0
    assert isinstance(encrypted, str)
    assert isinstance(salt, str)


def test_decrypt_phone_number():
    """Test decrypting a phone number"""
    phone = "13800138000"
    encrypted, salt = encrypt_amount(phone)
    decrypted = decrypt_amount(encrypted, salt)
    # Note: encrypt_amount/decrypt_amount work with floats, so convert to string and remove decimal
    assert str(int(decrypted)) == phone


def test_mask_phone_number():
    """Test masking phone number for display"""
    from app.utils.phone import mask_phone_number

    # Standard 11-digit Chinese phone number
    assert mask_phone_number("13800138000") == "138****8000"
    assert mask_phone_number("15912345678") == "159****5678"

    # None input
    assert mask_phone_number(None) is None

    # Empty string
    assert mask_phone_number("") == ""


def test_different_phones_encrypt_differently():
    """Test that different phones produce different ciphertext (due to random salt)"""
    phone1 = "13800138000"
    phone2 = "13900139000"
    enc1, salt1 = encrypt_amount(phone1)
    enc2, salt2 = encrypt_amount(phone2)
    # Different phone numbers should produce different encrypted values
    assert enc1 != enc2


def test_same_phone_encrypts_differently_each_time():
    """Test that same phone produces different ciphertext (due to random salt)"""
    phone = "13800138000"
    enc1, salt1 = encrypt_amount(phone)
    enc2, salt2 = encrypt_amount(phone)
    # Same value encrypted twice should produce different ciphertext (different salts)
    assert enc1 != enc2
    assert salt1 != salt2
    # But both should decrypt correctly
    assert decrypt_amount(enc1, salt1) == float(phone)
    assert decrypt_amount(enc2, salt2) == float(phone)


def test_mask_phone_number_short():
    """Test masking short phone numbers"""
    from app.utils.phone import mask_phone_number

    # Too short to mask properly - should return as-is
    assert mask_phone_number("12345") == "12345"
    assert mask_phone_number("123456") == "123456"
    # 7 digits is the minimum for masking (3 + 4)
    assert mask_phone_number("1234567") == "123****4567"


def test_mask_phone_number_with_plus():
    """Test masking phone number with country code prefix"""
    from app.utils.phone import mask_phone_number

    # With country code
    assert mask_phone_number("+8613800138000") == "+86****8000"


def test_roundtrip_various_phone_formats():
    """Test encryption/decryption roundtrip for various phone formats"""
    test_phones = [
        "13800138000",  # Standard Chinese mobile
        "15912345678",  # Another Chinese mobile
        "10000000000",  # Edge case
        "99999999999",  # Edge case
    ]

    for phone in test_phones:
        encrypted, salt = encrypt_amount(phone)
        decrypted = decrypt_amount(encrypted, salt)
        # Convert to int to remove decimal, then to string for comparison
        assert str(int(decrypted)) == phone, f"Failed for phone: {phone}"
