import os
import re

class PersonaLoader:
    BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__) or os.getcwd())), 'personas')

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
                "voice": "Braaains..",
                "rules": []
            }

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse markdown sections with regex
        # Extract Voice & Tone (Capture the bullet points before "Example style")
        voice_match = re.search(r'## 1\. Voice & Tone\s*(.*?)(?=\*\*Example style:\*\*|\n\n##)', content, re.DOTALL)
        if voice_match:
             voice = voice_match.group(1).strip()
             # Clean up markdown bullet characters if present
             voice = voice.replace('- ', '').replace('* ', '')
        else:
             voice = "Casual, slightly rambling, dark humor about decay/hunger."

        # Extract Behavioral Rules (list items)
        rules_match = re.search(r'## 2\. Behavioral Rules\s*(.*?)(?=\s*---|\s*$)', content, re.DOTALL)
        rules_content = rules_match.group(1) if rules_match else ""
        
        # Extract individual rules from markdown list
        rules = []
        rule_lines = re.findall(r'\d+\.\s*(.*?)(?=\d+\.\s*|\s*$)', rules_content)
        for line in rule_lines:
            # Remove markdown list prefix from rule
            clean_line = re.sub(r'^\d+\.\s*', '', line.strip())
            rules.append(clean_line)
        
        # Set role based on the document
        role = "You are a zombie ('shambler') on Deadit, a social network for the undead."

        return {
            "role": role,
            "voice": voice,
            "rules": rules
        }
        
    @staticmethod
    def load_zombie_persona(name):
        """
        Loads a specific zombie's persona from personas/zombies/Zombie<name>.json
        """
        path = os.path.join(PersonaLoader.BASE_PATH, 'zombies', f"Zombie{name}.json")
        if not os.path.exists(path):
            # Fallback: check if old format exists or just return empty
            old_path = os.path.join(PersonaLoader.BASE_PATH, 'zombies', f"{name}.json")
            if os.path.exists(old_path):
                 path = old_path
            else:
                return {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        except Exception as e:
            print(f"Error loading zombie persona {name}: {e}")
            return {}
    
    @staticmethod
    def load_subdeadit_style(subdeadit):
        """
        Loads community overrides from personas/subdeadits/<subdeadit>.json
        """
        # Remove r/ prefix for filename
        filename = subdeadit[2:] if subdeadit.startswith('r/') else subdeadit
        path = os.path.join(PersonaLoader.BASE_PATH, 'subdeadits', f"{filename}.json")
        
        if not os.path.exists(path):
            return {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                import json
                return json.load(f)
        except Exception as e:
            print(f"Error loading subdeadit style {subdeadit}: {e}")
            return {}