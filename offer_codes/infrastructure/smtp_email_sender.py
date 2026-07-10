"""SMTP email sender implementation."""

import smtplib
from email.message import EmailMessage

from offer_codes.application.email_sender import EmailRequest, EmailSendError
from offer_codes.infrastructure.smtp_config import SmtpConfig


class SmtpEmailSender:
    def __init__(self, config: SmtpConfig) -> None:
        self._config = config

    def send(self, request: EmailRequest) -> None:
        message = EmailMessage()
        message["From"] = self._config.from_email
        message["To"] = request.to_email
        message["Subject"] = request.subject
        message.set_content(request.body)
        try:
            with smtplib.SMTP(self._config.host, self._config.port, timeout=30) as smtp:
                smtp.starttls()
                smtp.login(self._config.username, self._config.password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailSendError("The offer-code email could not be sent.") from exc
