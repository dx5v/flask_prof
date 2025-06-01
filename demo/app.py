from flask import Flask, render_template, request

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Dynamic user route
@app.route('/user/<username>')
def user_profile(username):
    return render_template('user.html', username=username)

# Form input handling
@app.route('/greet', methods=['GET', 'POST'])
def greet():
    if request.method == 'POST':
        name = request.form.get('name')
        return render_template('greet.html', name=name)
    return render_template('greet.html', name=None)

if __name__ == '__main__':
    app.run(debug=True)
