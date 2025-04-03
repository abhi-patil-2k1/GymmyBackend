# GymBuddy API Backend

GymBuddy API Backend is a comprehensive RESTful API built with FastAPI to support the GymBuddy fitness social platform. This backend provides all necessary endpoints for user management, social interactions, trainer marketplace, gym administration, messaging, and more.

## Features

- **Firebase Authentication Integration**:
  - Secure user authentication
  - Role-based access control (users, trainers, gym admins)
  - Token verification middleware

- **User Management**:
  - User profiles and preferences
  - Connection management
  - Activity tracking

- **Trainer Marketplace**:
  - Trainer profiles and specialities
  - Booking and schedule management
  - Rating and review system

- **Gym Administration**:
  - Gym profiles and facility management
  - Member and trainer management
  - Analytics and statistics

- **Social Features**:
  - Social feed with posts, comments, and likes
  - Activity sharing
  - Milestone tracking

- **Messaging**:
  - Real-time chat (with Firebase)
  - Conversation management
  - Read receipts

- **Milestone System**:
  - Achievement tracking
  - Progress monitoring
  - Gamification elements

## Technical Stack

- **Framework**: FastAPI
- **Authentication**: Firebase Authentication
- **Database**: Firebase Firestore
- **Storage**: Firebase Cloud Storage
- **Deployment**: Docker/Kubernetes compatible

## Project Structure

The project follows a clean, maintainable structure:

```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── config/                 # Configuration
├── core/                   # Core functionality (auth, security)
├── db/                     # Database clients
├── api/                    # API routes
│   └── routes/             # Endpoint routers
├── models/                 # Data models
├── schemas/                # Pydantic schemas
├── services/               # Business logic
└── utils/                  # Utilities
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Firebase project with Firestore and Authentication enabled
- Firebase Admin SDK credentials

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/gymbuddy-api.git
   cd gymbuddy-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Firebase credentials:
   
   Create a `.env` file in the project root with the following content:
   ```
   FIREBASE_SERVICE_ACCOUNT_PATH=path/to/firebase-credentials.json
   FIREBASE_STORAGE_BUCKET=your-firebase-bucket.appspot.com
   ```

   Or set environment variables directly.

5. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API documentation at http://localhost:8000/docs

## API Documentation

The API provides comprehensive endpoints for all application features:

### Authentication

- POST `/api/v1/auth/verify-token` - Verify Firebase ID token
- POST `/api/v1/auth/register/user` - Register user
- POST `/api/v1/auth/register/trainer` - Register trainer
- POST `/api/v1/auth/register/gym-admin` - Register gym admin
- POST `/api/v1/auth/logout` - Logout

### Users

- GET `/api/v1/users/me` - Get current user profile
- PUT `/api/v1/users/me` - Update user profile
- GET `/api/v1/users/active` - Get active users
- GET `/api/v1/users/{user_id}` - Get user profile
- GET `/api/v1/users` - List users with filtering

### Trainers

- GET `/api/v1/trainers/me` - Get current trainer profile
- PUT `/api/v1/trainers/me` - Update trainer profile
- GET `/api/v1/trainers/me/availability` - Get trainer availability
- POST `/api/v1/trainers/me/availability` - Add availability slot
- GET `/api/v1/trainers/{trainer_id}` - Get trainer profile
- GET `/api/v1/trainers` - List trainers with filtering

### Gyms

- GET `/api/v1/gyms/me` - Get current gym admin profile
- PUT `/api/v1/gyms/me` - Update gym profile
- GET `/api/v1/gyms/me/members` - Get gym members
- GET `/api/v1/gyms/me/trainers` - Get gym trainers
- GET `/api/v1/gyms/{gym_id}` - Get gym profile
- GET `/api/v1/gyms` - List gyms with filtering

### Social

- GET `/api/v1/social/feed` - Get social feed
- POST `/api/v1/social/posts` - Create post
- GET `/api/v1/social/posts/{post_id}` - Get post
- POST `/api/v1/social/posts/{post_id}/like` - Like post
- POST `/api/v1/social/posts/{post_id}/comments` - Comment on post

### Connections

- GET `/api/v1/connections` - Get user connections
- POST `/api/v1/connections/{user_id}` - Send connection request
- PUT `/api/v1/connections/{connection_id}` - Accept/reject request
- DELETE `/api/v1/connections/{connection_id}` - Remove connection

### Chat

- GET `/api/v1/chat/conversations` - Get conversations
- POST `/api/v1/chat/conversations` - Create conversation
- GET `/api/v1/chat/conversations/{conversation_id}/messages` - Get messages
- POST `/api/v1/chat/messages` - Send message

### Milestones

- GET `/api/v1/milestones` - Get user milestones
- GET `/api/v1/milestones/{milestone_id}` - Get milestone details
- POST `/api/v1/milestones/{milestone_id}/progress` - Update milestone progress

## Development

### Coding Standards

- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Include docstrings for all modules, classes, and functions

### Testing

Run tests with pytest:
```bash
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Deployment

### Docker

Build and run with Docker:
```bash
docker build -t gymbuddy-api .
docker run -p 8000:8000 -e FIREBASE_SERVICE_ACCOUNT_JSON='...' gymbuddy-api
```

### Kubernetes

Kubernetes deployment files are available in the `k8s/` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.