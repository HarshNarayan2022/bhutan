# Mental Health Chatbot Application

A comprehensive multi-agent mental health support application that combines AI-powered conversational assistance with assessment tools, sentiment analysis, and user management features.

## 🌟 Features

### Core Functionality
- **AI-Powered Chatbot**: Multi-agent system using CrewAI for intelligent mental health conversations
- **RAG (Retrieval-Augmented Generation)**: Knowledge base integration for evidence-based responses
- **Real-time Chat Interface**: Modern web-based chat UI with typing indicators and message history
- **Voice Integration**: Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities
- **Sentiment Analysis**: Real-time emotion detection and sentiment tracking
- **Mental Health Assessments**: Standardized questionnaires (PHQ-9, GAD-7, DAST-10, AUDIT, Bipolar)

### User Management
- **User Registration & Authentication**: Secure account creation and login
- **User Dashboard**: Personalized dashboard with assessment history and insights
- **Guest Access**: Anonymous chat sessions for privacy-conscious users
- **Account Management**: Profile management and secure account deletion

### Advanced Features
- **Crisis Detection**: Automatic identification of mental health emergencies
- **Condition Classification**: AI-powered categorization of mental health concerns
- **Session Management**: Persistent chat history and conversation tracking
- **PDF Report Generation**: Downloadable assessment reports
- **Multi-Agent Architecture**: Specialized agents for different aspects of mental health support

## 🏗️ Architecture

### Frontend (Flask Web Application)
- **Templates**: HTML templates with modern CSS styling
- **Static Assets**: CSS files, images, and client-side JavaScript
- **Routes**: Web endpoints for UI rendering and user interactions

### Backend Services

#### Flask Application (`main.py`)
- User authentication and session management
- Web interface routing
- Voice processing (Whisper integration)
- Text-to-Speech generation (Edge TTS)
- Database operations (SQLite with SQLAlchemy)
- Chat session management

#### FastAPI Application (`fastapi_app.py`)
- AI message processing endpoints
- CrewAI integration for multi-agent responses
- RAG system integration
- Sentiment analysis
- Assessment processing
- PDF report generation

### AI Agents System (`crew_ai/`)
- **Crisis Detection Agent**: Identifies emergency situations
- **Mental Condition Classifier**: Categorizes mental health concerns
- **RAG Agents**: Knowledge retrieval and summarization
- **Assessment Conductor**: Administers standardized questionnaires
- **Response Generator**: Produces empathetic, helpful responses

### Data Layer
- **SQLite Database**: User profiles, assessments, chat history
- **Vector Store**: Knowledge base for RAG system
- **Session Storage**: Temporary chat data and user context

## 🚀 Docker Deployment for Render.com

This application is optimized for single-container Docker deployment on Render.com.

### Prerequisites
- Docker
- Git
- Render.com account

### Environment Variables

Create the following environment variables in your Render deployment:

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
SESSION_COOKIE_SECURE=true
```

#### Optional Configuration
```env
FLASK_ENV=production
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.onrender.com
```

### Deployment Steps

1. **Fork or Clone Repository**
   ```bash
   git clone <repository-url>
   cd bhutan
   ```

2. **Connect to Render**
   - Create a new **Web Service** on Render.com
   - Connect your GitHub repository
   - Choose **Docker** as the runtime

3. **Configure Render Settings**
   - **Name**: `mental-health-chatbot`
   - **Region**: Choose your preferred region
   - **Branch**: `main` (or your deployment branch)
   - **Root Directory**: Leave empty (uses repository root)
   - **Dockerfile Path**: `./Dockerfile`

4. **Set Environment Variables**
   Add all required environment variables in the Render dashboard under "Environment"

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy using the Dockerfile
   - Monitor the deployment logs for any issues

### Dockerfile Configuration

The included `Dockerfile` is optimized for Render deployment:

- Uses Python 3.11 slim base image
- Installs all system dependencies (gcc, ffmpeg, etc.)
- Sets up proper port handling with `$PORT` environment variable
- Includes health checks for monitoring
- Uses `render_start.py` for optimized startup

### Startup Process

The application uses `render_start.py` which:

1. **Starts FastAPI Backend**: Launches on an internal port as a background service
2. **Starts Flask Frontend**: Runs on the main Render port (`$PORT`)
3. **Health Monitoring**: Both services include health check endpoints
4. **Graceful Shutdown**: Handles termination signals properly

### Health Checks

- **Flask Health**: `https://yourdomain.onrender.com/health`
- **FastAPI Health**: Internal health checks for service communication

### Monitoring and Logs

Access logs through the Render dashboard:
- **Deploy Logs**: Build and deployment information
- **Service Logs**: Application runtime logs
- **Metrics**: CPU, memory, and request metrics

### Troubleshooting

#### Common Issues

1. **Build Failures**
   - Check that all required environment variables are set
   - Verify API keys are valid
   - Review build logs for missing dependencies

2. **Service Timeouts**
   - Increase health check timeout in Render settings
   - Monitor startup logs for initialization issues
   - Ensure sufficient memory allocation

3. **Database Issues**
   - The application uses SQLite by default (file-based)
   - Data persists between deployments in `/app/data/`
   - For production, consider upgrading to PostgreSQL via Render add-ons

#### Performance Optimization

- **Memory**: Recommended minimum 1GB RAM
- **CPU**: Single CPU core sufficient for moderate traffic
- **Scaling**: Render auto-scales based on traffic
- **Response Time**: Typical response time under 2 seconds

## 📱 Usage Guide

### For Users

#### Getting Started
1. **Registration**: Create an account or use guest access
2. **Assessment**: Complete initial mental health assessments
3. **Chat**: Start conversations with the AI assistant
4. **Dashboard**: View your progress and assessment history

#### Chat Features
- **Text Messages**: Type messages and receive AI responses
- **Voice Input**: Click the microphone icon to speak
- **Text-to-Speech**: Click the speaker icon to hear responses
- **Message History**: Previous conversations are saved and accessible

#### Assessments
- **PHQ-9**: Depression screening
- **GAD-7**: Anxiety assessment
- **DAST-10**: Substance abuse screening
- **AUDIT**: Alcohol use assessment
- **Bipolar**: Bipolar disorder screening

### For Developers

#### Local Development

For local development and testing:

```bash
# Clone the repository
git clone <repository-url>
cd bhutan

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally (development mode)
python main.py  # Flask on port 5000
python -m uvicorn fastapi_app:app --port 8000  # FastAPI on port 8000
```

#### Adding New Features

1. **New Assessments**: Add questionnaire JSON files in `crew_ai/questionnaires/`
2. **Custom Agents**: Modify configurations in `config/agents.yaml`
3. **Knowledge Base**: Add PDF documents to `knowledge/` directory
4. **UI Updates**: Modify templates in `templates/` and styles in `static/`

#### Docker Testing

Test the Docker build locally before deploying:

```bash
# Build the Docker image
docker build -t mental-health-app .

# Run locally with Docker
docker run -p 10000:10000 --env-file .env mental-health-app

# Test health endpoints
curl http://localhost:10000/health
```

## 🔧 Configuration

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GOOGLE_API_KEY` | Yes | Google AI API key | - |
| `GROQ_API_KEY` | Yes | Groq API key | - |
| `OPENAI_API_KEY` | Yes | OpenAI API key | - |
| `SECRET_KEY` | Yes | Flask secret key | - |
| `PORT` | No | Application port | 10000 |
| `FLASK_ENV` | No | Flask environment | production |
| `DEBUG` | No | Debug mode | false |
| `ALLOWED_ORIGINS` | No | CORS origins | * |

### Agent Configuration

The AI agents can be configured via `config/agents.yaml`:

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
