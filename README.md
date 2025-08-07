# Mental Health Chatbot - Bhutan

A comprehensive mental health support application built with Flask frontend and FastAPI backend, optimized for cloud deployment.

## 🚀 Architecture

### **Flask + FastAPI Design**
```
┌─────────────────────┐    ┌─────────────────────┐
│   Flask Frontend    │    │   FastAPI Backend   │
│   (Port 5001)       │◄──►│   (Port 8001)       │
│   main.py           │    │   fastapi_app.py    │
│                     │    │                     │
│ • Web Templates     │    │ • AI Processing     │
│ • User Sessions     │    │ • Chat API          │
│ • Form Handling     │    │ • Assessment Engine │
│ • Static Assets     │    │ • CrewAI Agents     │
└─────────────────────┘    └─────────────────────┘
         │                          │
         └──────────┬─────────────────┘
                    │
       ┌─────────────────────┐
       │   SQLite Database   │
       │                     │
       │ • User Management   │
       │ • Chat Sessions     │
       │ • Assessment Data   │
       │ • Vector Store      │
       └─────────────────────┘
```

### **Deployment Options**

#### 🔧 Local Development (Full Features)
- Flask frontend with rich UI templates
- FastAPI backend with full AI stack
- CrewAI agents and RAG system
- Complete assessment tools
- All features enabled

#### ☁️ Render Cloud (512MB RAM Optimized)
- Memory-optimized Flask app (`app_render.py`)
- Lightweight dependencies only
- Basic sentiment analysis with TextBlob
- Keyword-based responses
- Health monitoring included

## 🌟 Core Features

### Frontend (Flask)
- **Web Interface**: Modern HTML templates with responsive design
- **User Authentication**: Session-based login and registration
- **Interactive Forms**: Mental health assessments and questionnaires
- **Real-time Chat**: AJAX-powered messaging interface
- **Dashboard**: User profile and assessment history
- **Static Assets**: Optimized CSS, JavaScript, and images

### Backend (FastAPI)
- **AI-Powered Chatbot**: Multi-agent system using CrewAI for intelligent conversations
- **RAG System**: Knowledge base integration for evidence-based responses
- **Chat API**: RESTful endpoints for real-time messaging
- **Assessment Engine**: Automated scoring of mental health questionnaires
- **Sentiment Analysis**: Real-time emotion detection and tracking
- **Crisis Detection**: Automatic identification of mental health emergencies

### Core Capabilities
- **Mental Health Assessments**: Standardized questionnaires (PHQ-9, GAD-7, DAST-10, AUDIT, Bipolar)
- **Session Management**: Secure guest and user sessions with chat history
- **PDF Report Generation**: Downloadable assessment reports
- **Multi-Agent Architecture**: Specialized agents for different aspects of mental health support
- **Database Integration**: SQLite with SQLAlchemy for data persistence

## 🏗️ Detailed Architecture

### Flask Frontend (`main.py`)
- **Route Handlers**: Home, chat, assessment, user dashboard pages
- **Template Engine**: Jinja2 for dynamic HTML rendering
- **Session Management**: Flask sessions for user state
- **Form Processing**: WTForms for validation and CSRF protection
- **Static File Serving**: CSS, JavaScript, images
- **API Integration**: HTTP requests to FastAPI backend

### FastAPI Backend (`fastapi_app.py`)
- **Chat Endpoints**: POST `/api/chat` for message processing
- **Assessment API**: POST `/api/assessment` for questionnaire scoring
- **User Management**: Registration, login, profile endpoints
- **AI Processing**: CrewAI agents for intelligent responses
- **Database Operations**: SQLAlchemy models and queries
- **Background Tasks**: Async processing for heavy operations

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
- **File Storage**: PDF reports and uploaded assets

## 🚀 Local Development Setup

### Prerequisites
- Python 3.11+
- Git
- Required API keys (Google, OpenAI, Groq)

### Installation

1. **Clone Repository**
   ```bash
   git clone <your-repository>
   cd bhutan
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**
   ```bash
   # Create .env file
   GOOGLE_API_KEY=your_google_api_key
   GROQ_API_KEY=your_groq_api_key
   OPENAI_API_KEY=your_openai_api_key
   SECRET_KEY=your_secret_key
   FLASK_SECRET_KEY=your_flask_secret_key
   DATABASE_URL=sqlite:///mental_health.db
   ```

5. **Initialize Database**
   ```bash
   python -c "from main import init_db; init_db()"
   ```

### Running the Application

#### Start FastAPI Backend (Port 8001)
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8001 --reload
```

#### Start Flask Frontend (Port 5001)
```bash
python main.py
```

#### Access the Application
- **Frontend**: http://localhost:5001
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Development Workflow

1. **Frontend Development**: Edit templates in `templates/`, static files in `static/`
2. **Backend Development**: Modify `fastapi_app.py` for API endpoints
3. **AI Agents**: Update `crew_ai/` directory for agent logic
4. **Database**: Modify models in `models/` directory
5. **Testing**: Run tests with `pytest`

## 🛠️ File Structure

```
bhutan/
├── main.py                    # Flask frontend application
├── fastapi_app.py            # FastAPI backend application
├── requirements.txt          # Full development dependencies
├── requirements_render.txt   # Lightweight production dependencies
├── app_render.py            # Render-optimized single-file app
├── Dockerfile               # Production Docker configuration
├── .env                     # Environment variables (create this)
├── models/                  # Database models
│   ├── __init__.py
│   ├── user.py
│   └── chat_session.py
├── crew_ai/                 # AI agents system
│   ├── __init__.py
│   ├── chatbot.py
│   ├── tools.py
│   └── config.py
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html
│   ├── ChatbotUI.html
│   ├── assessment.html
│   └── user_dashboard.html
├── static/                  # CSS, JavaScript, images
│   ├── stylehome.css
│   ├── styleChatBotUI.css
│   └── mental-health_12560579.png
├── config/                  # Configuration files
│   ├── agents.yaml
│   ├── rag.yaml
│   └── tasks.yaml
├── knowledge/               # RAG knowledge base
├── data/                    # Application data
├── logs/                    # Application logs
└── chat_sessions/          # Session storage
```

## 🎉 DEPLOYMENT SUCCESS!

**✅ Your Bhutan Mental Health Chatbot is LIVE on Render!**

**Live URL**: `https://bhutan-mental-health-chatbot.onrender.com`

### 🚀 What's Working
- ✅ Docker build completed successfully
- ✅ Flask app running on port 10000
- ✅ Health checks passing
- ✅ Memory usage optimized for 512MB
- ✅ All endpoints functional

### 🔧 Recent Production Optimization
- **Added Gunicorn**: Production WSGI server for better performance
- **Memory tuned**: 1 worker + 2 threads for 512MB RAM
- **Timeout configured**: 120s for processing requests

---

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

## 🚀 Production Deployment (Render Cloud)

The application is pre-configured for production deployment on Render with 512MB RAM optimization.

### Quick Deploy to Render

#### 1. Prerequisites
- GitHub/GitLab repository with this code
- Render account (free tier available)

#### 2. Automatic Setup
```bash
# Run the deployment preparation script
python deploy_render.py

# Optional: Test Docker build locally
python validate_docker.py
```

#### 3. Deploy to Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure:
   - **Environment**: Docker
   - **Branch**: main
   - **Dockerfile**: ./Dockerfile

#### 4. Environment Variables
```env
PORT=10000                    # Auto-set by Render
FLASK_ENV=production
SECRET_KEY=your-secret-key    # Generate secure key
```

### Production Architecture

#### Memory-Optimized Stack
```
Render Production (512MB RAM):
├── app_render.py (Flask only)
├── requirements_render.txt (26 lightweight packages)
├── SQLite database (no external DB needed)
├── TextBlob sentiment analysis
├── Keyword-based responses
└── Health monitoring
```

#### Features in Production
- ✅ Mental health chatbot with keyword responses
- ✅ Basic sentiment analysis
- ✅ Crisis resource information
- ✅ Simple mental health assessment
- ✅ Chat session logging
- ✅ Health monitoring
- ✅ Responsive web interface
- ✅ Auto-scaling and high availability

### Development vs Production

| Feature | Development (Local) | Production (Render) |
|---------|-------------------|-------------------|
| **Frontend** | Flask with full templates | Flask with embedded HTML |
| **Backend** | FastAPI + CrewAI agents | Lightweight Flask only |
| **AI/ML** | Advanced LLMs + RAG | TextBlob sentiment |
| **Dependencies** | 50+ packages | 26 essential packages |
| **Memory Usage** | 1-2GB | 200-300MB |
| **Database** | SQLite with full schema | SQLite with basic tables |
| **Responses** | AI-generated | Keyword-based patterns |

### Monitoring and Maintenance

#### Health Checks
- **Endpoint**: `https://your-app.onrender.com/health`
- **Status**: Service health and memory usage
- **Monitoring**: Automatic uptime monitoring

#### Logs and Debugging
- **Access logs**: Via Render dashboard
- **Application logs**: Real-time in Render interface
- **Error tracking**: Built-in error logging
- **Performance**: Memory and CPU usage metrics

#### Scaling and Updates
- **Auto-deployment**: Pushes to main branch auto-deploy
- **Zero-downtime**: Rolling updates with health checks
- **Backup**: Database is automatically backed up
- **Rollback**: Easy rollback to previous versions

### 🔧 Customization

#### Adding Features to Production
To add features to the production version:

1. **Edit `app_render.py`** for new routes/functionality
2. **Update `requirements_render.txt`** if new packages needed
3. **Test memory usage** with `validate_docker.py`
4. **Deploy** by pushing to main branch

#### Memory Optimization Tips
- Use lightweight alternatives to heavy packages
- Implement caching for repeated operations
- Optimize database queries
- Use streaming responses for large data
- Monitor memory usage regularly

### 🆘 Troubleshooting

#### Common Issues
1. **Build failures**: Check requirements_render.txt for package conflicts
2. **Memory errors**: Monitor usage, optimize code, or upgrade plan
3. **Database issues**: Check SQLite file permissions and disk space
4. **Health check failures**: Verify /health endpoint responds correctly

#### Performance Tuning
- **Database optimization**: Use indexes, limit query size
- **Response caching**: Cache frequent responses
- **Static assets**: Optimize CSS/JS file sizes
- **Connection pooling**: Reuse database connections

## 🧪 Testing

### Local Testing
```bash
# Test Flask frontend
python main.py
# Access: http://localhost:5001

# Test FastAPI backend  
uvicorn fastapi_app:app --port 8001
# Access: http://localhost:8001/docs

# Test production build
docker build -t test-app .
docker run -p 10000:10000 test-app
```

### Automated Testing
```bash
# Run test suite
pytest tests/

# Test API endpoints
python test_api.py

# Validate deployment
python validate_docker.py
```

## 📊 Configuration

### Agent Configuration (`config/agents.yaml`)
```yaml
crisis_detector:
  role: Crisis Detection Specialist
  goal: Identify mental health emergencies
  backstory: Trained to recognize crisis situations

response_generator:
  role: Mental Health Assistant
  goal: Provide supportive responses
  backstory: Empathetic AI assistant
```

### RAG Configuration (`config/rag.yaml`)
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
