import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Find the absolute path of the directory containing this file
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for session management and CSRF protection
    # IMPORTANT: Change this to a random, secret value in production!
    # You can generate one using: python -c 'import secrets; print(secrets.token_hex())'
    #SECRET_KEY = os.environ.get('SECRET_KEY') 
    SECRET_KEY = 'ImE4MTllYzg4OTNjNDkyYTEyZGMxNTA3YTAwNTlhOGFmN2MzZDBhZjAi.Z-roBA.S0dB181qB-opq3_7_vYSr4IGA8c'
    WTF_CSRF_ENABLED=False

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'points.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Disable modification tracking to save resources

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads/avatars')
    ALLOWED_EXTENSIONS_EXCEL = {'xlsx', 'xls'}
    ALLOWED_EXTENSIONS_AVATAR = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload size (adjust as needed)

    # Ensure the upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)