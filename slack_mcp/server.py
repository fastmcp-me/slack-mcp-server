"""Slack MCP Server implementation."""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx
from fastmcp import FastMCP
from .credentials import CredentialManager, get_slack_credentials

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("slack-mcp-server")


class SlackClient:
    """Client for interacting with Slack Web API."""

    def __init__(self):
        self.credential_manager = CredentialManager()
        self.base_url = "https://slack.com/api"

        # Get credentials from keychain first, fallback to environment variables
        credentials = get_slack_credentials()
        self.api_token = credentials.get("api_token") or os.getenv("SLACK_API_TOKEN")
        self.workspace_id = credentials.get("workspace_id") or os.getenv("SLACK_WORKSPACE_ID")

        # Log credential source (without exposing values)
        if credentials.get("api_token"):
            logger.debug("Using API token from keychain")
        elif os.getenv("SLACK_API_TOKEN"):
            logger.debug("Using API token from environment variable")
        else:
            logger.warning("No API token found in keychain or environment variables")

    def _validate_config(self) -> bool:
        """Validate that required configuration is present."""
        if not self.api_token:
            logger.warning("Slack API token not found in keychain or environment variables")
            logger.info("Use 'python -m slack_mcp.setup' to configure credentials securely")
            return False
        return True

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Slack API."""
        if not self._validate_config():
            raise ValueError(
                "Slack API token not configured. Use 'python -m slack_mcp.setup' to configure credentials."
            )

        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, params=params, json=json_data, timeout=30.0)

            data = response.json()

            if not data.get("ok", False):
                error_msg = data.get("error", "Unknown error")
                raise Exception(f"Slack API error: {error_msg}")

            return data

    async def list_channels(
        self, types: Optional[List[str]] = None, exclude_archived: bool = True, limit: int = 100
    ) -> Dict[str, Any]:
        """List all channels in the workspace."""
        params = {"exclude_archived": exclude_archived, "limit": limit}

        if types:
            params["types"] = ",".join(types)

        return await self._make_request("GET", "conversations.list", params=params)

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific channel."""
        params = {"channel": channel_id}
        return await self._make_request("GET", "conversations.info", params=params)

    async def list_users(self, limit: int = 100, include_locale: bool = False) -> Dict[str, Any]:
        """List all users in the workspace."""
        params = {"limit": limit, "include_locale": include_locale}
        return await self._make_request("GET", "users.list", params=params)

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user."""
        params = {"user": user_id}
        return await self._make_request("GET", "users.info", params=params)

    async def send_message(
        self, channel: str, text: str, thread_ts: Optional[str] = None, blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send a message to a channel."""
        data = {"channel": channel, "text": text}

        if thread_ts:
            data["thread_ts"] = thread_ts

        if blocks:
            data["blocks"] = blocks

        return await self._make_request("POST", "chat.postMessage", json_data=data)

    async def update_message(
        self, channel: str, ts: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Update an existing message."""
        data = {"channel": channel, "ts": ts, "text": text}

        if blocks:
            data["blocks"] = blocks

        return await self._make_request("POST", "chat.update", json_data=data)

    async def delete_message(self, channel: str, ts: str) -> Dict[str, Any]:
        """Delete a message from a channel."""
        data = {"channel": channel, "ts": ts}
        return await self._make_request("POST", "chat.delete", json_data=data)

    async def get_channel_history(
        self,
        channel: str,
        limit: int = 100,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        inclusive: bool = True,
    ) -> Dict[str, Any]:
        """Get message history for a channel."""
        params = {"channel": channel, "limit": limit, "inclusive": inclusive}

        if oldest:
            params["oldest"] = oldest

        if latest:
            params["latest"] = latest

        return await self._make_request("GET", "conversations.history", params=params)

    async def search_messages(
        self, query: str, sort: str = "timestamp", sort_dir: str = "desc", count: int = 20
    ) -> Dict[str, Any]:
        """Search for messages across the workspace."""
        params = {"query": query, "sort": sort, "sort_dir": sort_dir, "count": count}
        return await self._make_request("GET", "search.messages", params=params)

    async def upload_file(
        self,
        channels: List[str],
        content: str,
        filename: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to one or more channels."""
        data = {"channels": ",".join(channels), "content": content, "filename": filename}

        if title:
            data["title"] = title

        if initial_comment:
            data["initial_comment"] = initial_comment

        return await self._make_request("POST", "files.upload", json_data=data)

    async def add_reaction(self, channel: str, timestamp: str, name: str) -> Dict[str, Any]:
        """Add a reaction to a message."""
        data = {"channel": channel, "timestamp": timestamp, "name": name}
        return await self._make_request("POST", "reactions.add", json_data=data)

    async def remove_reaction(self, channel: str, timestamp: str, name: str) -> Dict[str, Any]:
        """Remove a reaction from a message."""
        data = {"channel": channel, "timestamp": timestamp, "name": name}
        return await self._make_request("POST", "reactions.remove", json_data=data)

    async def get_team_info(self) -> Dict[str, Any]:
        """Get information about the Slack workspace/team."""
        return await self._make_request("GET", "team.info")

    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new channel."""
        data = {"name": name, "is_private": is_private}
        return await self._make_request("POST", "conversations.create", json_data=data)

    async def archive_channel(self, channel: str) -> Dict[str, Any]:
        """Archive a channel."""
        data = {"channel": channel}
        return await self._make_request("POST", "conversations.archive", json_data=data)

    async def unarchive_channel(self, channel: str) -> Dict[str, Any]:
        """Unarchive a channel."""
        data = {"channel": channel}
        return await self._make_request("POST", "conversations.unarchive", json_data=data)

    async def invite_to_channel(self, channel: str, users: List[str]) -> Dict[str, Any]:
        """Invite users to a channel."""
        data = {"channel": channel, "users": ",".join(users)}
        return await self._make_request("POST", "conversations.invite", json_data=data)

    async def set_channel_topic(self, channel: str, topic: str) -> Dict[str, Any]:
        """Set the topic for a channel."""
        data = {"channel": channel, "topic": topic}
        return await self._make_request("POST", "conversations.setTopic", json_data=data)

    async def set_channel_purpose(self, channel: str, purpose: str) -> Dict[str, Any]:
        """Set the purpose for a channel."""
        data = {"channel": channel, "purpose": purpose}
        return await self._make_request("POST", "conversations.setPurpose", json_data=data)


@mcp.tool()
async def list_channels(types: Optional[str] = None, exclude_archived: bool = True, limit: int = 100) -> str:
    """
    List all channels in the Slack workspace.

    Args:
        types: Comma-separated channel types (public_channel, private_channel, mpim, im)
        exclude_archived: Whether to exclude archived channels
        limit: Maximum number of channels to return (1-1000)
    """
    try:
        client = SlackClient()
        types_list = types.split(",") if types else None
        result = await client.list_channels(types_list, exclude_archived, limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_channel_info(channel_id: str) -> str:
    """
    Get detailed information about a specific Slack channel.

    Args:
        channel_id: The ID of the channel
    """
    try:
        client = SlackClient()
        result = await client.get_channel_info(channel_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def list_users(limit: int = 100, include_locale: bool = False) -> str:
    """
    List all users in the Slack workspace.

    Args:
        limit: Maximum number of users to return
        include_locale: Include locale information for each user
    """
    try:
        client = SlackClient()
        result = await client.list_users(limit, include_locale)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_user_info(user_id: str) -> str:
    """
    Get detailed information about a specific Slack user.

    Args:
        user_id: The ID of the user
    """
    try:
        client = SlackClient()
        result = await client.get_user_info(user_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_message(channel: str, text: str, thread_ts: Optional[str] = None, blocks: Optional[str] = None) -> str:
    """
    Send a message to a Slack channel.

    Args:
        channel: Channel ID or name
        text: Message text (fallback text for notifications)
        thread_ts: Thread timestamp for replies
        blocks: JSON string of Block Kit blocks for rich formatting
    """
    try:
        client = SlackClient()
        blocks_data = json.loads(blocks) if blocks else None
        result = await client.send_message(channel, text, thread_ts, blocks_data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def update_message(channel: str, ts: str, text: str, blocks: Optional[str] = None) -> str:
    """
    Update an existing Slack message.

    Args:
        channel: Channel ID where the message exists
        ts: Timestamp of the message to update
        text: New message text (fallback text for notifications)
        blocks: JSON string of Block Kit blocks for rich formatting
    """
    try:
        client = SlackClient()
        blocks_data = json.loads(blocks) if blocks else None
        result = await client.update_message(channel, ts, text, blocks_data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def delete_message(channel: str, ts: str) -> str:
    """
    Delete a message from a Slack channel.

    Args:
        channel: Channel ID where the message exists
        ts: Timestamp of the message to delete
    """
    try:
        client = SlackClient()
        result = await client.delete_message(channel, ts)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_channel_history(
    channel: str, limit: int = 100, oldest: Optional[str] = None, latest: Optional[str] = None
) -> str:
    """
    Get message history for a Slack channel.

    Args:
        channel: Channel ID
        limit: Maximum number of messages to return
        oldest: Only messages after this timestamp
        latest: Only messages before this timestamp
    """
    try:
        client = SlackClient()
        result = await client.get_channel_history(channel, limit, oldest, latest)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def search_messages(query: str, sort: str = "timestamp", sort_dir: str = "desc", count: int = 20) -> str:
    """
    Search for messages across the Slack workspace.

    Args:
        query: Search query
        sort: Sort by 'score' or 'timestamp'
        sort_dir: Sort direction 'asc' or 'desc'
        count: Number of results to return
    """
    try:
        client = SlackClient()
        result = await client.search_messages(query, sort, sort_dir, count)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def upload_file(
    channels: str, content: str, filename: str, title: Optional[str] = None, initial_comment: Optional[str] = None
) -> str:
    """
    Upload a file to one or more Slack channels.

    Args:
        channels: Comma-separated list of channel IDs
        content: File content as text
        filename: Name for the file
        title: Title of the file
        initial_comment: Initial comment for the file
    """
    try:
        client = SlackClient()
        channels_list = channels.split(",")
        result = await client.upload_file(channels_list, content, filename, title, initial_comment)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def add_reaction(channel: str, timestamp: str, emoji_name: str) -> str:
    """
    Add a reaction emoji to a message.

    Args:
        channel: Channel ID where the message exists
        timestamp: Timestamp of the message
        emoji_name: Name of the emoji (without colons)
    """
    try:
        client = SlackClient()
        result = await client.add_reaction(channel, timestamp, emoji_name)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def remove_reaction(channel: str, timestamp: str, emoji_name: str) -> str:
    """
    Remove a reaction emoji from a message.

    Args:
        channel: Channel ID where the message exists
        timestamp: Timestamp of the message
        emoji_name: Name of the emoji (without colons)
    """
    try:
        client = SlackClient()
        result = await client.remove_reaction(channel, timestamp, emoji_name)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def get_team_info() -> str:
    """Get information about the Slack workspace/team."""
    try:
        client = SlackClient()
        result = await client.get_team_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def create_channel(name: str, is_private: bool = False) -> str:
    """
    Create a new Slack channel.

    Args:
        name: Name for the new channel
        is_private: Whether the channel should be private
    """
    try:
        client = SlackClient()
        result = await client.create_channel(name, is_private)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def archive_channel(channel: str) -> str:
    """
    Archive a Slack channel.

    Args:
        channel: Channel ID to archive
    """
    try:
        client = SlackClient()
        result = await client.archive_channel(channel)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def unarchive_channel(channel: str) -> str:
    """
    Unarchive a Slack channel.

    Args:
        channel: Channel ID to unarchive
    """
    try:
        client = SlackClient()
        result = await client.unarchive_channel(channel)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def invite_to_channel(channel: str, users: str) -> str:
    """
    Invite users to a Slack channel.

    Args:
        channel: Channel ID
        users: Comma-separated list of user IDs
    """
    try:
        client = SlackClient()
        users_list = users.split(",")
        result = await client.invite_to_channel(channel, users_list)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def set_channel_topic(channel: str, topic: str) -> str:
    """
    Set the topic for a Slack channel.

    Args:
        channel: Channel ID
        topic: New topic text
    """
    try:
        client = SlackClient()
        result = await client.set_channel_topic(channel, topic)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def set_channel_purpose(channel: str, purpose: str) -> str:
    """
    Set the purpose for a Slack channel.

    Args:
        channel: Channel ID
        purpose: New purpose text
    """
    try:
        client = SlackClient()
        result = await client.set_channel_purpose(channel, purpose)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


class BlockKitBuilder:
    """Utility class for building Block Kit elements."""

    @staticmethod
    def header(text: str) -> Dict[str, Any]:
        """Create a header block."""
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text
            }
        }

    @staticmethod
    def section(text: str, text_type: str = "mrkdwn") -> Dict[str, Any]:
        """Create a section block with text."""
        return {
            "type": "section",
            "text": {
                "type": text_type,
                "text": text
            }
        }

    @staticmethod
    def divider() -> Dict[str, Any]:
        """Create a divider block."""
        return {"type": "divider"}

    @staticmethod
    def fields_section(fields: List[str]) -> Dict[str, Any]:
        """Create a section block with multiple fields."""
        return {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": field
                }
                for field in fields
            ]
        }

    @staticmethod
    def context(elements: List[str]) -> Dict[str, Any]:
        """Create a context block with multiple text elements."""
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": element
                }
                for element in elements
            ]
        }

    @staticmethod
    def image(image_url: str, alt_text: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create an image block."""
        block = {
            "type": "image",
            "image_url": image_url,
            "alt_text": alt_text
        }
        if title:
            block["title"] = {
                "type": "plain_text",
                "text": title
            }
        return block

    @staticmethod
    def button(text: str, action_id: str, value: Optional[str] = None, url: Optional[str] = None, style: Optional[str] = None) -> Dict[str, Any]:
        """Create a button element."""
        element = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text
            },
            "action_id": action_id
        }
        if value:
            element["value"] = value
        if url:
            element["url"] = url
        if style in ["primary", "danger"]:
            element["style"] = style
        return element

    @staticmethod
    def actions(*elements) -> Dict[str, Any]:
        """Create an actions block with interactive elements."""
        return {
            "type": "actions",
            "elements": list(elements)
        }

    @staticmethod
    def select_menu(placeholder: str, action_id: str, options: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create a static select menu element."""
        return {
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": placeholder
            },
            "action_id": action_id,
            "options": [
                {
                    "text": {
                        "type": "plain_text",
                        "text": option["text"]
                    },
                    "value": option["value"]
                }
                for option in options
            ]
        }

    @staticmethod
    def section_with_accessory(text: str, accessory: Dict[str, Any], text_type: str = "mrkdwn") -> Dict[str, Any]:
        """Create a section block with an accessory element."""
        return {
            "type": "section",
            "text": {
                "type": text_type,
                "text": text
            },
            "accessory": accessory
        }

    @staticmethod
    def code_block(code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Create a formatted code block."""
        formatted_code = f"```{language + chr(10) if language else ''}{code}```"
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": formatted_code
            }
        }

    @staticmethod
    def quote_block(text: str) -> Dict[str, Any]:
        """Create a quote block."""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f">{text}"
            }
        }

    @staticmethod
    def rich_text_block(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a rich text block with various formatting elements."""
        return {
            "type": "rich_text",
            "elements": elements
        }

    @staticmethod
    def rich_text_section(*elements) -> Dict[str, Any]:
        """Create a rich text section with inline elements."""
        return {
            "type": "rich_text_section",
            "elements": list(elements)
        }

    @staticmethod
    def rich_text_list(items: List[str], style: str = "bullet") -> Dict[str, Any]:
        """Create a rich text list (bullet or ordered)."""
        return {
            "type": "rich_text_list",
            "style": style,
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": item}]
                }
                for item in items
            ]
        }


@mcp.tool()
async def send_formatted_message(
    channel: str,
    title: Optional[str] = None,
    text: Optional[str] = None,
    fields: Optional[str] = None,
    context: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> str:
    """
    Send a formatted message using Block Kit with common elements.

    Args:
        channel: Channel ID or name
        title: Header text (optional)
        text: Main message text (optional)
        fields: Comma-separated fields for side-by-side display (optional)
        context: Context text at bottom (optional)
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        blocks = []
        
        if title:
            blocks.append(BlockKitBuilder.header(title))
        
        if text:
            blocks.append(BlockKitBuilder.section(text))
        
        if fields:
            field_list = [field.strip() for field in fields.split(",")]
            blocks.append(BlockKitBuilder.fields_section(field_list))
        
        if context:
            blocks.append(BlockKitBuilder.context([context]))
        
        if not blocks:
            return json.dumps({"error": "At least one of title, text, fields, or context must be provided"}, indent=2)
        
        fallback_text = title or text or "Formatted message"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_notification_message(
    channel: str,
    status: str,
    title: str,
    description: str,
    details: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> str:
    """
    Send a structured notification message with status indicator.

    Args:
        channel: Channel ID or name
        status: Status type (success, warning, error, info)
        title: Notification title
        description: Main description
        details: Additional details (optional)
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        # Status emojis and colors
        status_config = {
            "success": {"emoji": "✅", "color": "#28a745"},
            "warning": {"emoji": "⚠️", "color": "#ffc107"},
            "error": {"emoji": "❌", "color": "#dc3545"},
            "info": {"emoji": "ℹ️", "color": "#17a2b8"}
        }
        
        config = status_config.get(status.lower(), status_config["info"])
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{config['emoji']} *{title}*\n{description}"
                }
            }
        ]
        
        if details:
            blocks.append(BlockKitBuilder.divider())
            blocks.append(BlockKitBuilder.context([details]))
        
        fallback_text = f"{config['emoji']} {title}: {description}"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_list_message(
    channel: str,
    title: str,
    items: str,
    description: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> str:
    """
    Send a formatted list message.

    Args:
        channel: Channel ID or name
        title: List title
        items: Newline or comma-separated list items
        description: Optional description text
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        blocks = [BlockKitBuilder.header(title)]
        
        if description:
            blocks.append(BlockKitBuilder.section(description))
            blocks.append(BlockKitBuilder.divider())
        
        # Process items
        if "\n" in items:
            item_list = [item.strip() for item in items.split("\n") if item.strip()]
        else:
            item_list = [item.strip() for item in items.split(",") if item.strip()]
        
        # Create formatted list
        formatted_items = "\n".join([f"• {item}" for item in item_list])
        blocks.append(BlockKitBuilder.section(formatted_items))
        
        fallback_text = f"{title}: {', '.join(item_list)}"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_interactive_message(
    channel: str,
    title: str,
    description: str,
    buttons: str,
    thread_ts: Optional[str] = None
) -> str:
    """
    Send an interactive message with buttons.

    Args:
        channel: Channel ID or name
        title: Message title
        description: Message description
        buttons: JSON string of button configurations [{"text": "Button Text", "action_id": "action_1", "style": "primary"}]
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        blocks = [
            BlockKitBuilder.header(title),
            BlockKitBuilder.section(description)
        ]
        
        # Parse button configurations
        button_configs = json.loads(buttons)
        button_elements = []
        
        for btn_config in button_configs:
            button = BlockKitBuilder.button(
                text=btn_config["text"],
                action_id=btn_config["action_id"],
                value=btn_config.get("value"),
                url=btn_config.get("url"),
                style=btn_config.get("style")
            )
            button_elements.append(button)
        
        if button_elements:
            blocks.append(BlockKitBuilder.actions(*button_elements))
        
        fallback_text = f"{title}: {description}"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_code_snippet(
    channel: str,
    title: str,
    code: str,
    language: Optional[str] = None,
    description: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> str:
    """
    Send a formatted code snippet message.

    Args:
        channel: Channel ID or name
        title: Code snippet title
        code: The code content
        language: Programming language for syntax highlighting (optional)
        description: Optional description
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        blocks = [BlockKitBuilder.header(title)]
        
        if description:
            blocks.append(BlockKitBuilder.section(description))
        
        blocks.append(BlockKitBuilder.code_block(code, language))
        
        fallback_text = f"{title}: {code[:100]}{'...' if len(code) > 100 else ''}"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_form_message(
    channel: str,
    title: str,
    description: str,
    select_options: str,
    select_placeholder: str = "Choose an option",
    select_action_id: str = "form_select",
    thread_ts: Optional[str] = None
) -> str:
    """
    Send a form-like message with a select menu.

    Args:
        channel: Channel ID or name
        title: Form title
        description: Form description
        select_options: JSON string of select options [{"text": "Option 1", "value": "opt1"}]
        select_placeholder: Placeholder text for select menu
        select_action_id: Action ID for the select menu
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        blocks = [
            BlockKitBuilder.header(title),
            BlockKitBuilder.section(description)
        ]
        
        # Parse select options
        options = json.loads(select_options)
        
        select_menu = BlockKitBuilder.select_menu(
            placeholder=select_placeholder,
            action_id=select_action_id,
            options=options
        )
        
        blocks.append(BlockKitBuilder.section_with_accessory(
            "Please make your selection:",
            select_menu
        ))
        
        fallback_text = f"{title}: {description}"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
async def send_announcement(
    channel: str,
    title: str,
    message: str,
    author: Optional[str] = None,
    timestamp: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> str:
    """
    Send a formatted announcement message.

    Args:
        channel: Channel ID or name
        title: Announcement title
        message: Main announcement message
        author: Author name (optional)
        timestamp: Custom timestamp (optional)
        thread_ts: Thread timestamp for replies (optional)
    """
    try:
        blocks = [
            BlockKitBuilder.header(f"📢 {title}"),
            BlockKitBuilder.section(message)
        ]
        
        # Add context with author and timestamp
        context_elements = []
        if author:
            context_elements.append(f"*By:* {author}")
        if timestamp:
            context_elements.append(f"*Date:* {timestamp}")
        else:
            context_elements.append(f"*Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if context_elements:
            blocks.append(BlockKitBuilder.context(context_elements))
        
        fallback_text = f"📢 {title}: {message}"
        
        client = SlackClient()
        result = await client.send_message(channel, fallback_text, thread_ts, blocks)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def main():
    """Main entry point for the server."""
    mcp.run()


if __name__ == "__main__":
    main()
