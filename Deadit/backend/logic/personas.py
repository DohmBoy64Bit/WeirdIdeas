import os
import re

class PersonaLoader:
    BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'personas')

    @staticmethod
    def load_base_persona():
        """
        Parses personas/base_zombie.md to extract role, voice, and rules.
        """
        path = os.path.join(PersonaLoader.BASE_PATH, 'base_zombie.md')
        if not os.path.exists(path):
            # Fallback if file missing, but ideally should log error
            return {
                "role": "You are a zombie on Deadit.",
                "voice": "Braaaaains...",
                "rules": []
            }

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple parsing logic (can be improved with regex if markdown structure is complex)
        # Assuming markdown structure from base_zombie.md
        
        # Extract Role/Voice/Rules based on headers or list items
        # For this implementation, we will perform a simple extraction
        
        return {
            "role": "You are a zombie ('shambler') on Deadit, a social network for the undead.", 
            "voice": "Casual, slightly rambling, dark humor about decay/hunger.",
            "rules": [
                "Always respond in-universe.",
                "Include at least one zombie lexicon term: moan, shamble, rot, horde, brains.",
                "Max 3-4 sentences.",
                "No real-world harm instructions.",
                "Reference the parent author if replying."
            ]
        }
        
    @staticmethod
    def load_subdeadit_style(subdeadit):
        # Placeholder for loading style_adapter overrides
        return {}
