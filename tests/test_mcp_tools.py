"""Tests for MCP tools with Block Kit support."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
import slack_mcp.server as server


class TestEnhancedMCPTools:
    """Test the enhanced MCP tools with Block Kit support."""

    @pytest.mark.asyncio
    async def test_send_message_with_blocks(self):
        """Test send_message MCP tool with blocks parameter."""
        blocks_json = json.dumps([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Test message"
                }
            }
        ])
        
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_message("C123", "Fallback text", None, blocks_json)
            
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
        """Test send_message MCP tool without blocks parameter."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_message("C123", "Plain text message")
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            mock_client.send_message.assert_called_once_with("C123", "Plain text message", None, None)

    @pytest.mark.asyncio
    async def test_send_message_invalid_json(self):
        """Test send_message MCP tool with invalid blocks JSON."""
        with patch('slack_mcp.server.SlackClient'):
            result = await server.send_message("C123", "Text", None, "invalid json")
            
            result_data = json.loads(result)
            assert "error" in result_data

    @pytest.mark.asyncio
    async def test_update_message_with_blocks(self):
        """Test update_message MCP tool with blocks parameter."""
        blocks_json = json.dumps([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Updated message"
                }
            }
        ])
        
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.update_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.update_message("C123", "123456.789", "Updated text", blocks_json)
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            mock_client.update_message.assert_called_once_with(
                "C123",
                "123456.789",
                "Updated text",
                [{"type": "section", "text": {"type": "mrkdwn", "text": "Updated message"}}]
            )

    @pytest.mark.asyncio
    async def test_update_message_without_blocks(self):
        """Test update_message MCP tool without blocks parameter."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.update_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.update_message("C123", "123456.789", "Plain updated text")
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            mock_client.update_message.assert_called_once_with("C123", "123456.789", "Plain updated text", None)


class TestNewBlockKitTools:
    """Test the new Block Kit-specific MCP tools."""

    @pytest.mark.asyncio
    async def test_send_formatted_message_full(self):
        """Test send_formatted_message with all parameters."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_formatted_message(
                "C123",
                "Test Header",
                "Main content",
                "Field 1, Field 2",
                "Context info"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            # Verify the blocks structure
            call_args = mock_client.send_message.call_args
            blocks = call_args[1]["blocks"]
            
            assert len(blocks) == 4  # header, section, fields_section, context
            assert blocks[0]["type"] == "header"
            assert blocks[1]["type"] == "section"
            assert blocks[2]["type"] == "section" and "fields" in blocks[2]
            assert blocks[3]["type"] == "context"

    @pytest.mark.asyncio
    async def test_send_formatted_message_minimal(self):
        """Test send_formatted_message with minimal parameters."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_formatted_message("C123", "Just a title")
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}

    @pytest.mark.asyncio
    async def test_send_formatted_message_no_content(self):
        """Test send_formatted_message with no content."""
        result = await server.send_formatted_message("C123")
        
        result_data = json.loads(result)
        assert "error" in result_data

    @pytest.mark.asyncio
    async def test_send_notification_message_success(self):
        """Test send_notification_message with success status."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_notification_message(
                "C123",
                "success",
                "Deployment Complete",
                "Successfully deployed to production",
                "Build #123"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            # Verify the blocks contain success emoji
            call_args = mock_client.send_message.call_args
            blocks = call_args[1]["blocks"]
            assert "✅" in blocks[0]["text"]["text"]

    @pytest.mark.asyncio
    async def test_send_notification_message_error(self):
        """Test send_notification_message with error status."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_notification_message(
                "C123",
                "error",
                "Deployment Failed",
                "Deployment failed with errors"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            # Verify the blocks contain error emoji
            call_args = mock_client.send_message.call_args
            blocks = call_args[1]["blocks"]
            assert "❌" in blocks[0]["text"]["text"]

    @pytest.mark.asyncio
    async def test_send_notification_message_unknown_status(self):
        """Test send_notification_message with unknown status defaults to info."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            result = await server.send_notification_message(
                "C123",
                "unknown",
                "Some Message",
                "Description"
            )
            
            # Should default to info emoji
            call_args = mock_client.send_message.call_args
            blocks = call_args[1]["blocks"]
            assert "ℹ️" in blocks[0]["text"]["text"]

    @pytest.mark.asyncio
    async def test_send_list_message_newline_items(self):
        """Test send_list_message with newline-separated items."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            items = "Item 1\nItem 2\nItem 3"
            result = await server.send_list_message(
                "C123",
                "My List",
                items,
                "List description"
            )
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            # Verify the blocks structure
            call_args = mock_client.send_message.call_args
            blocks = call_args[1]["blocks"]
            
            # Should have header, section (description), divider, and list section
            assert len(blocks) == 4
            assert blocks[0]["type"] == "header"
            assert blocks[1]["type"] == "section"  # description
            assert blocks[2]["type"] == "divider"
            assert blocks[3]["type"] == "section"  # list
            assert "• Item 1" in blocks[3]["text"]["text"]
            assert "• Item 2" in blocks[3]["text"]["text"]
            assert "• Item 3" in blocks[3]["text"]["text"]

    @pytest.mark.asyncio
    async def test_send_list_message_comma_items(self):
        """Test send_list_message with comma-separated items."""
        with patch('slack_mcp.server.SlackClient') as mock_client_class:
            mock_client = Mock()
            mock_client.send_message = AsyncMock(return_value={"ok": True, "ts": "123456.789"})
            mock_client_class.return_value = mock_client
            
            items = "Item 1, Item 2, Item 3"
            result = await server.send_list_message("C123", "My List", items)
            
            result_data = json.loads(result)
            assert result_data == {"ok": True, "ts": "123456.789"}
            
            # Should have header and list section (no description or divider)
            call_args = mock_client.send_message.call_args
            blocks = call_args[1]["blocks"]
            assert len(blocks) == 2
            assert blocks[0]["type"] == "header"
            assert blocks[1]["type"] == "section"  # list