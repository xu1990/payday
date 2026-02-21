"""
Phone number masking utility for display purposes
"""
from typing import Optional


def mask_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Mask phone number for display (e.g., 138****8000)

    Args:
        phone: Original phone number string

    Returns:
        Masked phone number or None if input is None
        Returns empty string if input is empty string
    """
    if phone is None:
        return None

    if phone == "":
        return ""

    if len(phone) < 7:
        # Too short to mask properly, return as-is
        return phone

    # Keep first 3 and last 4 digits
    return f"{phone[:3]}****{phone[-4:]}"
