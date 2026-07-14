"""Application service for offer-code emails."""

import threading

from offer_codes.application.android_closed_test_email_template import ANDROID_CLOSED_TEST_BODY_TEMPLATE
from offer_codes.application.email_sender import EmailRequest, EmailSender
from offer_codes.application.offer_code_email_template import OFFER_CODE_BODY_TEMPLATE


class OfferCodeEmailService:
    def __init__(self, sender: EmailSender) -> None:
        self._sender = sender

    def send_offer_code(self, to_email: str, offer_number: str, cancel_event: threading.Event | None = None) -> None:
        self._sender.send(
            EmailRequest(
                to_email=to_email.strip(),
                subject="Your Sudoku offer code",
                body=self._build_body(offer_number),
            ),
            cancel_event,
        )

    def send_android_closed_test_email(self, to_email: str, cancel_event: threading.Event | None = None) -> None:
        self._sender.send(
            EmailRequest(
                to_email=to_email.strip(),
                subject="Welcome to the SudoKu Fresh Closed Test Program",
                body=ANDROID_CLOSED_TEST_BODY_TEMPLATE,
            ),
            cancel_event,
        )

    def _build_body(self, offer_number: str) -> str:
        return OFFER_CODE_BODY_TEMPLATE.format(offer_number=offer_number)

    def cancel_active_send(self) -> None:
        cancel = getattr(self._sender, "cancel_active_send", None)
        if callable(cancel):
            cancel()
