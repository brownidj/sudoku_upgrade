from offer_codes.domain.models import OfferCodeRecord
from offer_codes.infrastructure.offer_code_yaml_repository import OfferCodeYamlError, OfferCodeYamlRepository


def test_yaml_repository_round_trips_offer_code_records(tmp_path) -> None:
    path = tmp_path / "offer-codes.yaml"
    repository = OfferCodeYamlRepository(path)
    records = [
        OfferCodeRecord("U3A-001", "person@example.com", "CODE-1", "2026-07-09", "Ada", "Lovelace", "Android"),
        OfferCodeRecord("", "", "CODE-2", ""),
    ]

    repository.save_all(records)

    assert repository.load_all() == records


def test_yaml_repository_rejects_invalid_device_type(tmp_path) -> None:
    path = tmp_path / "offer-codes.yaml"
    path.write_text(
        "\n".join(
            [
                '- U3A_number: ""',
                '  email: ""',
                '  offer_number: "CODE-1"',
                '  first_name: ""',
                '  last_name: ""',
                '  device_type: "Windows"',
                '  issued: ""',
            ]
        ),
        encoding="utf-8",
    )

    try:
        OfferCodeYamlRepository(path).load_all()
    except OfferCodeYamlError as exc:
        assert "Android or iPhone" in str(exc)
    else:
        raise AssertionError("Expected invalid device type to be rejected.")
