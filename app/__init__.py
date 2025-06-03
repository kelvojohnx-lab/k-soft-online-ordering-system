from flask import Flask
import pyrebase
from .routes import main
from datetime import datetime


def datetimeformat(value):
    if isinstance(value, int):  # If it's a Unix timestamp in milliseconds
        return datetime.fromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M')
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return value

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # Replace with a strong secret key!

    # Firebase configuration dictionary
    config = {
        "apiKey": "AIzaSyBYNIaS70xfp99WMc497O-G12YkYthRqVI",
        "authDomain": "k-soft-online-ordering-system.firebaseapp.com",
        "databaseURL": "https://k-soft-online-ordering-system-default-rtdb.europe-west1.firebasedatabase.app/",
        "projectId" : "k-soft-online-ordering-system",
        "storageBucket": "k-soft-online-ordering-system.appspot.com",
        "messagingSenderId": "470041103810",
        "appId": "1:470041103810:web:6c5b003395ae9639ec5a5b"
    }

    # Initialize Firebase
    firebase = pyrebase.initialize_app(config)

    # Attach auth and database clients to app
    app.firebase_auth = firebase.auth()
    app.firebase_db   = firebase.database()
    app.config['ADMIN_EMAIL'] = 'anthonymutindak@gmail.com'
    app.config['ADMIN_PASSWORD'] = '401'
    # Register your routes blueprint
    app.register_blueprint(main)

    # Register the Jinja filter here
    app.jinja_env.filters['datetimeformat'] = datetimeformat

    return app
