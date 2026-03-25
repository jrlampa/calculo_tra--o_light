# Environment Setup Guide

## Overview

This guide explains how to set up the development and testing environment for the calculo_tração_light project.

## Prerequisites

### System Requirements
- Python 3.10 or higher
- Node.js 16 or higher
- PostgreSQL 15
- Redis 7
- Docker (optional, for containerized deployment)

### Development Tools
- Git
- pip (Python package manager)
- npm (Node.js package manager)

## Environment Configuration

### 1. Clone the Repository
```bash
git clone https://github.com/your-organization/calculo-tração-light.git
cd calculo-tração-light
```

### 2. Create Environment File
Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

Edit the `.env` file with your actual configuration values:
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/calculo_tracao_dev

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Configuration
FRONTEND_URL=http://localhost:3000
API_URL=http://localhost:8000

# Security Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

### 3. Backend Setup (Python)

#### Create Virtual Environment
```bash
cd python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Database Setup
```bash
# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python db/seed_data.py
```

#### Run Backend Server
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup (Node.js)

#### Install Dependencies
```bash
cd ../
npm install
```

#### Run Frontend Development Server
```bash
npm run dev
```

### 5. Testing Environment

#### Configure Test Database
```bash
# Create test database
createdb calculo_tracao_test

# Run test migrations
cd python
alembic upgrade head
```

#### Run Tests
```bash
# Backend tests
python -m pytest tests/ -v

# Frontend tests
npm test

# E2E tests
npx playwright test
```

## CI/CD Environment

### GitHub Secrets Configuration

For the CI/CD pipeline to work properly, configure the following secrets in your GitHub repository:

#### Required Secrets
- `DATABASE_URL`: PostgreSQL connection string for testing
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase service key
- `REDIS_URL`: Redis connection string

#### Optional Secrets
- `GITHUB_TOKEN`: For GitHub API access
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password
- `SLACK_WEBHOOK`: For notifications

### Local CI/CD Testing

To test the CI/CD pipeline locally, you can use the `act` tool:

```bash
# Install act
brew install act  # On macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflows locally
act -j test-python
act -j test-frontend
act -j test-persistence
```

## Docker Setup (Optional)

### Build Docker Images
```bash
# Build backend image
docker build -f Dockerfile.api -t calculo-tração-light:backend .

# Build frontend image
docker build -f Dockerfile.web -t calculo-tração-light:frontend .
```

### Run with Docker Compose
```bash
# Development environment
docker-compose up -d

# Test environment
docker-compose -f docker-compose.test.yml up -d
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U username -d calculo_tracao_dev
```

#### Redis Connection Errors
```bash
# Check if Redis is running
redis-cli ping

# Expected response: PONG
```

#### Python Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Node.js Module Errors
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Environment Variables Not Loading

If environment variables are not being loaded:

1. Ensure `.env` file exists in the project root
2. Check that the file has the correct permissions
3. Restart your development servers after making changes

### CI/CD Pipeline Issues

If the CI/CD pipeline is failing:

1. Check GitHub Actions logs for specific error messages
2. Verify all required secrets are configured
3. Test locally using the `act` tool
4. Check workflow YAML syntax

## Performance Optimization

### Development Environment
- Use `--reload` flag for fast development feedback
- Enable hot reloading for frontend changes
- Use database connection pooling

### Testing Environment
- Use in-memory databases for faster tests
- Parallelize test execution
- Cache dependencies between runs

### Production Environment
- Use production-grade database instances
- Configure proper Redis caching
- Enable application monitoring

## Security Best Practices

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique secrets for each environment
- Rotate secrets regularly

### Database Security
- Use strong passwords
- Enable SSL/TLS connections
- Limit database access permissions

### Application Security
- Keep dependencies updated
- Use security scanning tools
- Implement proper input validation

## Monitoring and Logging

### Application Logs
- Configure structured logging
- Set appropriate log levels
- Monitor error rates and performance

### Database Monitoring
- Track query performance
- Monitor connection pool usage
- Set up alerts for critical issues

### Infrastructure Monitoring
- Monitor resource usage (CPU, memory, disk)
- Track application response times
- Set up health checks

## Getting Help

If you encounter issues not covered in this guide:

1. Check the project documentation
2. Review GitHub Issues for similar problems
3. Ask for help in the project's communication channels
4. Create a detailed issue report with:
   - Environment details
   - Steps to reproduce
   - Error messages
   - Expected vs actual behavior

## Next Steps

After setting up your environment:

1. Run the test suite to ensure everything works
2. Explore the codebase structure
3. Check out existing issues to contribute
4. Review the project's coding standards and guidelines