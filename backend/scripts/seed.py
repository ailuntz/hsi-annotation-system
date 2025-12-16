#!/usr/bin/env python3
"""Seed the database with development data."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def seed_users() -> None:
    """Seed the database with test users."""
    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        if result.scalar_one_or_none():
            print("Admin user already exists, skipping seed")
            return

        # Create admin user
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
        )
        session.add(admin)

        # Create test user
        test_user = User(
            email="test@example.com",
            hashed_password=hash_password("test123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False,
        )
        session.add(test_user)

        await session.commit()
        print("Seed data created successfully")


async def main() -> None:
    """Main entry point."""
    await seed_users()


if __name__ == "__main__":
    asyncio.run(main())
