from uuid import uuid4

import pytest

from taskapp.application.authenticate_user import AuthenticateUser
from taskapp.application.login_user import LoginUser
from taskapp.application.register_user import RegisterUser
from taskapp.domain.errors import EmailTaken, InvalidCredentials, InvalidToken, ValidationError
from tests.fakes import (
    FakePasswordHasher,
    FakeTokenService,
    InMemoryTaskRepository,
    InMemoryUnitOfWork,
    InMemoryUserRepository,
)


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def auth_uow(users: InMemoryUserRepository) -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork(InMemoryTaskRepository(), users)


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


async def test_ac01_register_stores_a_hash_and_never_the_password(
    auth_uow: InMemoryUnitOfWork, users: InMemoryUserRepository, hasher: FakePasswordHasher
) -> None:
    user = await RegisterUser(auth_uow, hasher).execute(
        email=" Alice@Example.com ", name="Alice", password="s3cret-pass"
    )

    assert (user.email, user.name) == ("alice@example.com", "Alice")
    assert users.all() == [user]
    stored = users.stored_hash(user.id)
    assert stored is not None
    assert stored != "s3cret-pass"
    assert auth_uow.commits == 1


@pytest.mark.parametrize(
    ("email", "name", "password"),
    [
        ("not-an-email", "Alice", "s3cret-pass"),
        ("alice@example.com", "", "s3cret-pass"),
        ("alice@example.com", "Alice", "short"),
    ],
)
async def test_ac02_register_with_invalid_input_stores_nothing(
    auth_uow: InMemoryUnitOfWork,
    users: InMemoryUserRepository,
    hasher: FakePasswordHasher,
    email: str,
    name: str,
    password: str,
) -> None:
    with pytest.raises(ValidationError):
        await RegisterUser(auth_uow, hasher).execute(email=email, name=name, password=password)

    assert users.all() == []
    assert auth_uow.commits == 0


async def test_ac02_register_rejects_a_duplicate_email_in_any_case_and_keeps_the_original(
    auth_uow: InMemoryUnitOfWork, users: InMemoryUserRepository, hasher: FakePasswordHasher
) -> None:
    first = await RegisterUser(auth_uow, hasher).execute(
        email="alice@example.com", name="Alice", password="s3cret-pass"
    )

    with pytest.raises(EmailTaken):
        await RegisterUser(auth_uow, hasher).execute(
            email="ALICE@example.com", name="Impostor", password="another-pass"
        )

    assert users.all() == [first]
    assert users.stored_hash(first.id) == "hashed:s3cret-pass"
    assert auth_uow.commits == 1


async def register_alice(uow: InMemoryUnitOfWork, hasher: FakePasswordHasher) -> None:
    await RegisterUser(uow, hasher).execute(
        email="alice@example.com", name="Alice", password="s3cret-pass"
    )


async def test_ac03_login_returns_a_token_for_the_user_matching_email_in_any_case(
    auth_uow: InMemoryUnitOfWork, hasher: FakePasswordHasher
) -> None:
    await register_alice(auth_uow, hasher)
    tokens = FakeTokenService()

    token = await LoginUser(auth_uow, hasher, tokens).execute(
        email="  ALICE@example.com ", password="s3cret-pass"
    )

    assert token.expires_in == 1800
    user = await AuthenticateUser(auth_uow, tokens).execute(token.token)
    assert user.email == "alice@example.com"


async def test_ac04_unknown_email_and_wrong_password_fail_identically(
    auth_uow: InMemoryUnitOfWork, hasher: FakePasswordHasher
) -> None:
    await register_alice(auth_uow, hasher)
    login = LoginUser(auth_uow, hasher, FakeTokenService())

    with pytest.raises(InvalidCredentials) as unknown:
        await login.execute(email="nobody@example.com", password="s3cret-pass")
    with pytest.raises(InvalidCredentials) as wrong:
        await login.execute(email="alice@example.com", password="wrong-password")

    assert str(unknown.value) == str(wrong.value)


async def test_ac04_an_unknown_email_still_costs_a_password_hash(
    auth_uow: InMemoryUnitOfWork, hasher: FakePasswordHasher
) -> None:
    await register_alice(auth_uow, hasher)
    hashes_before = hasher.hash_calls

    with pytest.raises(InvalidCredentials):
        await LoginUser(auth_uow, hasher, FakeTokenService()).execute(
            email="nobody@example.com", password="s3cret-pass"
        )

    assert hasher.hash_calls == hashes_before + 1


async def test_ac05_an_untrusted_token_is_rejected(auth_uow: InMemoryUnitOfWork) -> None:
    with pytest.raises(InvalidToken):
        await AuthenticateUser(auth_uow, FakeTokenService()).execute("garbage")


async def test_ac05_a_token_for_a_user_that_no_longer_exists_is_rejected(
    auth_uow: InMemoryUnitOfWork, users: InMemoryUserRepository, hasher: FakePasswordHasher
) -> None:
    tokens = FakeTokenService()
    ghost = (await tokens.issue(uuid4())).token

    with pytest.raises(InvalidToken):
        await AuthenticateUser(auth_uow, tokens).execute(ghost)


async def test_ac04_an_oversized_password_is_refused_without_hashing_it(
    auth_uow: InMemoryUnitOfWork, hasher: FakePasswordHasher
) -> None:
    await register_alice(auth_uow, hasher)
    hashes_before = (hasher.hash_calls, hasher.verify_calls)

    with pytest.raises(InvalidCredentials):
        await LoginUser(auth_uow, hasher, FakeTokenService()).execute(
            email="alice@example.com", password="p" * 129
        )

    assert (hasher.hash_calls, hasher.verify_calls) == hashes_before
