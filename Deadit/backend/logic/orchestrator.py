import random
from extensions import db
from backend.models.user import User
from backend.models.content import Post, Comment
from backend.logic.generator import ZombieGenerator

class Orchestrator:
    def __init__(self):
        self.generator = ZombieGenerator()

    def orchestrate_moan(self, post_id, parent_comment_id=None, app=None):
        """
        Triggers AI response generation for a new post or a new comment.
        """
        if app:
            with app.app_context():
                self._process(post_id, parent_comment_id)
        else:
            self._process(post_id, parent_comment_id)

    def _process(self, post_id, parent_comment_id):
        try:
            post = Post.query.get(post_id)
            if not post:
                return

            parent_comment = None
            depth = 0
            if parent_comment_id:
                parent_comment = Comment.query.get(parent_comment_id)
                if parent_comment:
                    # Calculate depth
                    temp = parent_comment
                    depth = 1
                    while temp.parent:
                        depth += 1
                        temp = temp.parent

            # Enforce max depth of 3 as per documentation
            if depth >= 3:
                print(f"Skipping AI moan: Max depth {depth} reached.")
                return

            # --- NEW: Pick identity and load persona BEFORE generation ---
            zombie_name, zombie_user = self._get_or_create_zombie(post_id)
            
            from backend.logic.personas import PersonaLoader
            persona_override = PersonaLoader.load_zombie_persona(zombie_name)
            
            # --- ADD: Include subdeadit context in persona_override ---
            from backend.logic.style_adapter import StyleAdapter
            style = StyleAdapter().get_subdeadit_style(post.subdeadit)
            if 'lexicon' in style:
                if 'lexicon' not in persona_override:
                    persona_override['lexicon'] = []
                persona_override['lexicon'].extend(style['lexicon'])
            if 'tone' in style:
                persona_override['tone'] = style['tone']
            
            comment_data = self.generator.generate_comment(
                post, 
                parent_comment=parent_comment, 
                depth=depth,
                persona_override=persona_override
            )
            
            if comment_data:
                self._save_ai_comment(post.id, parent_comment_id, comment_data, zombie_user)
              
        except Exception as e:
            print(f"Orchestration Error: {e}")

    def _get_or_create_zombie(self, post_id):
        import json
        import os
        import glob
        
        # 1. Load Shamblers from roster.json
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__) or os.getcwd()))
        roster_path = os.path.join(base_path, 'personas', 'roster.json')
        
        shamblers = []
        try:
            with open(roster_path, 'r', encoding='utf-8') as f:
                roster = json.load(f)
                shamblers = roster.get('shamblers', [])
        except Exception as e:
            print(f"Error loading roster from {roster_path}: {e}")
            shamblers = ["GoryGarry", "LimpingLarry"] # Fallback

        # 2. Scan Directory for Custom Zombies (Zombie*.json)
        zombies_path = os.path.join(base_path, 'personas', 'zombies')
        custom_zombies = []
        try:
             # Find all files starting with "Zombie"
             files = glob.glob(os.path.join(zombies_path, "Zombie*.json"))
             for f in files:
                 # Extract name: "ZombieRottingRon.json" -> "RottingRon"
                 filename = os.path.basename(f)
                 name = filename.replace("Zombie", "").replace(".json", "")
                 custom_zombies.append(name)
        except Exception as e:
            print(f"Error scanning personas directory: {e}")

        # Combine pools
        zombie_names = custom_zombies + shamblers

        post = Post.query.get(post_id)
        existing_authors = {c.author.username for c in post.comments}
        available_names = [n for n in zombie_names if n not in existing_authors]
        
        zombie_name = random.choice(available_names if available_names else zombie_names)
        zombie_user = User.query.filter_by(username=zombie_name).first()
        
        if not zombie_user:
            zombie_user = User(username=zombie_name, is_zombie=True)
            zombie_user.set_password("brains")
            db.session.add(zombie_user)
            db.session.commit()
            
        return zombie_name, zombie_user

    def _save_ai_comment(self, post_id, parent_comment_id, comment_data, zombie_user):
        # Create the comment
        comment = Comment(
            body=comment_data.get('body', 'Ungh... brains...'),
            flair=comment_data.get('flair'),
            post_id=post_id,
            user_id=zombie_user.id,
            parent_id=parent_comment_id
        )
        db.session.add(comment)
        db.session.commit()
        
        # --- Horde Mentality: Recursive Triggers ---
        import threading
        from flask import current_app
        app = current_app._get_current_object()
        
        # 1. Deepening (Reply to this AI moan)
        # Probability decays: 60% at root, 30% at level 1, 0% at level 2 (since reply would be level 3)
        depth = 0
        temp = comment
        while temp.parent:
            depth += 1
            temp = temp.parent
            
        deep_prob = 0.6 if depth == 0 else (0.3 if depth == 1 else 0)
        if random.random() < deep_prob:
            threading.Thread(target=self.orchestrate_moan, args=(post_id, comment.id, app)).start()
            
        # 2. Branching (New Top-Level moan on this post)
        # 30% chance to simulate another zombie joining the thread independently
        if random.random() < 0.3:
            threading.Thread(target=self.orchestrate_moan, args=(post_id, None, app)).start()

