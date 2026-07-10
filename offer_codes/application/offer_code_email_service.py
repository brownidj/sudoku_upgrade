"""Application service for offer-code emails."""

from offer_codes.application.email_sender import EmailRequest, EmailSender


class OfferCodeEmailService:
    def __init__(self, sender: EmailSender) -> None:
        self._sender = sender

    def send_offer_code(self, to_email: str, offer_number: str) -> None:
        self._sender.send(
            EmailRequest(
                to_email=to_email.strip(),
                subject="Your Sudoku offer code",
                body=self._build_body(offer_number),
            )
        )

    def _build_body(self, offer_number: str) -> str:
        return "\n".join(
            [
                "Hello,",
                "",
                f"Your Sudoku offer code is: {offer_number}",
                "",
                "Regards,",
                "Sudoku",
            ]
        )
