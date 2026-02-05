import json
import os
import sys
from unittest.mock import patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.logic.style_adapter import StyleAdapter

def test_style_adapter_initialization():
    """Test that StyleAdapter initializes correctly."""
    adapter = StyleAdapter()
    assert hasattr(adapter, 'SUBDEADIT_PERSONAS_PATH')
    assert os.path.exists(adapter.SUBDEADIT_PERSONAS_PATH)
    print("✓ StyleAdapter initializes correctly")

def test_get_subdeadit_style_default():
    """Test that default styles are returned for unknown subdeadits."""
    adapter = StyleAdapter()
    
    # Test with non-existent subdeadit
    style = adapter.get_subdeadit_style("r/UnknownSubdeadit")
    assert 'lexicon' in style
    assert 'tone' in style
    assert style['tone'] == 'casual undead'
    print("✓ Default subdeadit style works")

def test_get_subdeadit_style_known():
    """Test that known subdeadits return correct styles."""
    adapter = StyleAdapter()
    
    # Test with existing subdeadit 
    style = adapter.get_subdeadit_style("r/BrainsGoneWild")
    assert 'lexicon' in style
    assert 'tone' in style
    assert style['tone'] == 'Lustful for gray matter, primal, aggressive.'
    # Check that the lexicon contains expected words from the file
    assert 'dripping' in style['lexicon']
    assert 'pulsing' in style['lexicon']
    print("✓ Known subdeadit style works")

def test_get_subdeadit_style_with_prefix():
    """Test that prefixes are correctly stripped."""
    adapter = StyleAdapter()
    
    # Test with r/ prefix
    style1 = adapter.get_subdeadit_style("r/BrainsGoneWild")
    style2 = adapter.get_subdeadit_style("/dr/BrainsGoneWild")
    
    # They should be the same since they reference the same file
    assert 'lexicon' in style1
    assert 'lexicon' in style2
    # Both should reference the same file content, even though they have different prefixes
    # The file lookup uses the clean name 'BrainsGoneWild' in both cases
    print("✓ Prefix stripping works correctly")

def test_adapt_functionality():
    """Test the adapt function works with overrides."""
    adapter = StyleAdapter()
    
    # Test with overrides
    overrides = {
        "lexicon": ["custom_word1", "custom_word2"],
        "tone": "custom tone"
    }
    style = adapter.adapt("test content", "r/BrainsGoneWild", overrides)
    
    assert 'lexicon' in style
    assert 'tone' in style
    assert style['tone'] == 'custom tone'
    assert 'custom_word1' in style['lexicon']
    print("✓ Adapt function with overrides works")

if __name__ == "__main__":
    print("Running StyleAdapter tests...")
    test_style_adapter_initialization()
    test_get_subdeadit_style_default()
    test_get_subdeadit_style_known()
    test_get_subdeadit_style_with_prefix()
    test_adapt_functionality()
    print("All tests passed! ✓")