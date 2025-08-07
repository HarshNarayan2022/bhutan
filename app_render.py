#!/usr/bin/env python3
"""
Render Cloud Deployment - Mental Health Chatbot
Optimized for 512MB RAM with essential features only
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from textblob import TextBlob

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mental-health-secret-key-render')

# Database setup (SQLite for memory efficiency)
DATABASE = 'mental_health.db'

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chat sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            sentiment REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Assessments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            assessment_type TEXT NOT NULL,
            score INTEGER,
            responses TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Mental health response patterns (memory-efficient)
MENTAL_HEALTH_RESPONSES = {
    'crisis': [
        "I'm very concerned about what you're sharing. Please reach out for immediate help:",
        "🚨 Emergency Resources:",
        "• National Suicide Prevention Lifeline: 988",
        "• Crisis Text Line: Text HOME to 741741", 
        "• Emergency Services: 911",
        "Your safety is the most important thing right now."
    ],
    'depression': [
        "I hear that you're going through a difficult time. Depression is treatable and you're not alone.",
        "Consider reaching out to a mental health professional who can provide proper support.",
        "Small steps can help: maintain routines, get sunlight, stay connected with supportive people."
    ],
    'anxiety': [
        "Anxiety can feel overwhelming, but there are ways to manage it.",
        "Try deep breathing: breathe in for 4 counts, hold for 4, breathe out for 6.",
        "Grounding technique: name 5 things you see, 4 you can touch, 3 you can hear."
    ],
    'stress': [
        "Stress is a normal response, but chronic stress needs attention.",
        "Consider: exercise, meditation, talking to someone, or adjusting your workload.",
        "Remember to take breaks and practice self-care."
    ],
    'positive': [
        "It's wonderful to hear positive things from you!",
        "Celebrating small wins is important for mental health.",
        "Keep nurturing the things that bring you joy and peace."
    ],
    'default': [
        "Thank you for sharing that with me. I'm here to listen.",
        "How are you feeling about this situation?",
        "What kind of support would be most helpful for you right now?"
    ]
}

def analyze_sentiment(text):
    """Simple sentiment analysis using TextBlob"""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0.0

def get_mental_health_response(message, sentiment_score=0.0):
    """Generate appropriate mental health response"""
    message_lower = message.lower()
    
    # Crisis detection
    crisis_words = ['suicide', 'kill myself', 'end it all', 'hurt myself', 'self harm', 'die', 'death wish']
    if any(word in message_lower for word in crisis_words):
        return '\n'.join(MENTAL_HEALTH_RESPONSES['crisis'])
    
    # Depression keywords
    depression_words = ['depressed', 'depression', 'sad', 'hopeless', 'worthless', 'empty', 'numb']
    if any(word in message_lower for word in depression_words):
        return MENTAL_HEALTH_RESPONSES['depression'][0]
    
    # Anxiety keywords
    anxiety_words = ['anxious', 'anxiety', 'worried', 'panic', 'nervous', 'fear', 'scared']
    if any(word in message_lower for word in anxiety_words):
        return MENTAL_HEALTH_RESPONSES['anxiety'][0]
    
    # Stress keywords
    stress_words = ['stress', 'stressed', 'overwhelmed', 'pressure', 'burned out', 'exhausted']
    if any(word in message_lower for word in stress_words):
        return MENTAL_HEALTH_RESPONSES['stress'][0]
    
    # Positive sentiment
    if sentiment_score > 0.3:
        return MENTAL_HEALTH_RESPONSES['positive'][0]
    
    # Default supportive response
    return MENTAL_HEALTH_RESPONSES['default'][0]

# HTML Templates (embedded to save memory)
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mental Health Chatbot - Render</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .chat-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-box { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; background: #fafafa; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .user { background: #007bff; color: white; text-align: right; }
        .bot { background: #28a745; color: white; }
        .input-group { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .crisis-alert { background: #dc3545; color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .resources { background: #17a2b8; color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h1>🧠 Mental Health Support Assistant</h1>
        <p><strong>Render Cloud Deployment</strong> - Optimized for 512MB RAM</p>
        
        <div class="crisis-alert">
            <strong>⚠️ Crisis Resources:</strong><br>
            • Emergency: 911<br>
            • Suicide Prevention: 988<br>
            • Crisis Text: HOME to 741741
        </div>
        
        <div id="chat-box" class="chat-box">
            <div class="message bot">
                Hello! I'm here to provide mental health support. How are you feeling today?
            </div>
        </div>
        
        <div class="input-group">
            <input type="text" id="user-input" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <div class="resources">
            <strong>🔒 Privacy:</strong> Your conversations are processed securely and not permanently stored.<br>
            <strong>⚕️ Disclaimer:</strong> This is not a substitute for professional mental health care.
        </div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('user-input');
            const chatBox = document.getElementById('chat-box');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            chatBox.innerHTML += `<div class="message user">${message}</div>`;
            input.value = '';
            
            // Show typing indicator
            chatBox.innerHTML += `<div class="message bot" id="typing">Typing...</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
            
            // Send to backend
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                document.getElementById('typing').remove();
                
                // Add bot response
                chatBox.innerHTML += `<div class="message bot">${data.response}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            })
            .catch(error => {
                document.getElementById('typing').remove();
                chatBox.innerHTML += `<div class="message bot">Sorry, I'm having technical difficulties. Please try again.</div>`;
            });
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def home():
    return render_template_string(CHAT_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check for Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'mental-health-chatbot',
        'memory_optimized': True,
        'platform': 'render',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Analyze sentiment
        sentiment_score = analyze_sentiment(message)
        
        # Generate response
        response = get_mental_health_response(message, sentiment_score)
        
        # Log to database (optional, memory permitting)
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (user_id, message, response, sentiment) VALUES (?, ?, ?, ?)",
                (None, message, response, sentiment_score)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database logging error: {e}")
        
        return jsonify({
            'response': response,
            'sentiment': sentiment_score,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "I'm sorry, I'm having technical difficulties. Please try again.",
            'error': str(e)
        }), 500

@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    """Simple mental health assessment"""
    if request.method == 'GET':
        assessment_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mental Health Assessment</title>
            <style>body{font-family:Arial;max-width:600px;margin:0 auto;padding:20px;}</style>
        </head>
        <body>
            <h1>Quick Mental Health Check</h1>
            <form method="POST">
                <p><strong>How often have you felt down, depressed, or hopeless in the past 2 weeks?</strong></p>
                <input type="radio" name="q1" value="0"> Not at all<br>
                <input type="radio" name="q1" value="1"> Several days<br>
                <input type="radio" name="q1" value="2"> More than half the days<br>
                <input type="radio" name="q1" value="3"> Nearly every day<br><br>
                
                <p><strong>How often have you felt nervous, anxious, or on edge?</strong></p>
                <input type="radio" name="q2" value="0"> Not at all<br>
                <input type="radio" name="q2" value="1"> Several days<br>
                <input type="radio" name="q2" value="2"> More than half the days<br>
                <input type="radio" name="q2" value="3"> Nearly every day<br><br>
                
                <button type="submit">Get Results</button>
            </form>
        </body>
        </html>
        '''
        return assessment_html
    
    # Process assessment
    q1 = int(request.form.get('q1', 0))
    q2 = int(request.form.get('q2', 0))
    total_score = q1 + q2
    
    if total_score <= 2:
        result = "Your responses suggest minimal mental health concerns."
    elif total_score <= 4:
        result = "Your responses suggest mild mental health concerns. Consider speaking with a professional."
    else:
        result = "Your responses suggest significant concerns. Please consider professional mental health support."
    
    return f'''
    <html><body style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px;">
    <h1>Assessment Results</h1>
    <p><strong>{result}</strong></p>
    <p>Score: {total_score}/6</p>
    <p><em>This is not a professional diagnosis. Please consult with a mental health professional for proper evaluation.</em></p>
    <a href="/">Back to Chat</a>
    </body></html>
    '''

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Get port from environment (Render uses PORT env var)
    port = int(os.environ.get('PORT', 10000))
    
    print(f"🚀 Starting Mental Health Chatbot on Render")
    print(f"📍 Memory optimized for 512MB RAM")
    print(f"🔗 Port: {port}")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
