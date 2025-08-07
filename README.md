# Mental Health Chatbot - Bhutan

A comprehensive mental health support application optimized for cloud deployment with multiple platform support.

## 🚀 Deployment Platforms

### ✅ Render Cloud (Primary - 512MB RAM Optimized)
**Ready for immediate deployment with Docker**

- **Memory optimized**: Runs efficiently in 512MB RAM
- **Lightweight stack**: Flask + SQLite + TextBlob
- **Auto-scaling**: Handles traffic spikes gracefully
- **Health monitoring**: Built-in health checks

### 🔧 Local Development
- Full-featured development environment
- Advanced AI agents with CrewAI
- RAG system for knowledge retrieval
- Complete testing suite

### 🌟 Hugging Face Spaces (Alternative)
- Fallback deployment option
- Gradio interface available
- Public demo hosting

## 🏗️ Architecture

### **Multi-Platform Design**
```
Render Deployment (Production):
├── Dockerfile (memory-optimized)
├── app_render.py (Flask + SQLite)
├── requirements_render.txt (lightweight)
└── 512MB RAM compatible

Local Development:
├── Full AI stack with CrewAI
├── Advanced RAG system
├── Complete assessment tools
└── All features enabled
```

## 🌟 Core Features

### Core Functionality
- **AI-Powered Chatbot**: Multi-agent system using CrewAI for intelligent mental health conversations
- **RAG (Retrieval-Augmented Generation)**: Knowledge base integration for evidence-based responses
- **Real-time Chat Interface**: Modern Gradio-based chat UI with typing indicators and message history
- **Voice Integration**: Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities
- **Sentiment Analysis**: Real-time emotion detection and sentiment tracking
- **Mental Health Assessments**: Standardized questionnaires (PHQ-9, GAD-7, DAST-10, AUDIT, Bipolar)

### User Management
- **Session Management**: Secure guest sessions with chat history
- **User Dashboard**: Assessment history and insights tracking
- **Anonymous Access**: Privacy-focused chat sessions
- **Assessment Storage**: Persistent assessment results and reports

### Advanced Features
- **Crisis Detection**: Automatic identification of mental health emergencies
- **Condition Classification**: AI-powered categorization of mental health concerns
- **Session Persistence**: Chat history maintained during session
- **PDF Report Generation**: Downloadable assessment reports
- **Multi-Agent Architecture**: Specialized agents for different aspects of mental health support

## 🏗️ Architecture

### Gradio Interface (`app.py`)
- **Multi-tab Interface**: Chat, Voice, Assessment, Resources, and About tabs
- **Real-time Chat**: Message processing with typing indicators
- **Voice Processing**: Whisper integration for speech-to-text
- **Assessment Integration**: Interactive mental health questionnaires
- **Session Management**: User context and history preservation

### Backend Services

#### Flask Application (`main.py`)
- Core chat response generation
- Voice processing (Whisper integration)
- Text-to-Speech generation (Edge TTS)
- Database operations (SQLite with SQLAlchemy)
- Chat session management

#### AI Agents System (`crew_ai/`)
- **Crisis Detection Agent**: Identifies emergency situations
- **Mental Condition Classifier**: Categorizes mental health concerns
- **RAG Agents**: Knowledge retrieval and summarization
- **Assessment Conductor**: Administers standardized questionnaires
- **Response Generator**: Produces empathetic, helpful responses

### Data Layer
- **SQLite Database**: User profiles, assessments, chat history
- **Vector Store**: Knowledge base for RAG system
- **Session Storage**: Temporary chat data and user context

## 🚀 Render Cloud Deployment (Recommended)

### Quick Start for Render

**The application is pre-configured for Render deployment with 512MB RAM optimization.**

#### 1. Prerequisites
- GitHub/GitLab repository with this code
- Render account (free tier available)

#### 2. Automatic Deployment
```bash
# Run the deployment preparation script
python deploy_render.py

# Validate Docker build (optional)
python validate_docker.py
```

#### 3. Render Dashboard Setup
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure:
   - **Environment**: Docker
   - **Branch**: main
   - **Dockerfile**: ./Dockerfile
   - **Plan**: Free (512MB RAM)

#### 4. Environment Variables
Set these in Render dashboard:
```env
PORT=10000                    # Auto-set by Render
FLASK_ENV=production
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
SECRET_KEY=your-secret-key    # Generate secure key
```

#### 5. Deploy
- Click "Create Web Service"
- Wait 5-10 minutes for build
- Access at: `https://your-app.onrender.com`

### 📊 Render Optimization Features

#### Memory Efficiency (512MB RAM)
- **Lightweight dependencies**: Only essential packages
- **SQLite database**: No external database needed
- **Minimal Python base**: python:3.11-slim
- **Memory monitoring**: Built-in resource tracking

#### Performance
- **Health checks**: `/health` endpoint for monitoring
- **Fast startup**: ~10-15 seconds cold start
- **Auto-scaling**: Handles traffic spikes
- **Persistent storage**: SQLite data persistence

#### File Structure for Render
```
bhutan/
├── Dockerfile              # Render-optimized Docker config
├── requirements_render.txt # Lightweight dependencies
├── app_render.py           # Memory-optimized Flask app
├── render.yaml            # Render service configuration
├── deploy_render.py       # Deployment preparation script
└── validate_docker.py     # Docker validation tool
```

### 🔧 Render Deployment Files

#### Key Files Explained
- **`app_render.py`**: Optimized Flask app with embedded HTML/JS UI
- **`requirements_render.txt`**: Minimal dependencies (Flask, SQLite, TextBlob)
- **`Dockerfile`**: Multi-stage build with health checks
- **`render.yaml`**: Service configuration for auto-deployment

#### Features Included in Render Version
- ✅ Mental health chatbot with keyword-based responses
- ✅ Sentiment analysis using TextBlob
- ✅ Crisis resource information
- ✅ Simple mental health assessment
- ✅ SQLite database for chat logging
- ✅ Health monitoring and status checks
- ✅ Responsive web interface

#### Limitations on Free Tier
- Service sleeps after 15 minutes of inactivity
- 750 hours/month free compute time
- No persistent file storage (use database for data)

### 🔍 Testing Render Deployment

```bash
# Build and test locally
docker build -t mental-health-test .
docker run -p 10000:10000 --memory=512m mental-health-test

# Test endpoints
curl http://localhost:10000/health
curl http://localhost:10000/
curl -X POST http://localhost:10000/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

### 📈 Monitoring on Render

- **Logs**: Real-time in Render dashboard
- **Metrics**: Memory, CPU usage monitoring
- **Health**: Automatic health check monitoring
- **Alerts**: Email notifications for service issues

### 🆘 Troubleshooting Render Deployment

#### Build Issues
- Check Dockerfile syntax
- Verify requirements_render.txt packages
- Monitor build logs in Render dashboard

#### Runtime Issues
- Check application logs
- Verify environment variables
- Test health endpoint: `/health`
- Ensure database initialization

#### Memory Issues
- Monitor resource usage in dashboard
- Check for memory leaks in logs
- Restart service if needed

---

## 🚀 Alternative: Hugging Face Spaces Deployment

This application is containerized and optimized for deployment on Hugging Face Spaces using Docker, integrating both Flask (main.py) and FastAPI (fastapi_app.py) backends.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gradio UI     │    │   Flask App     │    │  FastAPI App    │
│   (Port 7860)   │◄──►│   (Port 5001)   │◄──►│  (Port 8001)    │
│   app.py        │    │   main.py       │    │  fastapi_app.py │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  SQLite Database│
                    │  Vector Store   │
                    │  Session Data   │
                    └─────────────────┘
```

### Prerequisites
- Hugging Face account with Spaces access
- Required API keys (Google, OpenAI, Groq)
- Git for repository management

### Environment Variables

Set the following secrets in your Hugging Face Space:

#### Required API Keys
```env
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

#### Security
```env
SECRET_KEY=your_super_secure_secret_key
FLASK_SECRET_KEY=your_flask_secret_key
```

### Deployment Steps

1. **Create a New Docker Space**
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose **Docker** as the SDK
   - Name your space (e.g., `mental-health-ai-assistant`)

2. **Clone and Prepare Repository**
   ```bash
   git clone <your-repository>
   cd bhutan
   
   # Verify Docker files are present
   ls -la Dockerfile app.py requirements.txt
   ```

3. **Initialize Space Repository**
   ```bash
   # Initialize git for Spaces
   git init
   git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   
   # Add all files
   git add .
   git commit -m "Deploy Mental Health AI Assistant to Hugging Face Spaces"
   git push -u origin main
   ```

4. **Configure Space Settings**
   - Go to your Space's Settings tab
   - Add all required API keys in "Repository secrets"
   - Choose hardware tier (CPU Basic recommended minimum)

5. **Monitor Deployment**
   - Watch the build logs in your Space
   - The Docker container will automatically:
     - Install system dependencies (FFmpeg, GCC, etc.)
     - Install Python packages
     - Start Flask backend (port 5001)
     - Start FastAPI backend (port 8001) 
     - Launch Gradio interface (port 7860)

### Docker Configuration Details

#### Multi-Service Architecture
The application runs three services in a single container:

1. **Gradio Frontend (app.py)**
   - Main user interface on port 7860
   - Handles user interactions and session management
   - Communicates with Flask and FastAPI backends

2. **Flask Backend (main.py)**
   - Core application logic on port 5001
   - Chat response generation
   - Voice processing (Whisper)
   - Database operations (SQLite)

3. **FastAPI Backend (fastapi_app.py)**
   - AI services on port 8001
   - CrewAI multi-agent system
   - Assessment processing
   - PDF report generation

#### Container Specifications
- **Base Image**: Python 3.11-slim
- **System Packages**: FFmpeg, GCC, libffi-dev, libssl-dev
- **Exposed Port**: 7860 (Gradio)
- **Health Check**: HTTP probe on port 7860
- **Working Directory**: /app

#### File Structure
```
├── Dockerfile              # Container configuration
├── .dockerignore           # Build optimization
├── app.py                  # Gradio entry point
├── main.py                 # Flask backend
├── fastapi_app.py          # FastAPI backend
├── requirements.txt        # Python dependencies
├── config_manager.py       # Configuration
├── models/                 # Database models
├── crew_ai/               # AI agents
├── knowledge/             # Knowledge base
└── static/                # Assets
```

### Monitoring and Logs

Access logs and metrics through the Hugging Face Spaces interface:

#### Build Logs
- Docker image building process
- Dependency installation progress
- System package installation
- Application startup sequence

#### Runtime Logs
- Application logs and error messages
- User interaction tracking
- AI response generation logs
- Health check status

#### Performance Metrics
- Container resource usage (CPU, Memory)
- Request response times
- User session analytics
- Error rates and debugging info

### Troubleshooting

#### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs in Spaces interface
   # Common causes:
   # - Missing or invalid API keys
   # - Dependency conflicts
   # - Insufficient disk space during build
   ```

2. **Container Startup Issues**
   ```bash
   # Monitor runtime logs for:
   # - Database initialization errors
   # - Missing environment variables
   # - Port binding conflicts
   ```

3. **Memory Issues**
   ```bash
   # Symptoms: Container restarts, OOM errors
   # Solutions:
   # - Upgrade to CPU Upgrade plan
   # - Optimize model loading
   # - Reduce concurrent request handling
   ```

4. **API Rate Limiting**
   ```bash
   # Monitor for API quota exceeded errors
   # Solutions:
   # - Check API key quotas
   # - Implement request caching
   # - Add rate limiting in application
   ```

#### Performance Optimization

1. **Container Efficiency**
   - Multi-stage Docker builds reduce image size
   - .dockerignore excludes unnecessary files
   - System dependencies are cached between builds

2. **Application Performance**
   - Database connections are pooled
   - Static assets are served efficiently
   - AI model responses are cached when possible

3. **Resource Management**
   - Memory usage is optimized for container limits
   - CPU usage is balanced across features
   - Network requests are handled asynchronously

### Local Development and Testing

#### Local Docker Testing
```bash
# Build the Docker image locally
docker build -t mental-health-chatbot .

# Run locally with environment variables
docker run -p 7860:7860 \
  -e GOOGLE_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -e SECRET_KEY=your_secret \
  mental-health-chatbot

# Access the application
# Open browser to http://localhost:7860
```

#### Development Without Docker
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY=your_key
export GROQ_API_KEY=your_key
export OPENAI_API_KEY=your_key
export SECRET_KEY=your_secret

# Run the Gradio application
python app.py
```

### Security and Privacy

#### Container Security
- **Isolated Environment**: Application runs in isolated Docker container
- **Minimal Base Image**: Uses slim Python image with minimal attack surface
- **Non-persistent Secrets**: API keys are passed as environment variables
- **Network Security**: Only port 7860 is exposed

#### Data Privacy
- **Session-based Storage**: Chat data is not permanently stored
- **Local Processing**: Most AI processing happens within the container
- **API Security**: API keys are securely managed through Spaces secrets
- **User Anonymity**: No personal data collection or tracking

## 🌟 Features

### Core Functionality
- **AI-Powered Chatbot**: Multi-agent system using CrewAI for intelligent mental health conversations
- **RAG (Retrieval-Augmented Generation)**: Knowledge base integration for evidence-based responses
- **Real-time Chat Interface**: Modern Gradio-based chat UI with typing indicators and message history
- **Voice Integration**: Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities
- **Sentiment Analysis**: Real-time emotion detection and sentiment tracking
- **Mental Health Assessments**: Standardized questionnaires (PHQ-9, GAD-7, DAST-10, AUDIT, Bipolar)

### User Management
- **Session Management**: Secure guest sessions with chat history
- **User Dashboard**: Assessment history and insights tracking
- **Anonymous Access**: Privacy-focused chat sessions
- **Assessment Storage**: Persistent assessment results and reports

### Advanced Features
- **Crisis Detection**: Automatic identification of mental health emergencies
- **Condition Classification**: AI-powered categorization of mental health concerns
- **Session Persistence**: Chat history maintained during session
- **PDF Report Generation**: Downloadable assessment reports
- **Multi-Agent Architecture**: Specialized agents for different aspects of mental health support

## 🏗️ Architecture

### Gradio Interface (`app.py`)
- **Multi-tab Interface**: Chat, Voice, Assessment, Resources, and About tabs
- **Real-time Chat**: Message processing with typing indicators
- **Voice Processing**: Whisper integration for speech-to-text
- **Assessment Integration**: Interactive mental health questionnaires
- **Session Management**: User context and history preservation

### Backend Services

#### Flask Application (`main.py`)
- Core chat response generation
- Voice processing (Whisper integration)
- Text-to-Speech generation (Edge TTS)
- Database operations (SQLite with SQLAlchemy)
- Chat session management

#### AI Agents System (`crew_ai/`)
- **Crisis Detection Agent**: Identifies emergency situations
- **Mental Condition Classifier**: Categorizes mental health concerns
- **RAG Agents**: Knowledge retrieval and summarization
- **Assessment Conductor**: Administers standardized questionnaires
- **Response Generator**: Produces empathetic, helpful responses

### Data Layer
- **SQLite Database**: User profiles, assessments, chat history
- **Vector Store**: Knowledge base for RAG system
- **Session Storage**: Temporary chat data and user context

## 🚀 Hugging Face Spaces Deployment

This application is optimized for deployment on Hugging Face Spaces using Gradio.

### Prerequisites
- Hugging Face account
- Git
- Required API keys (Google, OpenAI, Groq)

### Environment Variables

Set the following secrets in your Hugging Face Space:

#### Required API Keys
```env
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

#### Security
```env
SECRET_KEY=your_super_secure_secret_key
FLASK_SECRET_KEY=your_flask_secret_key
```

#### Optional Configuration
```env
FLASK_ENV=production
DEBUG=false
HUGGINGFACE_SPACES=1
```

### Deployment Steps

1. **Create a New Space**
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Choose **Gradio** as the SDK
   - Select **Python** as the programming language

2. **Upload Your Code**
   ```bash
   git clone <your-repository>
   cd bhutan
   
   # Initialize git for Spaces
   git init
   git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   
   # Add and commit files
   git add .
   git commit -m "Initial deployment to Hugging Face Spaces"
   git push -u origin main
   ```

3. **Configure Space Settings**
   - **Hardware**: Choose CPU Basic (free) or upgrade for better performance
   - **Visibility**: Public or Private as preferred
   - **Secrets**: Add all required environment variables in the Settings tab

4. **Set Up Dependencies**
   The `requirements.txt` file is already configured for Spaces deployment with:
   - Gradio for the interface
   - Flask for backend logic
   - AI/ML libraries (optimized versions)
   - All necessary dependencies

5. **Entry Point**
   The application uses `app.py` as the main entry point, which:
   - Creates a Gradio Blocks interface
   - Integrates all Flask backend functionality
   - Provides tabs for Chat, Voice, Assessment, Resources, and About
   - Handles session management and user interactions

### Space Configuration

#### Hardware Requirements
- **CPU Basic**: Suitable for basic chat functionality
- **CPU Upgrade**: Recommended for full AI features including voice processing
- **GPU**: Not required but can improve response times

#### File Structure for Spaces
```
app.py                 # Main Gradio entry point
requirements.txt       # Hugging Face Spaces dependencies
README.md             # This documentation
main.py               # Flask backend logic
config_manager.py     # Configuration management
models/               # Database models
crew_ai/              # AI agents system
knowledge/            # Knowledge base files
static/               # CSS and assets
templates/            # HTML templates (used by Flask components)
```

### Features in Spaces

#### Chat Tab
- Real-time conversation with AI mental health assistant
- Message history preservation during session
- Typing indicators and response streaming
- Crisis detection and appropriate responses

#### Voice Tab
- Speech-to-text using Whisper
- Text-to-speech for responses
- Voice conversation mode
- Audio file upload support

#### Assessment Tab
- Interactive mental health questionnaires
- Real-time scoring and analysis
- PDF report generation
- Assessment history tracking

#### Resources Tab
- Mental health resources and information
- Crisis hotlines and emergency contacts
- Self-help tools and techniques
- Educational materials

#### About Tab
- Application information and usage guide
- Privacy policy and data handling
- Contact information and support

### Monitoring and Logs

Access logs and metrics through the Hugging Face Spaces interface:
- **Build Logs**: Installation and setup information
- **Application Logs**: Runtime logs and error messages
- **Usage Analytics**: Space visits and user interactions

### Troubleshooting

#### Common Issues

1. **Build Failures**
   - Check that all required secrets are set correctly
   - Verify API keys are valid and have sufficient quotas
   - Review build logs for missing dependencies

## 📚 Additional Resources

### Documentation
- **API Documentation**: Available at `/docs` endpoint when running
- **Agent Configuration**: See `config/` directory for YAML configurations
- **Database Schema**: Check `models/` directory for SQLAlchemy models

### Support
- **GitHub Issues**: For bug reports and feature requests
- **Community Discussions**: Join the Hugging Face Space comments
- **Documentation Updates**: Contributing to improve documentation is welcome

### License
This project is open source. Please check the LICENSE file for details.

---

**Ready for Hugging Face Spaces!** 🚀

This application has been fully optimized for Hugging Face Spaces deployment with Gradio interface, removing all Docker and Render-specific configurations.

```yaml
emotion_detector:
  role: Emotion Detector
  goal: Analyze user input to determine their emotional state
  backstory: You are an empathetic AI skilled at identifying emotions

crisis_detector:
  role: Crisis Detector
  goal: Identify potential mental health emergencies
  backstory: You are trained to recognize signs of crisis
```

### RAG Configuration

Knowledge retrieval settings in `config/rag.yaml`:

```yaml
vector_store:
  chunk_size: 1000
  chunk_overlap: 200
  
retrieval:
  top_k: 5
  similarity_threshold: 0.7
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review Render deployment logs

## 🔒 Security

- All user data is encrypted in transit
- Passwords are hashed using bcrypt
- Session management with secure cookies
- API keys are stored as environment variables
- No sensitive data in logs or version control

---

**Disclaimer**: This application is designed to provide mental health support and information but is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified healthcare providers for mental health concerns.
