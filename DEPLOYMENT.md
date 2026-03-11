# SolarSnap Backend Deployment Guide

This guide covers deploying the SolarSnap Backend to Render with PostgreSQL.

## 🚀 Quick Deploy to Render

### 1. Prerequisites

- GitHub repository with your code
- Render account (free tier available)
- Environment variables ready

### 2. Create Render Web Service

1. **Connect Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `Backend` directory as root

2. **Configure Service**
   ```
   Name: solarsnap-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --config gunicorn.conf.py run:app
   ```

3. **Set Environment Variables**
   Add these in the Render dashboard:
   ```
   FLASK_ENV=production
   FLASK_DEBUG=False
   SECRET_KEY=<generate-strong-random-key>
   JWT_SECRET_KEY=<generate-strong-random-key>
   CORS_ORIGINS=*
   UPLOAD_FOLDER=uploads
   MAX_CONTENT_LENGTH=52428800
   LOG_LEVEL=INFO
   ```

### 3. Create PostgreSQL Database

1. **Add Database**
   - In Render dashboard: "New +" → "PostgreSQL"
   - Name: `solarsnap-db`
   - Plan: Free (or paid for production)

2. **Connect Database**
   - Copy the "External Database URL"
   - Add as environment variable:
   ```
   DATABASE_URL=<your-postgresql-url>
   ```

### 4. Deploy and Initialize

1. **Deploy Service**
   - Render will automatically deploy when you push to main branch
   - Monitor deployment logs for any issues

2. **Initialize Database**
   ```bash
   # SSH into your Render service or run locally with production DATABASE_URL
   python init_db.py
   ```

## 🔧 Manual Deployment Steps

### 1. Environment Setup

Create production `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with production values:
```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-production-key
JWT_SECRET_KEY=your-jwt-secret-production-key
DATABASE_URL=postgresql://user:password@host:port/database
CORS_ORIGINS=https://yourdomain.com
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
LOG_LEVEL=INFO
```

### 2. Database Setup

**Option A: Using Render PostgreSQL**
1. Create PostgreSQL database in Render
2. Use the provided DATABASE_URL
3. Run initialization script

**Option B: External PostgreSQL**
1. Create PostgreSQL database
2. Create user and grant permissions:
   ```sql
   CREATE DATABASE solarsnap;
   CREATE USER solarsnap_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE solarsnap TO solarsnap_user;
   ```
3. Update DATABASE_URL in environment

### 3. Application Deployment

**Using Render (Recommended)**
```yaml
# render.yaml
services:
  - type: web
    name: solarsnap-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --config gunicorn.conf.py run:app
```

**Manual Server Deployment**
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start with Gunicorn
gunicorn --config gunicorn.conf.py run:app
```

## 🔍 Health Checks

### Application Health
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "SolarSnap API is running",
  "database": "connected",
  "environment": "production"
}
```

### Database Health
```bash
python health_check.py https://your-app.onrender.com
```

## 📊 Monitoring

### Logs
- **Render**: View logs in dashboard
- **Manual**: Check `logs/solarsnap.log`

### Performance Monitoring
```bash
# Check application status
curl https://your-app.onrender.com/

# Test authentication endpoint
curl -X POST https://your-app.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}'
```

## 🔐 Security Checklist

### Environment Variables
- [ ] Strong SECRET_KEY (32+ characters)
- [ ] Strong JWT_SECRET_KEY (32+ characters)
- [ ] Specific CORS_ORIGINS (not *)
- [ ] Secure DATABASE_URL
- [ ] FLASK_DEBUG=False

### Database Security
- [ ] Strong database password
- [ ] Limited database user permissions
- [ ] SSL connection enabled
- [ ] Regular backups configured

### Application Security
- [ ] HTTPS enabled
- [ ] Security headers configured
- [ ] File upload limits set
- [ ] Input validation enabled

## 🚨 Troubleshooting

### Common Issues

**Database Connection Error**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: Check DATABASE_URL format and network connectivity

**Import Errors**
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Ensure PYTHONPATH includes application directory

**Permission Errors**
```
PermissionError: [Errno 13] Permission denied: 'uploads'
```
**Solution**: Check file system permissions for upload directory

**Memory Issues**
```
gunicorn.errors.HaltServer: Worker failed to boot
```
**Solution**: Reduce worker count or increase memory allocation

### Debug Commands

```bash
# Test database connection
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.session.execute('SELECT 1')"

# Check environment variables
python -c "import os; print(os.getenv('DATABASE_URL')[:50])"

# Test application import
python -c "from app import create_app; print('Import successful')"

# Run health check
python health_check.py
```

## 📈 Scaling

### Horizontal Scaling
- Increase Render service instances
- Use load balancer for multiple instances
- Implement session storage (Redis)

### Database Scaling
- Upgrade to paid PostgreSQL plan
- Implement read replicas
- Add connection pooling

### Performance Optimization
- Enable gzip compression
- Implement caching (Redis)
- Optimize database queries
- Use CDN for static files

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy to Render
on:
  push:
    branches: [main]
    paths: ['Backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}"
```

### Automated Testing
```bash
# Run tests before deployment
python -m pytest tests/
python health_check.py
```

## 📋 Post-Deployment Checklist

- [ ] Application starts successfully
- [ ] Database connection works
- [ ] Health check passes
- [ ] Authentication endpoints work
- [ ] File upload works
- [ ] CORS configured correctly
- [ ] Logs are being written
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented
- [ ] SSL certificate valid

## 🆘 Support

For deployment issues:
1. Check Render service logs
2. Run health check script
3. Verify environment variables
4. Test database connectivity
5. Check application logs

---

**Last Updated**: March 2026  
**Render Documentation**: https://render.com/docs  
**PostgreSQL Documentation**: https://www.postgresql.org/docs/