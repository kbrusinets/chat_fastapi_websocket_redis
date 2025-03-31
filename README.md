# FastAPI WebSocket Chat with Redis Balancer


A scalable WebSocket chat application using FastAPI, Redis, and Nginx for load balancing.

## 🏗 Infrastructure
- <strong>Frontend:</strong> Simple JavaScript client
- <strong>Backend:</strong> Multiple instances running in parallel
- <strong>Load Balancer:</strong> Nginx as balancer
- <strong>Message Queue:</strong> Redis for communication between the backend instances
- <strong>Database:</strong> PostgreSQL with SQLAlchemy ORM
- <strong>Backend is split in multiple modules:</strong>
  - <strong>Chat, Message, Progress, User:</strong> Handle database requests
  - <strong>Authentication:</strong> JWT-based authorization with access/refresh tokens stored in cookies
  - <strong>WebSocket:</strong> Manages user websocket connections and broadcasts websocket messages to the frontend
  - <strong>Redis:</strong> Publishes and receives redis messages, subscribes and unsubscribes from redis topics
- <strong>Testing:</strong> Covers Websocket and Redis modules
- <strong>API</strong>: FastAPI, http and ws
- <strong>Migrations:</strong> Alembic-ready with pre-created users and chats
- <strong>Admin Tool:</strong> RedisInsight for convenient debugging and monitoring Redis if interested

## 🚀Features
- <strong>Group & Private Chats:</strong> Create, invite, join and leave conversations
- <strong>Real-Time Messaging:</strong> WebSockets for instant updates
- <strong>Read System:</strong> Messages are marked as "read" when all users have seen them
- <strong>Multi-Device Support:</strong> Seamless sync across logged-in devices even from the same accounts
- <strong>API Docs:</strong> Auto-generated Swagger documentation

## 🔧Requirements
- Docker Compose

## 🛠 Installation
1. Clone the repository
2. Ensure required ports are available
3. Run `docker-compose up -d` and wait for all services to start
4. Access the application - http://127.0.0.1:8080

## 👥Available users 
- first@example.com 
- second@example.com
- third@example.com 
- <strong>Password</strong>: `password` (same for all users)

## 📊 Redis Monitoring (Optional)
1. Open RedisInsight - http://127.0.0.1:5540/
2. Click <strong>"+ Add Redis database"</strong> on the top left 
3. Enter `redis://:secret@redis:6379` as connection URL
4. Click <strong>"Add Database"</strong>
5. Select the newly added  connection in the list and click the `((()))` button on the left
6. Click <strong>"Subscribe"</strong> (top right) 
7. Now you are able to see all conversations between the backend instances
