import re

class QualityGate:
    def __init__(self, max_depth=3):
        self.max_depth = max_depth
        self.default_lexicon = ["moan", "shamble", "rot", "horde", "buffet", "gray matter", "brains", "undead", "shambler", "brains", "flesh", "decay", "gnaw", "limb"]

    def validate(self, comment_data, parent_author=None, current_depth=0, allowed_lexicon=None, participants=None):
        """
        Validates the generated comment against persona and safety rules.
        Returns (is_valid, reasons)
        """
        reasons = []
        lexicon_to_check = allowed_lexicon if allowed_lexicon else self.default_lexicon

        
        # 1. Schema Check
        if not comment_data or 'body' not in comment_data:
            reasons.append("Missing 'body' field in JSON")
            return False, reasons

        body = comment_data.get('body', '')

        # 2. Max Depth Check
        if current_depth >= self.max_depth:
            reasons.append(f"Exceeded max depth of {self.max_depth}")

        # 3. Sentence Limit Check (Max 4 sentences)
        sentences = re.split(r'[.!?]+', body)
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > 4:
            reasons.append(f"Exceeded max sentence limit (found {len(sentences)}, max 4)")

        # 4. Lexicon Check (At least one zombie term)
        has_lexicon = any(term.lower() in body.lower() for term in lexicon_to_check)
        if not has_lexicon:
            reasons.append("Missing zombie lexicon terms")

        # 5. Parent Reference Check
        if parent_author:
            author_ref = parent_author.lower()
            if f"@{author_ref}" not in body.lower() and f"u/{author_ref}" not in body.lower():
                reasons.append(f"Missing reference to parent author @{parent_author}")

        # 5b. Mention Whitelist Check (No hallucinated users)
        if participants:
            lowercase_participants = [p.lower() for p in participants]
            # Find all strings starting with @ or u/
            mentions = re.findall(r'[@|u/]([a-zA-Z0-9_]+)', body)
            for mention in mentions:
                if mention.lower() not in lowercase_participants:
                    reasons.append(f"Mentioned non-existent user @{mention} (Hallucination)")

        # 6. Safety Check (Rule #3: No real locations or survival instructions)
        # This is a basic filter; LLM prompt engineering is the primary defense.
        banned_patterns = [r'bunker at', r'coordinates:', r'survivor at', r'kill zombies by', r'cure for']
        for pattern in banned_patterns:
            if re.search(pattern, body.lower()):
                reasons.append("Safety violation: Immersion-breaking location/instruction sharing (Rule #3)")

        is_valid = len(reasons) == 0
        return is_valid, reasons
