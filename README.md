# Mental Health Chatbot Application

A comprehensive multi-agent mental health support application that combines AI-powered conversational assistance with assessment tools, sentiment analysis, and user management features. **Now optimized for Hugging Face Spaces deployment.**

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
