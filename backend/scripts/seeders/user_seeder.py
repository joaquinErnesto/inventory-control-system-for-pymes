from sqlalchemy.orm import Session

from app.schemas.core import UserRole

from app.models.core import User
from app.security import get_password_hash

from scripts.seeders.utils import (
    already_exists,
    print_created,
    print_exists,
    print_section,
    save,
)


def seed_users(db: Session) -> None:
    """
    Seed the initial application users.

    This function is safe to execute multiple times.
    Existing users are not duplicated.
    """

    print_section("Users")

    users = [
        {
            "username": "admin_user2",
            "password": "admin1234",
            "role": "admin",
        },
        {
            "username": "employee2",
            "password": "employee1234",
            "role": "employee",
        },
    ]

    for user_data in users:

        if already_exists(
            db,
            User,
            username=user_data["username"],
        ):
            print_exists(
                f"User '{user_data['username']}' already exists."
            )
            continue

        user = User(
            username=user_data["username"],
            password_hash=get_password_hash(
                user_data["password"]
            ),
            role=user_data["role"],
        )

        save(db, user)

        print_created(
            f"User '{user.username}' created successfully."
        )