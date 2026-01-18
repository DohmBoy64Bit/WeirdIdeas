from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
import threading
from backend.models.content import Post, Comment, Vote
from extensions import db

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('feed.html', posts=posts, title='Home')

@bp.route('/dr/<subdeadit>')
def subdeadit(subdeadit):
    # Ensure we search for r/ prefix in DB since that's how they are stored
    db_name = subdeadit if subdeadit.startswith('r/') else f'r/{subdeadit}'
    display_name = db_name
    posts = Post.query.filter_by(subdeadit=db_name).order_by(Post.created_at.desc()).all()
    return render_template('feed.html', posts=posts, title=display_name, current_subdeadit=subdeadit)

@bp.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('thread.html', post=post)

@bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        subdeadit = request.form['subdeadit']
        
        # Ensure subdeadit starts with r/
        if not subdeadit.startswith('r/'):
            subdeadit = f'r/{subdeadit}'
            
        # Official list check
        official_subs = [
            "r/BrainsGoneWild", "r/FreshMeat", "r/MoanHelpDesk", "r/ZombieSurvival",
            "r/ShambleSports", "r/AskRottingOnes", "r/ApocalypseMemes",
            "r/UndeadRelationships", "r/RottingAesthetics", "r/HordeManagement"
        ]
        if subdeadit not in official_subs:
            flash(f"Error: {subdeadit} is not a registered subdeadit.", "danger")
            return redirect(url_for('main.create_post'))
            
        post = Post(title=title, body=body, subdeadit=subdeadit, author=current_user)
        db.session.add(post)
        db.session.commit()
        
        # Trigger AI Response Generation in Background
        try:
            from backend.logic.orchestrator import Orchestrator
            orchestrator = Orchestrator()
            
            # Use current_app._get_current_object() to pass the actual app instance
            app = current_app._get_current_object()
            thread = threading.Thread(target=orchestrator.orchestrate_moan, args=(post.id, None, app))
            thread.start()
            
        except Exception as e:
            print(f"Error initiating background AI task: {e}")
            # Don't fail the written post if AI fails
        
        return redirect(url_for('main.post_detail', post_id=post.id))
        
    prefilled_subdeadit = request.args.get('subdeadit', '')
    return render_template('create_post.html', title='New Moan', prefilled_subdeadit=prefilled_subdeadit)

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get('body')
    parent_id = request.form.get('parent_id')
    
    if body:
        comment = Comment(
            body=body,
            post_id=post_id,
            user_id=current_user.id,
            parent_id=int(parent_id) if parent_id else None
        )
        db.session.add(comment)
        db.session.commit()
        
        # Trigger AI Response for Comment
        try:
            from backend.logic.orchestrator import Orchestrator
            orchestrator = Orchestrator()
            app = current_app._get_current_object()
            thread = threading.Thread(target=orchestrator.orchestrate_moan, args=(post.id, comment.id, app))
            thread.start()
        except Exception as e:
            print(f"Error initiating background AI comment task: {e}")
            
        flash('Moan added!', 'success')
    
    return redirect(url_for('main.post_detail', post_id=post_id))

@bp.route('/vote/<string:item_type>/<int:item_id>/<string:direction>', methods=['POST'])
@login_required
def vote(item_type, item_id, direction):
    if item_type == 'post':
        item = Post.query.get_or_404(item_id)
        existing_vote = Vote.query.filter_by(user_id=current_user.id, post_id=item_id).first()
    else:
        item = Comment.query.get_or_404(item_id)
        existing_vote = Vote.query.filter_by(user_id=current_user.id, comment_id=item_id).first()
        
    score = 1 if direction == 'up' else -1
    
    if existing_vote:
        if existing_vote.score == score:
            # Toggle off: user clicked the same button, remove vote
            item.upvotes -= score
            db.session.delete(existing_vote)
        else:
            # Switch direction: user switched from up to down or vice versa
            item.upvotes += (score - existing_vote.score)
            existing_vote.score = score
    else:
        # New vote
        new_vote = Vote(user_id=current_user.id, score=score)
        if item_type == 'post':
            new_vote.post_id = item_id
        else:
            new_vote.comment_id = item_id
        db.session.add(new_vote)
        item.upvotes += score
        
    db.session.commit()
    return jsonify({'upvotes': item.upvotes})

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('main.index'))
    
    # Search in titles and bodies
    posts = Post.query.filter(
        (Post.title.ilike(f'%{query}%')) | (Post.body.ilike(f'%{query}%'))
    ).order_by(Post.created_at.desc()).all()
    
    return render_template('feed.html', posts=posts, title=f"Search Results: {query}")

from flask import jsonify
