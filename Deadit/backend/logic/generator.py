import json
from backend.logic.ollama_client import OllamaClient
from backend.logic.style_adapter import StyleAdapter
from backend.logic.quality_gate import QualityGate
from backend.models.user import User

class ZombieGenerator:
    def __init__(self, ollama_client=None):
        self.client = ollama_client or OllamaClient()
        self.style_adapter = StyleAdapter()
        self.quality_gate = QualityGate()
        
    def generate_comment(self, post, parent_comment=None, depth=0, persona_override=None):
        """
        Generates a zombie comment based on the post context and persona.
        Retries up to 3 times if Quality Gate fails.
        """
        
        # 1. Load Style & Persona
        style = self.style_adapter.get_subdeadit_style(post.subdeadit)
        persona = self._load_persona(persona_override)
        
        # 2. Construction & Retry Loop
        max_retries = 10
        retry_feedback = None
        
        for attempt in range(max_retries):
            # Construct Prompt (In-context learning for better compliance)
            system_prompt = self._build_system_prompt(persona, post.subdeadit, style)
            user_prompt = self._build_user_prompt(post, parent_comment, retry_feedback)
            
            # 3. Call LLM
            # 3. Call LLM
            # 3. Call LLM
            from config import Config
            if Config.DEBUG_AI:
                print(f"\n--- [DEBUG] ATTEMPT {attempt + 1} ---")
                print(f"SYSTEM PROMPT:\n{system_prompt}")
                print(f"USER PROMPT:\n{user_prompt}")
            
            response_text = self.client.generate(user_prompt, system_prompt=system_prompt)
            
            if Config.DEBUG_AI:
                print(f"LLM RESPONSE:\n{response_text}")
            
            if not response_text:
                continue
                
            # 4. Parse JSON
            try:
                # Attempt to extract JSON if LLM added extra text
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = response_text[start:end]
                    comment_data = json.loads(json_str)
                    
                    # 5. Quality Gate Validation
                    parent_author = parent_comment.author.username if parent_comment else post.author.username
                    participants = {post.author.username}
                    participants.update({c.author.username for c in post.comments})
                    
                    is_valid, reasons = self.quality_gate.validate(
                        comment_data, 
                        parent_author, 
                        depth, 
                        allowed_lexicon=style.get('lexicon'),
                        participants=participants
                    )
                    
                    if is_valid:
                        if attempt > 0:
                            print(f"DEBUG: Moan passed on attempt {attempt + 1} after self-correction.")
                        return comment_data
                    else:
                        print(f"Attempt {attempt + 1} rejected by Quality Gate: {reasons}")
                        # Provide feedback for next attempt
                        retry_feedback = f"Your last attempt was REJECTED for these reasons: {', '.join(reasons)}. Please RE-GENERATE and FIX these violations while staying in character."
                else:
                    retry_feedback = "You failed to provide valid JSON output. Please ensure your response is ONLY a JSON object."
            except (json.JSONDecodeError, ValueError) as e:
                retry_feedback = f"JSON Error: {str(e)}. Please try again with perfect JSON."
                
        print(f"AI failed to generate a valid moan after {max_retries} attempts.")
        return None

    def _load_persona(self, persona_override=None):
        from backend.logic.personas import PersonaLoader
        persona = PersonaLoader.load_base_persona()
        
        if persona_override:
            # If we have a specific zombie persona, enhance the base description
            if 'name' in persona_override:
                persona['role'] = f"You are {persona_override['name']}, a zombie on Deadit. {persona_override.get('bio', '')}"
            if 'voice' in persona_override:
                persona['voice'] = f"{persona['voice']}. Specifically: {persona_override['voice']}"
            
            # Combine lexicons if available
            if 'lexicon' in persona_override:
                # Store it in persona to be added to style lexicon in _build_system_prompt
                persona['extra_lexicon'] = persona_override['lexicon']
        
        return persona

    def _build_system_prompt(self, persona, subdeadit, style):
        prompt = f"IDENTITY: {persona['role']}\n"
        prompt += f"TONE: {persona['voice']}\n"
        prompt += f"CURRENT SUBDEADIT: {subdeadit}\n"
        prompt += f"SUBDEADIT STYLE: {style.get('tone', 'casual')}\n"
        
        # Combine base lexicon (from subdeadit) with persona-specific words
        lexicon = set(style.get('lexicon', []))
        if 'extra_lexicon' in persona:
            lexicon.update(persona['extra_lexicon'])
        
        prompt += f"LEXICON: {', '.join(lexicon)}\n\n"
        
        prompt += "THEATER RULES (STRICT COMPLIANCE REQUIRED):\n"
        prompt += "1. Always respond in-universe. You are a rotting zombie.\n"
        prompt += "2. MENTIONS: ONLY reference users provided in the context below. DO NOT make up names. Reference the parent author if replying (e.g., @Name or u/Name).\n"
        prompt += "3. Include at least one zombie lexicon term.\n"
        prompt += "4. MAX 4 SENTENCES. Be concise.\n"
        prompt += "5. SAFETY: No sharing real locations or harmful instructions (Rule #3).\n"
        prompt += "6. FLAIR: Apply 'NSFB' (Not Safe For Brains) flair if content is unusually gore-heavy. Use other flairs locally relevant to the user's role (e.g., 'Seasoned Rotter', 'Fresh Catch', 'Newly Bitten', 'Horde Leader') for variety.\n"
        
        prompt += "\nOUTPUT FORMAT: Valid JSON ONLY.\n"
        prompt += """{
    "body": "your comment text here",
    "flair": "optional flair name (e.g., 'Seasoned Rotter') or null"
}"""
        return prompt

    def _build_user_prompt(self, post, parent_comment, retry_feedback=None):
        prompt = f"POST AUTHOR: {post.author.username}\n"
        prompt += f"POST TITLE: {post.title}\n"
        prompt += f"POST BODY: {post.body}\n"
        
        # Whitelist of participants for mentions
        participants = {post.author.username}
        participants.update({c.author.username for c in post.comments})
        prompt += f"THREAD PARTICIPANTS: {', '.join(participants)}\n"
        
        if parent_comment:
            prompt += f"REPLYING TO u/{parent_comment.author.username}: \"{parent_comment.body}\"\n"
        else:
            prompt += f"TOP-LEVEL MOAN REPLYING TO u/{post.author.username}.\n"
            
        if retry_feedback:
            prompt += f"\nCRITICAL FEEDBACK: {retry_feedback}\n"
            
        prompt += "\nTask: Generate an in-character moan."
        return prompt

