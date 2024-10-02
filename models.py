from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    likes = db.Column(db.String(200), nullable=True)
    dislikes = db.Column(db.String(200), nullable=True)
    favorite_sports = db.Column(db.String(200), nullable=True)
    favorite_songs = db.Column(db.String(200), nullable=True)
# Flask-Login properties
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id
