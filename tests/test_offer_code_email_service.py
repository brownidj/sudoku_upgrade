from offer_codes.application.email_sender import EmailRequest
from offer_codes.application.offer_code_email_service import OfferCodeEmailService


class FakeSender:
    def __init__(self) -> None:
        self.requests: list[EmailRequest] = []

    def send(self, request: EmailRequest) -> None:
        self.requests.append(request)


def test_offer_code_email_service_builds_offer_code_email() -> None:
    sender = FakeSender()
    service = OfferCodeEmailService(sender)

    service.send_offer_code("person@example.com", "CODE-123")

    assert sender.requests == [
        EmailRequest(
            to_email="person@example.com",
            subject="Your Sudoku offer code",
            body="Hello,\n\nYour Sudoku offer code is: CODE-123\n\nRegards,\nSudoku",
        )
    ]
