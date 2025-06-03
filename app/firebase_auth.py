import pyrebase

config = {
    "apiKey": "your-api-key",
    "authDomain": "your-app.firebaseapp.com",
    "databaseURL": "https://k-soft-online-ordering-system-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "your-project-id",
    "storageBucket": "your-app.appspot.com",
    "messagingSenderId": "your-messagingSenderId",
    "appId": "your-app-id",
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
