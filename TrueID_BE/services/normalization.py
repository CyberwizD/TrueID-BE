import re


def normalize_phone_number(phone_number: str, default_country_code: str = "234") -> str:
    digits = re.sub(r"\D", "", phone_number)
    if not digits:
        raise ValueError("Phone number must contain digits.")

    if digits.startswith(default_country_code):
        normalized_digits = digits
    elif digits.startswith("0"):
        normalized_digits = f"{default_country_code}{digits[1:]}"
    elif digits.startswith("00"):
        normalized_digits = digits[2:]
    else:
        normalized_digits = digits

    if len(normalized_digits) < 10 or len(normalized_digits) > 15:
        raise ValueError("Phone number must be between 10 and 15 digits after normalization.")

    return f"+{normalized_digits}"
