from offer_codes.domain.models import AndroidTesterRecord
from offer_codes.infrastructure.android_tester_yaml_repository import AndroidTesterYamlRepository


def test_android_tester_yaml_repository_round_trips_records(tmp_path) -> None:
    path = tmp_path / "android-testers.yaml"
    repository = AndroidTesterYamlRepository(path)
    records = [
        AndroidTesterRecord("U3A-001", "person@example.com", "Ada", "Lovelace", "Android", "2026-07-10"),
        AndroidTesterRecord("", "", "", "", "Android", ""),
    ]

    repository.save_all(records)

    assert repository.load_all() == records
