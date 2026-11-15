import pytest

from taskapp.domain.errors import ValidationError
from taskapp.domain.user import User, check_password


def test_ac01_user_create_normalizes_the_email_and_keeps_the_name() -> None:
    user = User.create(email="  Alice@Example.COM ", name="Alice")

    assert user.email == "alice@example.com"
    assert user.name == "Alice"
    assert user.id is not None


@pytest.mark.parametrize(
    "email",
    ["", "no-at-sign", "a@", "@b.com", "two@@b.com", "has space@b.com", "a@b", "a" * 250 + "@b.co"],
)
def test_ac02_invalid_emails_are_rejected(email: str) -> None:
    with pytest.raises(ValidationError):
        User.create(email=email, name="Alice")


def test_ac02_an_email_of_254_characters_is_accepted() -> None:
    email = "a" * 242 + "@example.com"
    assert len(email) == 254

    assert User.create(email=email, name="Alice").email == email


@pytest.mark.parametrize("length", [1, 100])
def test_ac02_names_within_bounds_are_accepted(length: int) -> None:
    assert len(User.create(email="a@b.co", name="n" * length).name) == length


@pytest.mark.parametrize("name", ["", "   ", "n" * 101])
def test_ac02_names_outside_bounds_are_rejected(name: str) -> None:
    with pytest.raises(ValidationError):
        User.create(email="a@b.co", name=name)


@pytest.mark.parametrize("length", [8, 128])
def test_ac02_passwords_within_bounds_are_accepted(length: int) -> None:
    check_password("p" * length)


@pytest.mark.parametrize("length", [0, 7, 129])
def test_ac02_passwords_outside_bounds_are_rejected(length: int) -> None:
    with pytest.raises(ValidationError):
        check_password("p" * length)
