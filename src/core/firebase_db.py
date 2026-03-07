import os
import pyrebase
from dotenv import load_dotenv

# Load environment variables from frontend .env file in the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

# Firebase configuration
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
}

class FirebaseManager:
    def __init__(self):
        self.firebase = pyrebase.initialize_app(firebase_config)
        self.auth = self.firebase.auth()
        self.db = self.firebase.database()
        
        # Keep track of the currently logged in user
        self.current_user = None

    def sign_up(self, name, dob_age, email, password):
        """
        Creates a new user and stores their profile data in the database.
        dob_age: The calculated age from DOB or an age string.
        """
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            self.current_user = user
            uid = user['localId']
            
            # Store profile info in Realtime Database under 'users/{uid}'
            data = {
                "name": name,
                "age": dob_age,
                "email": email
            }
            self.db.child("users").child(uid).set(data)
            return True, "Registration successful."
        except Exception as e:
            # Parse Pyrebase error messages
            error_msg = str(e)
            return False, f"Registration failed: {error_msg}"

    def login(self, email, password):
        """
        Authenticates a user and retrieves their profile data.
        """
        try:
            user = self.auth.sign_in_with_email_and_password(email, password)
            self.current_user = user
            
            # Fetch user profile data
            uid = user['localId']
            profile = self.db.child("users").child(uid).get()
            
            if profile.val():
                return True, profile.val()
            else:
                return True, {"name": "User", "age": None}
                
        except Exception as e:
            error_msg = str(e)
            return False, f"Login failed: Invalid email or password."

    def get_current_user_profile(self):
        """
        Returns the profile of the currently logged in user, or None if not logged in.
        """
        if not self.current_user:
            return None
            
        uid = self.current_user['localId']
        profile = self.db.child("users").child(uid).get()
        return profile.val()
        
    def logout(self):
        self.current_user = None
