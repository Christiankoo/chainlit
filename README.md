# FastAPI + Chainlit Application

A production-ready web application that integrates **FastAPI** with **Chainlit** for building conversational AI interfaces, featuring **Microsoft Entra ID** (Azure AD) authentication, **Azure SQL Database** integration, and comprehensive session management.

## 🌟 Features

- **FastAPI Backend**: Modern, high-performance Python web framework
- **Chainlit Integration**: Interactive chat interface mounted at `/`
- **Microsoft Entra ID Authentication**: OAuth 2.0 / OpenID Connect flow with JWT validation
- **Session Management**: Persistent session storage in Azure SQL Database
- **Custom Middleware**: 
  - JWT-based authentication middleware (`AuthGate`)
  - Session middleware for state management
- **Azure SQL Database**: SQLAlchemy ORM for data persistence
- **Azure Monitor Integration**: Optional Application Insights telemetry
- **Docker Support**: Containerized deployment with Docker Compose
- **Health Check Endpoint**: `/healthz` for monitoring and orchestration

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- Azure SQL Database instance
- Microsoft Entra ID (Azure AD) application registration
- ODBC Driver 18 for SQL Server (included in Docker image)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Application               │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────────────┐     │
│  │  /healthz    │  │   Entra ID Auth          │     │
│  │  (health)    │  │   /api/auth/login        │     │
│  │              │  │   /api/auth/callback     │     │
│  └──────────────┘  └──────────────────────────┘     │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │   Session CRUD API                           │   │
│  │   /api/sessions (GET, POST, PUT, DELETE)     │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │   Chainlit Chat Interface                    │   │
│  │   / (mounted Chainlit app)               │   │
│  └──────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Middleware Stack:                                  │
│  - AuthGate (JWT verification)                      │
│  - SessionMiddleware (session state)                │
├─────────────────────────────────────────────────────┤
│  Database Layer (SQLAlchemy)                        │
│  - Azure SQL Database                               │
└─────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py                    # Environment configuration
│   ├── main.py                      # FastAPI application entry point
│   ├── crud/
│   │   ├── __init__.py
│   │   └── sessions.py              # Session CRUD operations & API routes
│   ├── db/
│   │   ├── __init__.py
│   │   ├── db.py                    # Database connection & session management
│   │   └── models.py                # SQLAlchemy ORM models
│   ├── entraid/
│   │   ├── __init__.py
│   │   └── entraid.py               # Microsoft Entra ID OAuth flow
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py       # JWT authentication middleware
│   └── tests/
│       ├── __init__.py
│       └── test_sessions_data_layer.py
├── cl_app/
│   ├── __init__.py
│   └── app.py                       # Chainlit chat application
├── docker-compose.yml               # Docker Compose configuration
├── Dockerfile                       # Container image definition
├── pytest.ini                       # Pytest configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔧 Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chainlit
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root (or set environment variables):
   
   ```bash
   # Azure Entra ID Configuration
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_REDIRECT_URI=http://localhost:8000/api/auth/callback
   AZURE_SECRET_ID=your-client-secret
   
   # Session Secret (generate a random string)
   SESSION_SECRET=your-session-secret-key
   
   # Azure SQL Database Configuration
   AZURE_SQL_SERVER=your-server.database.windows.net
   AZURE_SQL_DB=your-database-name
   AZURE_SQL_USER=your-username
   AZURE_SQL_PASSWORD=your-password
   
   # Optional: Application Insights
   APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Chat Interface: http://localhost:8000
   - Health Check: http://localhost:8000/healthz

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t myapp:local .
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up
   ```

3. **Access the application**
   - Application: http://localhost:8000

## 🔐 Authentication Flow

1. **User accesses protected route** → Redirected to `/api/auth/login`
2. **Login endpoint** → Redirects to Microsoft Entra ID authorization
3. **User authenticates** → Entra ID redirects to `/api/auth/callback` with auth code
4. **Callback endpoint**:
   - Exchanges code for tokens
   - Validates ID token using JWKS
   - Creates JWT session cookie (`cl_auth`)
   - Redirects to original destination
5. **AuthGate middleware** → Validates JWT on subsequent requests

### Public Paths (No Authentication Required)

- `/healthz` - Health check endpoint
- `/api/auth/login` - Login endpoint
- `/api/auth/callback` - OAuth callback endpoint

## 🗄️ Database Schema

### Sessions Table

```sql
CREATE TABLE sessions (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(200),
    created_at DATETIME2 DEFAULT SYSUTCDATETIME() NOT NULL
);
```

## 📡 API Endpoints

### Authentication

- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - Handle OAuth callback

### Session Management

- `GET /api/sessions` - List sessions (with optional filtering)
  - Query params: `user_id`, `limit`, `offset`
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{session_id}` - Get session by ID
- `PUT /api/sessions/{session_id}` - Update session
- `DELETE /api/sessions/{session_id}` - Delete session

### Health & Monitoring

- `GET /healthz` - Health check endpoint

### Chat Interface

- `/` - Chainlit conversational interface

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html
```

## 🛠️ Technologies

- **[FastAPI](https://fastapi.tiangolo.com/)** (v0.128.0) - Modern web framework
- **[Chainlit](https://chainlit.io/)** (v2.9.4) - Conversational AI interface
- **[SQLAlchemy](https://www.sqlalchemy.org/)** (v2.0.45) - ORM for database
- **[PyJWT](https://pyjwt.readthedocs.io/)** (v2.8.0) - JWT token handling
- **[Uvicorn](https://www.uvicorn.org/)** (v0.40.0) - ASGI server
- **[PyODBC](https://github.com/mkleehammer/pyodbc)** (v5.3.0) - SQL Server connectivity
- **[Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-overview)** (v1.8.3) - Application monitoring

## 🚀 Deployment

### Azure App Service

1. Build and push Docker image to Azure Container Registry
2. Configure App Service to use the container image
3. Set environment variables in App Service configuration
4. Ensure App Service has network access to Azure SQL Database

### Environment Variables for Production

Ensure all required environment variables are set in your deployment environment:

- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_REDIRECT_URI` (update for production URL)
- `AZURE_SECRET_ID`
- `SESSION_SECRET` (use a strong, random key)
- `AZURE_SQL_SERVER`
- `AZURE_SQL_DB`
- `AZURE_SQL_USER`
- `AZURE_SQL_PASSWORD`
- `APPLICATIONINSIGHTS_CONNECTION_STRING` (optional)

## 📝 Configuration

### config.py

The `app/config.py` file manages all configuration through environment variables:

- **Entra ID Settings**: Tenant, client, redirect URI, secret
- **Database Credentials**: Azure SQL connection parameters
- **Security**: Session secret for JWT signing
- **Telemetry**: Optional Application Insights integration
- **Public Paths**: Routes that bypass authentication

### Middleware Configuration

- **SessionMiddleware**: Handles session state with secure cookies
- **AuthGate**: Custom JWT authentication middleware with configurable public paths

## 🔒 Security Considerations

- JWT tokens are signed with `SESSION_SECRET`
- ID tokens are validated using Microsoft's JWKS
- Tenant ID is enforced at multiple layers
- HTTPS should be enabled in production (`https_only=True`)
- Cookies use `same_site="lax"` for CSRF protection
- Session cookies expire based on JWT `exp` claim

## 📊 Monitoring

When `APPLICATIONINSIGHTS_CONNECTION_STRING` is configured, the application automatically enables:

- Request/response telemetry
- Dependency tracking
- Exception logging
- Performance metrics

## 🆘 Troubleshooting

### Database Connection Issues

- Verify Azure SQL firewall rules allow connections
- Check connection string format and credentials
- Ensure ODBC Driver 18 is installed

### Authentication Issues

- Verify Entra ID app registration settings
- Check redirect URI matches exactly
- Ensure client secret hasn't expired
- Verify tenant ID is correct

### Docker Issues

- Ensure MSSQL ODBC driver installation is successful
- Check environment variables are passed to container
- Verify network connectivity from container to Azure SQL