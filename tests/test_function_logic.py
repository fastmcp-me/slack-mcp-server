"""Tests for Block Kit function logic without MCP wrapper."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from slack_mcp.server import BlockKitBuilder, SlackClient


async def _send_message_impl(channel: str, text: str, thread_ts=None, blocks=None):
    """Direct implementation of send_message logic for testing."""
    try:
        client = SlackClient()
        blocks_data = json.loads(blocks) if blocks else None
        result = await client.send_message(channel, text, thread_ts, blocks_data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


async def _update_message_impl(channel: str, ts: str, text: str, blocks=None):
    """Direct implementation of update_message logic for testing."""
    try:
        client = SlackClient()
        blocks_data = json.loads(blocks) if blocks else None
        result = await client.update_message(channel, ts, text, blocks_data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


async def _send_formatted_message_impl(
    channel: str,
    title=None,
    text=None,
    fields=None,
    context=None,
    thread_ts=None
):
    """Direct implementation of send_formatted_message logic for testing."""
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


async def _send_notification_message_impl(
    channel: str,
    status: str,
    title: str,
    description: str,
    details=None,
    thread_ts=None
):
    """Direct implementation of send_notification_message logic for testing."""
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


async def _send_list_message_impl(
    channel: str,
    title: str,
    items: str,
    description=None,
    thread_ts=None
):
    """Direct implementation of send_list_message logic for testing."""
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


class TestFunctionLogic:
    """Test the function logic directly."""

    @pytest.mark.asyncio
    async def test_send_message_with_blocks(self):
        """Test send_message function logic with blocks parameter."""
        blocks_json = json.dumps([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Test message"
                }
            }
        ])
        
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await _send_message_impl("C123", "Fallback text", None, blocks_json)
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            mock_client.send_message.assert_called_once_with(
                "C123",
                "Fallback text",
                None,
                [{"type": "section", "text": {"type": "mrkdwn", "text": "Test message"}}]
            )

    @pytest.mark.asyncio
    async def test_send_message_without_blocks(self):
        """Test send_message function logic without blocks parameter."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await _send_message_impl("C123", "Plain text message")
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            mock_client.send_message.assert_called_once_with("C123", "Plain text message", None, None)

    @pytest.mark.asyncio
    async def test_send_message_invalid_json(self):
        """Test send_message function logic with invalid blocks JSON."""
        with patch('slack_mcp.server.SlackClient'), \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            result = await _send_message_impl("C123", "Text", None, "invalid json")
            
            result_data = json.loads(result)
            assert "error" in result_data

    @pytest.mark.asyncio
    async def test_send_formatted_message_full(self):
        """Test send_formatted_message function logic with all parameters."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await _send_formatted_message_impl(
                "C123",
                "Test Header",
                "Main content",
                "Field 1, Field 2",
                "Context info"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            # Verify the call was made
            assert mock_client.send_message.called

    @pytest.mark.asyncio
    async def test_send_formatted_message_no_content(self):
        """Test send_formatted_message function logic with no content."""
        result = await _send_formatted_message_impl("C123")
        
        result_data = json.loads(result)
        assert "error" in result_data

    @pytest.mark.asyncio
    async def test_send_notification_message_success(self):
        """Test send_notification_message function logic with success status."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await _send_notification_message_impl(
                "C123",
                "success",
                "Deployment Complete",
                "Successfully deployed to production",
                "Build #123"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}

    @pytest.mark.asyncio
    async def test_send_notification_message_unknown_status(self):
        """Test send_notification_message function logic with unknown status defaults to info."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await _send_notification_message_impl(
                "C123",
                "unknown",
                "Some Message",
                "Description"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}

    @pytest.mark.asyncio
    async def test_send_list_message_newline_items(self):
        """Test send_list_message function logic with newline-separated items."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            items = "Item 1\nItem 2\nItem 3"
            result = await _send_list_message_impl(
                "C123",
                "My List",
                items,
                "List description"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}

    @pytest.mark.asyncio
    async def test_send_list_message_comma_items(self):
        """Test send_list_message function logic with comma-separated items."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class, \
             patch('slack_mcp.server.get_slack_credentials', return_value={"api_token": "test-token"}):
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            items = "Item 1, Item 2, Item 3"
            result = await _send_list_message_impl("C123", "My List", items)
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}