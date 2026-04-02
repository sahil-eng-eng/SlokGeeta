"""CLI script to promote a user to superadmin by email.

Usage:
    python -m app.cli.make_superadmin user@example.com
"""

import asyncio
import sys

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.constants.enums import UserRole


async def make_superadmin(email: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Error: No user found with email '{email}'")
            sys.exit(1)

        if user.role == UserRole.SUPERADMIN.value:
            print(f"User '{email}' is already a superadmin.")
            return

        await session.execute(
            update(User).where(User.id == user.id).values(role=UserRole.SUPERADMIN.value)
        )
        await session.commit()
        print(f"User '{email}' has been promoted to superadmin.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli.make_superadmin <email>")
        sys.exit(1)
    asyncio.run(make_superadmin(sys.argv[1]))


if __name__ == "__main__":
    main()
