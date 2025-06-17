from flask import Flask, request, jsonify
from config import DATABASE_URI
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables at startup
with app.app_context():
    db.create_all()

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.json.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": f"User {username} added."})

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username} for u in users])

if __name__ == '__main__':
    app.run(debug=True)
