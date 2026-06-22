import os

# Manual dotenv loader to keep setup simple and dependency-free
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    # Strip quotes if present
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    os.environ[k] = v

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'unfv-tutor-secret-key-12345')
    
    # Database configuration
    # Check for DATABASE_URL (common in Docker/Heroku), fallback to SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Standardize postgres:// to postgresql:// if needed
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///tutor_unfv.db'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # LLM API configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Notification configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'tutor.inteligente@unfv.edu.pe')
