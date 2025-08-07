from flask import Flask, render_template, request, session, redirect, url_for, jsonify, Response , send_file
import requests
import numpy as np
import os
import io
from datetime import datetime
import json
from pathlib import Path
import re
import uuid
import gc  # For garbage collection
# Add these imports at the top
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import secrets


import asyncio
import edge_tts


import tempfile

from functools import lru_cache
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class MessageRequest:
    message: str
    user_context: Dict[str, Any]
    session_id: Optional[str] = None

@dataclass  
class ChatMessageRequest:
    message: str
    user_context: Dict[str, Any]
    session_id: Optional[str] = None


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.getenv('FLASK_SECRET_KEY', 'mental_health_app'))
app.config["SESSION_COOKIE_NAME"] = "mental_health_app_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour

# FastAPI backend URL - configurable for different deployment environments
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')


# Helper function to extract topics
def extract_topics(text):
    """Extract mental health related topics from text."""
    topics = []
    topic_patterns = {
        "anxiety": r"\b(anxious|anxiety|worried|worry|nervous)\b",
        "depression": r"\b(depress|sad|hopeless|down|blue)\b",
        "stress": r"\b(stress|overwhelm|pressure|burden)\b",
        "sleep": r"\b(sleep|insomnia|tired|fatigue|rest)\b",
        "therapy": r"\b(therapy|therapist|counseling|treatment)\b",
        "medication": r"\b(medication|medicine|pills|prescription)\b",
        "coping": r"\b(cope|coping|manage|deal|handle)\b",
        "relationships": r"\b(relationship|family|friend|partner|social)\b",
        "work": r"\b(work|job|career|workplace|boss)\b",
        "school": r"\b(school|test|exam|study|fail|grade)\b",
        "self-care": r"\b(self-care|exercise|meditation|mindfulness)\b"
    }
    
    text_lower = text.lower()
    for topic, pattern in topic_patterns.items():
        if re.search(pattern, text_lower):
            topics.append(topic)
    
    return topics


# Load Whisper model once at startup with memory optimization
whisper_model = None

# Check if AI models should be skipped (free tier mode)
if os.environ.get('SKIP_AI_MODELS') == '1' or os.environ.get('MEMORY_MODE') == 'free_tier':
    print("🔧 Skipping Whisper model loading - running in free tier mode")
    whisper_model = None
else:
    try:
        import openai_whisper as whisper  # Try openai-whisper first
        if hasattr(whisper, 'load_model'):
            # Use tiny model with memory optimization for Render
            whisper_model = whisper.load_model("tiny", device="cpu", download_root="/tmp")
            print("✅ OpenAI Whisper model loaded successfully (tiny, CPU-optimized)")
        else:
            print("⚠️ OpenAI Whisper load_model not available")
            whisper_model = None
    except ImportError:
        try:
            import whisper  # Fallback to regular whisper
            if hasattr(whisper, 'load_model'):
                whisper_model = whisper.load_model("tiny", device="cpu", download_root="/tmp")
                print("✅ Whisper model loaded successfully (tiny, CPU-optimized)")
            else:
                print("⚠️ Whisper load_model not available, using fallback")
                whisper_model = None
        except Exception as e:
            print(f"⚠️ Whisper not available: {e}")
            whisper_model = None

# Cache for TTS to avoid regenerating same text
tts_cache = {}

@lru_cache(maxsize=100)
def get_cached_tts(text_hash):
    """Cache TTS results to avoid regenerating same text"""
    return tts_cache.get(text_hash)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Check if Whisper is available
        if not whisper_model:
            return jsonify({
                'error': 'Voice transcription is not available in this deployment mode. Please type your message instead.',
                'transcript': ''
            }), 503
        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        audio_data = audio_file.read()
        print(f"Received audio file: {audio_file.filename}, size: {len(audio_data)} bytes")
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            print(f"Saved temp file: {temp_file.name}")
            
            try:
                # Skip WAV conversion for speed - try direct transcription first
                if whisper_model:
                    print("Starting fast transcription...")
                    
                    # Use fastest Whisper settings with memory optimization
                    result = whisper_model.transcribe(
                        temp_file.name,
                        language='en',
                        task='transcribe',
                        temperature=0.0,
                        no_speech_threshold=0.3,  # More lenient
                        logprob_threshold=-1.0,   # More lenient
                        compression_ratio_threshold=2.4,  # Faster processing
                        fp16=False,  # Use FP32 to avoid CPU warnings
                        verbose=False,  # Reduce memory usage
                        word_timestamps=False  # Reduce memory usage
                    )
                    
                    transcript = result['text'].strip()
                    print(f"Fast transcription result: '{transcript}'")
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
                    
                    # Force garbage collection to free memory
                    del result
                    gc.collect()
                    
                    if not transcript or len(transcript) < 2:
                        return jsonify({
                            'transcript': '',
                            'error': 'No speech detected. Please speak clearly and hold the button longer.'
                        })
                    
                    return jsonify({'transcript': transcript})
                else:
                    return jsonify({'error': 'Whisper model not available'}), 500
                    
            except Exception as e:
                print(f"Transcription error: {e}")
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
                return jsonify({'error': f'Transcription failed: {str(e)}'}), 500
                
    except Exception as e:
        print(f"General transcription error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'en-US-AriaNeural')  # Changed to AriaNeural (more reliable)
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        clean_text = clean_text_for_tts(text)
        
        # Ensure we have some text after cleaning
        if not clean_text or len(clean_text.strip()) < 3:
            return jsonify({'error': 'Text too short after cleaning'}), 400
        
        print(f"Generating TTS for: '{clean_text[:100]}...' with voice: {voice}")
        
        # Check cache first
        cache_key = f"edge_{voice}_{hashlib.md5(clean_text.encode()).hexdigest()}"
        if cache_key in tts_cache:
            print("Using cached TTS")
            return send_file(
                io.BytesIO(tts_cache[cache_key]), 
                mimetype='audio/mpeg', 
                as_attachment=False
            )
        
        # Generate with Edge TTS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            audio_data = loop.run_until_complete(generate_edge_tts(clean_text, voice))
            
            if not audio_data or len(audio_data) < 100:
                raise Exception(f"No audio generated. Voice: {voice}, Text length: {len(clean_text)}")
            
            # Cache the result
            tts_cache[cache_key] = audio_data
            
            print(f"Edge TTS generated successfully, audio size: {len(audio_data)} bytes")
            
            return send_file(
                io.BytesIO(audio_data), 
                mimetype='audio/mpeg', 
                as_attachment=False
            )
            
        finally:
            loop.close()
        
    except Exception as e:
        print(f"Edge TTS error: {e}")
        # Fallback to a simple message
        try:
            fallback_text = "I apologize, but I'm having trouble with voice generation right now."
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                audio_data = loop.run_until_complete(generate_edge_tts(fallback_text, 'en-US-AriaNeural'))
                if audio_data and len(audio_data) > 100:
                    return send_file(
                        io.BytesIO(audio_data), 
                        mimetype='audio/mpeg', 
                        as_attachment=False
                    )
            finally:
                loop.close()
        except:
            pass
        
        return jsonify({'error': f'TTS generation failed: {str(e)}'}), 500

async def generate_edge_tts(text, voice):
    """Generate speech using Edge TTS with speed control"""
    try:
        print(f"Edge TTS - Voice: {voice}, Text: '{text[:50]}...'")
        
        # Validate voice format
        if not voice.startswith('en-'):
            voice = 'en-US-AriaNeural'
        
        # Create communicate object with speed settings
        communicate = edge_tts.Communicate(
            text, 
            voice,
            rate="+15%",  # Increase speed by 40%
            # pitch="+0Hz",  # Keep normal pitch
            # volume="+0%"   # Keep normal volume
        )
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        print(f"Generated {len(audio_data)} bytes of audio at +40% speed")
        return audio_data
        
    except Exception as e:
        print(f"Error in generate_edge_tts: {e}")
        raise e

def clean_text_for_tts(text):
    """Enhanced text cleaning for TTS"""
    if not text:
        return ''


    
    # Remove markdown formatting but keep the content
    text = text.replace('```', '')  # Remove code block markers
    text = text.replace('`', '')    # Remove inline code markers
    text = text.replace('**', '')   # Remove bold markers
    text = text.replace('*', '')    # Remove italic markers
    text = text.replace('__', '')   # Remove underline markers
    text = text.replace('_', '')    # Remove italic markers
    text = text.replace('#', '')    # Remove heading markers
    
    # Convert markdown lists to spoken format
    text = text.replace('- ', '. ')
    text = text.replace('+ ', '. ')
    text = text.replace('* ', '. ')
    
    # Handle numbered lists
    import re
    text = re.sub(r'^\s*\d+\.\s+', '. ', text, flags=re.MULTILINE)
    
    # Clean up links - keep the text, remove the URL
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Replace multiple newlines with periods
    text = re.sub(r'\n{2,}', '. ', text)
    text = text.replace('\n', ' ')
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Ensure sentences end properly
    text = text.strip()
    if text and not text.endswith(('.', '!', '?')):
        text += '.'
    
    # Only limit if extremely long (increased limit)
    if len(text) > 1000:  # Increased from 300
        # Try to cut at sentence boundary
        sentences = text.split('. ')
        truncated = ''
        for sentence in sentences:
            if len(truncated + sentence + '. ') <= 950:
                truncated += sentence + '. '
            else:
                break
        if truncated:
            text = truncated.strip()
        else:
            text = text[:950] + '...'
    
    return text



# Database setup
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# Get database URL from environment
database_url = os.getenv('DATABASE_URL', os.getenv('SUPABASE_DB_URI', 'sqlite:///mental_health_app.db'))
print(f"🔗 Connecting to database: {database_url.split('://')[0]}://...")

engine = create_engine(database_url)
DBSession = sessionmaker(bind=engine)

# User Model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    has_completed_initial_survey = Column(Boolean, default=False)
    initial_survey_date = Column(DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class UserAssessment(Base):
    __tablename__ = 'user_assessments'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assessment_type = Column(String(50), default='comprehensive')
    basic_info = Column(Text)  # JSON string
    questionnaire_data = Column(Text)  # JSON string
    assessment_result = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Latest assessment

class ConversationHistory(Base):
    __tablename__ = 'conversation_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    agent_name = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)



# Create tables
Base.metadata.create_all(engine)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Initialize session on each request
@app.before_request
def initialize_session():
    if 'user_data' not in session:
        session['user_data'] = {
            "name": "Guest",
            "age": "",
            "gender": "",
            "emotion": "neutral/unsure",
            "score": None,
            "result": "Unknown"
        }



# Update the home route 
@app.route("/")
def home():
    return render_template("home.html")

# Health check endpoint for Render deployment
@app.route("/health")
def health():
    """Health check endpoint for monitoring and load balancers"""
    try:
        # Basic health check - ensure app is responsive
        from sqlalchemy import text
        db_session = DBSession()
        # Simple database connectivity test
        db_session.execute(text("SELECT 1"))
        db_session.close()
        
        return jsonify({
            "status": "healthy",
            "service": "Mental Health Chatbot Flask App",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "Mental Health Chatbot Flask App",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

# Update the login route 
# Update the login route to load user history
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        db_session = DBSession()
        
        user = db_session.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db_session.commit()
            
            # Set basic session
            session['user_id'] = user.id
            session['username'] = user.username
            
            # Load user's latest assessment data
            latest_assessment = db_session.query(UserAssessment).filter_by(
                user_id=user.id, 
                is_active=True
            ).order_by(UserAssessment.created_at.desc()).first()
            
            if latest_assessment:
                # Restore assessment data to session
                session['assessment_data'] = {
                    'basic_info': json.loads(latest_assessment.basic_info),
                    'questionnaire_data': json.loads(latest_assessment.questionnaire_data),
                    'assessment_result': json.loads(latest_assessment.assessment_result),
                    'completed_date': latest_assessment.created_at.isoformat()
                }
                
                basic_info = json.loads(latest_assessment.basic_info)
                assessment_result = json.loads(latest_assessment.assessment_result)
                
                session['user_data'] = {
                    'name': user.full_name or basic_info.get('name', ''),
                    'age': basic_info.get('age', ''),
                    'gender': basic_info.get('gender', ''),
                    'location': basic_info.get('location', ''),
                    'emotion': basic_info.get('emotion', 'neutral'),
                    'has_completed_survey': True,
                    'result': assessment_result.get('overall_status', 'Assessment Complete'),
                    'assessment_date': latest_assessment.created_at.strftime('%Y-%m-%d')
                }
                
                print(f"✅ Loaded assessment data for user {user.username}")
            else:
                # No previous assessment
                session['user_data'] = {
                    'name': user.full_name,
                    'has_completed_survey': False,
                    'result': 'No Assessment'
                }
                print(f"ℹ️ No previous assessment found for user {user.username}")
            
            if remember:
                session.permanent = True
            
            db_session.close()
            return redirect(url_for('user_dashboard'))
        else:
            db_session.close()
            return render_template('home.html', 
                                 login_error='Invalid username or password', 
                                 show_login_modal=True)
    
    return render_template('home.html', show_login_modal=True)

# Update the signup route (around line 178)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords match
        if password != confirm_password:
            return render_template('home.html', 
                                 signup_error='Passwords do not match',
                                 show_signup_modal=True)
        
        db_session = DBSession()
        
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            db_session.close()
            return render_template('home.html', 
                                 signup_error='Invalid username format',
                                 show_signup_modal=True)
        
        # Check if user exists
        existing_user = db_session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            db_session.close()
            # Provide more specific error message
            if existing_user.username == username and existing_user.email == email:
                error_msg = 'Both username and email are already registered'
            elif existing_user.username == username:
                error_msg = f'Username "{username}" is already taken'
            else:
                error_msg = f'Email "{email}" is already registered'
            
            return render_template('home.html', 
                                signup_error=error_msg,
                                show_signup_modal=True)
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name
        )
        new_user.set_password(password)
        
        db_session.add(new_user)
        db_session.commit()
        
        # Auto-login the new user
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['user_data'] = {
            'name': new_user.full_name,
            'has_completed_survey': False
        }
        
        db_session.close()
        
        # Redirect to user dashboard
        return redirect(url_for('user_dashboard'))
    
    return render_template('home.html', show_signup_modal=True)
# Find your user_dashboard function and replace it with:

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    """User dashboard"""
    user_data = session.get('user_data', {})
    
    # Option 1: Use the dashboard template we created
    return render_template('user_dashboard.html', user_data=user_data)
    
    # Option 2: Or redirect to chatbot instead
    # return redirect(url_for('chatbot'))

# Add new route for assessment
@app.route('/assessment')
@login_required
def assessment():
    """Show the assessment form with step management"""
    # Initialize assessment session if not exists
    if 'assessment_data' not in session:
        session['assessment_data'] = {}
        session['current_step'] = 1
    
    current_step = session.get('current_step', 1)
    return render_template('assessment.html', current_step=current_step, 
                         assessment_data=session.get('assessment_data', {}))

# Add/update the assessment submission route (around line 650)
@app.route('/assessment/submit', methods=['POST'])
def submit_assessment():
    try:
        # Get all form data
        form_data = request.form.to_dict()
        
        # Extract basic information
        basic_info = {
            'name': form_data.get('Name', ''),
            'age': form_data.get('Age', ''),
            'gender': form_data.get('Sex', ''),
            'location': form_data.get('Location', ''),
            'days_indoors': form_data.get('days_indoors', ''),
            'emotion': form_data.get('Emotion', ''),
            'history_of_mental_illness': form_data.get('history_of_mental_illness', ''),
            'treatment': form_data.get('treatment', '')
        }
        
        # Extract questionnaire responses
        questionnaire_data = {}
        
        # PHQ-9 responses
        phq9_scores = []
        for i in range(1, 10):
            score = int(form_data.get(f'PHQ9_{i}', 0))
            phq9_scores.append(score)
        questionnaire_data['PHQ9'] = phq9_scores
        questionnaire_data['PHQ9_total'] = sum(phq9_scores)
        
        # GAD-7 responses
        gad7_scores = []
        for i in range(1, 8):
            score = int(form_data.get(f'GAD7_{i}', 0))
            gad7_scores.append(score)
        questionnaire_data['GAD7'] = gad7_scores
        questionnaire_data['GAD7_total'] = sum(gad7_scores)
        
        # DAST-10 responses
        dast_scores = []
        for i in range(1, 11):
            response = form_data.get(f'DAST_{i}', 'No')
            score = 1 if response == 'Yes' else 0
            dast_scores.append(score)
        questionnaire_data['DAST'] = dast_scores
        questionnaire_data['DAST_total'] = sum(dast_scores)
        
        # AUDIT responses
        audit_scores = []
        audit_mapping = {
            'Never': 0, 'Monthly or less': 1, '2 to 4 times a month': 2,
            '2 to 3 times a week': 3, '4 or more times a week': 4,
            '1 or 2': 0, '3 or 4': 1, '5 or 6': 2, '7, 8, or 9': 3, '10 or more': 4,
            'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4,
            'No': 0, 'Yes, but not in the last year': 2, 'Yes, during the last year': 4
        }
        
        for i in range(1, 11):
            response = form_data.get(f'AUDIT_{i}', 'Never')
            score = audit_mapping.get(response, 0)
            audit_scores.append(score)
        questionnaire_data['AUDIT'] = audit_scores
        questionnaire_data['AUDIT_total'] = sum(audit_scores)
        
        # Bipolar responses
        bipolar_scores = []
        for i in range(1, 12):
            response = form_data.get(f'BIPOLAR_{i}', 'No')
            score = 1 if response == 'Yes' else 0
            bipolar_scores.append(score)
        questionnaire_data['BIPOLAR'] = bipolar_scores
        questionnaire_data['BIPOLAR_total'] = sum(bipolar_scores)
        
        # Generate assessment interpretation
        assessment_result = generate_assessment_interpretation(questionnaire_data)
        
        # Store in session for chatbot use
        session['assessment_data'] = {
            'basic_info': basic_info,
            'questionnaire_data': questionnaire_data,
            'assessment_result': assessment_result,
            'completed_date': datetime.now().isoformat()
        }
        
        # Save to database for logged-in users
        if session.get('user_id'):
            db_session = DBSession()
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            
            if user:
                # Mark previous assessments as inactive
                db_session.query(UserAssessment).filter_by(
                    user_id=user.id, 
                    is_active=True
                ).update({'is_active': False})
                
                # Create new assessment record
                new_assessment = UserAssessment(
                    user_id=user.id,
                    assessment_type='comprehensive',
                    basic_info=json.dumps(basic_info),
                    questionnaire_data=json.dumps(questionnaire_data),
                    assessment_result=json.dumps(assessment_result),
                    is_active=True
                )
                
                # Update user completion status
                user.has_completed_initial_survey = True
                user.initial_survey_date = datetime.utcnow()
                
                db_session.add(new_assessment)
                db_session.commit()
                
                print(f"✅ Saved assessment to database for user {user.username}")
            
            db_session.close()
        
        # Update session user data
        session['user_data'].update({
            'age': basic_info['age'],
            'gender': basic_info['gender'],
            'location': basic_info['location'],
            'emotion': basic_info['emotion'],
            'has_completed_survey': True,
            'result': assessment_result.get('overall_status', 'Assessment Complete')
        })
        
        session.modified = True
        
        # Redirect to chatbot with assessment complete flag
        return redirect(url_for('chatbot', assessment_complete=True))
        
    except Exception as e:
        print(f"Error submitting assessment: {e}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('assessment'))

def generate_assessment_interpretation(data):
    """Generate interpretation of assessment scores"""
    result = {
        'detailed_scores': {},
        'recommendations': [],
        'emergency_info': None,
        'overall_status': 'Normal'
    }
    
    # PHQ-9 interpretation
    phq9_total = data.get('PHQ9_total', 0)
    if phq9_total <= 4:
        phq9_level = 'Minimal depression'
    elif phq9_total <= 9:
        phq9_level = 'Mild depression'
    elif phq9_total <= 14:
        phq9_level = 'Moderate depression'
    elif phq9_total <= 19:
        phq9_level = 'Moderately severe depression'
    else:
        phq9_level = 'Severe depression'
    
    result['detailed_scores']['PHQ9'] = {
        'score': phq9_total,
        'level': phq9_level,
        'max_score': 27
    }
    
    # GAD-7 interpretation
    gad7_total = data.get('GAD7_total', 0)
    if gad7_total <= 4:
        gad7_level = 'Minimal anxiety'
    elif gad7_total <= 9:
        gad7_level = 'Mild anxiety'
    elif gad7_total <= 14:
        gad7_level = 'Moderate anxiety'
    else:
        gad7_level = 'Severe anxiety'
    
    result['detailed_scores']['GAD7'] = {
        'score': gad7_total,
        'level': gad7_level,
        'max_score': 21
    }
    
    # DAST interpretation
    dast_total = data.get('DAST_total', 0)
    if dast_total == 0:
        dast_level = 'No drug problems reported'
    elif dast_total <= 2:
        dast_level = 'Low level'
    elif dast_total <= 5:
        dast_level = 'Moderate level'
    else:
        dast_level = 'Substantial to severe level'
    
    result['detailed_scores']['DAST'] = {
        'score': dast_total,
        'level': dast_level,
        'max_score': 10
    }
    
    # AUDIT interpretation
    audit_total = data.get('AUDIT_total', 0)
    if audit_total <= 7:
        audit_level = 'Low risk'
    elif audit_total <= 15:
        audit_level = 'Hazardous drinking'
    elif audit_total <= 19:
        audit_level = 'Harmful drinking'
    else:
        audit_level = 'Possible alcohol dependence'
    
    result['detailed_scores']['AUDIT'] = {
        'score': audit_total,
        'level': audit_level,
        'max_score': 40
    }
    
    # Bipolar interpretation
    bipolar_total = data.get('BIPOLAR_total', 0)
    if bipolar_total <= 6:
        bipolar_level = 'Unlikely'
    else:
        bipolar_level = 'Possible bipolar symptoms'
    
    result['detailed_scores']['BIPOLAR'] = {
        'score': bipolar_total,
        'level': bipolar_level,
        'max_score': 11
    }
    
    # Overall status and recommendations
    high_scores = []
    if phq9_total >= 10:
        high_scores.append('depression')
    if gad7_total >= 10:
        high_scores.append('anxiety')
    if dast_total >= 3:
        high_scores.append('substance use')
    if audit_total >= 8:
        high_scores.append('alcohol use')
    if bipolar_total >= 7:
        high_scores.append('bipolar symptoms')
    
    if high_scores:
        result['overall_status'] = 'Elevated concerns detected'
        result['recommendations'].extend([
            'Consider speaking with a mental health professional',
            'These scores suggest you may benefit from professional support',
            'Remember that early intervention can be very helpful'
        ])
    else:
        result['overall_status'] = 'No significant concerns detected'
        result['recommendations'].extend([
            'Continue maintaining good mental health practices',
            'Stay connected with supportive people in your life',
            'Don\'t hesitate to seek help if you notice changes in your mood or behavior'
        ])
    
    # Check for emergency situations (PHQ-9 question 9)
    if data.get('PHQ9', [0]*9)[8] >= 1:  # Question 9 about self-harm thoughts
        result['emergency_info'] = {
            'level': 'high',
            'message': 'You indicated thoughts of self-harm. Please reach out for immediate support.',
            'resources': [
                'Emergency: Call 112 (Bhutan Emergency)',
                'Mental Health Helpline: Contact your local health center',
                'Crisis support is available 24/7'
            ]
        }
        result['overall_status'] = 'Immediate support recommended'
    
    return result

def process_complete_assessment():
    """Process the complete assessment and calculate scores"""
    try:
        assessment_data = session.get('assessment_data', {})
        
        # Import questionnaire processing (with fallback for missing dependencies)
        try:
            from crew_ai.questionnaire import (
                calculate_phq9_score, calculate_gad7_score, 
                calculate_dast10_score, calculate_audit_score, 
                calculate_bipolar_score, get_assessment_recommendations
            )
            use_advanced_scoring = True
        except ImportError:
            print("⚠️ Advanced scoring unavailable - using basic scoring")
            use_advanced_scoring = False
        
        # Calculate scores for each questionnaire
        scores = {}
        
        if use_advanced_scoring:
            # PHQ-9 Depression Score
            phq9_responses = [int(assessment_data.get(f'PHQ9_{i}', 0)) for i in range(1, 10)]
            scores['phq9'] = calculate_phq9_score(phq9_responses)
            
            # GAD-7 Anxiety Score  
            gad7_responses = [int(assessment_data.get(f'GAD7_{i}', 0)) for i in range(1, 8)]
            scores['gad7'] = calculate_gad7_score(gad7_responses)
            
            # DAST-10 Substance Use Score
            dast_responses = []
            for i in range(1, 11):
                response = assessment_data.get(f'DAST_{i}', 'No')
                # Convert to score based on question (some are reverse scored)
                if i == 3:  # Question 3 is reverse scored
                    dast_responses.append(1 if response == 'No' else 0)
                else:
                    dast_responses.append(1 if response == 'Yes' else 0)
            scores['dast10'] = calculate_dast10_score(dast_responses)
        else:
            # Basic scoring when advanced functions not available
            # PHQ-9 Depression Score (sum of responses)
            phq9_responses = [int(assessment_data.get(f'PHQ9_{i}', 0)) for i in range(1, 10)]
            scores['phq9'] = {
                'score': sum(phq9_responses),
                'interpretation': 'Basic scoring - total: ' + str(sum(phq9_responses)),
                'severity': 'mild' if sum(phq9_responses) < 10 else 'moderate' if sum(phq9_responses) < 15 else 'severe'
            }
            
            # GAD-7 Anxiety Score (sum of responses)
            gad7_responses = [int(assessment_data.get(f'GAD7_{i}', 0)) for i in range(1, 8)]
            scores['gad7'] = {
                'score': sum(gad7_responses),
                'interpretation': 'Basic scoring - total: ' + str(sum(gad7_responses)),
                'severity': 'mild' if sum(gad7_responses) < 10 else 'moderate' if sum(gad7_responses) < 15 else 'severe'
            }
            
            # Basic DAST-10 scoring
            scores['dast10'] = {
                'score': 0,
                'interpretation': 'Basic scoring not available for substance use assessment',
                'severity': 'unknown'
            }
        
        if use_advanced_scoring:
            # AUDIT Alcohol Use Score
            audit_responses = []
            audit_scoring = {
                'AUDIT_1': {'Never': 0, 'Monthly or less': 1, '2 to 4 times a month': 2, '2 to 3 times a week': 3, '4 or more times a week': 4},
                'AUDIT_2': {'1 or 2': 0, '3 or 4': 1, '5 or 6': 2, '7, 8, or 9': 3, '10 or more': 4},
                'AUDIT_3': {'Never': 0, 'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4},
                'AUDIT_4': {'Never': 0, 'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4},
                'AUDIT_5': {'Never': 0, 'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4},
                'AUDIT_6': {'Never': 0, 'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4},
                'AUDIT_7': {'Never': 0, 'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4},
                'AUDIT_8': {'Never': 0, 'Less than monthly': 1, 'Monthly': 2, 'Weekly': 3, 'Daily or almost daily': 4},
                'AUDIT_9': {'No': 0, 'Yes, but not in the last year': 2, 'Yes, during the last year': 4},
                'AUDIT_10': {'No': 0, 'Yes, but not in the last year': 2, 'Yes, during the last year': 4}
            }
            
            for i in range(1, 11):
                field = f'AUDIT_{i}'
                response = assessment_data.get(field, '')
                score = audit_scoring.get(field, {}).get(response, 0)
                audit_responses.append(score)
            scores['audit'] = calculate_audit_score(audit_responses)
            
            # Bipolar Screening Score
            bipolar_responses = [1 if assessment_data.get(f'BIPOLAR_{i}', 'No') == 'Yes' else 0 for i in range(1, 12)]
            scores['bipolar'] = calculate_bipolar_score(bipolar_responses)
        else:
            # Basic AUDIT scoring
            scores['audit'] = {
                'score': 0,
                'interpretation': 'Basic scoring not available for alcohol assessment',
                'severity': 'unknown'
            }
            
            # Basic Bipolar scoring
            scores['bipolar'] = {
                'score': 0,
                'interpretation': 'Basic scoring not available for bipolar assessment', 
                'severity': 'unknown'
            }
        
        # Calculate overall assessment
        if use_advanced_scoring:
            recommendations = get_assessment_recommendations(scores)
        else:
            # Basic recommendations
            recommendations = {
                'overall_assessment': 'Basic assessment completed. Professional evaluation recommended for detailed analysis.',
                'next_steps': ['Consult with a mental health professional', 'Monitor your mental health regularly'],
                'resources': ['Contact local health services', 'Consider professional counseling']
            }
        
        # Store results in session for chatbot context
        assessment_results = {
            'scores': scores,
            'recommendations': recommendations,
            'basic_info': {
                'name': assessment_data.get('Name', ''),
                'age': assessment_data.get('Age', ''),
                'gender': assessment_data.get('Sex', ''),
                'location': assessment_data.get('Location', ''),
                'emotion': assessment_data.get('Emotion', 'neutral')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Update user session with assessment results
        session['assessment_results'] = assessment_results
        session['user_data'] = {
            'name': assessment_data.get('Name', session.get('user_data', {}).get('name', '')),
            'age': assessment_data.get('Age', ''),
            'gender': assessment_data.get('Sex', ''),
            'emotion': assessment_data.get('Emotion', 'neutral'),
            'score': scores,
            'result': recommendations.get('overall_status', 'Completed'),
            'assessment_complete': True
        }
        
        # Clear assessment process data
        session.pop('assessment_data', None)
        session.pop('current_step', None)
        session.modified = True
        
        # Redirect to chatbot with assessment results
        return redirect(url_for('chatbot'))
        
    except Exception as e:
        print(f"Error processing assessment: {e}")
        return render_template('assessment.html', 
                             error="There was an error processing your assessment. Please try again.")
    

@app.route('/chatbot')
def chatbot():
    """Main chatbot interface"""
    user_data = session.get('user_data', {})
    is_guest = session.get('is_guest', False)
    
    # Check if user has completed assessment
    has_assessment = 'assessment_data' in session
    assessment_complete = request.args.get('assessment_complete', False)
    
    # For logged-in users who haven't completed assessment, suggest it
    suggest_assessment = (
        not is_guest and 
        not has_assessment and 
        not user_data.get('has_completed_survey', False)
    )
    
    # Initialize chat session if not exists
    if 'chat_session' not in session:
        session['chat_session'] = {
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'user_name': user_data.get('name', 'Guest'),
            'messages': [],
            'topics': []
        }
    print(f"Chatbot session: {session['chat_session']}")
    return render_template('ChatbotUI.html', 
                         user_data=user_data,
                         is_guest=is_guest,
                         suggest_assessment=suggest_assessment,
                         assessment_complete=assessment_complete,
                         has_assessment=has_assessment,
                         chat_history=session['chat_session'].get('messages', []))



@app.route('/guest_access')
def guest_access():
    # Set guest session
    session['user_data'] = {
        'name': 'Guest',
        'age': '',
        'gender': '',
        'emotion': 'neutral/unsure',
        'score': None,
        'result': 'Unknown'
    }
    session['is_guest'] = True
    # Guests go directly to chatbot (they can't access assessment)
    return redirect(url_for('chatbot'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/about")
def about():
    return render_template("aboutt.html")


# Update the chat route (around line 320)
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        user_data = data.get('user_data', {})
        
        # Get user data from session
        session_user_data = session.get('user_data', {})
        user_emotion = session_user_data.get('emotion', 'neutral/unsure')
        user_name = session_user_data.get('name', 'Guest')
        prediction_result = session_user_data.get('result', '') or 'Unknown'
        user_age = session_user_data.get('age', '')

        # Track message count
        message_count = session.get('message_count', 0) + 1
        session['message_count'] = message_count

        # Initialize chat session if not exists
        if 'chat_session' not in session:
            session['chat_session'] = {
                'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'user_name': user_name,
                'messages': [],
                'topics': []
            }

        # Add user message to session
        user_topics = extract_topics(message)
        session['chat_session']['messages'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'topics': user_topics
        })
        
        # Prepare context for backend
        user_context = {
            "emotion": user_emotion,
            "name": user_name,
            "mental_health_status": prediction_result,
            "age": user_age,
            "original_query": message,
            "message_count": message_count
        }
        
        # Add enhanced context if available from professional assessment
        if 'assessment_data' in session:
            assessment_data = session['assessment_data']
            user_context.update({
                "detailed_scores": assessment_data.get('assessment_result', {}).get('detailed_scores', {}),
                "recommendations": assessment_data.get('assessment_result', {}).get('recommendations', []),
                "assessment_type": "comprehensive",
                "emergency_info": assessment_data.get('assessment_result', {}).get('emergency_info')
            })

        # Use the unified FastAPI endpoint - it handles everything automatically
        try:
            response = requests.post(
                f"{BACKEND_URL}/process_message",  # Single unified endpoint
                json={
                    "message": message,
                    "user_context": user_context,
                    "session_id": session['chat_session']['session_id']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "I'm sorry, I couldn't process your request.")
                agent_name = result.get("agent", "Assistant")
                method_used = result.get("method", "unknown")
                
                print(f"✅ FastAPI Response - Agent: {agent_name}, Method: {method_used}")
                
                # Add assistant response to session
                response_topics = extract_topics(response_text)
                session['chat_session']['messages'].append({
                    'role': 'assistant',
                    'content': response_text,
                    'timestamp': datetime.now().isoformat(),
                    'agent': agent_name,
                    'method': method_used,
                    'topics': response_topics
                })
                
                # Mark session as modified
                session.modified = True
                
                return jsonify({
                    "response": response_text,
                    "agent": agent_name,
                    "method": method_used
                })
            else:
                print(f"FastAPI Backend error: {response.status_code} - {response.text}")
                return _flask_fallback_response(message, user_context)
                
        except requests.exceptions.RequestException as e:
            print(f"Backend connection error: {e}")
            return _flask_fallback_response(message, user_context)
            
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({
            "response": "I apologize, but I encountered an error. Please try again.",
            "agent": "Error Handler"
        }), 500

# Update send_message route (around line 1036)
@app.route("/send_message", methods=["POST"])
def send_message():
    try:
        user_query = request.form.get("message", "")
        
        # Get user data from session
        user_data = session.get('user_data', {})
        user_emotion = user_data.get('emotion', 'neutral/unsure')
        user_name = user_data.get('name', 'Guest')
        prediction_result = user_data.get('result', '') or 'Unknown'
        user_age = user_data.get('age', '')

        # Track message count
        message_count = session.get('message_count', 0) + 1
        session['message_count'] = message_count
        session.modified = True

        # Initialize chat session if not exists
        if 'chat_session' not in session:
            session['chat_session'] = {
                'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'user_name': user_name,
                'messages': [],
                'topics': []
            }

        # Add user message to session
        user_topics = extract_topics(user_query)
        session['chat_session']['messages'].append({
            'role': 'user',
            'content': user_query,
            'timestamp': datetime.now().isoformat(),
            'topics': user_topics
        })
        
        # Prepare context for backend
        user_context = {
            "emotion": user_emotion,
            "name": user_name,
            "mental_health_status": prediction_result,
            "age": user_age,
            "original_query": user_query,
            "message_count": message_count
        }

        # Use unified FastAPI endpoint
        response = requests.post(
            f"{BACKEND_URL}/process_message",  # Single endpoint handles everything
            json={
                "message": user_query,
                "user_context": user_context,
                "session_id": session['chat_session']['session_id']
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "I'm sorry, I couldn't process your request.")
            agent_name = result.get("agent", "Assistant")
            method_used = result.get("method", "unknown")
            
            print(f"✅ Response - Agent: {agent_name}, Method: {method_used}")
            
            # Add assistant response to session
            response_topics = extract_topics(response_text)
            session['chat_session']['messages'].append({
                'role': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat(),
                'agent': agent_name,
                'method': method_used,
                'topics': response_topics
            })
            
            # Save session periodically
            if len(session['chat_session']['messages']) % 5 == 0:
                save_chat_session_to_backend(session['chat_session'])
            
            return jsonify({
                "response": response_text,
                "agent": agent_name,
                "method": method_used,
                "user_emotion": user_emotion,
                "mental_health_status": prediction_result,
                "message_count": message_count
            })
        else:
            return _flask_fallback_response(user_query, user_context)
            
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return _flask_fallback_response("", {})
    




@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Permanently delete user account and all associated data"""
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User not found in session'
            }), 400
        
        print(f"🗑️ Starting account deletion for user ID: {user_id}, username: {username}")
        
        # Step 1: Delete from FastAPI backend (if available)
        try:
            response = requests.delete(
                f"{BACKEND_URL}/api/v1/delete/{user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Successfully deleted user data from FastAPI backend")
            else:
                print(f"⚠️ FastAPI deletion failed: {response.status_code}")
        except Exception as backend_error:
            print(f"⚠️ Backend deletion error (continuing anyway): {backend_error}")
        
        # Step 2: Delete from local SQLite database
        db_session = DBSession()
        
        try:
            # Find the user
            user = db_session.query(User).filter_by(id=user_id).first()
            
            if not user:
                db_session.close()
                return jsonify({
                    'status': 'error',
                    'message': 'User not found in database'
                }), 404
            
            # Delete associated data first (due to foreign key constraints)
            print("🗑️ Deleting conversation history...")
            conversation_count = db_session.query(ConversationHistory).filter_by(user_id=user_id).count()
            db_session.query(ConversationHistory).filter_by(user_id=user_id).delete()
            print(f"✅ Deleted {conversation_count} conversation records")
            
            print("🗑️ Deleting user assessments...")
            assessment_count = db_session.query(UserAssessment).filter_by(user_id=user_id).count()
            db_session.query(UserAssessment).filter_by(user_id=user_id).delete()
            print(f"✅ Deleted {assessment_count} assessment records")
            
            # Delete the user account
            print("🗑️ Deleting user account...")
            db_session.delete(user)
            
            # Commit all changes
            db_session.commit()
            print(f"✅ Successfully deleted user account: {username}")
            
        except Exception as db_error:
            db_session.rollback()
            print(f"❌ Database deletion error: {db_error}")
            raise db_error
        finally:
            db_session.close()
        
        # Step 3: Clear session completely
        session.clear()
        
        return jsonify({
            'status': 'success',
            'message': f'Account "{username}" has been permanently deleted',
            'redirect': '/'
        })
        
    except Exception as e:
        print(f"❌ Critical error in delete_account: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete account: {str(e)}'
        }), 500


@app.route('/chat_message', methods=['POST'])
def chat_message():
    try:
        print("🎯 /chat_message endpoint hit!")
        data = request.get_json()
        print(f"📨 Received data: {data}")

        if not data:
            print("❌ No JSON data received")
            return jsonify({"error": "No data received"}), 400
        
        
        message = data.get('message', '')
        user_data = data.get('user_data', {})
        
        print(f"💬 Processing message: {message}")


        if not message:
            print("❌ Empty message")
            return jsonify({"error": "Empty message"}), 400

        
        # Skip test messages from debug
        if message == "Test message from debug":
            print("⏭️ Skipping debug test message")
            return jsonify({
                "response": "Debug test received - please type a real message.",
                "agent": "System",
                "method": "debug_skip"
            })
        
        # Initialize chat session if needed
        if 'chat_session' not in session:
            session['chat_session'] = {
                'session_id': str(uuid.uuid4()),
                'messages': [],
                'topics': [],
                'mood_history': []
            }
        
        # Add user message to session
        session['chat_session']['messages'].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Prepare user context
        user_context = {
            'name': user_data.get('name', 'Guest'),
            'emotion': user_data.get('emotion', 'neutral'),
            'mental_health_status': user_data.get('result', 'Unknown'),
            'session_id': session['chat_session']['session_id'],
            'message_history': [msg['content'] for msg in session['chat_session']['messages'][-5:]]
        }
        
        # Enhanced context if available from professional assessment
        if 'assessment_data' in session:
            assessment_data = session['assessment_data']
            user_context.update({
                "detailed_scores": assessment_data.get('assessment_result', {}).get('detailed_scores', {}),
                "recommendations": assessment_data.get('assessment_result', {}).get('recommendations', []),
                "assessment_type": "comprehensive",
                "emergency_info": assessment_data.get('assessment_result', {}).get('emergency_info')
            })
        
        # Use unified FastAPI endpoint with shorter timeout
        try:
            print("🚀 Connecting to FastAPI unified endpoint...")
            
            response = requests.post(
                f"{BACKEND_URL}/process_message",  # Single unified endpoint
                json={
                    "message": message,
                    "user_context": user_context
                },
                timeout=15  # Reasonable timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "I'm here to support you.")
                agent_name = result.get("agent", "Assistant")
                method_used = result.get("method", "unified")
                
                print(f"✅ FastAPI Success - Agent: {agent_name}, Method: {method_used}")
                
                # Add assistant response to session
                session['chat_session']['messages'].append({
                    'role': 'assistant',
                    'content': response_text,
                    'timestamp': datetime.now().isoformat(),
                    'agent': agent_name,
                    'method': method_used
                })
                
                return jsonify({
                    "response": response_text,
                    "agent": agent_name,
                    "method": method_used
                }), 200 
            
            else:
                print(f"⚠️ FastAPI failed with status: {response.status_code}")
                return _flask_fallback_response(message, user_context)
                
        except Exception as api_error:
            print(f"⚠️ FastAPI connection failed: {api_error}")
            return _flask_fallback_response(message, user_context)
        
    except Exception as e:
        print(f"❌ Critical error in chat_message: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "response": "I apologize, but I encountered an error. Please try again.",
            "agent": "Error Handler",
            "method": "error_fallback"
        }), 500



@app.route('/test_backend_connection')
def test_backend_connection():
    """Test if FastAPI backend is available"""
    try:
        response = requests.get(f"{BACKEND_URL}/debug_systems", timeout=5)
        if response.status_code == 200:
            return jsonify({"status": "connected", "backend": "FastAPI"})
        else:
            return jsonify({"status": "error", "message": f"Backend returned {response.status_code}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Backend not available: {str(e)}"}), 500

# Add this helper function for fallback responses
def _flask_fallback_response(message: str, user_context: dict):
    """Generate intelligent fallback response when FastAPI is unavailable"""
    try:
        message_lower = message.lower()
        user_name = user_context.get('name', 'there')
        
        # Crisis detection
        if any(word in message_lower for word in ['suicide', 'kill myself', 'want to die', 'hurt myself']):
            response_text = f"🆘 I'm very concerned about what you've shared, {user_name}. Please reach out for immediate help. In Bhutan: Emergency Services (112), National Mental Health Program (1717). Your life has value."
            agent_name = "Crisis Support Assistant"
        
        # Emotional support
        elif any(word in message_lower for word in ['sad', 'depressed', 'down', 'hopeless']):
            response_text = f"I understand you're feeling sad, {user_name}. These feelings are valid and you're not alone. Depression can feel overwhelming, but there are effective ways to manage it. Would you like to explore some coping strategies?"
            agent_name = "Mental Health Support Assistant"
            
        elif any(word in message_lower for word in ['anxious', 'worried', 'panic', 'nervous']):
            response_text = f"I hear that you're experiencing anxiety, {user_name}. These feelings can be very challenging, but there are proven techniques that can help. Would you like to try some breathing exercises?"
            agent_name = "Mental Health Support Assistant"
            
        elif any(word in message_lower for word in ['angry', 'frustrated', 'mad']):
            response_text = f"I understand you're feeling angry or frustrated, {user_name}. Anger is a normal emotion. What's been contributing to these feelings lately?"
            agent_name = "Mental Health Support Assistant"
            
        else:
            response_text = f"Thank you for sharing with me, {user_name}. I'm here to support you with your mental health concerns. While I'm experiencing some technical difficulties, I want you to know that your feelings matter and help is available."
            agent_name = "Local Mental Health Assistant"
        
        return jsonify({
            "response": response_text,
            "agent": agent_name,
            "method": "flask_fallback"
        })
        
    except Exception as e:
        print(f"Error in fallback response: {e}")
        return jsonify({
            "response": "I'm here to support you, though I'm having some technical difficulties. For immediate mental health support in Bhutan, contact the National Mental Health Program at 1717.",
            "agent": "Emergency Fallback",
            "method": "emergency_fallback"
        })


@app.get("/debug_rag_status")
async def debug_rag_status():
    """Debug RAG system status"""
    try:
        rag = app.state.rag
        
        # Test a simple query
        test_result = rag.process_query(
            "test query about mental health",
            user_emotion="neutral",
            mental_health_status="Unknown"
        )
        
        return {
            "rag_available": True,
            "knowledge_folder_exists": Path("knowledge").exists(),
            "pdf_files": list(Path("knowledge").glob("*.pdf")) if Path("knowledge").exists() else [],
            "test_confidence": test_result.get("confidence", 0.0),
            "test_response_preview": test_result.get("response", "")[:100]
        }
    except Exception as e:
        return {"rag_available": False, "error": str(e)}

def save_chat_session_to_backend(chat_session):
    """Helper function to save chat session to backend"""
    try:
        # Transform the session data to match FastAPI's expected format
        session_data = {
            "session_id": chat_session['session_id'],
            "user_name": chat_session['user_name'],
            "messages": chat_session['messages'],
            "metadata": {
                "topics": chat_session.get('topics', [])
            }
        }
        response = requests.post(f"{BACKEND_URL}/save_chat_session", json=session_data)
        if response.status_code != 200:
            print(f"Failed to save chat session: {response.status_code}")
    except Exception as e:
        print(f"Error saving chat session: {e}")



# Update the load_conversation_history route 
@app.route('/load_conversation_history')
def load_conversation_history():  
    """Load conversation history for all users"""
    try:
        user_id = session.get('user_id')
        user_name = session.get('user_data', {}).get('name', 'Guest')
        
        # For guests, just return empty history
        if not user_id or user_name == 'Guest':
            return jsonify({'messages': []}), 200
        
        # For logged-in users, return session messages
        messages = []
        
        # If there's a current chat session, include those messages
        if 'chat_session' in session and session['chat_session'].get('messages'):
            for msg in session['chat_session']['messages']:
                if msg['role'] in ['user', 'assistant']:
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content'],
                        'timestamp': msg['timestamp']
                    })
        
        return jsonify({'messages': messages})
        
    except Exception as e:
        print(f"Error loading conversation history: {e}")
        return jsonify({'messages': []}), 200

@app.route('/delete_conversation_history', methods=['POST'])
@login_required
def delete_conversation_history():
    """Delete conversation history for logged-in users"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'User not found'}), 400
        
        # Clear current chat session
        if 'chat_session' in session:
            session['chat_session']['messages'] = []
            session.modified = True
        
        # Here you would delete from database when implemented
        # db_session = DBSession()
        # db_session.query(ConversationHistory).filter_by(user_id=user_id).delete()
        # db_session.commit()
        # db_session.close()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Error deleting conversation history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



   
    
# Add these routes to handle assessment data with FastAPI backend
@app.route('/save_conversation', methods=['POST'])
def save_conversation_route():
    """Save conversation to FastAPI backend"""
    try:
        data = request.get_json()
        
        # Get user information
        user_id = session.get('user_uuid', session.get('user_id', 'guest'))
        
        # Prepare data for FastAPI
        conversation_data = {
            "user_id": str(user_id),
            "message": data.get('message', ''),
            "response": data.get('response', ''),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to FastAPI backend
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat/save",
            json=conversation_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({'status': 'success'})
        else:
            print(f"FastAPI save error: {response.status_code}")
            return jsonify({'status': 'success'})  # Graceful degradation
            
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return jsonify({'status': 'success'})  # Graceful degradation


@app.route("/clear_session", methods=["POST"])
def clear_session():
    """Clear session and save chat data"""
    try:
        # Save chat session before clearing
        if 'chat_session' in session and len(session['chat_session']['messages']) > 0:
            # Only save if not a guest
            user_data = session.get('user_data', {})
            if user_data.get('name', 'Guest').lower() not in ['guest', 'guest user', '']:
                save_chat_session_to_backend(session['chat_session'])
    except Exception as e:
        print(f"Error saving chat session: {e}")
    
    session.clear()
    return jsonify({"status": "success", "redirect": url_for('home')})


def get_chat_response(message, session_id=None):
    """Simple chat response function for integration with Gradio app"""
    try:
        # Default backend URL
        backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        
        # Simple user context for Gradio integration
        user_context = {
            "emotion": "neutral",
            "name": "User",
            "mental_health_status": "Unknown", 
            "age": "",
            "original_query": message,
            "message_count": 1
        }
        
        # Make request to FastAPI backend
        response = requests.post(
            f"{backend_url}/process_message",
            json={
                "message": message,
                "user_context": user_context,
                "session_id": session_id or "gradio_session"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "I'm sorry, I couldn't process your request.")
        else:
            return "I'm having trouble connecting to the chat backend. Please try again."
            
    except Exception as e:
        print(f"Error in get_chat_response: {e}")
        return "I'm sorry, I'm having technical difficulties. Please try again later."


def init_db():
    """Initialize the database with tables"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Database tables created/verified successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False


if __name__ == "__main__":
    # For Hugging Face Spaces compatibility
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    # Use FLASK_RUN_PORT if available, otherwise default to 5000
    port = int(os.getenv('FLASK_RUN_PORT', os.getenv('PORT', 5000)))
    
    # Initialize database
    init_db()
    
    if debug_mode:
        app.run(debug=True, host=host, port=port)
    else:
        # For Hugging Face Spaces, this runs as a background service to app.py
        app.run(debug=False, host=host, port=port, threaded=True)