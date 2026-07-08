"""Composition root for the Tkinter offer code app."""

from pathlib import Path

from offer_codes.application.clock import DateProvider
from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.infrastructure.offer_code_yaml_repository import OfferCodeYamlRepository
from offer_codes.ui.message_effects import MessageEffects
from offer_codes.ui.offer_code_controller import OfferCodeController
from offer_codes.ui.tkinter_app import OfferCodeTkinterApp


def run() -> None:
    root_dir = Path(__file__).resolve().parents[2]
    repository = OfferCodeYamlRepository(root_dir / "data" / "offer-codes.yaml")
    service = OfferCodeService(repository=repository, date_provider=DateProvider())
    controller = OfferCodeController(service=service, effects=MessageEffects())
    OfferCodeTkinterApp(controller=controller).run()
