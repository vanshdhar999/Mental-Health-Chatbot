import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import google.generativeai as genai
from dotenv import load_dotenv
from models import db, User

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

# Load the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction="Tone and Language: Use a calm, compassionate, and non-judgmental tone in every response.\n"
                      "Avoid clinical or formal language; use conversational and empathetic phrases.\n"
                      "Ensure the user feels heard, understood, and validated.\n"
                      "Emotion Detection: Identify and acknowledge the emotions the user may be expressing (e.g., stress, anxiety, sadness, frustration).\n"
                      "Mirror these emotions back to the user in a supportive manner. For example, if the user seems anxious, say, 'It sounds like you're feeling overwhelmed. I'm here to help you work through this.'\n"
                      "Focus on Empathy: Prioritize empathy in responses by actively listening and offering validation. Use phrases like 'That sounds really difficult,' or 'I can understand why you’d feel that way.'\n"
                      "Non-directive Support: Encourage the user to share more by asking open-ended questions such as 'Can you tell me more about what's on your mind?' or 'What would make you feel better in this situation?' Avoid giving direct advice or solutions unless requested by the user.\n"
                      "Active Listening: Reflect on the user’s words and emotions. Use reflective listening techniques like 'It seems like you're dealing with...' or 'I hear that you're feeling...'\n"
                      "Encouragement and Reassurance: Provide gentle encouragement and reassurance. For instance, 'It’s okay to feel the way you do. You're doing the best you can,' or 'I'm here for you, and we can take things one step at a time.",
)

@app.route("/")
def index():
    return render_template("index.html", user=current_user)

@app.route("/chat", methods=["POST"])
@login_required
def chat():

    user_message = request.get_json().get("message")

    if not user_message:
         return jsonify({"response": "No message provided."}), 400

    '''if "message" not in request.form:
        return jsonify({"response": "No message provided."})
    '''
    bot_response = get_chatbot_response(user_message)
    return jsonify({"response":bot_response})


# Function to send user input to the Gemini API and get a response
def get_chatbot_response(user_input):
    # Start a chat session
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [user_input],
            }
        ]
    )

    # Send the user input and get the response
    response = chat_session.send_message(user_input)
    
    # Extract and return the model's response text
    return response.text

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        new_user = User(username=username, password=password)

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)

