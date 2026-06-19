from app.models.enums import StatusEnum
from app.models.user import User


def test_user_and_trainer_model_instantiation():
    user = User(
        name="john Doe",
        email="john@doe.com",
        username="johndoe",
        status=StatusEnum.ACTIVE,
        password="secret",
    )

    assert user.name == "john Doe"
    assert user.email == "john@doe.com"
    assert user.username == "johndoe"
    assert user.status == StatusEnum.ACTIVE
    assert user.created_at is not None
