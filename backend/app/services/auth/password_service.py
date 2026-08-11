from pwdlib import PasswordHash


class PasswordService:
    """Service responsible for password hashing and verification."""

    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password using Argon2id.

        Args:
            password: Plain text password.

        Returns:
            The hashed password.
        """
        return self._password_hash.hash(password)

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """
        Verify a plain password against its hash.

        Args:
            plain_password: Password provided by the user.
            hashed_password: Stored password hash.

        Returns:
            True if the password matches, otherwise False.
        """
        return self._password_hash.verify(
            plain_password,
            hashed_password,
        )
