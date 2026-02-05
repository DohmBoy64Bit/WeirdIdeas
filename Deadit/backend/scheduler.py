from flask_apscheduler import APScheduler
from backend.logic.orchestrator import Orchestrator
import random
from config import Config

scheduler = APScheduler()

def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()

# Schedule the Life Cycle Job
# We use a single interval job that decides what to do based on probability
@scheduler.task('interval', id='deadit_lifecycle', seconds=60, misfire_grace_time=900)
def deadit_lifecycle():
    # We need to access 'app' here. Since we are outside init_scheduler, 
    # we need the current_app context or pass app. 
    # APScheduler running in Flask context usually handles this if app is running.
    # However, 'current_app' works inside the job if the scheduler was init'd with app.
    from flask import current_app
    
    # Safety check if we are in app context
    try:
        app = current_app._get_current_object()
    except RuntimeError:
        # If running in background thread via scheduler, try looking at the bound app
        if scheduler.app:
            app = scheduler.app
        else:
            print("⚠️  No app context found for lifecycle.")
            return

    with app.app_context():
        # Only run if explicitly enabled in production or dev
        check_interval = Config.RUMBLE_INTERVAL if hasattr(Config, 'RUMBLE_INTERVAL') else 300
        
        # Simple randomness check to decouple full execution from the 60s tick
        # If interval is 300s (5 mins), we want roughly a 1/5 chance per minute
        # For simplicity in this demo, we kept the logic simple. 
        # But to respect RUMBLE_INTERVAL strictly, we should just rely on this function firing.
        # But the decorator says 'seconds=60'. 
        
        # Let's trust the probabilities I wrote earlier:
        print("💀 [LifeCycle] Heartbeat...")
        orchestrator = Orchestrator()
        
        # Action 1: New Post (Rare)
        action_taken = False
        new_thread_chance = Config.RUMBLE_NEW_THREAD_CHANCE
        if random.random() < new_thread_chance:
            print("💀 [LifeCycle] Triggering New Zombie Thread...")
            orchestrator.orchestrate_post(app)
            action_taken = True
            
        # Action 2: Horde Replier (Common)
        reply_chance = Config.RUMBLE_REPLY_CHANCE
        if random.random() < reply_chance:
            from backend.models.content import Post
            # Get posts from last 24 hours
            recent_posts = Post.query.order_by(Post.created_at.desc()).limit(20).all()
            if recent_posts:
                target_post = random.choice(recent_posts)
                print(f"💀 [LifeCycle] Triggering Reply to {target_post.title}...")
                orchestrator.orchestrate_moan(target_post.id, app=app)
                action_taken = True
        
        if not action_taken:
            print("💀 [LifeCycle] Resting... (No chaos this tick)")

