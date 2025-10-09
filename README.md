# WellnessWeavers 🌟

A comprehensive AI-powered mental health support platform built with Python Flask, featuring advanced analytics, crisis detection, and community support.

## 🚀 Features

### Core Features
- **🤖 AI Chat Companion** - 24/7 mental health support with Google Cloud AI
- **📊 Mood Tracking** - Advanced mood logging with pattern recognition
- **📈 Analytics Dashboard** - Comprehensive wellness insights and trends
- **👥 Community Support** - Support groups and peer connections
- **🏆 Gamification** - Achievement system with points and levels
- **🚨 Crisis Detection** - Real-time crisis intervention system
- **📱 Mobile Responsive** - Works perfectly on all devices

### Advanced Features
- **🎯 Personalized Insights** - AI-generated wellness recommendations
- **📧 Smart Notifications** - Email and SMS reminders
- **🔍 Pattern Recognition** - Identify mood triggers and trends
- **🛡️ Safety Features** - Emergency contacts and crisis intervention
- **📊 Data Analytics** - Advanced mood and wellness analytics
- **🌍 Multi-language Support** - International accessibility

## 🛠️ Technology Stack

### Backend
- **Flask 3.1.2** - Web framework
- **SQLAlchemy 2.0** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **Celery** - Background tasks

### AI & ML
- **Google Cloud AI** - Natural language processing
- **OpenAI API** - Backup AI services
- **NLTK** - Text analysis
- **scikit-learn** - Machine learning

### Frontend
- **Bootstrap 5** - Responsive UI framework
- **Chart.js** - Data visualization
- **Font Awesome** - Icon library
- **JavaScript ES6** - Interactive features

### Services
- **Twilio** - SMS notifications
- **SendGrid** - Email services
- **Google Cloud Storage** - File storage
- **Sentry** - Error monitoring

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 16+ (for frontend assets)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/WellnessWeavers.git
cd WellnessWeavers
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python manage.py init-db
python manage.py seed-db
```

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` to see the application!

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/wellnessweavers

# Google Cloud AI
GOOGLE_CLOUD_API_KEY=your_api_key
GOOGLE_CLOUD_PROJECT_ID=your_project_id

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# SMS
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_PHONE=+1234567890

# Security
SECRET_KEY=your_secret_key
API_KEY=your_api_key
```

## 📊 API Documentation

### Authentication
```bash
# Get API key
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### Mood Tracking
```bash
# Log mood
curl -X POST http://localhost:5000/api/moods \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mood_score": 8, "mood_label": "great", "notes": "Feeling good today!"}'
```

### AI Chat
```bash
# Send message to AI
curl -X POST http://localhost:5000/api/chat/message \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am feeling anxious today"}'
```

## 🎯 Management CLI

### Database Operations
```bash
# Initialize database
python manage.py init-db

# Reset database (WARNING: Deletes all data!)
python manage.py reset-db

# Seed with sample data
python manage.py seed-db
```

### User Management
```bash
# Create new user
python manage.py create-user

# Check user data
python manage.py check-user-data --user-id 1

# Process user insights
python manage.py process-insights --all
```

### System Maintenance
```bash
# Clean up old data
python manage.py cleanup-old-data

# Test crisis detection
python manage.py test-crisis-detection --text "I want to hurt myself"

# Send test notifications
python manage.py send-test-notifications
```

## 🏗️ Architecture

### Project Structure
```
WellnessWeavers/
├── app.py                 # Main Flask application
├── manage.py             # CLI management tool
├── config.py             # Configuration settings
├── database.py           # Database initialization
├── requirements.txt      # Python dependencies
├── models/               # Database models
│   ├── user.py
│   ├── mood.py
│   ├── conversation.py
│   └── ...
├── routes/               # API routes
│   ├── auth.py
│   ├── dashboard.py
│   ├── community.py
│   └── api.py
├── services/             # Business logic
│   ├── ai_service.py
│   ├── crisis_detection.py
│   └── notification_service.py
├── utils/                # Utilities
│   ├── data_processor.py
│   └── background_tasks.py
├── templates/            # HTML templates
├── static/              # Static assets
└── tests/               # Test files
```

### Database Schema
- **Users** - User accounts and profiles
- **Moods** - Mood tracking entries
- **Conversations** - AI chat interactions
- **Achievements** - Gamification system
- **Support Groups** - Community features
- **Crisis Alerts** - Safety monitoring

## 🔒 Security Features

### Crisis Detection
- Real-time text analysis for crisis indicators
- Automatic intervention triggers
- Emergency contact notifications
- Safety plan integration

### Data Protection
- Encrypted sensitive data
- GDPR compliance
- Secure API endpoints
- Rate limiting

### Privacy
- Anonymous posting options
- Data export capabilities
- Account deletion
- Privacy controls

## 📈 Analytics & Insights

### Mood Analytics
- Trend analysis
- Pattern recognition
- Trigger identification
- Wellness scoring

### AI Insights
- Personalized recommendations
- Behavioral analysis
- Progress tracking
- Goal setting

## 🚀 Deployment

### Production Setup
```bash
# Install production dependencies
pip install -r requirements.txt

# Set up production database
python manage.py init-db

# Configure environment variables
export FLASK_ENV=production

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```bash
# Build Docker image
docker build -t wellnessweavers .

# Run container
docker run -p 5000:5000 wellnessweavers
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py
```

### Test Coverage
- Unit tests for all models
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Crisis detection testing

## 📚 Documentation

### API Documentation
- Complete API reference
- Authentication guide
- Rate limiting
- Error handling

### User Guide
- Getting started
- Feature walkthrough
- Troubleshooting
- FAQ

### Developer Guide
- Code structure
- Contributing guidelines
- Testing procedures
- Deployment guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.wellnessweavers.com](https://docs.wellnessweavers.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/WellnessWeavers/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/WellnessWeavers/discussions)
- **Email**: support@wellnessweavers.com

## 🙏 Acknowledgments

- Google Cloud AI for natural language processing
- Bootstrap for responsive design
- Chart.js for data visualization
- The mental health community for inspiration

---

**WellnessWeavers** - Empowering mental health through technology 🌟