import json
import os

class StyleAdapter:
    SUBDEADIT_PERSONAS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'personas', 'subdeadits')

    def __init__(self):
        # Create directory if it doesn't exist
        if not os.path.exists(self.SUBDEADIT_PERSONAS_PATH):
            os.makedirs(self.SUBDEADIT_PERSONAS_PATH)

    def adapt(self, comment_body, subdeadit, persona_overrides=None):
        """
        Adapts the comment body to subdeadit-specific style.
        In this implementation, we will pass subdeadit-specific context to the generator prompt
        rather than doing post-processing text replacement, as LLMs handle tone better during generation.
        However, we store subdeadit-specific lexicon/tone settings here to be injected.
        """
        style = self.get_subdeadit_style(subdeadit)
        if persona_overrides:
            style.update(persona_overrides)
        return style

    def get_subdeadit_style(self, subdeadit):
        """
        Loads subdeadit-specific style JSON if it exists.
        """
        # Remove /dr/ or r/ prefix for filename
        clean_name = subdeadit.replace('r/', '').replace('/dr/', '')
        path = os.path.join(self.SUBDEADIT_PERSONAS_PATH, f"{clean_name}.json")
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        
        # Default subdeadit styles
        defaults = {
            "r/BrainsGoneWild": {
                "lexicon": ["buffet", "scent", "feast", "fresh catch", "curves", "rotting"],
                "tone": "enthusiastic, hungry, slightly sexualized in a zombie way"
            },
            "r/ZombieSurvival": {
                "lexicon": ["bunker", "ammo", "hiding spot", "survivor", "trap", "prepper"],
                "tone": "paranoid, tactical, cautious"
            },
            "r/MoanHelpDesk": {
                "lexicon": ["detached", "staple", "bandage", "decay", "sew", "glue"],
                "tone": "frustrated, technical, helpful"
            },
            "r/FreshMeat": {
                "lexicon": ["living", "warm", "heartbeat", "pulse", "chase"],
                "tone": "predatory, focused, primal"
            },
            "r/ShambleSports": {
                "lexicon": ["race", "limp", "crawl", "finish line", "stamina"],
                "tone": "competitive, slow-paced, athletic"
            },
            "r/AskRottingOnes": {
                "lexicon": ["advice", "wisdom", "old age", "decomposition", "reminisce"],
                "tone": "philosophical, helpful, nostalgic"
            },
            "r/ApocalypseMemes": {
                "lexicon": ["humor", "joke", "funny", "ironic", "clumsy"],
                "tone": "sarcastic, witty, lighthearted"
            },
            "r/UndeadRelationships": {
                "lexicon": ["love", "heart", "attachment", "date", "together"],
                "tone": "romantic, dramatic, messy"
            },
            "r/RottingAesthetics": {
                "lexicon": ["beauty", "pale", "mold", "maggot", "texture"],
                "tone": "appreciative, artistic, sensory"
            },
            "r/HordeManagement": {
                "lexicon": ["group", "lead", "follow", "direction", "coordination"],
                "tone": "authoritative, organizational, strategic"
            }
        }
        
        return defaults.get(subdeadit, {
            "lexicon": ["shamble", "moan", "rot", "brains"],
            "tone": "casual undead"
        })
