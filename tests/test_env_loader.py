import os

from offer_codes.infrastructure.env_loader import EnvLoader


def test_env_loader_loads_dotenv_values(tmp_path, monkeypatch) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "\n".join(
            [
                "OFFER_CODES_SMTP_HOST=smtp.gmail.com",
                'OFFER_CODES_SMTP_USERNAME="brownidj@gmail.com"',
                "OFFER_CODES_SMTP_PASSWORD='app-password'",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("OFFER_CODES_SMTP_HOST", raising=False)
    monkeypatch.delenv("OFFER_CODES_SMTP_USERNAME", raising=False)
    monkeypatch.delenv("OFFER_CODES_SMTP_PASSWORD", raising=False)

    EnvLoader().load(path)

    assert os.environ["OFFER_CODES_SMTP_HOST"] == "smtp.gmail.com"
    assert os.environ["OFFER_CODES_SMTP_USERNAME"] == "brownidj@gmail.com"
    assert os.environ["OFFER_CODES_SMTP_PASSWORD"] == "app-password"
