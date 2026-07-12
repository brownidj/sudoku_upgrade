"""Composition root for the Tkinter offer code app."""

from pathlib import Path

from offer_codes.application.auth_service import AuthService
from offer_codes.application.clock import DateProvider
from offer_codes.application.offer_code_email_service import OfferCodeEmailService
from offer_codes.application.offer_code_service import OfferCodeService
from offer_codes.infrastructure.env_loader import EnvLoader
from offer_codes.infrastructure.offer_code_yaml_repository import OfferCodeYamlRepository
from offer_codes.infrastructure.smtp_config import SmtpConfig
from offer_codes.infrastructure.smtp_email_sender import SmtpEmailSender
from offer_codes.infrastructure.user_scoped_offer_code_repository import UserScopedOfferCodeRepository
from offer_codes.infrastructure.user_yaml_repository import UserYamlRepository
from offer_codes.ui.message_effects import MessageEffects
from offer_codes.ui.offer_code_controller import OfferCodeController
from offer_codes.ui.tkinter_app import OfferCodeTkinterApp


def run() -> None:
    root_dir = Path(__file__).resolve().parents[2]
    EnvLoader().load(root_dir / ".env")
    repository = OfferCodeYamlRepository(root_dir / "data" / "offer-codes.yaml")
    user_repository = UserYamlRepository(root_dir / "data" / "users.yaml")
    auth_service = AuthService(repository=user_repository)
    email_service = OfferCodeEmailService(sender=SmtpEmailSender(SmtpConfig.from_env()))
    effects = MessageEffects()

    def controller_factory(user: str) -> OfferCodeController:
        scoped_repository = UserScopedOfferCodeRepository(repository=repository, user=user)
        service = OfferCodeService(repository=scoped_repository, date_provider=DateProvider())
        return OfferCodeController(service=service, email_service=email_service, effects=effects)

    OfferCodeTkinterApp(controller_factory=controller_factory, auth_service=auth_service).run()
