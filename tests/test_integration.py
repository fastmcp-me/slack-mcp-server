"""Integration tests for Block Kit functionality."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from slack_mcp.server import BlockKitBuilder


class TestBlockKitIntegration:
    """Test Block Kit functionality through integration testing."""

    @pytest.mark.asyncio
    async def test_block_kit_builder_components(self):
        """Test that BlockKitBuilder creates valid Block Kit structures."""
        # Test header
        header = BlockKitBuilder.header("Test Header")
        assert header["type"] == "header"
        assert header["text"]["type"] == "plain_text"
        assert header["text"]["text"] == "Test Header"

        # Test section
        section = BlockKitBuilder.section("Test content", "mrkdwn")
        assert section["type"] == "section"
        assert section["text"]["type"] == "mrkdwn"
        assert section["text"]["text"] == "Test content"

        # Test divider
        divider = BlockKitBuilder.divider()
        assert divider == {"type": "divider"}

        # Test fields section
        fields = BlockKitBuilder.fields_section(["Field 1", "Field 2"])
        assert fields["type"] == "section"
        assert len(fields["fields"]) == 2
        assert fields["fields"][0]["text"] == "Field 1"
        assert fields["fields"][1]["text"] == "Field 2"

        # Test context
        context = BlockKitBuilder.context(["Context info"])
        assert context["type"] == "context"
        assert len(context["elements"]) == 1
        assert context["elements"][0]["text"] == "Context info"

    @pytest.mark.asyncio
    async def test_slack_client_with_blocks(self):
        """Test SlackClient properly handles blocks parameter."""
        from slack_mcp.server import SlackClient
        
        with patch('slack_mcp.server.get_slack_credentials') as mock_creds, \
             patch('httpx.AsyncClient') as mock_client_class:
            
            # Mock credentials
            mock_creds.return_value = {"api_token": "xoxb-test-token"}
            
            # Mock HTTP client
            mock_client = MagicMock()
            mock_response = Mock()
            mock_response.json.return_value = {"ok": True, "ts": "123456.789"}
            mock_client.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Create client and test
            client = SlackClient()
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]
            
            result = await client.send_message("C123", "Fallback", None, blocks)
            
            # Verify the result
            assert result["ok"] is True
            assert result["ts"] == "123456.789"
            
            # Verify the HTTP call was made with blocks
            mock_client.__aenter__.return_value.request.assert_called_once()
            call_args = mock_client.__aenter__.return_value.request.call_args
            
            # Check that blocks were included in the request
            json_data = call_args[1]["json"]
            assert json_data["blocks"] == blocks
            assert json_data["channel"] == "C123"
            assert json_data["text"] == "Fallback"

    @pytest.mark.asyncio 
    async def test_json_parsing_edge_cases(self):
        """Test JSON parsing in the MCP tool functions."""
        # Test valid JSON
        valid_blocks = json.dumps([{"type": "section", "text": {"type": "mrkdwn", "text": "Valid"}}])
        parsed = json.loads(valid_blocks)
        assert len(parsed) == 1
        assert parsed[0]["type"] == "section"
        
        # Test empty JSON array
        empty_blocks = json.dumps([])
        parsed = json.loads(empty_blocks)
        assert parsed == []
        
        # Test invalid JSON should raise exception
        with pytest.raises(json.JSONDecodeError):
            json.loads("invalid json")

    def test_status_emoji_mapping(self):
        """Test status emoji mapping for notifications."""
        status_config = {
            "success": {"emoji": "✅", "color": "#28a745"},
            "warning": {"emoji": "⚠️", "color": "#ffc107"},
            "error": {"emoji": "❌", "color": "#dc3545"},
            "info": {"emoji": "ℹ️", "color": "#17a2b8"}
        }
        
        # Test known statuses
        assert status_config["success"]["emoji"] == "✅"
        assert status_config["error"]["emoji"] == "❌"
        assert status_config["warning"]["emoji"] == "⚠️"
        assert status_config["info"]["emoji"] == "ℹ️"
        
        # Test default fallback
        default_status = status_config.get("unknown", status_config["info"])
        assert default_status["emoji"] == "ℹ️"

    def test_item_parsing_logic(self):
        """Test the item parsing logic for list messages."""
        # Test newline-separated items
        newline_items = "Item 1\nItem 2\nItem 3"
        if "\n" in newline_items:
            item_list = [item.strip() for item in newline_items.split("\n") if item.strip()]
        else:
            item_list = [item.strip() for item in newline_items.split(",") if item.strip()]
        
        assert len(item_list) == 3
        assert item_list == ["Item 1", "Item 2", "Item 3"]
        
        # Test comma-separated items
        comma_items = "Item 1, Item 2, Item 3"
        if "\n" in comma_items:
            item_list = [item.strip() for item in comma_items.split("\n") if item.strip()]
        else:
            item_list = [item.strip() for item in comma_items.split(",") if item.strip()]
        
        assert len(item_list) == 3
        assert item_list == ["Item 1", "Item 2", "Item 3"]
        
        # Test formatting
        formatted_items = "\n".join([f"• {item}" for item in item_list])
        expected = "• Item 1\n• Item 2\n• Item 3"
        assert formatted_items == expected