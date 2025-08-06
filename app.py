#!/usr/bin/env python3
"""
Hugging Face Spaces Entry Point for Mental Health Chatbot
Combines Flask and FastAPI into a single Gradio interface
"""

import gradio as gr
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Set environment variables for Hugging Face Spaces
os.environ['HUGGINGFACE_SPACES'] = '1'
os.environ['GRADIO_SERVER_NAME'] = '0.0.0.0'
os.environ['GRADIO_SERVER_PORT'] = '7860'

# Import our Flask app components
from main import app as flask_app, get_chat_response
from models.chat_session import User, ChatSession
from config_manager import ConfigManager

# Initialize configuration
config_manager = ConfigManager()

# Global variables for session management
current_user = None
chat_history = []

def create_user_session(name="Guest"):
    """Create a user session for the chat"""
    global current_user
    current_user = {
        'id': f'gradio_user_{int(time.time())}',
        'name': name,
        'session_id': f'session_{int(time.time())}',
        'assessment_data': None
    }
    return f"Welcome {name}! Ready to chat with your mental health assistant."

def process_chat_message(message, history):
    """Process chat message and return response"""
    global current_user, chat_history
    
    if not message.strip():
        return history, ""
    
    # Ensure user session exists
    if not current_user:
        create_user_session()
    
    try:
        # Use the existing chat response function from main.py
        with flask_app.app_context():
            # Simulate request context for our chat function
            user_context = {
                'user_id': current_user['id'],
                'session_id': current_user['session_id'],
                'name': current_user['name'],
                'emotion': 'neutral',
                'mental_health_status': 'Unknown'
            }
            
            # Get response from our existing function
            response_data = get_chat_response(message, user_context)
            
            if isinstance(response_data, dict) and 'response' in response_data:
                bot_response = response_data['response']
                agent = response_data.get('agent', 'Assistant')
                
                # Format response with agent info
                if agent and agent != 'Assistant':
                    bot_response = f"**[{agent}]**\n\n{bot_response}"
                    
            else:
                bot_response = "I'm sorry, I'm having trouble processing your message right now. Could you please try again?"
        
        # Update history
        history.append([message, bot_response])
        
        return history, ""
        
    except Exception as e:
        print(f"Error processing chat message: {e}")
        error_response = "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment."
        history.append([message, error_response])
        return history, ""

def process_voice_input(audio):
    """Process voice input using Whisper"""
    if audio is None:
        return "No audio received. Please try recording again."
    
    try:
        # Import whisper functionality
        from main import whisper_model
        
        if whisper_model is None:
            return "Voice transcription is not available at the moment. Please type your message instead."
        
        # Transcribe the audio
        result = whisper_model.transcribe(audio)
        transcript = result['text'].strip()
        
        if transcript:
            return transcript
        else:
            return "Could not understand the audio. Please try speaking more clearly."
            
    except Exception as e:
        print(f"Voice transcription error: {e}")
        return "Voice transcription failed. Please type your message instead."

def take_assessment():
    """Placeholder for assessment functionality"""
    return """
    ## Mental Health Assessment
    
    Our comprehensive assessment includes:
    
    🧠 **Available Assessments:**
    - PHQ-9 (Depression Screening)
    - GAD-7 (Anxiety Assessment) 
    - DAST-10 (Substance Use Screening)
    - AUDIT (Alcohol Use Assessment)
    - Bipolar Disorder Screening
    
    📝 **Instructions:**
    To take a full assessment, please type "I want to take an assessment" in the chat, 
    and our AI assistant will guide you through the appropriate questionnaire based on your needs.
    
    💡 **Note:** The assessment will be conducted through the chat interface where our 
    specialized agents can provide personalized guidance and immediate results.
    """

def get_resources():
    """Get mental health resources"""
    return """
    ## 🆘 Mental Health Resources
    
    ### Emergency Support
    - **National Suicide Prevention Lifeline:** 988
    - **Crisis Text Line:** Text HOME to 741741
    - **Emergency Services:** 911
    
    ### Bhutan Mental Health Resources  
    - **National Mental Health Program:** 1717 (24/7)
    - **Emergency Services:** 112
    
    ### Professional Help
    - Contact your healthcare provider
    - Seek therapy or counseling services
    - Consult with a mental health professional
    
    ### Self-Care Tips
    - Practice mindfulness and meditation
    - Maintain regular exercise
    - Connect with supportive friends and family
    - Prioritize sleep and nutrition
    
    **Important:** This chatbot is for support and information only. 
    For serious mental health concerns, please seek professional help immediately.
    """

# Create Gradio interface
def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(
        title="Mental Health AI Assistant",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1000px !important;
            margin: auto !important;
        }
        .chat-message {
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 20%;
        }
        .bot-message {
            background-color: #f5f5f5;
            margin-right: 20%;
        }
        """
    ) as interface:
        
        gr.Markdown("""
        # 🧠 Mental Health AI Assistant
        ### Advanced Multi-Agent AI System for Comprehensive Mental Wellness Support
        
        Welcome to our intelligent mental health support system powered by specialized AI agents including:
        - 🤖 **Crisis Detection Agent** - Identifies emergency situations
        - 🎯 **Mental Health Assessment Specialist** - Conducts standardized screenings  
        - 📚 **Knowledge Retrieval Agent** - Provides evidence-based guidance
        - 💡 **Personalized Recommendation Engine** - Offers tailored support strategies
        
        **✨ Features:** Multi-Agent AI • Crisis Detection • Evidence-Based Assessments • Voice Interaction
        """)
        
        with gr.Tab("💬 Chat Assistant"):
            gr.Markdown("Start a conversation with our AI mental health assistant. You can ask questions, share your feelings, or discuss any concerns.")
            
            with gr.Row():
                with gr.Column(scale=2):
                    name_input = gr.Textbox(
                        label="Your Name (Optional)",
                        placeholder="Enter your name or use 'Guest'",
                        value="Guest"
                    )
                    start_btn = gr.Button("Start New Session", variant="primary")
                    session_status = gr.Textbox(label="Session Status", interactive=False)
            
            chatbot = gr.Chatbot(
                height=500,
                label="Mental Health Assistant",
                bubble_full_width=False,
                avatar_images=("👤", "🤖")
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here... Ask me anything about mental health!",
                    scale=4
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("Clear Chat", variant="secondary")
                
        with gr.Tab("🎤 Voice Chat"):
            gr.Markdown("Use voice input to communicate with the assistant. Click record, speak your message, and get a text response.")
            
            with gr.Row():
                audio_input = gr.Audio(
                    label="Record Your Message",
                    sources=["microphone"],
                    type="filepath"
                )
                transcribe_btn = gr.Button("Transcribe", variant="primary")
            
            transcribed_text = gr.Textbox(
                label="Transcribed Text",
                placeholder="Your transcribed message will appear here..."
            )
            
            send_voice_btn = gr.Button("Send Voice Message", variant="primary")
            voice_response = gr.Textbox(
                label="Assistant Response",
                lines=5
            )
        
        with gr.Tab("📋 Mental Health Assessment"):
            gr.Markdown("Take comprehensive mental health screenings to better understand your wellness.")
            assessment_info = gr.Markdown(take_assessment())
            
        with gr.Tab("🆘 Resources & Support"):
            gr.Markdown("Access mental health resources and emergency support information.")
            resources_info = gr.Markdown(get_resources())
        
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## About This Application
            
            This Mental Health AI Assistant uses advanced artificial intelligence to provide:
            
            ### 🤖 **Multi-Agent AI Technology**
            - **CrewAI Framework:** Specialized agents working together
            - **Crisis Detection:** Automatic identification of emergency situations
            - **Condition Classification:** AI-powered mental health assessment
            - **Knowledge Retrieval:** Evidence-based information from mental health databases
            
            ### 🎯 **Evidence-Based Assessments**
            - **PHQ-9:** Depression screening questionnaire
            - **GAD-7:** Generalized anxiety disorder assessment  
            - **DAST-10:** Drug abuse screening test
            - **AUDIT:** Alcohol use disorders identification test
            - **Bipolar Screening:** Mood disorder assessment
            
            ### 🔒 **Privacy & Safety**
            - Your conversations are not stored permanently
            - No personal data is shared with third parties
            - Crisis detection provides immediate resource recommendations
            - Professional help referrals when needed
            
            ### ⚠️ **Important Disclaimer**
            This tool is for informational and support purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. 
            
            **In case of emergency, please contact:**
            - Emergency Services: 911 (US) or 112 (International)
            - National Suicide Prevention Lifeline: 988
            - Crisis Text Line: Text HOME to 741741
            """)
        
        # Event handlers
        start_btn.click(
            fn=create_user_session,
            inputs=[name_input],
            outputs=[session_status]
        )
        
        send_btn.click(
            fn=process_chat_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            fn=process_chat_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        clear_btn.click(
            fn=lambda: [],
            outputs=[chatbot]
        )
        
        transcribe_btn.click(
            fn=process_voice_input,
            inputs=[audio_input],
            outputs=[transcribed_text]
        )
        
        send_voice_btn.click(
            fn=lambda text, history: process_chat_message(text, history) if text.strip() else (history, ""),
            inputs=[transcribed_text, chatbot],
            outputs=[chatbot, transcribed_text]
        )
    
    return interface

if __name__ == "__main__":
    # Initialize the Flask app context
    with flask_app.app_context():
        # Create database tables
        try:
            from models.chat_session import db
            db.create_all()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
    
    # Create and launch the Gradio interface
    print("🚀 Starting Mental Health AI Assistant on Hugging Face Spaces...")
    interface = create_interface()
    
    # Launch with Hugging Face Spaces configuration
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False,
        show_error=True,
        quiet=False
    )
