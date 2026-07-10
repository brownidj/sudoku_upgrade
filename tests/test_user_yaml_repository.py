from offer_codes.domain.user import UserCredential
from offer_codes.infrastructure.user_yaml_repository import UserYamlRepository


def test_user_yaml_repository_loads_users(tmp_path) -> None:
    path = tmp_path / "users.yaml"
    path.write_text(
        "\n".join(
            [
                '- user: "Teruko"',
                '  password: "okuret"',
                '- user: "Mihoko"',
                '  password: "okohim"',
            ]
        ),
        encoding="utf-8",
    )

    users = UserYamlRepository(path).load_all()

    assert users == [
        UserCredential("Teruko", "okuret"),
        UserCredential("Mihoko", "okohim"),
    ]
