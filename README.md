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

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git

### Development Setup
```bash
# Clone the repository
git clone <repository-url>
cd bhutan

# Quick setup with Make
make setup

# Or manual setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.production .env
# Edit .env with your configuration

# Run the application
make run
# Or manually
python start_services.py
```

### Docker Deployment
```bash
# Development
make deploy

# Production
make deploy-prod

# Using deployment script
./deploy.sh deploy production
```

### Kubernetes Deployment
```bash
# Deploy to Kubernetes
make deploy-k8s

# Check status
kubectl get pods
kubectl logs -f deployment/mental-health-app
```

## 🚀 Setup and Installation

### Prerequisites
- Python 3.11 or higher
- pip or uv package manager
- Docker and Docker Compose (for containerized deployment)
- Node.js (for any frontend dependencies, if needed)

### Quick Start (Docker - Recommended)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd bhutan
   cp .env.production .env
   # Edit .env with your API keys and configuration
   ```

2. **Deploy with Docker Compose**
   ```bash
   # Development
   docker-compose -f docker-compose.dev.yml up -d
   
   # Production
   docker-compose up -d
   ```

3. **Access the Application**
   - Main Application: http://localhost:5000
   - API Documentation: http://localhost:8000/docs

### Manual Installation (Development)

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd bhutan
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Development
   pip install -r requirements.txt
   
   # Production
   pip install -r requirements.prod.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.production .env
   # Edit .env with your actual values
   ```

5. **Initialize Database**
   ```bash
   python -c "from main import init_db; init_db()"
   ```

6. **Run the Application**
   ```bash
   # Using the service manager
   python start_services.py
   
   # Or separately
   # Terminal 1: FastAPI
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
   
   # Terminal 2: Flask
   python main.py
   ```

## 🐳 Production Deployment

### Docker Deployment

The application is fully containerized and production-ready with Docker.

#### Using Make Commands
```bash
# Build and deploy
make docker-build
make deploy-prod

# Monitor
make logs
make health
make status

# Backup
make backup

# Update
make prod-update
```

#### Using Deployment Script
```bash
# Make executable
chmod +x deploy.sh

# Full deployment
./deploy.sh deploy production

# Monitor and manage
./deploy.sh status
./deploy.sh logs
./deploy.sh backup
./deploy.sh health
```

### Kubernetes Deployment

For cloud deployment, use the provided Kubernetes manifests:

```bash
# Apply configurations
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Monitor deployment
kubectl get pods
kubectl logs -f deployment/mental-health-app

# Scale application
kubectl scale deployment mental-health-app --replicas=3
```

### Environment Variables

Essential environment variables for production:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key

# Security
SECRET_KEY=your_super_secure_secret_key
SESSION_COOKIE_SECURE=true

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@host:5432/mental_health_app

# Server
FLASK_ENV=production
DEBUG=false
WORKERS=4

# Optional
REDIS_URL=redis://redis:6379/0
SENTRY_DSN=your_sentry_dsn
```

### Load Balancing and Scaling

The application supports horizontal scaling:

1. **Docker Compose**: Adjust replica count in `docker-compose.yml`
2. **Kubernetes**: Use `kubectl scale` command
3. **Load Balancer**: Configure Nginx or cloud load balancer

### Monitoring and Logging

#### Health Checks
- Flask: `http://localhost:5000/`
- FastAPI: `http://localhost:8000/health`

#### Log Files
- Application: `/app/logs/app.log`
- Gunicorn: `/app/logs/gunicorn_*.log`
- Error: `/app/logs/error.log`

#### Monitoring Commands
```bash
# Docker logs
docker-compose logs -f

# System health
./deploy.sh health

# Resource usage
docker stats
```

### Backup and Disaster Recovery

#### Automated Backup
```bash
# Create backup
./deploy.sh backup

# Restore from backup
./deploy.sh restore /path/to/backup
```

#### Manual Backup
```bash
# Database
docker exec container_name pg_dump -U user dbname > backup.sql

# User files
tar -czf backup.tar.gz data/ uploads/ chat_sessions/
```

### Security Considerations

1. **HTTPS**: Configure SSL certificates in production
2. **Firewall**: Restrict access to necessary ports only
3. **Secrets**: Use environment variables, never commit secrets
4. **Updates**: Regularly update dependencies and base images
5. **Monitoring**: Set up intrusion detection and log monitoring

### Performance Optimization

1. **Caching**: Enable Redis for session and response caching
2. **Database**: Use PostgreSQL with connection pooling
3. **Workers**: Adjust Gunicorn workers based on CPU cores
4. **CDN**: Use CDN for static assets in production
5. **Monitoring**: Set up APM tools like Sentry or New Relic

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

#### Adding New Assessments
1. Create questionnaire JSON in `crew_ai/questionnaires/`
2. Update `crew_ai/questionnaire.py` to include new assessment
3. Add classification logic in the condition classifier agent

#### Customizing Agents
1. Modify agent configurations in `config/agents.yaml`
2. Update agent implementations in `crew_ai/chatbot.py`
3. Adjust tools and capabilities as needed

#### Extending the Knowledge Base
1. Add PDF documents to `knowledge/` directory
2. Run document ingestion scripts in `scripts/ingest/`
3. Update vector store configuration if needed

## 🔧 Configuration

### Agent Configuration (`config/agents.yaml`)
Configure AI agent behaviors, roles, and capabilities:
```yaml
emotion_detector:
  role: Emotion Detector
  goal: Analyze user input to determine their emotional state
  backstory: You are an empathetic AI skilled at identifying emotions
```

### RAG Configuration (`config/rag.yaml`)
Configure retrieval-augmented generation settings:
```yaml
vector_store:
  collection_name: mental_health_docs
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
```

### Task Configuration (`config/tasks.yaml`)
Define task flows and dependencies for the multi-agent system.

## 🗃️ Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: User email address
- `password_hash`: Encrypted password
- `created_at`: Account creation timestamp

### User Assessments
- Links users to completed assessments
- Stores scores and timestamps
- Tracks assessment types and results

### Conversation History
- Stores chat messages and responses
- Links to user sessions
- Includes sentiment analysis results

## 🤖 AI Agents Overview

### Crisis Detection Agent
- **Purpose**: Identifies mental health emergencies
- **Tools**: Crisis classification algorithms
- **Response**: Immediate escalation and resource provision

### Mental Condition Classifier
- **Purpose**: Categorizes user concerns
- **Tools**: NLP classification models
- **Output**: Condition type and confidence score

### RAG Retriever Agent
- **Purpose**: Finds relevant knowledge base content
- **Tools**: Vector similarity search
- **Output**: Relevant document excerpts

### Assessment Conductor
- **Purpose**: Administers standardized questionnaires
- **Tools**: Questionnaire management system
- **Output**: Assessment scores and interpretations

### Response Generator
- **Purpose**: Creates empathetic, helpful responses
- **Tools**: Language models and response templates
- **Output**: Contextual, supportive messages

## 🔒 Security and Privacy

### Data Protection
- Passwords are hashed using secure algorithms
- Session management with secure cookies
- Option for anonymous guest sessions
- User data deletion capabilities

### Privacy Features
- No persistent storage for guest users
- Secure session management
- Optional account deletion
- Data minimization practices

## 📊 Monitoring and Analytics

### Sentiment Tracking
- Real-time emotion analysis
- Conversation sentiment trends
- User mood tracking over time

### Assessment Analytics
- Score tracking and trends
- Risk factor identification
- Progress monitoring

### System Monitoring
- Agent performance metrics
- Response time tracking
- Error logging and monitoring

## 🐳 Docker Deployment

Build and run using Docker:

```bash
# Build the image
docker build -t mental-health-app .

# Run the container
docker run -p 5000:5000 -p 8000:8000 mental-health-app
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility (>=3.11)

#### 2. Database Issues
- Initialize database: `python -c "from main import init_db; init_db()"`
- Check file permissions for SQLite database

#### 3. API Key Errors
- Verify `.env` file configuration
- Ensure API keys are valid and active

#### 4. Voice Features Not Working
- Check microphone permissions in browser
- Verify Whisper model installation
- Ensure audio file formats are supported

#### 5. Agent Response Issues
- Check FastAPI backend is running on port 8000
- Verify agent configurations in `config/` directory
- Review logs for specific error messages

### Debug Mode
Enable debug mode for detailed error information:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Follow the existing code style
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for complex functions
- Include error handling and logging

### Testing
- Run existing tests before submitting changes
- Add tests for new features
- Ensure all agents work correctly in isolation

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support and Resources

### Mental Health Resources
- **Crisis Hotlines**: Immediate help for mental health emergencies
- **Professional Services**: Information about therapy and counseling
- **Self-Help Resources**: Coping strategies and wellness tips

### Technical Support
- Check the troubleshooting section above
- Review system logs for detailed error information
- Consult the API documentation at `/docs` endpoint

### Community
- Report bugs and request features through GitHub issues
- Contribute to the project following the contribution guidelines
- Share feedback and suggestions for improvement

---

**Disclaimer**: This application is designed to provide mental health support and information but is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified healthcare providers for mental health concerns.
