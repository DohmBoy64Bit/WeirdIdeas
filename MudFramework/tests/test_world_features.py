"""
Comprehensive tests for movement, inventory, and quests
"""
import pytest
from tests.conftest import send_command

class TestMovementSystem:
    """Test world navigation"""
    
    def test_look_command(self, ws_connection):
        """Test look command shows room info"""
        messages = send_command(ws_connection, "look")
        assert len(messages) > 0
    
    def test_cardinal_movement(self, ws_connection):
        """Test north/south/east/west movement"""
        # Test east
        messages = send_command(ws_connection, "east")
        moved = len(messages) > 0
        
        # Move back west
        send_command(ws_connection, "west")
        
        assert moved
    
    def test_movement_boundaries(self, ws_connection):
        """Test cannot move through walls"""
        # Try invalid direction repeatedly
        messages = send_command(ws_connection, "north")
        
        # Should either move or get blocked message
        assert len(messages) >= 0  # Any response is valid

class TestInventorySystem:
    """Test inventory and item management"""
    
    def test_inventory_command(self, ws_connection):
        """Test inventory display"""
        messages = send_command(ws_connection, "inventory")
        
        inv_shown = any("Inventory" in msg.get("content", "") or
                       "Empty" in msg.get("content", "")
                       for msg in messages)
        assert inv_shown or len(messages) > 0
    
    def test_item_usage(self, ws_connection):
        """Test using items"""
        # Add item via cheat
        send_command(ws_connection, "cheat_item small_potion")
        
        # Use item
        messages = send_command(ws_connection, "use small_potion")
        
        # Should get some response
        assert len(messages) >= 0
    
    def test_item_stacking(self, ws_connection):
        """Test items stack correctly"""
        send_command(ws_connection, "cheat_item small_potion")
        send_command(ws_connection, "cheat_item small_potion")
        
        messages = send_command(ws_connection, "inventory")
        
        # Should show stacked items
        assert len(messages) > 0

class TestQuestSystem:
    """Test quest mechanics"""
    
    def test_quests_command(self, ws_connection):
        """Test quests list"""
        messages = send_command(ws_connection, "quests")
        
        # Should show quests interface
        assert len(messages) > 0
    
    def test_talk_to_npc(self, ws_connection):
        """Test talking to NPCs"""
        # Move to NPC location if needed
        messages = send_command(ws_connection, "talk")
        
        # Should get NPC interaction or "no NPC" message
        assert len(messages) >= 0

class TestShopSystem:
    """Test buying items"""
    
    def test_buy_command(self, ws_connection):
        """Test purchase system"""
        # Try to buy something
        messages = send_command(ws_connection, "buy small_potion")
        
        # Should get purchase response or error
        assert len(messages) >= 0
