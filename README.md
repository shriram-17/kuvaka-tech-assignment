# Gemini Backend Clone - Kuvaka Tech Assignment

A FastAPI-based chat application with AI-powered responses, subscription management, and real-time messaging capabilities.

## 🚀 Features

- **OTP-based Authentication** - Secure mobile number verification with JWT tokens
- **AI-Powered Chat** - Google Gemini AI integration for intelligent responses  
- **Subscription System** - Stripe-powered Basic/Pro tier management
- **Real-time Processing** - Celery + Redis queue for async AI responses
- **Rate Limiting** - Basic tier: 5 messages/day, Pro tier: Unlimited
- **Caching** - Redis-based chatroom caching for performance
- **RESTful API** - Clean, documented endpoints with Swagger UI

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Queue System](#queue-system)
- [Gemini AI Integration](#gemini-ai-integration)
- [Testing with Postman](#testing-with-postman)
- [Deployment](#deployment)
- [Design Decisions](#design-decisions)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Database      │
│   (Client)      │◄──►│   Backend       │◄──►│   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Stripe        │    │   Redis         │    │   Celery        │
│   Payments      │    │   Cache/Queue   │    │   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Gemini AI     │
                       │   API           │
                       └─────────────────┘
```

### Core Components

1. **FastAPI Application** (`app.py`) - Main application with router registration
2. **Authentication System** (`auth.py`) - OTP + JWT token-based auth
3. **Chatroom Management** (`chatroom.py`) - CRUD operations for chats and messages
4. **Subscription System** (`subscription.py`) - Stripe integration for Pro upgrades
5. **Background Processing** - Celery workers for async AI responses
6. **Caching Layer** - Redis for chatroom list optimization

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and message queue
- **Celery** - Asynchronous task processing
- **Pydantic** - Data validation and serialization

### External Services
- **Google Gemini AI** - Conversational AI responses
- **Stripe** - Payment processing and subscriptions
- **Redis Cloud** - Managed Redis instance

### Authentication & Security
- **JWT Tokens** - Stateless authentication
- **OTP Verification** - SMS-based user verification
- **bcrypt** - Password hashing
- **CORS** - Cross-origin resource sharing

## 🔧 Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Redis instance
- Stripe account
- Google Gemini API key

### 1. Clone Repository
```bash
git clone <repository-url>
cd kuvaka-tech-assignment
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Create PostgreSQL database
createdb chatapp

# Run migrations (if using Alembic)
alembic upgrade head
```

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# Core Application
SECRET_KEY=your_super_secret_key_here_replace_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatapp

# Redis Configuration
REDIS_HOST=redis-12758.c240.us-east-1-3.ec2.redns.redis-cloud.com
REDIS_PORT=12758
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Frontend URL (for redirects)
FRONTEND_URL=http://localhost:3000
```

### Required API Keys

1. **Gemini API Key**: Get from [Google AI Studio](https://aistudio.google.com)
2. **Stripe Keys**: Get from [Stripe Dashboard](https://dashboard.stripe.com)
3. **Redis**: Use Redis Cloud free tier or local Redis

## 🚀 Running the Application

### 1. Start the FastAPI Server
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Celery Worker
```bash
# For Windows (using solo pool)
celery -A src.celery_app worker --loglevel=info --pool=solo

# For macOS/Linux
celery -A src.celery_app worker --loglevel=info
```

### 3. Access the Application
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## 📖 API Documentation

### Authentication Flow
```
1. POST /auth/signup - Register with mobile number
2. POST /auth/send-otp - Generate OTP for mobile
3. POST /auth/verify-otp - Verify OTP and get JWT token
4. Use Bearer token in Authorization header for protected endpoints
```

### Core Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/signup` | Register new user | ❌ |
| POST | `/auth/send-otp` | Send OTP to mobile | ❌ |
| POST | `/auth/verify-otp` | Verify OTP & get token | ❌ |
| GET | `/user/me` | Get current user info | ✅ |
| GET | `/chatroom` | List user chatrooms | ✅ |
| POST | `/chatroom` | Create new chatroom | ✅ |
| POST | `/chatroom/{id}/message` | Send message (triggers AI) | ✅ |
| GET | `/chatroom/{id}/messages` | Get chat history | ✅ |
| DELETE | `/chatroom/{id}` | Delete chatroom | ✅ |
| POST | `/subscribe/pro` | Create Pro subscription | ✅ |
| GET | `/subscribe/status` | Get subscription status | ✅ |
| POST | `/subscribe/webhook` | Stripe webhook handler | ❌ |

## 🔄 Queue System Explanation

### Architecture
The application uses **Celery + Redis** for asynchronous processing of AI responses:

```
User Message → FastAPI → Celery Task → Gemini AI → Database
     ↓              ↓         ↓           ↓          ↓
   Saved to DB   Returns 202  Queued     Processes  Saves AI Response
```

### Why Async Processing?
1. **User Experience**: Immediate response (202 Accepted) while AI processes in background
2. **Scalability**: Handle multiple concurrent AI requests
3. **Reliability**: Queue persistence ensures no message loss
4. **Rate Limiting**: Proper handling of API quotas

### Task Flow
```python
# 1. User sends message
POST /chatroom/1/message
{
  "content": "Hello, how are you?"
}

# 2. FastAPI saves user message and enqueues task
process_gemini_message.delay(
    message_content="Hello, how are you?",
    chatroom_id=1,
    user_id=123
)

# 3. Returns immediately
{
  "id": 456,
  "content": "Hello, how are you?",
  "is_from_user": true,
  "created_at": "2025-09-14T16:30:00"
}

# 4. Celery worker processes in background
# 5. AI response saved to database
# 6. Client polls /chatroom/1/messages to see AI response
```

## 🤖 Gemini AI Integration

### Configuration
```python
import google.generativeai as genai
genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content(user_message)
```

### Model Choice: Gemini 2.5 Flash
- **Fast Response Time**: Optimized for quick conversations
- **Cost Effective**: Efficient token usage
- **High Quality**: Advanced reasoning capabilities
- **Free Tier**: Generous usage limits for development

### Error Handling
- **API Failures**: Graceful fallback with user-friendly messages
- **Rate Limiting**: Automatic retry with exponential backoff
- **Timeout Handling**: 5-minute task timeout for long responses

## 🧪 Testing with Postman

### Setup Postman Collection

1. **Import Environment Variables**:
```json
{
  "base_url": "http://localhost:8000",
  "access_token": ""
}
```

### Test Sequence

#### 1. User Registration & Authentication
```bash
# Register user
POST {{base_url}}/auth/signup
Content-Type: application/json

{
  "mobile_number": "+1234567890"
}

# Send OTP
POST {{base_url}}/auth/send-otp
Content-Type: application/json

{
  "mobile_number": "+1234567890"
}

# Verify OTP (use OTP from response)
POST {{base_url}}/auth/verify-otp
Content-Type: application/json

{
  "mobile_number": "+1234567890",
  "otp": "123456"
}

# Save access_token from response for subsequent requests
```

#### 2. Chatroom Operations
```bash
# Create chatroom
POST {{base_url}}/chatroom
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "name": "My First Chat"
}

# Send message (triggers AI)
POST {{base_url}}/chatroom/1/message
Authorization: Bearer {{access_token}}
Content-Type: application/json

{
  "content": "Hello, tell me a joke!"
}

# Get messages (check for AI response)
GET {{base_url}}/chatroom/1/messages
Authorization: Bearer {{access_token}}
```

#### 3. Subscription Testing
```bash
# Check current subscription
GET {{base_url}}/subscribe/status
Authorization: Bearer {{access_token}}

# Create Pro subscription
POST {{base_url}}/subscribe/pro
Authorization: Bearer {{access_token}}
```

### Expected Rate Limiting Behavior
- **Basic Users**: 5 messages/day → 429 error after limit
- **Pro Users**: Unlimited messages
- **Daily Reset**: Counter resets at UTC midnight

## 🚀 Deployment

### Production Environment Variables
```env
# Production Database
DATABASE_URL=postgresql://user:password@prod-host:5432/chatapp

# Production Redis
REDIS_HOST=your-production-redis.com
REDIS_PASSWORD=production_redis_password

# Production Secrets
SECRET_KEY=super_long_random_production_key
STRIPE_SECRET_KEY=sk_live_your_live_stripe_key
GEMINI_API_KEY=your_production_gemini_key
FRONTEND_URL=https://your-frontend-domain.com
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Deployment Platforms
- **Recommended**: Railway, Render, or Digital Ocean App Platform
- **Advanced**: AWS ECS, Google Cloud Run, or Azure Container Instances

### Production Checklist
- ✅ Set `DEBUG=False`
- ✅ Use production database (PostgreSQL)
- ✅ Configure production Redis
- ✅ Set strong `SECRET_KEY`
- ✅ Enable HTTPS
- ✅ Configure CORS properly
- ✅ Set up monitoring and logging
- ✅ Configure Stripe webhooks with production URL

## 💡 Design Decisions & Assumptions

### Authentication Strategy
- **Mobile-based**: Chosen over email for broader accessibility
- **OTP Verification**: More secure than password-only systems
- **JWT Tokens**: Stateless, scalable authentication
- **No Password Required**: Simplified onboarding flow

### Database Design
```sql
-- Users: Core user information with subscription tracking
users (id, mobile_number, subscription_tier, daily_message_count)

-- Chatrooms: User-owned conversation spaces  
chatrooms (id, name, user_id, created_at)

-- Messages: Both user and AI messages in same table
messages (id, content, is_from_user, chatroom_id, user_id, created_at)
```

### Rate Limiting Implementation
- **Database-based**: Daily counter stored in user record
- **Tier-based**: Basic (5/day) vs Pro (unlimited)
- **UTC Reset**: Simple daily reset logic
- **Pre-increment**: Check limit before processing

### Caching Strategy
- **Chatroom Lists**: 5-minute TTL, high read frequency
- **Cache Invalidation**: On create/delete operations
- **Redis Storage**: Persistent, shared across workers
- **JSON Serialization**: Handle datetime objects properly

### Error Handling Philosophy
- **User-friendly Messages**: Hide technical details
- **Comprehensive Logging**: Full error context for debugging
- **Graceful Degradation**: Continue operation when possible
- **Background Task Resilience**: Don't crash on external API failures

### Scalability Considerations
- **Async Processing**: Non-blocking AI requests
- **Horizontal Scaling**: Stateless design supports multiple instances  
- **Queue-based**: Distribute load across workers
- **Database Optimization**: Proper indexes and relationships

## 📝 API Testing Examples

### Complete User Journey
```python
# 1. Registration
response = requests.post("http://localhost:8000/auth/signup", json={
    "mobile_number": "+1234567890"
})
# Response: 201 Created

# 2. OTP Generation  
response = requests.post("http://localhost:8000/auth/send-otp", json={
    "mobile_number": "+1234567890"
})
otp = response.json()["otp"]  # In real app, sent via SMS

# 3. Authentication
response = requests.post("http://localhost:8000/auth/verify-otp", json={
    "mobile_number": "+1234567890",
    "otp": otp
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 4. Create Chat
response = requests.post("http://localhost:8000/chatroom", 
    json={"name": "AI Assistant"}, headers=headers)
chatroom_id = response.json()["id"]

# 5. Send Message
response = requests.post(f"http://localhost:8000/chatroom/{chatroom_id}/message",
    json={"content": "Explain quantum computing"}, headers=headers)
# Response: 202 Accepted (processing in background)

# 6. Check Messages (after a few seconds)
response = requests.get(f"http://localhost:8000/chatroom/{chatroom_id}/messages", 
    headers=headers)
messages = response.json()
# Should contain both user message and AI response
```

## 🔍 Troubleshooting

### Common Issues

1. **Celery Tasks Not Processing**
   ```bash
   # Check Redis connection
   redis-cli -h your-redis-host -p 12758 -a your-password ping
   
   # Verify worker is running
   celery -A src.celery_app inspect active
   ```

2. **Gemini API Errors**
   ```bash
   # Verify API key
   export GEMINI_API_KEY=your_key
   python -c "import google.generativeai as genai; genai.configure(api_key='$GEMINI_API_KEY'); print('OK')"
   ```

3. **Database Connection Issues**
   ```bash
   # Test database URL
   python -c "from sqlalchemy import create_engine; engine = create_engine('your_db_url'); print(engine.execute('SELECT 1').scalar())"
   ```

### Logs to Monitor
- FastAPI application logs: Request/response cycle
- Celery worker logs: Background task processing
- Redis logs: Queue and cache operations
- Database logs: Query performance and errors

## 📞 Support & Development

### Project Structure
```
├── src/
│   ├── api/v1/          # API route handlers
│   ├── core/            # Configuration and security
│   ├── database/        # Database connection and base
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   └── utils/           # Utility functions
├── app.py               # FastAPI application
├── celery_worker.py     # Celery worker entry point
├── requirements.txt     # Python dependencies
└── .env                 # Environment configuration
```

### Development Workflow
1. Make changes to code
2. Test locally with uvicorn auto-reload
3. Verify Celery tasks work correctly
4. Test with Postman collection
5. Deploy to staging environment
6. Run integration tests
7. Deploy to production

***

## 🎯 Next Steps for Enhancement

1. **Real-time Features**: WebSocket support for live message updates
2. **Advanced AI**: Conversation context and memory
3. **File Uploads**: Image and document processing
4. **Analytics**: Usage tracking and insights
5. **Mobile App**: Native iOS/Android clients
6. **Multi-language**: i18n support
7. **Admin Panel**: User and subscription management

Built with ❤️ for Kuvaka Tech Assignment
