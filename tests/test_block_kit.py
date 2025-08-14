"""Tests for Block Kit functionality."""

import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from slack_mcp.server import BlockKitBuilder, SlackClient


class TestBlockKitBuilder:
    """Test the BlockKitBuilder utility class."""

    def test_header(self):
        """Test header block creation."""
        block = BlockKitBuilder.header("Test Header")
        expected = {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Test Header"
            }
        }
        assert block == expected

    def test_section(self):
        """Test section block creation."""
        block = BlockKitBuilder.section("Test content")
        expected = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Test content"
            }
        }
        assert block == expected

    def test_section_with_plain_text(self):
        """Test section block with plain text type."""
        block = BlockKitBuilder.section("Plain text content", "plain_text")
        expected = {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": "Plain text content"
            }
        }
        assert block == expected

    def test_divider(self):
        """Test divider block creation."""
        block = BlockKitBuilder.divider()
        expected = {"type": "divider"}
        assert block == expected

    def test_fields_section(self):
        """Test fields section creation."""
        fields = ["Field 1", "Field 2", "Field 3"]
        block = BlockKitBuilder.fields_section(fields)
        expected = {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "Field 1"},
                {"type": "mrkdwn", "text": "Field 2"},
                {"type": "mrkdwn", "text": "Field 3"}
            ]
        }
        assert block == expected

    def test_context(self):
        """Test context block creation."""
        elements = ["Context 1", "Context 2"]
        block = BlockKitBuilder.context(elements)
        expected = {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Context 1"},
                {"type": "mrkdwn", "text": "Context 2"}
            ]
        }
        assert block == expected

    def test_image_without_title(self):
        """Test image block creation without title."""
        block = BlockKitBuilder.image("https://example.com/image.png", "Alt text")
        expected = {
            "type": "image",
            "image_url": "https://example.com/image.png",
            "alt_text": "Alt text"
        }
        assert block == expected

    def test_image_with_title(self):
        """Test image block creation with title."""
        block = BlockKitBuilder.image("https://example.com/image.png", "Alt text", "Image Title")
        expected = {
            "type": "image",
            "image_url": "https://example.com/image.png",
            "alt_text": "Alt text",
            "title": {
                "type": "plain_text",
                "text": "Image Title"
            }
        }
        assert block == expected


class TestSlackClientBlockSupport:
    """Test SlackClient Block Kit support."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock SlackClient."""
        with patch('slack_mcp.server.get_slack_credentials') as mock_creds:
            mock_creds.return_value = {"api_token": "test-token"}
            client = SlackClient()
            return client

    @pytest.mark.asyncio
    async def test_send_message_with_blocks(self, mock_client):
        """Test sending message with blocks."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Test message"
                }
            }
        ]
        
        with patch.object(mock_client, '_make_request') as mock_request:
            mock_request.return_value = {"ok": True, "ts": "123456.789"}
            
            result = await mock_client.send_message("C123", "Fallback text", None, blocks)
            
            mock_request.assert_called_once_with(
                "POST",
                "chat.postMessage",
                json_data={
                    "channel": "C123",
                    "text": "Fallback text",
                    "blocks": blocks
                }
            )
            assert result == {"ok": True, "ts": "123456.789"}

    @pytest.mark.asyncio
    async def test_update_message_with_blocks(self, mock_client):
        """Test updating message with blocks."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Updated message"
                }
            }
        ]
        
        with patch.object(mock_client, '_make_request') as mock_request:
            mock_request.return_value = {"ok": True, "ts": "123456.789"}
            
            result = await mock_client.update_message("C123", "123456.789", "Updated text", blocks)
            
            mock_request.assert_called_once_with(
                "POST",
                "chat.update",
                json_data={
                    "channel": "C123",
                    "ts": "123456.789",
                    "text": "Updated text",
                    "blocks": blocks
                }
            )
            assert result == {"ok": True, "ts": "123456.789"}


class TestAdvancedBlockKitBuilder:
    """Test the enhanced BlockKitBuilder functionality."""

    def test_button_basic(self):
        """Test basic button creation."""
        button = BlockKitBuilder.button("Click Me", "click_action")
        expected = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Click Me"
            },
            "action_id": "click_action"
        }
        assert button == expected

    def test_button_with_options(self):
        """Test button with all options."""
        button = BlockKitBuilder.button(
            "Submit", "submit_action", 
            value="form_data", 
            url="https://example.com", 
            style="primary"
        )
        expected = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Submit"
            },
            "action_id": "submit_action",
            "value": "form_data",
            "url": "https://example.com",
            "style": "primary"
        }
        assert button == expected

    def test_actions_block(self):
        """Test actions block creation."""
        button1 = BlockKitBuilder.button("Yes", "yes_action")
        button2 = BlockKitBuilder.button("No", "no_action")
        actions = BlockKitBuilder.actions(button1, button2)
        
        expected = {
            "type": "actions",
            "elements": [button1, button2]
        }
        assert actions == expected

    def test_select_menu(self):
        """Test select menu creation."""
        options = [
            {"text": "Option 1", "value": "opt1"},
            {"text": "Option 2", "value": "opt2"}
        ]
        select = BlockKitBuilder.select_menu("Choose...", "menu_action", options)
        
        expected = {
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": "Choose..."
            },
            "action_id": "menu_action",
            "options": [
                {
                    "text": {
                        "type": "plain_text",
                        "text": "Option 1"
                    },
                    "value": "opt1"
                },
                {
                    "text": {
                        "type": "plain_text",
                        "text": "Option 2"
                    },
                    "value": "opt2"
                }
            ]
        }
        assert select == expected

    def test_section_with_accessory(self):
        """Test section with accessory element."""
        button = BlockKitBuilder.button("Click", "click_action")
        section = BlockKitBuilder.section_with_accessory("Text content", button)
        
        expected = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Text content"
            },
            "accessory": button
        }
        assert section == expected

    def test_code_block(self):
        """Test code block creation."""
        code = "print('Hello, World!')"
        block = BlockKitBuilder.code_block(code, "python")
        
        expected = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```python\nprint('Hello, World!')```"
            }
        }
        assert block == expected

    def test_code_block_without_language(self):
        """Test code block without language."""
        code = "echo 'Hello'"
        block = BlockKitBuilder.code_block(code)
        
        expected = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```echo 'Hello'```"
            }
        }
        assert block == expected

    def test_quote_block(self):
        """Test quote block creation."""
        block = BlockKitBuilder.quote_block("This is a quote")
        expected = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ">This is a quote"
            }
        }
        assert block == expected

    def test_rich_text_list(self):
        """Test rich text list creation."""
        items = ["Item 1", "Item 2", "Item 3"]
        block = BlockKitBuilder.rich_text_list(items, "bullet")
        
        expected = {
            "type": "rich_text_list",
            "style": "bullet",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": "Item 1"}]
                },
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": "Item 2"}]
                },
                {
                    "type": "rich_text_section",
                    "elements": [{"type": "text", "text": "Item 3"}]
                }
            ]
        }
        assert block == expected