import pytest

from offer_codes.infrastructure.smtp_config import SmtpConfig, SmtpConfigError


def test_smtp_config_loads_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OFFER_CODES_SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("OFFER_CODES_SMTP_PORT", "587")
    monkeypatch.setenv("OFFER_CODES_SMTP_USERNAME", "brownidj@gmail.com")
    monkeypatch.setenv("OFFER_CODES_SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("OFFER_CODES_FROM_EMAIL", "brownidj@gmail.com")

    config = SmtpConfig.from_env()

    assert config == SmtpConfig(
        host="smtp.gmail.com",
        port=587,
        username="brownidj@gmail.com",
        password="app-password",
        from_email="brownidj@gmail.com",
    )


def test_smtp_config_requires_password(monkeypatch) -> None:
    monkeypatch.setenv("OFFER_CODES_SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("OFFER_CODES_SMTP_PORT", "587")
    monkeypatch.setenv("OFFER_CODES_SMTP_USERNAME", "brownidj@gmail.com")
    monkeypatch.delenv("OFFER_CODES_SMTP_PASSWORD", raising=False)
    monkeypatch.setenv("OFFER_CODES_FROM_EMAIL", "brownidj@gmail.com")

    with pytest.raises(SmtpConfigError, match="password"):
        SmtpConfig.from_env()
