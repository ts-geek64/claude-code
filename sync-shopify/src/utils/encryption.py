"""Encryption utilities for token handling."""

import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config.settings import settings


logger = logging.getLogger(__name__)


class EncryptionService:
    """Handle encryption and decryption of sensitive data."""

    def __init__(self):
        """Initialize service."""
        self._cipher: Optional[Fernet] = None

    @property
    def cipher(self) -> Fernet:
        """Lazy-loaded Fernet cipher."""
        if self._cipher is None:
            if not settings.FERNET_KEY:
                logger.error("FERNET_KEY is not set")
                raise ValueError("FERNET_KEY is required for encryption operations")
            try:
                self._cipher = Fernet(settings.FERNET_KEY.encode())
            except Exception as e:
                logger.error(f"Invalid Fernet key format: {str(e)}")
                raise ValueError(f"Invalid FERNET_KEY format: {str(e)}")
        return self._cipher

    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt access token.

        Args:
            encrypted_token: Encrypted token string

        Returns:
            Decrypted token or None if decryption fails
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except (InvalidToken, ValueError) as e:
            logger.error(f"Decryption failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during decryption: {str(e)}")
            return None

    def encrypt_token(self, token: str) -> Optional[str]:
        """
        Encrypt access token.

        Args:
            token: Plain token string

        Returns:
            Encrypted token or None if encryption fails
        """
        try:
            encrypted = self.cipher.encrypt(token.encode())
            return encrypted.decode()
        except ValueError as e:
            logger.error(f"Encryption failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during encryption: {str(e)}")
            return None


# Global encryption service instance
encryption_service = EncryptionService()
