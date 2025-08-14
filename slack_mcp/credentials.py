"""Secure credential management using macOS Keychain."""

import os
import sys
import logging
from typing import Optional, Dict, Any
import keyring
from keyring.errors import KeyringError
from typing import List

logger = logging.getLogger(__name__)

# Service name for keychain entries
SERVICE_NAME = "slack-mcp-server"


class CredentialManager:
    """Manages secure storage and retrieval of Slack API credentials."""

    def __init__(self, service_name: str = SERVICE_NAME):
        self.service_name = service_name
        self._ensure_keychain_available()

    def _ensure_keychain_available(self) -> None:
        """Ensure keychain is available on macOS."""
        if sys.platform != "darwin":
            logger.warning("Keychain storage is only available on macOS. Falling back to environment variables.")
            return

        try:
            # Test keychain access
            keyring.get_keyring()
        except Exception as e:
            logger.error(f"Failed to access keychain: {e}")
            raise RuntimeError("Keychain access failed. Please ensure your macOS keychain is unlocked.")

    def store_credential(self, key: str, value: str) -> bool:
        """
        Store a credential securely in the macOS Keychain.

        Args:
            key: The credential identifier (e.g., 'api_token')
            value: The credential value

        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            if sys.platform == "darwin":
                keyring.set_password(self.service_name, key, value)
                logger.info(f"Credential '{key}' stored successfully in keychain")
                return True
            else:
                logger.warning(f"Cannot store credential '{key}' - keychain only available on macOS")
                return False
        except KeyringError as e:
            logger.error(f"Failed to store credential '{key}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing credential '{key}': {e}")
            return False

    def get_credential(self, key: str) -> Optional[str]:
        """
        Retrieve a credential from the macOS Keychain.

        Args:
            key: The credential identifier

        Returns:
            str: The credential value, or None if not found
        """
        try:
            if sys.platform == "darwin":
                credential = keyring.get_password(self.service_name, key)
                if credential:
                    logger.debug(f"Retrieved credential '{key}' from keychain")
                    return credential
                else:
                    logger.debug(f"Credential '{key}' not found in keychain")
                    return None
            else:
                logger.debug(f"Keychain not available - falling back to environment variable for '{key}'")
                # Fallback to environment variables on non-macOS systems
                env_key = f"SLACK_{key.upper()}"
                return os.getenv(env_key)
        except KeyringError as e:
            logger.error(f"Failed to retrieve credential '{key}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving credential '{key}': {e}")
            return None

    def delete_credential(self, key: str) -> bool:
        """
        Delete a credential from the macOS Keychain.

        Args:
            key: The credential identifier

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if sys.platform == "darwin":
                keyring.delete_password(self.service_name, key)
                logger.info(f"Credential '{key}' deleted from keychain")
                return True
            else:
                logger.warning(f"Cannot delete credential '{key}' - keychain only available on macOS")
                return False
        except KeyringError as e:
            logger.error(f"Failed to delete credential '{key}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting credential '{key}': {e}")
            return False

    def list_stored_credentials(self) -> List[str]:
        """
        List all stored credential keys for this service.
        Note: This is a best-effort implementation as keyring doesn't provide
        a native way to list all keys for a service.

        Returns:
            List[str]: List of credential keys that are commonly used
        """
        common_keys = ["api_token", "workspace_id", "app_token"]
        stored_keys = []

        for key in common_keys:
            if self.get_credential(key) is not None:
                stored_keys.append(key)

        return stored_keys

    def get_all_credentials(self) -> Dict[str, Optional[str]]:
        """
        Get all Slack credentials as a dictionary.

        Returns:
            Dict[str, Optional[str]]: Dictionary of credential keys and values
        """
        credentials = {}

        # Standard Slack credentials
        credential_keys = [
            "api_token",  # Bot User OAuth Token
            "workspace_id",  # Slack Workspace ID (optional)
            "app_token",  # App-level token for Socket Mode (optional)
            "signing_secret",  # App signing secret (optional)
        ]

        for key in credential_keys:
            credentials[key] = self.get_credential(key)

        return credentials

    def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate that required credentials are present.

        Returns:
            Dict[str, Any]: Validation result with status and details
        """
        result = {"valid": True, "missing": [], "present": [], "errors": []}

        # Required credentials
        required_keys = ["api_token"]

        # Optional credentials
        optional_keys = ["workspace_id", "app_token", "signing_secret"]

        # Check required credentials
        for key in required_keys:
            credential = self.get_credential(key)
            if credential:
                result["present"].append(key)
            else:
                result["missing"].append(key)
                result["valid"] = False

        # Check optional credentials
        for key in optional_keys:
            credential = self.get_credential(key)
            if credential:
                result["present"].append(key)

        if not result["valid"]:
            result["errors"].append(f"Missing required credentials: {', '.join(result['missing'])}")

        return result


def get_slack_credentials() -> Dict[str, Optional[str]]:
    """
    Convenience function to get all Slack credentials.

    Returns:
        Dict[str, Optional[str]]: Dictionary of credential keys and values
    """
    manager = CredentialManager()
    return manager.get_all_credentials()


def setup_credential(key: str, value: str) -> bool:
    """
    Convenience function to store a single credential.

    Args:
        key: The credential identifier
        value: The credential value

    Returns:
        bool: True if stored successfully
    """
    manager = CredentialManager()
    return manager.store_credential(key, value)
