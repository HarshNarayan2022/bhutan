from fastapi import FastAPI, Form, HTTPException, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
import numpy as np
import os
import yaml
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiofiles
from functools import lru_cache
import time
import re
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from dotenv import load_dotenv
# for PDF generation
from typing import Dict, List, Optional, Any, Union
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Load environment variables
load_dotenv()

# Download required NLTK data
import nltk
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    nltk.download('punkt')
    nltk.download('stopwords')

# Create thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=4)

# Cache for insights data
insights_cache = {
    "data": None,
    "timestamp": None,
    "ttl": 60  # Cache for 60 seconds
}

user_insights_cache = {}  # Cache per user

# Create data storage directories
DATA_DIR = Path("survey_data")
CHAT_SESSIONS_DIR = Path("chat_sessions")
DATA_DIR.mkdir(exist_ok=True, parents=True)
CHAT_SESSIONS_DIR.mkdir(exist_ok=True, parents=True)

# Global sentiment analyzer instance
sentiment_analyzer = None

# Initialize shared components at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting FastAPI server...")
    
    try:
        # Import here to avoid circular imports (with fallback for missing dependencies)
        try:
            from Chat_sentiment_analysis import ChatSentimentAnalyzer
            sentiment_analyzer_available = True
        except ImportError as e:
            print(f"⚠️ Sentiment analyzer unavailable: {e}")
            sentiment_analyzer_available = False
            
        try:
            from opensource_rag import OpenSourceRAG
            print("📚 Initializing open source RAG system...")
            opensource_rag = OpenSourceRAG()
            rag_available = True
            print("✅ Open source RAG system ready")
        except ImportError as e:
            print(f"⚠️ Open source RAG unavailable: {e}")
            rag_available = False
            opensource_rag = None
            
        # Initialize sentiment analyzer in background
        global sentiment_analyzer
        if sentiment_analyzer_available:
            print("🧠 Loading sentiment analyzer model...")
            sentiment_analyzer = ChatSentimentAnalyzer()
            print("✅ Sentiment analyzer ready")
        else:
            sentiment_analyzer = None
            print("⚠️ Using basic sentiment analysis")
            
        # Get the open source RAG instance
        if rag_available and opensource_rag:
            print("📚 Setting up open source RAG...")
            
            # Store in app state
            app.state.rag = opensource_rag
            app.state.config = None  # No config needed for open source RAG
        else:
            print("⚠️ Using basic response generation")
            app.state.rag = None
            app.state.config = None
            
        # Initialize response cache
        print("🗄️ Initializing response cache...")
        app.state.response_cache = {}
        app.state.cache_timestamps = {}
        
        print("🎉 FastAPI startup complete!")
        
    except Exception as e:
        print(f"❌ Critical error during startup: {e}")
        import traceback
        traceback.print_exc()
        
        # Create minimal fallback system
        app.state.rag = None
        app.state.response_cache = {}
        app.state.cache_timestamps = {}
        print("⚠️ Running with minimal fallback system")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    if hasattr(app.state, 'executor'):
        app.state.executor.shutdown(wait=True)
    executor.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

# Allow CORS for local testing
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mental-health-fastapi",
        "version": "1.0.0"
    }

@app.get("/fastapi-health")
async def fastapi_health():
    """FastAPI health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "Mental Health Chatbot FastAPI Backend",
            "timestamp": datetime.utcnow().isoformat(),
            "rag_available": hasattr(app.state, 'rag') and app.state.rag is not None,
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "service": "Mental Health Chatbot FastAPI Backend",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Mental Health FastAPI Service", "status": "running"}

# Pydantic models
class ConversationSaveRequest(BaseModel):
    id: Optional[UUID] = None
    user_id: str
    message: str
    response: str
    timestamp: Optional[datetime] = None
    
class ChatMessage(BaseModel):
    role: str  
    content: str
    timestamp: datetime

class ConversationLoadResponse(BaseModel):
    messages: List[ChatMessage]

class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1)
    age: Optional[int] = Field(None, gt=0, le=150)
    gender: Optional[str]
    city_region: Optional[str]
    profession: Optional[str]
    marital_status: Optional[str]
    previous_mental_diagnosis: Optional[str] = "NA"
    ethnicity: Optional[str]
    email: str  # Changed from EmailStr to str to avoid email-validator dependency
    password: str

class LoginRequest(BaseModel):
    email: str  # Changed from EmailStr to str
    password: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    age: Optional[int]
    gender: Optional[str]
    city_region: Optional[str]
    profession: Optional[str]
    marital_status: Optional[str]
    previous_mental_diagnosis: Optional[str]
    ethnicity: Optional[str]
    email: str  # Changed from EmailStr to str

    class Config:
        from_attributes = True

class MessageRequest(BaseModel):
    message: str
    user_context: Dict[str, Any] = {}
    session_id: Optional[str] = None



class MessageResponse(BaseModel):
    response: str
    agent: str
    confidence: float
    method: str
    timestamp: str
    sources: Optional[List[Union[str, Dict[str, Any]]]] = []  # ✅ Allow both strings and dicts
    condition: Optional[str] = "general"
    is_crisis: Optional[bool] = False
    sources_used: Optional[int] = 0

class ChatMessageRequest(BaseModel):
    message: str
    user_context: Dict[str, Any]
    session_id: Optional[str] = None

class ChatSessionData(BaseModel):
    session_id: str
    user_name: str
    messages: List[Dict]
    metadata: Optional[Dict] = None

# Database utility functions (keep existing ones)
def get_db_connection():
    db_uri = os.getenv("SUPABASE_DB_URI") or os.getenv("DATABASE_URL")
    if not db_uri:
        db_uri = (
            f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}"
            f"@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
        )
    return psycopg2.connect(db_uri)

def save_conversation_util(id: UUID, user_id: str, message: str, response: str, timestamp: Optional[datetime] = None) -> bool:
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if not timestamp:
            timestamp = datetime.now()

        insert_query = """
            INSERT INTO conversation_history (id, user_id, message, response, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (str(id), user_id, message, response, timestamp))
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"[DB ERROR] {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def load_conversation_util(user_id: str) -> List[Dict]:
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        select_query = """
            SELECT message, response, timestamp
            FROM conversation_history
            WHERE user_id = %s
            ORDER BY timestamp ASC
        """
        cursor.execute(select_query, (user_id,))
        rows = cursor.fetchall()

        history = []
        for message, response, timestamp in rows:
            history.append({
                "role": "user",
                "content": message,
                "timestamp": timestamp
            })
            history.append({
                "role": "assistant",
                "content": response,
                "timestamp": timestamp
            })

        return history

    except psycopg2.Error as e:
        print(f"[DB ERROR] Exception: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_conversations_by_user_util(user_id: str) -> bool:
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversation_history WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user chats: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def register_user_util(user_data: dict) -> Optional[dict]:
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM user_profiles WHERE email = %s", (user_data['email'],))
        if cursor.fetchone():
            return None
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new user
        user_id = uuid4()
        insert_query = """
            INSERT INTO user_profiles (id, name, age, gender, city_region, profession, 
                                     marital_status, previous_mental_diagnosis, ethnicity, 
                                     email, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        cursor.execute(insert_query, (
            str(user_id), user_data['name'], user_data.get('age'), 
            user_data.get('gender'), user_data.get('city_region'),
            user_data.get('profession'), user_data.get('marital_status'),
            user_data.get('previous_mental_diagnosis', 'NA'),
            user_data.get('ethnicity'), user_data['email'], password_hash
        ))
        
        user_row = cursor.fetchone()
        conn.commit()
        
        if user_row:
            return {
                'id': user_row[0],
                'name': user_row[1],
                'age': user_row[2],
                'gender': user_row[3],
                'city_region': user_row[4],
                'profession': user_row[5],
                'marital_status': user_row[6],
                'previous_mental_diagnosis': user_row[7],
                'ethnicity': user_row[8],
                'email': user_row[10]
            }
        return None
        
    except Exception as e:
        print(f"Error registering user: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def login_user_util(email: str, password: str) -> Optional[dict]:
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_profiles WHERE email = %s", (email,))
        user_row = cursor.fetchone()
        
        if user_row and bcrypt.checkpw(password.encode('utf-8'), user_row[11].encode('utf-8')):
            return {
                'id': user_row[0],
                'name': user_row[1],
                'age': user_row[2],
                'gender': user_row[3],
                'city_region': user_row[4],
                'profession': user_row[5],
                'marital_status': user_row[6],
                'previous_mental_diagnosis': user_row[7],
                'ethnicity': user_row[8],
                'email': user_row[10]
            }
        return None
        
    except Exception as e:
        print(f"Error logging in user: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_user_util(user_id: str) -> bool:
    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete conversations first (foreign key constraint)
        cursor.execute("DELETE FROM conversation_history WHERE user_id = %s", (user_id,))
        # Delete user
        cursor.execute("DELETE FROM user_profiles WHERE id = %s", (user_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Create API router
router = APIRouter(prefix="/api/v1", tags=["database"])

def create_tables():
    try:
        db_uri = os.getenv("SUPABASE_DB_URI") or os.getenv("DATABASE_URL")
        print(f"Creating tables using URI: {db_uri[:50]}...")
        
        conn = psycopg2.connect(db_uri, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Check if user_profiles table exists and needs to be updated
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name IN ('email', 'password_hash')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add missing columns if needed
        if 'email' not in existing_columns:
            print("Adding email column to user_profiles table...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS email VARCHAR(120) UNIQUE;")
        
        if 'password_hash' not in existing_columns:
            print("Adding password_hash column to user_profiles table...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);")
        
        # Create user_profiles table if it doesn't exist
        print("Creating user_profiles table if not exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL,
                age INTEGER CHECK (age > 0 AND age <= 150),
                gender VARCHAR(20),
                city_region VARCHAR(100),
                profession VARCHAR(100),
                marital_status VARCHAR(30),
                previous_mental_diagnosis TEXT DEFAULT 'NA',
                ethnicity VARCHAR(50),
                email VARCHAR(120) UNIQUE,
                password_hash VARCHAR(255),
                email_id TEXT,
                user_password TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create conversation_history table
        print("Creating conversation_history table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create indexes safely
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_user_id ON conversation_history(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversation_history(timestamp);")
        
        # Try to create email index
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON user_profiles(email);")
        except:
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_email_id ON user_profiles(email_id);")
            except:
                print("Could not create email index")
        
        conn.commit()
        print("✅ Database tables created/updated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

@app.get("/api/v1/setup-db")
async def setup_database():
    """Setup database tables and verify connection"""
    try:
        create_tables()
        return {
            "status": "success",
            "message": "Database tables created/verified successfully",
            "tables": ["user_profiles", "conversation_history"]
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database setup failed: {str(e)}"
        }

@router.post("/chat/save")
async def save_conversation_endpoint(data: ConversationSaveRequest):
    conversation_id = data.id or uuid4()
    success = save_conversation_util(
        id=conversation_id,
        user_id=data.user_id,
        message=data.message,
        response=data.response,
        timestamp=data.timestamp
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save conversation")
    return {"status": "success", "conversation_id": str(conversation_id)}

@router.get("/chat/load/{user_id}", response_model=ConversationLoadResponse)
async def load_conversation_endpoint(user_id: str):
    messages = load_conversation_util(user_id)
    if not messages:
        return {"messages": []}
    return {"messages": [ChatMessage(**msg) for msg in messages]}

@router.delete("/chat/delete-all/{user_id}")
async def delete_all_conversations(user_id: str):
    success = delete_conversations_by_user_util(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user conversations")
    return {"status": "all deleted"}

@router.post("/login", response_model=UserResponse)
def login_user_endpoint(data: LoginRequest):
    user = login_user_util(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@router.post("/register", response_model=UserResponse)
def register_user_endpoint(data: UserProfileCreate):
    user = register_user_util(data.dict())
    if not user:
        raise HTTPException(status_code=400, detail="Registration failed - user may already exist")
    return user
# Add this route after your existing API routes:

@router.delete("/delete/{user_id}")
def delete_user_and_data(user_id: str):
    """Completely delete a user and all associated data"""
    try:
        print(f"🗑️ FastAPI: Deleting user {user_id} and all data...")
        
        # Delete conversation history
        conversations_deleted = delete_conversations_by_user_util(user_id)
        
        # Delete user profile
        user_deleted = delete_user_util(user_id)
        
        if user_deleted:
            print(f"✅ FastAPI: Successfully deleted user {user_id}")
            return {
                "status": "success",
                "message": f"User {user_id} and all associated data deleted",
                "conversations_deleted": conversations_deleted
            }
        else:
            print(f"❌ FastAPI: Failed to delete user {user_id}")
            raise HTTPException(status_code=500, detail="Failed to delete user")
            
    except Exception as e:
        print(f"❌ FastAPI deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# ==============================================================================
# SINGLE UNIFIED CHAT ENDPOINT - USING SHARED RAG ONLY
# ==============================================================================
@app.post("/process_message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """
    Unified chat processing endpoint using shared RAG system.
    This handles all chat requests - fast, full, and CrewAI modes.
    """
    start_time = time.time()
    
    try:
        print(f"💬 Processing message: {request.message[:50]}...")
        print(f"👤 User context: {request.user_context}")
        
        # Check if RAG system is available
        if not hasattr(app.state, 'rag') or app.state.rag is None:
            print("⚠️ RAG system not available, using fallback")
            return _generate_fallback_response(request, "system_unavailable")
        
        rag = app.state.rag
        
        # Try CrewAI integration first if available
        if hasattr(rag, 'process_query_with_crewai') and rag.crewai_enabled:
            print("🤖 Using CrewAI enhanced processing...")
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    rag.process_query_with_crewai,
                    request.message,
                    request.user_context
                )
                
                processing_time = time.time() - start_time
                print(f"✅ CrewAI response generated in {processing_time:.2f}s")
                
                return MessageResponse(
                    response=result.get("response", "I'm here to help you."),
                    agent=result.get("agent", "CrewAI Enhanced System"),
                    confidence=result.get("confidence", 0.85),
                    method="crewai_integrated",
                    timestamp=datetime.now().isoformat(),
                    sources=result.get("sources", [])[:3],  # Limit sources
                    condition=result.get("condition", "general"),
                    is_crisis=result.get("is_crisis", False),
                    sources_used=len(result.get("sources", []))
                )
                
            except Exception as crewai_error:
                print(f"⚠️ CrewAI processing failed: {crewai_error}")
                # Continue to regular RAG processing
        
        # ✅ FIX: Move this block to the correct indentation level
        print("📚 Using RAG processing...")
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                executor,
                rag.process_query,
                request.message,
                request.user_context.get('emotion', 'neutral'),
                request.user_context.get('mental_health_status', 'Unknown'),
                request.user_context
            )
            
            processing_time = time.time() - start_time
            print(f"✅ RAG response generated in {processing_time:.2f}s")
            print(f"📊 Confidence: {result.get('confidence', 0.0):.2f}")
            
            # ✅ FIX: Process sources properly
            raw_sources = result.get("sources", [])
            processed_sources = []
            
            for source in raw_sources[:3]:  # Limit to 3 sources
                if isinstance(source, dict):
                    # Extract just the source filename or create a simple string
                    source_text = source.get('source', 'Unknown source')
                    if 'knowledge/' in source_text:
                        source_text = source_text.split('knowledge/')[-1]  # Get just filename
                    processed_sources.append(source_text)
                elif isinstance(source, str):
                    processed_sources.append(source)
                else:
                    processed_sources.append(str(source))
            
            return MessageResponse(
                response=result.get("response", "I'm here to help you with your mental health concerns."),
                agent="Mental Health RAG Assistant",
                confidence=result.get("confidence", 0.7),
                method="rag_standard",
                timestamp=datetime.now().isoformat(),
                sources=processed_sources,  # ✅ Now properly formatted
                condition="general",
                is_crisis=False,
                sources_used=len(raw_sources)
            )
            
        except Exception as rag_error:
            print(f"❌ RAG processing failed: {rag_error}")
            return _generate_fallback_response(request, "rag_error")
            
    except Exception as e:
        print(f"❌ Critical error in process_message: {e}")
        import traceback
        traceback.print_exc()
        return _generate_fallback_response(request, "critical_error")

def _generate_fallback_response(request: MessageRequest, error_type: str) -> MessageResponse:
    """Generate intelligent fallback response based on message content"""
    try:
        message_lower = request.message.lower()
        user_name = request.user_context.get('name', 'there')
        
        # Crisis detection
        crisis_keywords = ['suicide', 'kill myself', 'want to die', 'hurt myself', 'end it all']
        if any(keyword in message_lower for keyword in crisis_keywords):
            response = f"🆘 I'm very concerned about what you've shared, {user_name}. Please reach out for immediate help. In Bhutan: Emergency Services (112), National Mental Health Program (1717). Your life has value and help is available."
            condition = 'crisis'
            is_crisis = True
        
        # Emotional categories
        elif any(word in message_lower for word in ['sad', 'depressed', 'depression', 'down', 'hopeless']):
            response = f"I understand you're feeling sad, {user_name}. These feelings are valid and you're not alone. Depression can feel overwhelming, but there are effective ways to manage it. Would you like to explore some coping strategies?"
            condition = 'depression'
            is_crisis = False
            
        elif any(word in message_lower for word in ['anxious', 'anxiety', 'worried', 'panic', 'nervous']):
            response = f"I hear that you're experiencing anxiety, {user_name}. These feelings can be very challenging, but there are proven techniques that can help. Would you like to try some breathing exercises?"
            condition = 'anxiety'
            is_crisis = False
            
        elif any(word in message_lower for word in ['angry', 'frustrated', 'mad', 'rage']):
            response = f"I understand you're feeling angry or frustrated, {user_name}. Anger is a normal emotion, and learning healthy ways to express it is important for your wellbeing. What's been contributing to these feelings?"
            condition = 'anger'
            is_crisis = False
            
        elif any(word in message_lower for word in ['lonely', 'alone', 'isolated']):
            response = f"I hear that you're feeling lonely, {user_name}. Loneliness can be very difficult to experience. You're reaching out here, which shows strength. Would you like to talk about ways to connect with others?"
            condition = 'loneliness'
            is_crisis = False
            
        else:
            response = f"Thank you for sharing with me, {user_name}. I'm here to support you with your mental health concerns. While I'm experiencing some technical difficulties, I want you to know that your feelings matter and help is available."
            condition = 'general'
            is_crisis = False
        
        # Add technical note for non-crisis situations
        if not is_crisis:
            if error_type == "system_unavailable":
                response += "\n\nI'm currently running in limited mode, but I'm still here to listen and provide support."
            elif error_type == "rag_error":
                response += "\n\nI'm having some difficulty accessing my knowledge base, but I can still offer emotional support and general guidance."
        
        return MessageResponse(
            response=response,
            agent="Mental Health Support Assistant",
            confidence=0.7,
            method=f"intelligent_fallback_{error_type}",
            timestamp=datetime.now().isoformat(),
            sources=[],
            condition=condition,
            is_crisis=is_crisis,
            sources_used=0
        )
        
    except Exception as e:
        print(f"Error generating fallback response: {e}")
        return MessageResponse(
            response="I'm experiencing technical difficulties, but I want you to know that I'm here to support you. For immediate mental health support in Bhutan, please contact the National Mental Health Program at 1717 (24/7).",
            agent="Emergency Support",
            confidence=0.5,
            method="emergency_fallback",
            timestamp=datetime.now().isoformat(),
            sources=[],
            condition="emergency",
            is_crisis=False,
            sources_used=0
        )

# Legacy endpoints for backward compatibility
@app.post("/process_message_fast", response_model=MessageResponse)
async def process_message_fast(request: MessageRequest):
    """Legacy fast endpoint - redirects to main processor"""
    print("📍 Legacy fast endpoint called, redirecting to main processor...")
    return await process_message(request)

@app.post("/process_message_with_crew", response_model=MessageResponse)
async def process_message_with_crew(request: MessageRequest):
    """Legacy CrewAI endpoint - redirects to main processor"""
    print("📍 Legacy CrewAI endpoint called, redirecting to main processor...")
    return await process_message(request)

# ==============================================================================
# UTILITY AND DEBUGGING ENDPOINTS
# ==============================================================================

@app.get("/debug_systems")
async def debug_systems():
    """Debug endpoint to check system status"""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "rag_available": hasattr(app.state, 'rag') and app.state.rag is not None,
            "sentiment_analyzer_available": sentiment_analyzer is not None
        }
        
        if hasattr(app.state, 'rag') and app.state.rag is not None:
            rag = app.state.rag
            status.update({
                "rag_type": str(type(rag)),
                "crewai_enabled": getattr(rag, 'crewai_enabled', False),
                "rag_methods": [method for method in dir(rag) if not method.startswith('_')]
            })
            
            # Test knowledge base
            try:
                collection_info = rag.retriever.get_collection_info()
                status["knowledge_status"] = {
                    "documents_count": collection_info.get('points_count', 0),
                    "collection_name": collection_info.get('name', 'unknown')
                }
            except Exception as e:
                status["knowledge_status"] = {"error": str(e)}
        
        return status
        
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/reingest_knowledge")
async def reingest_knowledge():
    """Force reingest knowledge base"""
    try:
        if not hasattr(app.state, 'rag') or app.state.rag is None:
            return {"error": "RAG system not available"}
        
        print("🔄 Force reingesting knowledge...")
        result = await asyncio.get_event_loop().run_in_executor(
            executor,
            app.state.rag.ingest_knowledge_folder,
            "knowledge"
        )
        
        return {
            "status": "success",
            "message": "Knowledge reingestion completed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==============================================================================
# KEEP EXISTING SURVEY AND SESSION ENDPOINTS
# ==============================================================================

def sanitize_filename(name: str) -> str:
    """Sanitize user name for use in filename"""
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized

@app.post("/save_chat_session")
async def save_chat_session(session_data: ChatSessionData):
    """Save chat session to disk"""
    # Don't save chat sessions for guest users (case-insensitive)
    if session_data.user_name.lower() in ['guest', 'guest user', '']:
        return {"status": "success", "message": "Guest chat sessions are not saved"}
    
    try:
        filename = f"chat_{session_data.user_name}_{session_data.session_id}.json"
        filepath = CHAT_SESSIONS_DIR / filename
        
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(session_data.dict(), indent=2))
        
        return {"status": "success", "message": "Chat session saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_chat_session/{session_id}")
async def get_chat_session(session_id: str):
    """Retrieve chat session by ID"""
    try:
        # Check if the session file exists
        filename = f"chat_*_{session_id}.json"
        filepath = CHAT_SESSIONS_DIR / filename
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Chat session not found")

        async with aiofiles.open(filepath, 'r') as f:
            session_data = await f.read()
            return {"status": "success", "data": json.loads(session_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Keep the professional assessment and other existing endpoints...
# (Professional assessment code remains the same as it's working)

# Professional assessment models and functions
class ProfessionalAssessmentRequest(BaseModel):
    """Request model for professional questionnaire assessment"""
    Name: str
    Age: int
    Sex: str
    Location: str
    days_indoors: int
    Emotion: str
    history_of_mental_illness: str
    treatment: str
    
    # PHQ-9 Depression Screening (0-3 scale)
    PHQ9_1: int
    PHQ9_2: int
    PHQ9_3: int
    PHQ9_4: int
    PHQ9_5: int
    PHQ9_6: int
    PHQ9_7: int
    PHQ9_8: int
    PHQ9_9: int
    
    # GAD-7 Anxiety Screening (0-3 scale)
    GAD7_1: int
    GAD7_2: int
    GAD7_3: int
    GAD7_4: int
    GAD7_5: int
    GAD7_6: int
    GAD7_7: int
    
    # DAST-10 Substance Use (Yes/No -> 1/0)
    DAST_1: str
    DAST_2: str
    DAST_3: str
    DAST_4: str
    DAST_5: str
    DAST_6: str
    DAST_7: str
    DAST_8: str
    DAST_9: str
    DAST_10: str
    
    # AUDIT Alcohol Use (string responses)
    AUDIT_1: str
    AUDIT_2: str
    AUDIT_3: str
    AUDIT_4: str
    AUDIT_5: str
    AUDIT_6: str
    AUDIT_7: str
    AUDIT_8: str
    AUDIT_9: str
    AUDIT_10: str
    
    # Bipolar Screening (Yes/No -> 1/0)
    BIPOLAR_1: str
    BIPOLAR_2: str
    BIPOLAR_3: str
    BIPOLAR_4: str
    BIPOLAR_5: str
    BIPOLAR_6: str
    BIPOLAR_7: str
    BIPOLAR_8: str
    BIPOLAR_9: str
    BIPOLAR_10: str
    BIPOLAR_11: str

class SurveyData(BaseModel):
    timestamp: str
    name: str
    age: int
    sex: str
    location: str
    emotion: str
    prediction: str
    score: float
    averages: Dict[str, float]
    raw_responses: Dict[str, List[float]]

@app.post("/store_survey")
async def store_survey(survey_data: SurveyData, background_tasks: BackgroundTasks):
    """Store survey data for insights and analytics"""
    
    # Don't store data for guest users
    if survey_data.name.lower() in ['guest', 'guest user', '']:
        return {"status": "success", "message": "Guest data not stored"}
    
    # Sanitize the name for filename
    safe_name = sanitize_filename(survey_data.name)
    filename = f"survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}.json"
    filepath = DATA_DIR / filename
    
    # Write asynchronously
    async with aiofiles.open(filepath, 'w') as f:
        await f.write(json.dumps(survey_data.dict(), indent=2))
    
    return {"status": "success", "message": "Survey data stored successfully"}

@app.post("/predict_professional")
def predict_professional(data: ProfessionalAssessmentRequest):
    """Professional mental health assessment using validated questionnaires"""
    
    # Score PHQ-9 Depression
    phq9_answers = {
        f"Q{i}": getattr(data, f"PHQ9_{i}") for i in range(1, 10)
    }
    phq9_score = sum(phq9_answers.values())
    phq9_interpretation = interpret_score("PHQ-9", phq9_score)
    
    # Score GAD-7 Anxiety
    gad7_answers = {
        f"Q{i}": getattr(data, f"GAD7_{i}") for i in range(1, 8)
    }
    gad7_score = sum(gad7_answers.values())
    gad7_interpretation = interpret_score("GAD-7", gad7_score)
    
    # Score DAST-10 Substance Use
    dast_answers = {}
    for i in range(1, 11):
        answer = getattr(data, f"DAST_{i}")
        # Handle reverse scoring for DAST-3 (able to stop)
        if i == 3:
            dast_answers[f"Q{i}"] = 1 if answer.lower() == "no" else 0
        else:
            dast_answers[f"Q{i}"] = 1 if answer.lower() == "yes" else 0
    
    dast_score = sum(dast_answers.values())
    dast_interpretation = interpret_score("DAST-10", dast_score)
    
    # Score AUDIT Alcohol Use
    audit_answers = {}
    for i in range(1, 11):
        audit_answers[f"Q{i}"] = getattr(data, f"AUDIT_{i}")
    
    audit_score = score_questionnaire("AUDIT", audit_answers)
    audit_interpretation = interpret_score("AUDIT", audit_score)
    
    # Score Bipolar Screening
    bipolar_answers = {}
    for i in range(1, 12):
        answer = getattr(data, f"BIPOLAR_{i}")
        bipolar_answers[f"Q{i}"] = 1 if answer.lower() == "yes" else 0
    
    bipolar_score = sum(bipolar_answers.values())
    bipolar_interpretation = interpret_score("Bipolar", bipolar_score)
    
    # Calculate overall risk level based on professional scores
    risk_factors = []
    
    # Depression risk
    if phq9_score >= 15:
        risk_factors.append("severe_depression")
    elif phq9_score >= 10:
        risk_factors.append("moderate_depression")
    elif phq9_score >= 5:
        risk_factors.append("mild_depression")
    
    # Anxiety risk
    if gad7_score >= 15:
        risk_factors.append("severe_anxiety")
    elif gad7_score >= 10:
        risk_factors.append("moderate_anxiety")
    elif gad7_score >= 5:
        risk_factors.append("mild_anxiety")
    
    # Substance use risk
    if dast_score >= 6:
        risk_factors.append("substance_concern")
    
    # Alcohol use risk
    if audit_score >= 15:
        risk_factors.append("alcohol_concern")
    
    # Bipolar risk
    if bipolar_score >= 7:
        risk_factors.append("bipolar_concern")
    
    # Determine overall prediction
    if any(factor.startswith("severe") for factor in risk_factors) or len(risk_factors) >= 3:
        overall_prediction = "Severe"
        overall_score = 4.0
    elif any(factor.startswith("moderate") for factor in risk_factors) or len(risk_factors) >= 2:
        overall_prediction = "Moderate"
        overall_score = 3.0
    elif len(risk_factors) >= 1:
        overall_prediction = "Mild"
        overall_score = 2.0
    else:
        overall_prediction = "Healthy"
        overall_score = 1.0
    
    # Generate professional recommendations
    recommendations = []
    if phq9_score >= 10:
        recommendations.append("Consider consulting a mental health professional for depression screening.")
    if gad7_score >= 10:
        recommendations.append("Consider discussing anxiety symptoms with a healthcare provider.")
    if dast_score >= 3:
        recommendations.append("Consider discussing substance use with a healthcare provider.")
    if audit_score >= 8:
        recommendations.append("Consider discussing alcohol use patterns with a healthcare provider.")
    if bipolar_score >= 7:
        recommendations.append("Consider discussing mood episodes with a mental health professional.")
    
    if not recommendations:
        recommendations.append("Continue maintaining good mental health practices and regular self-care.")
    
    # Emergency contact info for Bhutan
    emergency_info = None
    if phq9_score >= 15 or any(factor == "severe_depression" for factor in risk_factors):
        emergency_info = {
            "message": "If you're having thoughts of self-harm, please reach out for help immediately.",
            "emergency_contacts": [
                "Bhutan Emergency: 112",
                "Jigme Dorji Wangchuck National Referral Hospital: +975-2-322496",
                "Thimphu Police: +975-2-322222"
            ]
        }
    
    return {
        "prediction": overall_prediction,
        "score": overall_score,
        "detailed_scores": {
            "phq9": {"score": phq9_score, "interpretation": phq9_interpretation},
            "gad7": {"score": gad7_score, "interpretation": gad7_interpretation},
            "dast10": {"score": dast_score, "interpretation": dast_interpretation},
            "audit": {"score": audit_score, "interpretation": audit_interpretation},
            "bipolar": {"score": bipolar_score, "interpretation": bipolar_interpretation}
        },
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "emergency_info": emergency_info
    }

# Additional utility functions for scoring (keep existing)
def score_questionnaire(condition: str, answers: dict) -> int:
    """Score PHQ-9, GAD-7, DAST-10, Bipolar and AUDIT answers."""
    score = 0
    if condition in ["PHQ-9", "GAD-7"]:
        scale = {
            "0": 0, "not at all": 0,
            "1": 1, "several days": 1,
            "2": 2, "more than half the days": 2,
            "3": 3, "nearly every day": 3
        }
        for ans in answers.values():
            cleaned = str(ans).strip().lower()
            if '-' in cleaned:
                cleaned = cleaned.split("-", 1)[-1].strip()
            score += scale.get(cleaned, 0)
            
    elif condition == "DAST-10":
        for ans in answers.values():
            score += 1 if str(ans).lower() in ["yes", "y", "true", "1"] else 0

    elif condition == "AUDIT":
        scale_0_to_4 = {
            "never": 0,
            "monthly or less": 1,
            "less than monthly": 1,
            "2 to 4 times a month": 2,
            "5 or 6": 2,
            "monthly": 2,
            "2 to 3 times a week": 3,
            "7, 8, or 9": 3,
            "weekly": 3,
            "4 or more times a week": 4,
            "10 or more": 4,
            "daily or almost daily": 4,
            "1 or 2": 0,
            "3 or 4": 1  
        }

        scale_0_2_4 = {
            "no": 0,
            "yes, but not in the last year": 2,
            "yes, during the last year": 4
        }

        # Q1 logic (skip if "never")
        ans1 = answers.get("Q1", "").strip().lower()
        skip_to_end = ans1 == "never"
        
        if skip_to_end:
            score += 0
            # Score Q9 and Q10 only
            for qkey in ["Q9", "Q10"]:
                ans = answers.get(qkey, "").strip().lower()
                for key in scale_0_2_4:
                    if key in ans:
                        score += scale_0_2_4[key]
                        break
            return score
        else:
            for key in scale_0_to_4:
                if key in ans1:
                    score += scale_0_to_4[key]
                    break

        # Continue with Q2–Q8
        for qkey in [f"Q{i}" for i in range(2, 9)]:
            ans = answers.get(qkey, "").strip().lower()
            for key in scale_0_to_4:
                if key in ans:
                    score += scale_0_to_4[key]
                    break

        # Score Q9, Q10
        for qkey in ["Q9", "Q10"]:
            ans = answers.get(qkey, "").strip().lower()
            for key in scale_0_2_4:
                if key in ans:
                    score += scale_0_2_4[key]
                    break

    elif condition == "Bipolar":
        for ans in answers.values():
            score += 1 if str(ans).strip().lower() in ["yes", "y", "true", "1"] else 0

    return score

def interpret_score(condition: str, score: int) -> str:
    """Interpret the score based on condition."""
    if condition == "PHQ-9":
        if score <= 4: return "Minimal depression"
        elif score <= 9: return "Mild depression"
        elif score <= 14: return "Moderate depression"
        elif score <= 19: return "Moderately severe depression"
        return "Severe depression"

    if condition == "GAD-7":
        if score <= 4: return "Minimal anxiety"
        elif score <= 9: return "Mild anxiety"
        elif score <= 14: return "Moderate anxiety"
        return "Severe anxiety"

    if condition == "DAST-10":
        if score == 0: return "No problems reported"
        elif score <= 2: return "Low level of problems"
        elif score <= 5: return "Moderate problems"
        elif score <= 8: return "Substantial problems"
        return "Severe problems"
    
    if condition == "AUDIT":
        if score <= 7: return "Lower risk, usually no action needed."
        elif score >= 8 and score <= 14: return "Hazardous or harmful alcohol use. Brief advice or counseling may be appropriate."
        elif score >= 15 and score <= 19: return "Harmful alcohol use. Brief counseling and continued monitoring recommended."
        elif score >= 20: return "Likely alcohol dependence. Referral for specialist assessment and treatment is recommended."
        else:
            return "Score out of typical AUDIT range."

    if condition == "Bipolar":
        if score >= 7: return "Likely signs of bipolar disorder"
        return "Unlikely bipolar symptoms"

    return "Score interpreted"

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Production settings
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('FASTAPI_PORT', 8000))
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        reload=debug_mode,
        log_level="info" if not debug_mode else "debug"
    )