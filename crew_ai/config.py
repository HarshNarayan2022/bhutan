import os
from dotenv import load_dotenv

load_dotenv()

def get_config():
    """
    Returns a dictionary of configuration values used across the chatbot system.
    Pulls values from environment variables where appropriate.
    """
    return {
        # API Keys
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),

        # LLM settings
        "llm_model": os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile"),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.0")),
        "llm_max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "llm_timeout": int(os.getenv("LLM_TIMEOUT", "30")),
        "llm_max_retries": int(os.getenv("LLM_MAX_RETRIES", "2")),

        # Tool model settings
        "crisis_model": os.getenv("CRISIS_MODEL", "lmsdmn/crisis-detection-model"),

        # Questionnaire path
        "questionnaire_file": os.getenv("QUESTIONNAIRE_FILE", "questionnaire.json"),

        # Default profile for anonymous or test users
        "default_user_profile": {
            "id": "anon_user",
            "location": "null",
            "history": "null",
            "preferences": "null"
        },

        "CONDITION_TO_QUESTIONNAIRE" : {
                "anxiety": "GAD-7",
                "depression": "PHQ-9",
                "substance": "DAST-10",
                "alcohol": "AUDIT",
                "bipolar": "Bipolar",
                "audit": "AUDIT",
                "dast-10": "DAST-10",
                "phq-9": "PHQ-9",
                "gad-7": "GAD-7"
        }        
    }
