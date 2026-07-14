"""SMTP email sender implementation."""

import smtplib
import threading
from email.message import EmailMessage

from offer_codes.application.email_sender import EmailCancelledError, EmailRequest, EmailSendError
from offer_codes.infrastructure.smtp_config import SmtpConfig


class SmtpEmailSender:
    def __init__(self, config: SmtpConfig) -> None:
        self._config = config
        self._active_smtp: smtplib.SMTP | None = None
        self._lock = threading.Lock()

    def send(self, request: EmailRequest, cancel_event: threading.Event | None = None) -> None:
        message = EmailMessage()
        message["From"] = self._config.from_email
        message["To"] = request.to_email
        message["Subject"] = request.subject
        message.set_content(request.body)
        try:
            self._raise_if_cancelled(cancel_event)
            with smtplib.SMTP(self._config.host, self._config.port, timeout=30) as smtp:
                self._set_active_smtp(smtp)
                self._raise_if_cancelled(cancel_event)
                smtp.starttls()
                self._raise_if_cancelled(cancel_event)
                smtp.login(self._config.username, self._config.password)
                self._raise_if_cancelled(cancel_event)
                smtp.send_message(message)
        except EmailCancelledError:
            raise
        except (OSError, smtplib.SMTPException) as exc:
            if cancel_event is not None and cancel_event.is_set():
                raise EmailCancelledError("Email sending was cancelled.") from exc
            raise EmailSendError("The offer-code email could not be sent.") from exc
        finally:
            self._set_active_smtp(None)

    def cancel_active_send(self) -> None:
        with self._lock:
            if self._active_smtp is not None:
                try:
                    self._active_smtp.close()
                except OSError:
                    pass

    def _raise_if_cancelled(self, cancel_event: threading.Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise EmailCancelledError("Email sending was cancelled.")

    def _set_active_smtp(self, smtp: smtplib.SMTP | None) -> None:
        with self._lock:
            self._active_smtp = smtp
