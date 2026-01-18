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

            comment_data = self.generator.generate_comment(post, parent_comment=parent_comment, depth=depth)
            
            if comment_data:
                self._save_ai_comment(post.id, parent_comment_id, comment_data)
                
        except Exception as e:
            print(f"Orchestration Error: {e}")

    def _save_ai_comment(self, post_id, parent_comment_id, comment_data):
        # Find or create a Zombie user
        zombie_names = ["RottingRon", "ShamblingSally", "BrainBuffetBrian", "DecayDave"]
        zombie_name = random.choice(zombie_names)
        zombie_user = User.query.filter_by(username=zombie_name).first()
        
        if not zombie_user:
            zombie_user = User(username=zombie_name, is_zombie=True)
            zombie_user.set_password("brains")
            db.session.add(zombie_user)
            db.session.commit()
        
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

