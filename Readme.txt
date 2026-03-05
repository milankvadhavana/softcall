Act as a senior full-stack developer.

I want to build a production-ready voice calling mobile application using:

Frontend:
- Ionic Framework (Angular)
- TypeScript
- WebRTC for voice communication
- Socket.io or WebSocket for signaling

Backend:
- Python Django
- Django REST Framework
- Django Channels (for WebSocket support)
- Redis (for channels layer)
- PostgreSQL database
- JWT Authentication

Application Requirements:

1. User Authentication
   - Register
   - Login
   - JWT token authentication
   - Secure API endpoints

2. User Features
   - See online/offline users
   - Call another user
   - Accept/Reject call
   - End call
   - Store call history in database

3. Real-Time Features
   - WebSocket connection using Django Channels
   - WebRTC offer/answer exchange
   - ICE candidate exchange
   - Peer-to-peer voice connection

4. Backend Requirements
   - Proper project structure
   - Django app structure
   - Models for:
       - User
       - CallHistory
   - REST APIs for:
       - Register
       - Login
       - Fetch users
       - Call history
   - WebSocket routing configuration
   - Channels consumer implementation
   - Redis configuration
   - ASGI configuration

5. Frontend Requirements
   - Proper Ionic folder structure
   - Authentication service
   - WebSocket service
   - WebRTC service
   - Call UI screen
   - Incoming call screen
   - Call buttons (Call / Accept / Reject / End)
   - Permission handling (Microphone)

6. Provide:
   - Step-by-step setup instructions
   - Required package installation commands
   - Complete backend code
   - Complete frontend code
   - Environment configuration
   - How to run locally
   - How to build Android app
   - Deployment guidance

7. Follow best practices:
   - Clean architecture
   - Proper separation of concerns
   - Error handling
   - Production-ready structure
   - Security considerations

Explain clearly and provide full working code.