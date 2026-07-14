import threading

from offer_codes.application.email_sender import EmailRequest
from offer_codes.application.android_closed_test_email_template import ANDROID_CLOSED_TEST_BODY_TEMPLATE
from offer_codes.application.offer_code_email_service import OfferCodeEmailService
from offer_codes.application.offer_code_email_template import OFFER_CODE_BODY_TEMPLATE


class FakeSender:
    def __init__(self) -> None:
        self.requests: list[EmailRequest] = []

    def send(self, request: EmailRequest, cancel_event: threading.Event | None = None) -> None:
        self.requests.append(request)


def test_offer_code_email_service_builds_offer_code_email() -> None:
    sender = FakeSender()
    service = OfferCodeEmailService(sender)

    service.send_offer_code("person@example.com", "CODE-123")

    assert sender.requests == [
        EmailRequest(
            to_email="person@example.com",
            subject="Your Sudoku offer code",
            body=OFFER_CODE_BODY_TEMPLATE.format(offer_number="CODE-123"),
        )
    ]


def test_offer_code_email_service_builds_android_closed_test_email() -> None:
    sender = FakeSender()
    service = OfferCodeEmailService(sender)

    service.send_android_closed_test_email("person@example.com")

    assert sender.requests == [
        EmailRequest(
            to_email="person@example.com",
            subject="Welcome to the SudoKu Fresh Closed Test Program",
            body=ANDROID_CLOSED_TEST_BODY_TEMPLATE,
        )
    ]
