"""Checks shared by the registration, profile, and account screens."""
import re

from common.exceptions import ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^\+?\d{9,15}$")
STUDENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
NAME_PATTERN = re.compile(r"^[^<>]+$")
MAX_PASSWORD_BYTES = 72  # bcrypt silently cuts longer input


def clean_text(value: str | None, label: str, max_length: int) -> str:
    text = (value or "").strip()
    if not text:
        raise ValidationError(f"{label} is required.", label.lower())
    if len(text) > max_length:
        raise ValidationError(
            f"{label} must be at most {max_length} characters.", label.lower())
    return text


def validate_full_name(value: str | None) -> str:
    name = clean_text(value, "Full name", 100)
    if len(name) < 2:
        raise ValidationError("Full name must have at least 2 characters.")
    if not NAME_PATTERN.match(name):
        raise ValidationError(
            "Full name contains characters that are not allowed.")
    return name


def validate_email(value: str | None) -> str:
    email = clean_text(value, "Email", 100).lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError(
            "Enter a valid email address, for example name@example.com.")
    return email


def validate_phone(value: str | None) -> str:
    phone = clean_text(value, "Phone number", 15).replace(" ", "")
    if not PHONE_PATTERN.match(phone):
        raise ValidationError("Phone number must have 9 to 15 digits.")
    return phone


def validate_student_id(value: str | None) -> str:
    student_id = clean_text(value, "Student/Staff ID", 30)
    if not STUDENT_ID_PATTERN.match(student_id):
        raise ValidationError(
            "Student/Staff ID must have 3 to 30 letters, digits, dots, "
            "or dashes.")
    return student_id


def validate_password(value: str | None, label: str = "Password") -> str:
    password = value or ""
    if len(password) < 8:
        raise ValidationError(f"{label} must have at least 8 characters.")
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValidationError(f"{label} is too long.")
    if not any(c.isalpha() for c in password):
        raise ValidationError(f"{label} must contain at least one letter.")
    if not any(c.isdigit() for c in password):
        raise ValidationError(f"{label} must contain at least one digit.")
    return password


def validate_password_confirmation(password: str,
                                   confirmation: str | None) -> None:
    if password != (confirmation or ""):
        raise ValidationError("The two passwords do not match.")


def validate_positive_int(value: str | int | None, label: str,
                          maximum: int = 1_000_000) -> int:
    text = str(value or "").strip()
    if not text.isdigit():
        raise ValidationError(f"{label} must be a whole number.")
    number = int(text)
    if number < 1 or number > maximum:
        raise ValidationError(
            f"{label} must be between 1 and {maximum:,}.")
    return number
