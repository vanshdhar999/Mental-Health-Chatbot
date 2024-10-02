import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import google.generativeai as genai
from dotenv import load_dotenv
from models import db, User
from config import model


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Ensure to use a secure secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect here if a user is not logged in

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



@app.route("/")
def index():
    return render_template("homepage.html", user=current_user)

@app.route("/chat", methods=["GET"])
@login_required
def chat():
    
    return render_template("chat.html")

@app.route("/send_message", methods=["POST"])
def send_message():
    user_message = request.get_json().get("message")

    if not user_message:
        return jsonify({"response":"No message provided"}), 400
    
    bot_response = get_chatbot_response(user_message)
    return jsonify({"response":bot_response})
# Function to send user input to the Gemini API and get a response
def get_chatbot_response(user_input):
    # Collect user information for personalization
    user_info = f"""
    User's Name: {current_user.name}
    Likes: {', '.join(current_user.likes)}
    Dislikes: {', '.join(current_user.dislikes)}
    Favorite Sports: {', '.join(current_user.favorite_sports)}
    Favorite Songs: {', '.join(current_user.favorite_songs)}
    """

    # Prepend the user information to the user input
    full_input = user_info + "\nUser says: " + user_input

    # Start a chat session without context
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [full_input],
            }
        ]
    )

    # Send the user input and get the response
    response = chat_session.send_message(full_input)

    # Extract and return the model's response text
    return response.text

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        age = request.form["age"]
        likes = request.form.getlist("likes")  # Assuming likes is a multiple-choice input
        dislikes = request.form.getlist("dislikes")  # Assuming dislikes is a multiple-choice input
        favorite_sports = request.form.getlist("favorite_sports")  # Assuming sports is a multiple-choice input
        favorite_songs = request.form.getlist("favorite_songs")  # Assuming songs is a multiple-choice input

        new_user = User(
            username=username,
            password=password,
            name=name,
            age=age,
            likes=", ".join(likes),  # Convert list to a comma-separated string
            dislikes=", ".join(dislikes),  # Convert list to a comma-separated string
            favorite_sports=", ".join(favorite_sports),  # Convert list to a comma-separated string
            favorite_songs=", ".join(favorite_songs)  # Convert list to a comma-separated string
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful! You can now log in.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash("Username already exists. Please choose a different one.", "danger")
            print(e)  # Print exception for debugging
    
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            session["username"] = user.username
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.username)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/mood-zone')
def mood_zone():
    return render_template('mood_zone.html')

@app.route('/mood/<mood_name>')
def mood_page(mood_name):
    return render_template(f'moods/{mood_name}.html')

@app.route("/users")
def view_users():
    users = User.query.all()  # Query all users from the database
    return render_template("user.html", users=users)  # Render a template to display users

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)

