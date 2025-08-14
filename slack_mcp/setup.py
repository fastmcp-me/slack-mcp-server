#!/usr/bin/env python3
"""Secure credential setup for Slack MCP Server using macOS Keychain."""

import sys
import getpass
import re
from typing import Optional, Dict, Any
from .credentials import CredentialManager


def validate_slack_token(token: str) -> tuple[bool, str]:
    """
    Validate Slack API token format.

    Args:
        token: The token to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not token:
        return False, "Token cannot be empty"

    # Bot User OAuth Token format: xoxb-*
    if token.startswith("xoxb-"):
        if len(token) < 50:  # Typical length is around 50+ characters
            return False, "Bot token appears too short"
        return True, ""

    # User OAuth Token format: xoxp-*
    elif token.startswith("xoxp-"):
        if len(token) < 50:
            return False, "User token appears too short"
        return True, ""

    # App-level Token format: xapp-*
    elif token.startswith("xapp-"):
        if len(token) < 100:  # App tokens are longer
            return False, "App token appears too short"
        return True, ""

    else:
        return False, "Invalid token format. Slack tokens should start with 'xoxb-', 'xoxp-', or 'xapp-'"


def validate_workspace_id(workspace_id: str) -> tuple[bool, str]:
    """
    Validate Slack workspace ID format.

    Args:
        workspace_id: The workspace ID to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not workspace_id:
        return True, ""  # Workspace ID is optional

    # Workspace ID format: T followed by 8+ alphanumeric characters
    if re.match(r"^T[A-Z0-9]{8,}$", workspace_id):
        return True, ""
    else:
        return (
            False,
            "Invalid workspace ID format. Should start with 'T' followed by alphanumeric characters (e.g., 'T1234567890')",
        )


def print_header():
    """Print the setup header."""
    print("🔐 Slack MCP Server - Secure Credential Setup")
    print("=" * 50)
    print()


def print_token_help():
    """Print help for obtaining Slack tokens."""
    print("📋 How to get your Slack API token:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Create a new app or select an existing one")
    print("3. Navigate to 'OAuth & Permissions'")
    print("4. Add required scopes (see README.md)")
    print("5. Install the app to your workspace")
    print("6. Copy the 'Bot User OAuth Token' (starts with 'xoxb-')")
    print()


def setup_api_token(manager: CredentialManager) -> bool:
    """
    Setup the Slack API token.

    Args:
        manager: The credential manager instance

    Returns:
        bool: True if setup successful
    """
    print("🔑 Setting up Slack API Token")
    print_token_help()

    while True:
        token = getpass.getpass("Enter your Slack API token (input hidden): ").strip()

        if not token:
            choice = input("No token entered. Skip API token setup? [y/N]: ").lower()
            if choice in ("y", "yes"):
                return False
            continue

        is_valid, error_msg = validate_slack_token(token)

        if not is_valid:
            print(f"❌ {error_msg}")
            choice = input("Try again? [Y/n]: ").lower()
            if choice in ("n", "no"):
                return False
            continue

        # Store the token
        if manager.store_credential("api_token", token):
            print("✅ API token stored securely in keychain")
            return True
        else:
            print("❌ Failed to store API token")
            return False


def setup_workspace_id(manager: CredentialManager) -> bool:
    """
    Setup the Slack workspace ID (optional).

    Args:
        manager: The credential manager instance

    Returns:
        bool: True if setup successful or skipped
    """
    print("\n🏢 Setting up Slack Workspace ID (optional)")
    print("This helps with certain API operations but is not required for basic functionality.")
    print()

    workspace_id = input("Enter your Slack Workspace ID (starts with 'T', optional): ").strip()

    if not workspace_id:
        print("⏭️  Skipping workspace ID setup")
        return True

    is_valid, error_msg = validate_workspace_id(workspace_id)

    if not is_valid:
        print(f"❌ {error_msg}")
        print("⏭️  Skipping workspace ID setup")
        return True

    # Store the workspace ID
    if manager.store_credential("workspace_id", workspace_id):
        print("✅ Workspace ID stored securely in keychain")
        return True
    else:
        print("❌ Failed to store workspace ID")
        return True  # Non-critical, continue anyway


def setup_additional_credentials(manager: CredentialManager) -> None:
    """
    Setup additional optional credentials.

    Args:
        manager: The credential manager instance
    """
    print("\n🔧 Additional Credentials (optional)")
    print("These are only needed for advanced features:")
    print()

    # App token for Socket Mode
    choice = input("Do you need to set up an App Token for Socket Mode? [y/N]: ").lower()
    if choice in ("y", "yes"):
        app_token = getpass.getpass("Enter your App Token (starts with 'xapp-'): ").strip()
        if app_token:
            is_valid, error_msg = validate_slack_token(app_token)
            if is_valid:
                if manager.store_credential("app_token", app_token):
                    print("✅ App token stored securely in keychain")
                else:
                    print("❌ Failed to store app token")
            else:
                print(f"❌ {error_msg}")

    # Signing secret
    choice = input("Do you need to set up a Signing Secret for webhook verification? [y/N]: ").lower()
    if choice in ("y", "yes"):
        signing_secret = getpass.getpass("Enter your Signing Secret: ").strip()
        if signing_secret:
            if manager.store_credential("signing_secret", signing_secret):
                print("✅ Signing secret stored securely in keychain")
            else:
                print("❌ Failed to store signing secret")


def verify_setup(manager: CredentialManager) -> None:
    """
    Verify the credential setup.

    Args:
        manager: The credential manager instance
    """
    print("\n🔍 Verifying Setup")
    print("-" * 20)

    validation = manager.validate_credentials()

    if validation["valid"]:
        print("✅ All required credentials are configured!")
    else:
        print("❌ Setup incomplete - missing required credentials:")
        for missing in validation["missing"]:
            print(f"   • {missing}")

    if validation["present"]:
        print("\n📋 Configured credentials:")
        for credential in validation["present"]:
            print(f"   ✓ {credential}")


def list_credentials(manager: CredentialManager) -> None:
    """List currently stored credentials."""
    print("🔍 Currently Stored Credentials")
    print("-" * 30)

    stored = manager.list_stored_credentials()

    if stored:
        for key in stored:
            print(f"✓ {key}")
    else:
        print("No credentials found in keychain")


def delete_credentials(manager: CredentialManager) -> None:
    """Delete stored credentials."""
    print("🗑️  Delete Stored Credentials")
    print("-" * 30)

    stored = manager.list_stored_credentials()

    if not stored:
        print("No credentials found to delete")
        return

    print("Current credentials:")
    for i, key in enumerate(stored, 1):
        print(f"{i}. {key}")

    print(f"{len(stored) + 1}. Delete all")
    print("0. Cancel")

    try:
        choice = input("\nSelect credential to delete: ").strip()

        if choice == "0":
            print("Cancelled")
            return

        choice_num = int(choice)

        if choice_num == len(stored) + 1:
            # Delete all
            confirm = input("Are you sure you want to delete ALL credentials? [y/N]: ").lower()
            if confirm in ("y", "yes"):
                for key in stored:
                    manager.delete_credential(key)
                print("✅ All credentials deleted")
            else:
                print("Cancelled")
        elif 1 <= choice_num <= len(stored):
            # Delete specific credential
            key = stored[choice_num - 1]
            confirm = input(f"Are you sure you want to delete '{key}'? [y/N]: ").lower()
            if confirm in ("y", "yes"):
                if manager.delete_credential(key):
                    print(f"✅ Credential '{key}' deleted")
                else:
                    print(f"❌ Failed to delete credential '{key}'")
            else:
                print("Cancelled")
        else:
            print("Invalid choice")

    except ValueError:
        print("Invalid input - please enter a number")
    except KeyboardInterrupt:
        print("\nCancelled")


def main():
    """Main setup function."""
    if sys.platform != "darwin":
        print("⚠️  Warning: Keychain storage is only available on macOS.")
        print("On other systems, you can use environment variables instead.")
        print()

    try:
        manager = CredentialManager()
    except RuntimeError as e:
        print(f"❌ {e}")
        print("Please unlock your macOS keychain and try again.")
        sys.exit(1)

    while True:
        print_header()
        print("What would you like to do?")
        print("1. Set up new credentials")
        print("2. View current credentials")
        print("3. Delete credentials")
        print("4. Verify setup")
        print("0. Exit")
        print()

        try:
            choice = input("Select an option [1-4, 0]: ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break

            elif choice == "1":
                print()
                token_success = setup_api_token(manager)
                if token_success:
                    setup_workspace_id(manager)
                    setup_additional_credentials(manager)
                    verify_setup(manager)
                input("\nPress Enter to continue...")

            elif choice == "2":
                print()
                list_credentials(manager)
                input("\nPress Enter to continue...")

            elif choice == "3":
                print()
                delete_credentials(manager)
                input("\nPress Enter to continue...")

            elif choice == "4":
                print()
                verify_setup(manager)
                input("\nPress Enter to continue...")

            else:
                print("Invalid choice. Please select 1-4 or 0.")
                input("Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
