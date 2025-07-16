# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Social media application with Flask backend and server-side rendered frontend using Jinja2 templates. Features user authentication, posts, likes, comments, and follow system similar to Instagram.

## Architecture

### Backend (Flask + Jinja2)
- **Main App**: `backend/app_jinja.py` - Flask app with server-side rendering
- **Models**: `backend/models.py` - SQLAlchemy models (User, Post, Like, Comment, followers table)
- **Templates**: `backend/templates/` - Jinja2 templates for all pages
- **Authentication**: Session-based auth (not JWT) with password hashing
- **Database**: PostgreSQL (production) / SQLite (development fallback)

### Frontend Templates
- **Base Template**: `templates/base.html` - Common layout and navigation
- **Auth Pages**: `templates/auth/` - Login and registration forms
- **Home Feed**: `templates/home.html` - Main Instagram-like feed interface
- **Static Assets**: `backend/static/` - CSS, JS, and images served by Flask

### Database Schema
- **User**: id, username, password_hash + relationships
- **Post**: id, caption, timestamp, user_id
- **Like**: id, user_id, post_id (unique constraint on user+post)
- **Comment**: id, text, timestamp, user_id, post_id
- **followers**: Many-to-many association table for follow relationships

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Install test dependencies
pip install -r backend/requirements-test.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit .env with your DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY

# Initialize database (creates tables automatically on app start)
python backend/app_jinja.py
```

### Running the Application
```bash
# Start Flask development server
python backend/app_jinja.py
# Server runs on http://127.0.0.1:5001

# Seed database with sample data
python backend/seed_data.py
```

### Testing
```bash
# Run all tests with coverage (from backend directory)
python run_tests.py --all

# Run specific test categories
python run_tests.py --auth          # Authentication tests
python run_tests.py --models        # Database model tests
python run_tests.py --routes        # Route/endpoint tests
python run_tests.py --logging       # Logging system tests
python run_tests.py --security      # Security tests
python run_tests.py --fast          # Fast tests (exclude slow)

# Direct pytest usage
python -m pytest                    # Run all tests
python -m pytest tests/test_auth.py -v  # Run specific test file
python -m pytest -m unit           # Run unit tests only

# Clean test artifacts
python run_tests.py --clean
```

### Database Operations
```bash
# Start PostgreSQL with Docker
cd database && docker-compose up -d

# Seed sample data (8 users, 14 posts, likes, comments, follows)
python backend/seed_data.py
```

## Key Implementation Details

### Authentication Flow
- Session-based authentication (not JWT tokens as originally planned)
- `get_current_user()` helper function retrieves user from session
- `@app.context_processor` makes `current_user` available in all templates
- Password hashing with Werkzeug's `generate_password_hash`

### Feed Algorithm
Home feed shows posts from followed users + own posts, ordered by timestamp descending. User likes are tracked for heart icon display.

### Social Features
- Follow/unfollow with many-to-many relationship through `followers` table
- Like toggle (add if not exists, remove if exists)
- Comments with timestamp and author display
- Post creation with caption text

### Template Structure
All pages extend `base.html` which includes navigation, flash messages, and common styling. Server-side rendering handles all user interactions through form submissions and redirects.

### Logging System
- **Industrial-grade logging** with structured JSON format and multiple log files
- **Log files**: `application.log`, `security.log`, `audit.log`, `performance.log`, `errors.log`
- **Correlation IDs** for request tracking across all log entries
- **Decorators** available: `@log_execution_time()`, `@log_user_action()`
- **Event types**: Authentication, authorization, business events, performance metrics
- **Configuration**: Via environment variables (`LOG_LEVEL`, `LOG_DIR`, `FLASK_ENV`)

### Testing Architecture
- **Pytest-based** test suite with comprehensive coverage
- **Test categories**: unit, integration, auth, models, routes, logging, security
- **Test runner**: `backend/run_tests.py` with multiple options
- **Coverage reporting**: HTML reports generated in `htmlcov/`
- **Test isolation**: In-memory SQLite database for fast execution