import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

class Config:
    """Configuration management for the application"""
    
    def __init__(self, env_file: str = None):
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self.BASE_DIR = Path(__file__).parent.parent
        self.ENV = os.getenv('FLASK_ENV', 'development')
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
    # Application Settings
    @property
    def SECRET_KEY(self) -> str:
        key = os.getenv('SECRET_KEY')
        if not key:
            if self.DEBUG:
                return 'dev-secret-key-change-in-production'
            raise ValueError("SECRET_KEY must be set in production")
        return key
    
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv('DATABASE_URL', f'sqlite:///{self.BASE_DIR}/data/mental_health_app.db')
    
    @property
    def REDIS_URL(self) -> str:
        return os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # API Keys
    @property
    def GOOGLE_API_KEY(self) -> str:
        return os.getenv('GOOGLE_API_KEY', '')
    
    @property
    def GROQ_API_KEY(self) -> str:
        return os.getenv('GROQ_API_KEY', '')
    
    @property
    def OPENAI_API_KEY(self) -> str:
        return os.getenv('OPENAI_API_KEY', '')
    
    @property
    def ELEVENLABS_API_KEY(self) -> str:
        return os.getenv('ELEVENLABS_API_KEY', '')
    
    # Server Configuration
    @property
    def HOST(self) -> str:
        return os.getenv('HOST', '0.0.0.0')
    
    @property
    def PORT(self) -> int:
        return int(os.getenv('PORT', 5000))
    
    @property
    def FASTAPI_PORT(self) -> int:
        return int(os.getenv('FASTAPI_PORT', 8000))
    
    @property
    def WORKERS(self) -> int:
        return int(os.getenv('WORKERS', 1))
    
    # Security Settings
    @property
    def SESSION_COOKIE_SECURE(self) -> bool:
        return os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    
    @property
    def SESSION_COOKIE_HTTPONLY(self) -> bool:
        return os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    
    @property
    def SESSION_COOKIE_SAMESITE(self) -> str:
        return os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    
    @property
    def PERMANENT_SESSION_LIFETIME(self) -> int:
        return int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))
    
    # CORS Settings
    @property
    def ALLOWED_ORIGINS(self) -> list:
        origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')
        return [origin.strip() for origin in origins.split(',')]
    
    # Logging
    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def LOG_FILE(self) -> str:
        return os.getenv('LOG_FILE', str(self.BASE_DIR / 'logs' / 'app.log'))
    
    # File Upload Settings
    @property
    def MAX_UPLOAD_SIZE(self) -> int:
        return int(os.getenv('MAX_UPLOAD_SIZE', 10485760))  # 10MB
    
    @property
    def UPLOAD_FOLDER(self) -> str:
        return os.getenv('UPLOAD_FOLDER', str(self.BASE_DIR / 'uploads'))
    
    # Rate Limiting
    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        return int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    
    @property
    def RATE_LIMIT_PER_HOUR(self) -> int:
        return int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
    
    # Model Settings
    @property
    def WHISPER_MODEL(self) -> str:
        return os.getenv('WHISPER_MODEL', 'tiny')
    
    @property
    def TTS_VOICE(self) -> str:
        return os.getenv('TTS_VOICE', 'en-US-AriaNeural')
    
    # Vector Store Settings
    @property
    def VECTOR_STORE_PATH(self) -> str:
        return os.getenv('VECTOR_STORE_PATH', str(self.BASE_DIR / 'data' / 'vector_store'))
    
    @property
    def EMBEDDING_MODEL(self) -> str:
        return os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    
    # Monitoring
    @property
    def SENTRY_DSN(self) -> str:
        return os.getenv('SENTRY_DSN', '')
    
    @property
    def HEALTH_CHECK_INTERVAL(self) -> int:
        return int(os.getenv('HEALTH_CHECK_INTERVAL', 30))
    
    def get_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            'ENV': self.ENV,
            'DEBUG': self.DEBUG,
            'SECRET_KEY': '***' if self.SECRET_KEY else None,
            'DATABASE_URL': self.DATABASE_URL,
            'HOST': self.HOST,
            'PORT': self.PORT,
            'FASTAPI_PORT': self.FASTAPI_PORT,
            'WORKERS': self.WORKERS,
            'LOG_LEVEL': self.LOG_LEVEL,
            'WHISPER_MODEL': self.WHISPER_MODEL,
            'TTS_VOICE': self.TTS_VOICE,
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    def __init__(self):
        super().__init__()
        self.ENV = 'development'
        self.DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    def __init__(self):
        super().__init__()
        self.ENV = 'production'
        self.DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    def __init__(self):
        super().__init__()
        self.ENV = 'testing'
        self.DEBUG = True
        self.DATABASE_URL = 'sqlite:///:memory:'

def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Global config instance
config = get_config()
