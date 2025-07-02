from flask import Flask, request, render_template, redirect, url_for, flash, session, get_flashed_messages
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Post, Like, Comment, followers
from auth_decorators import login_required, post_owner_required, comment_owner_required, get_current_user
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///social_media.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

db.init_app(app)
jwt = JWTManager(app)

# Initialize database tables
with app.app_context():
    db.create_all()

# Note: get_current_user() is now imported from auth_decorators.py

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        user = User(username=username)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        flash('Registration successful! Welcome to Photo App!', 'success')
        return redirect(url_for('home'))
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    # Clear any existing flash messages to prevent accumulation
    get_flashed_messages()
    
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    
    # Get posts from followed users and own posts
    following_ids = [u.id for u in current_user.followed]
    following_ids.append(current_user.id)  # Include own posts
    
    posts = Post.query.filter(Post.user_id.in_(following_ids)).order_by(Post.timestamp.desc()).all()
    
    # Get user's likes for heart icon display
    user_likes = [like.post_id for like in current_user.likes]
    
    # Get suggested users (users not followed)
    suggested_users = User.query.filter(
        ~User.id.in_(following_ids)
    ).limit(5).all()
    
    # Get story users (just followed users for now)
    story_users = current_user.followed.limit(6).all()
    
    return render_template('home.html', 
                         posts=posts, 
                         user_likes=user_likes,
                         suggested_users=suggested_users,
                         story_users=story_users)

@app.route('/follow/<int:user_id>')
def follow_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    user_to_follow = User.query.get_or_404(user_id)
    
    if current_user.id == user_id:
        flash('You cannot follow yourself', 'error')
    else:
        current_user.follow(user_to_follow)
        db.session.commit()
        flash(f'You are now following {user_to_follow.username}', 'success')
    
    return redirect(url_for('home'))

@app.route('/unfollow/<int:user_id>')
def unfollow_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    user_to_unfollow = User.query.get_or_404(user_id)
    
    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    flash(f'You unfollowed {user_to_unfollow.username}', 'info')
    
    return redirect(url_for('home'))

@app.route('/toggle_like/<int:post_id>')
def toggle_like(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
    else:
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
    
    return redirect(url_for('home') + f'#post-{post_id}')

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    post = Post.query.get_or_404(post_id)
    text = request.form.get('text')
    
    if text and text.strip():
        comment = Comment(text=text.strip(), user_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added!', 'success')
    
    return redirect(url_for('home') + f'#post-{post_id}')

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = get_current_user()
    caption = request.form.get('caption')
    
    if caption and caption.strip():
        post = Post(caption=caption.strip(), user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
    
    return redirect(url_for('home'))

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@post_owner_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        caption = request.form.get('caption')
        if caption and caption.strip():
            post.caption = caption.strip()
            db.session.commit()
            flash('Post updated successfully!', 'success')
            return redirect(url_for('home') + f'#post-{post_id}')
        else:
            flash('Caption cannot be empty', 'error')
    
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@post_owner_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@comment_owner_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if request.method == 'POST':
        text = request.form.get('text')
        if text and text.strip():
            comment.text = text.strip()
            db.session.commit()
            flash('Comment updated successfully!', 'success')
            return redirect(url_for('home') + f'#post-{comment.post_id}')
        else:
            flash('Comment cannot be empty', 'error')
    
    return render_template('edit_comment.html', comment=comment)

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@comment_owner_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id  # Store post_id before deleting comment
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('home') + f'#post-{post_id}')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)