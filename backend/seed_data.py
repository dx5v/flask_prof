#!/usr/bin/env python3
from app import app, db
from models import User, Post, Like, Comment
from datetime import datetime, timedelta, timezone
import random

def create_sample_data():
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        Like.query.delete()
        Comment.query.delete()
        Post.query.delete()
        User.query.delete()
        db.session.commit()
        
        # Create users
        print("Creating users...")
        users_data = [
            {'username': 'john_doe', 'password': 'password123'},
            {'username': 'jane_smith', 'password': 'password123'},
            {'username': 'mike_johnson', 'password': 'password123'},
            {'username': 'sarah_wilson', 'password': 'password123'},
            {'username': 'alex_brown', 'password': 'password123'},
            {'username': 'emma_davis', 'password': 'password123'},
            {'username': 'david_miller', 'password': 'password123'},
            {'username': 'lisa_garcia', 'password': 'password123'},
        ]
        
        users = []
        for user_data in users_data:
            user = User(username=user_data['username'])
            user.set_password(user_data['password'])
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"Created {len(users)} users")
        
        # Create follows
        print("Creating follows...")
        follow_pairs = [
            (0, 1), (0, 2), (0, 3),  # john follows jane, mike, sarah
            (1, 0), (1, 4), (1, 5),  # jane follows john, alex, emma
            (2, 0), (2, 1), (2, 6),  # mike follows john, jane, david
            (3, 0), (3, 1), (3, 7),  # sarah follows john, jane, lisa
            (4, 1), (4, 2), (4, 3),  # alex follows jane, mike, sarah
            (5, 0), (5, 4), (5, 6),  # emma follows john, alex, david
            (6, 2), (6, 5), (6, 7),  # david follows mike, emma, lisa
            (7, 3), (7, 4), (7, 6),  # lisa follows sarah, alex, david
        ]
        
        for follower_idx, followed_idx in follow_pairs:
            users[follower_idx].follow(users[followed_idx])
        
        db.session.commit()
        print(f"Created {len(follow_pairs)} follow relationships")
        
        # Create posts
        print("Creating posts...")
        posts_data = [
            {'user_idx': 0, 'caption': 'Beautiful sunset from my balcony! 🌅'},
            {'user_idx': 0, 'caption': 'Coffee and coding - perfect morning combo ☕️💻'},
            {'user_idx': 1, 'caption': 'Exploring the city today! Amazing street art everywhere 🎨'},
            {'user_idx': 1, 'caption': 'Home-cooked pasta night 🍝 Recipe in comments!'},
            {'user_idx': 2, 'caption': 'Mountain hiking adventure! The view was worth every step 🏔️'},
            {'user_idx': 2, 'caption': 'New guitar arrived today, time to practice 🎸'},
            {'user_idx': 3, 'caption': 'Book club meeting was amazing! Currently reading sci-fi 📚'},
            {'user_idx': 3, 'caption': 'Homemade cookies for the weekend 🍪'},
            {'user_idx': 4, 'caption': 'Beach volleyball tournament! Our team made it to finals 🏐'},
            {'user_idx': 4, 'caption': 'Late night photography session in the city 📸'},
            {'user_idx': 5, 'caption': 'Garden is blooming beautifully this spring 🌸'},
            {'user_idx': 5, 'caption': 'Trying out a new art technique today 🎭'},
            {'user_idx': 6, 'caption': 'Weekend camping trip - nature is the best therapy 🏕️'},
            {'user_idx': 7, 'caption': 'Marathon training complete! Ready for race day 🏃‍♀️'},
        ]
        
        posts = []
        base_time = datetime.now(timezone.utc) - timedelta(days=7)
        
        for i, post_data in enumerate(posts_data):
            post = Post(
                caption=post_data['caption'],
                user_id=users[post_data['user_idx']].id,
                timestamp=base_time + timedelta(hours=i*3)
            )
            posts.append(post)
            db.session.add(post)
        
        db.session.commit()
        print(f"Created {len(posts)} posts")
        
        # Create likes
        print("Creating likes...")
        likes_data = []
        for post_idx, post in enumerate(posts):
            # Random number of likes per post (1-6 likes)
            num_likes = random.randint(1, 6)
            liked_users = random.sample(users, num_likes)
            
            for user in liked_users:
                if user.id != post.user_id:  # Users don't like their own posts
                    likes_data.append({'user_id': user.id, 'post_id': post.id})
        
        for like_data in likes_data:
            like = Like(user_id=like_data['user_id'], post_id=like_data['post_id'])
            db.session.add(like)
        
        db.session.commit()
        print(f"Created {len(likes_data)} likes")
        
        # Create comments
        print("Creating comments...")
        comments_data = [
            {'post_idx': 0, 'user_idx': 1, 'text': 'Absolutely gorgeous! 😍'},
            {'post_idx': 0, 'user_idx': 2, 'text': 'I love sunsets like this!'},
            {'post_idx': 1, 'user_idx': 3, 'text': 'What kind of coffee do you prefer?'},
            {'post_idx': 2, 'user_idx': 0, 'text': 'That street art is incredible!'},
            {'post_idx': 2, 'user_idx': 4, 'text': 'Which part of the city is this?'},
            {'post_idx': 3, 'user_idx': 5, 'text': 'Recipe please! 🙏'},
            {'post_idx': 3, 'user_idx': 6, 'text': 'Looks delicious!'},
            {'post_idx': 4, 'user_idx': 1, 'text': 'Amazing view! Which mountain?'},
            {'post_idx': 5, 'user_idx': 7, 'text': 'What kind of guitar did you get?'},
            {'post_idx': 6, 'user_idx': 2, 'text': 'What book are you reading?'},
            {'post_idx': 7, 'user_idx': 4, 'text': 'Those look amazing! 🤤'},
            {'post_idx': 8, 'user_idx': 3, 'text': 'Congrats on making finals!'},
            {'post_idx': 9, 'user_idx': 5, 'text': 'Great night photography!'},
            {'post_idx': 10, 'user_idx': 6, 'text': 'Your garden is beautiful!'},
            {'post_idx': 11, 'user_idx': 7, 'text': 'Love the artistic approach!'},
            {'post_idx': 12, 'user_idx': 0, 'text': 'Camping is the best! Where did you go?'},
            {'post_idx': 13, 'user_idx': 1, 'text': 'Good luck with the marathon! 💪'},
        ]
        
        for comment_data in comments_data:
            comment = Comment(
                text=comment_data['text'],
                user_id=users[comment_data['user_idx']].id,
                post_id=posts[comment_data['post_idx']].id,
                timestamp=posts[comment_data['post_idx']].timestamp + timedelta(minutes=random.randint(10, 120))
            )
            db.session.add(comment)
        
        db.session.commit()
        print(f"Created {len(comments_data)} comments")
        
        # Print summary
        print("\n=== SEED DATA SUMMARY ===")
        print(f"Users: {User.query.count()}")
        print(f"Posts: {Post.query.count()}")
        print(f"Likes: {Like.query.count()}")
        print(f"Comments: {Comment.query.count()}")
        print(f"Follow relationships: {len(follow_pairs)}")
        
        print("\n=== USER ACCOUNTS ===")
        for user in User.query.all():
            followers_count = user.followers.count()
            following_count = user.followed.count()
            posts_count = len(user.posts)
            print(f"@{user.username} - {posts_count} posts, {followers_count} followers, {following_count} following")

if __name__ == '__main__':
    create_sample_data()
    print("\n✅ Sample data created successfully!")