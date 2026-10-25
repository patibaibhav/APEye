"""Admin user creation script (Owner: Anvi).

Creates or resets an initial ADMIN user in the database.
Reads ADMIN_USERNAME and ADMIN_PASSWORD from environment variables or CLI arguments.
"""

import argparse
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.auth.security import hash_password  # noqa: E402
from app.db.repositories import user_repository  # noqa: E402
from app.db.session import session_scope  # noqa: E402


def create_or_update_admin(username: str, password: str) -> None:
    """Creates a new admin user or updates existing user to active ADMIN."""
    if not username:
        raise ValueError("Username cannot be empty")
    if not password:
        raise ValueError("Password cannot be empty")

    pwd_hash = hash_password(password)

    with session_scope() as session:
        existing = user_repository.get_user_by_username(session, username)
        if existing:
            existing.password_hash = pwd_hash
            existing.role = "ADMIN"
            existing.is_active = True
            session.flush()
            print(f"[OK] Admin user '{username}' already exists. Password and role updated.")
        else:
            user_repository.create_user(
                session=session,
                username=username,
                password_hash=pwd_hash,
                role="ADMIN",
            )
            print(f"[OK] Admin user '{username}' successfully created.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset initial APEye ADMIN user.")
    parser.add_argument(
        "--username",
        default=os.getenv("ADMIN_USERNAME", "admin"),
        help="Admin username (default: env ADMIN_USERNAME or 'admin')",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("ADMIN_PASSWORD"),
        help="Admin password (default: env ADMIN_PASSWORD)",
    )

    args = parser.parse_args()

    password = args.password
    if not password:
        password = os.getenv("ADMIN_PASSWORD")

    if not password:
        import getpass
        try:
            password = getpass.getpass("Enter password for admin user: ")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)

    if not password:
        print("[ERROR] Password is required.")
        sys.exit(1)

    try:
        create_or_update_admin(args.username, password)
    except Exception as e:
        print(f"[ERROR] Failed to create admin user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
