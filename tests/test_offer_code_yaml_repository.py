from offer_codes.domain.models import OfferCodeRecord
from offer_codes.infrastructure.offer_code_yaml_repository import OfferCodeYamlRepository


def test_yaml_repository_round_trips_offer_code_records(tmp_path) -> None:
    path = tmp_path / "offer-codes.yaml"
    repository = OfferCodeYamlRepository(path)
    records = [
        OfferCodeRecord("U3A-001", "person@example.com", "CODE-1", "2026-07-09", "Ada", "Lovelace"),
        OfferCodeRecord("", "", "CODE-2", ""),
    ]

    repository.save_all(records)

    assert repository.load_all() == records
