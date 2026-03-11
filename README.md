# SolarSnap Backend API

A robust Flask-based REST API powering the SolarSnap solar panel inspection system. Provides secure authentication, data management, file upload, and comprehensive reporting capabilities for solar farm inspection workflows.

## 🎯 Overview

The SolarSnap Backend API serves as the central data hub for the mobile inspection application, handling user authentication, inspection data storage, image management, and analytics generation. Built with Flask and designed for scalability and reliability.

## ✨ Key Features

### 🔐 Authentication & Security
- JWT-based authentication with refresh tokens
- Role-based access control (Inspector, Manager, Admin)
- Company-level data isolation
- Secure password hashing with bcrypt
- CORS support for cross-origin requests

### 📊 Data Management
- Complete inspection lifecycle management
- Site and panel inventory tracking
- Real-time sync status monitoring
- Comprehensive audit logging
- Flexible metadata storage (JSON fields)

### 📁 File Handling
- Thermal and visual image upload
- Batch upload support with progress tracking
- File compression and optimization
- Secure file storage with access controls
- Multiple storage backend support

### 📈 Analytics & Reporting
- Site-level performance analytics
- Fault trend analysis and reporting
- Maintenance scheduling recommendations
- Export capabilities (JSON, CSV ready)
- Real-time dashboard data

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- SQLite (included) or PostgreSQL (production)

### Installation

1. **Setup Virtual Environment**
   ```bash
   cd Backend
   python -m venv venv
   
   # Activate virtual environment
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize Database**
   ```bash
   python init_db.py
   ```
   This creates all tables and seeds with sample data:
   - 3 solar sites with 1,200 panels total
   - 50 sample inspections with realistic data
   - Test user accounts for development

5. **Start Development Server**
   ```bash
   python run.py
   ```
   Server starts at: `http://localhost:5000`

### Quick Test
```bash
# Health check
curl http://localhost:5000/health

# Login with test credentials
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "inspector1@solartech.com",
    "password": "password123",
    "companyId": "SOLARTECH-001"
  }'
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///solarsnap.db
# For PostgreSQL: postgresql://user:password@host:port/database

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=604800

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760  # 10MB max file size

# CORS
CORS_ORIGINS=*  # Set to specific domains in production

# Logging
LOG_LEVEL=INFO
```

### Production Configuration

For production deployment, update these settings:

```env
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://user:password@host:port/database
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=strong-random-production-key
JWT_SECRET_KEY=strong-random-jwt-key
```

## 📡 API Documentation

### Base URL
- Development: `http://localhost:5000`
- Production: `https://your-api-domain.com`

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login and get tokens | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh Token |
| POST | `/api/v1/auth/logout` | Logout and invalidate tokens | Yes |
| GET | `/api/v1/auth/me` | Get current user info | Yes |

### Sites Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/sites` | List all sites | Yes |
| GET | `/api/v1/sites/{siteId}` | Get site details | Yes |
| GET | `/api/v1/sites/{siteId}/panels` | Get panel layout | Yes |
| POST | `/api/v1/sites` | Create new site | Admin |
| PUT | `/api/v1/sites/{siteId}` | Update site | Admin |

### Inspections

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/inspections` | Create inspection | Yes |
| GET | `/api/v1/inspections` | List inspections | Yes |
| GET | `/api/v1/inspections/{id}` | Get inspection details | Yes |
| PUT | `/api/v1/inspections/{id}` | Update inspection | Yes |
| DELETE | `/api/v1/inspections/{id}` | Delete inspection | Yes |

### File Upload

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/upload/thermal` | Upload thermal image | Yes |
| POST | `/api/v1/upload/visual` | Upload visual image | Yes |
| POST | `/api/v1/upload/batch` | Batch upload multiple files | Yes |
| GET | `/api/v1/upload/status/{uploadId}` | Check upload status | Yes |

### Reports & Analytics

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/reports/site/{siteId}` | Site performance report | Yes |
| GET | `/api/v1/reports/fault` | Fault analysis report | Yes |
| GET | `/api/v1/reports/maintenance` | Maintenance recommendations | Yes |
| POST | `/api/v1/reports/export` | Export report data | Yes |

### Sync Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/sync/status` | Get sync status | Yes |
| GET | `/api/v1/sync/queue` | View upload queue | Yes |
| POST | `/api/v1/sync/retry/{id}` | Retry failed upload | Yes |
| DELETE | `/api/v1/sync/queue/{id}` | Remove from queue | Yes |

## 🗄️ Database Schema

### Core Tables

**users**
- `user_id` (Primary Key)
- `email` (Unique)
- `password_hash`
- `full_name`
- `role` (inspector, manager, admin)
- `company_id`
- `is_active`
- `created_at`, `updated_at`

**sites**
- `site_id` (Primary Key)
- `site_name`
- `company_id`
- `total_panels`
- `rows`, `panels_per_row`
- `latitude`, `longitude`
- `status` (active, maintenance, inactive)
- `created_at`, `updated_at`

**panels**
- `panel_id` (Primary Key)
- `site_id` (Foreign Key)
- `row_number`, `column_number`
- `string_number`
- `status` (healthy, warning, critical, not_inspected)
- `last_inspection_date`
- `created_at`, `updated_at`

**inspections**
- `inspection_id` (Primary Key)
- `inspection_uuid` (Unique)
- `site_id`, `panel_id` (Foreign Keys)
- `inspector_id` (Foreign Key)
- `temperature`, `delta_temp`
- `severity` (healthy, warning, critical)
- `issue_type`
- `latitude`, `longitude`
- `thermal_image_url`, `visual_image_url`
- `metadata` (JSON)
- `timestamp`, `created_at`

**upload_queue**
- `upload_id` (Primary Key)
- `inspection_id` (Foreign Key)
- `file_path`, `file_size`
- `status` (pending, uploading, completed, failed)
- `retry_count`, `max_retries`
- `error_message`
- `created_at`, `last_attempt_at`

## 🧪 Testing

### Test Credentials

**Inspector Account:**
- Email: `inspector1@solartech.com`
- Password: `password123`
- Company ID: `SOLARTECH-001`

**Manager Account:**
- Email: `manager1@solartech.com`
- Password: `password123`
- Company ID: `SOLARTECH-001`

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app tests/

# Run specific test file
python -m pytest tests/test_auth.py
```

### Manual API Testing

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "inspector1@solartech.com",
    "password": "password123",
    "companyId": "SOLARTECH-001"
  }' | jq -r '.access_token')

# 2. Get user info
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/auth/me

# 3. List sites
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/v1/sites

# 4. Create inspection
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "siteId": "SITE-001",
    "panelId": "PANEL-001-001",
    "temperature": 45.2,
    "deltaTemp": 12.5,
    "severity": "warning",
    "issueType": "hotspot",
    "latitude": 37.7749,
    "longitude": -122.4194
  }' \
  http://localhost:5000/api/v1/inspections
```

## 🚀 Deployment

### Local Development
```bash
python run.py
# Server runs on http://localhost:5000
```

### Production Deployment (Render)

1. **Create Render Web Service**
   - Repository: Connect your Git repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`

2. **Environment Variables**
   Add these in Render dashboard:
   ```
   DATABASE_URL=postgresql://...
   SECRET_KEY=production-secret-key
   JWT_SECRET_KEY=production-jwt-key
   FLASK_ENV=production
   ```

3. **Database Setup**
   ```bash
   # After deployment, initialize database
   python init_db.py
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

```bash
# Build and run
docker build -t solarsnap-backend .
docker run -p 5000:5000 solarsnap-backend
```

## 📁 Project Structure

```
Backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration management
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py              # User model
│   │   ├── site.py              # Site model
│   │   ├── panel.py             # Panel model
│   │   ├── inspection.py        # Inspection model
│   │   └── upload_queue.py      # Upload queue model
│   ├── routes/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes
│   │   ├── sites.py             # Site management routes
│   │   ├── inspections.py       # Inspection routes
│   │   ├── uploads.py           # File upload routes
│   │   ├── reports.py           # Analytics routes
│   │   ├── sync.py              # Sync management routes
│   │   └── settings.py          # Settings routes
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── auth.py              # Auth helpers
│       ├── validators.py        # Input validation
│       └── file_utils.py        # File handling
├── uploads/                     # Uploaded files storage
├── tests/                       # Test files
│   ├── test_auth.py
│   ├── test_sites.py
│   └── test_inspections.py
├── .env.example                 # Environment template
├── .gitignore
├── requirements.txt             # Python dependencies
├── requirements_minimal.txt     # Minimal dependencies
├── run.py                       # Application entry point
├── init_db.py                   # Database initialization
├── start.sh                     # Linux startup script
├── start.bat                    # Windows startup script
└── README.md                    # This file
```

## 🔍 Monitoring & Logging

### Application Logging
```python
# Logs are written to console and can be configured for file output
import logging
logging.basicConfig(level=logging.INFO)
```

### Health Check Endpoint
```bash
curl http://localhost:5000/health
# Returns: {"status": "healthy", "timestamp": "2026-03-12T10:30:00Z"}
```

### Performance Monitoring
- Request timing logged for all endpoints
- Database query performance tracking
- File upload progress monitoring
- Error rate tracking and alerting

## 🛠️ Development

### Adding New Endpoints

1. **Create route file** in `app/routes/`
2. **Define models** in `app/models/`
3. **Add validation** in `app/utils/validators.py`
4. **Register blueprint** in `app/__init__.py`
5. **Write tests** in `tests/`

### Database Migrations

```bash
# For schema changes, update models and run:
python init_db.py  # Recreates database (development only)

# For production, implement proper migrations
```

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check database URL and permissions
python -c "from app import create_app; app = create_app(); print('DB OK')"
```

**Port Already in Use**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

**JWT Token Issues**
```bash
# Verify JWT secret is set
python -c "import os; print(os.getenv('JWT_SECRET_KEY'))"
```

**File Upload Failures**
```bash
# Check upload directory permissions
ls -la uploads/
mkdir -p uploads && chmod 755 uploads
```

## 📄 License

Proprietary - FLIR App Challenge 2025

---

**API Version**: v1  
**Status**: Production Ready  
**Last Updated**: March 2026
