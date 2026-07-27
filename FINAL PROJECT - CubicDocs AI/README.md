# CubicDocs AI

## AI Document Control & Intelligence Platform

CubicDocs AI is a production-oriented standalone platform for managing engineering
and project documents throughout their complete lifecycle.

The application combines document control, revision management, approval workflows,
compliance analysis, relationship intelligence, cited document conversations,
analytics, authentication, role-based authorization, audit logging, and Docker
deployment in one unified product.

## Final Project

This repository contains the final production-readiness release of the AI Document
Control Assistant project.

## Planned Capabilities

- Secure authentication and user management
- Role-based access control
- Project workspaces
- Document registration and upload
- Document version and revision history
- Review and approval workflows
- Compliance analysis with evidence
- Document relationship knowledge graph
- Conversational assistant with citations
- Analytics and executive reporting
- Complete audit trail
- Docker deployment
- Health checks and metrics
- Automated testing
- Technical documentation
- User guide
- Final presentation and demonstration

## Technology Stack

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Prometheus metrics

### Frontend

- React
- TypeScript
- Vite

### Deployment

- Docker
- Docker Compose
- Nginx
- PostgreSQL
- Redis

## Current Development Status

The project foundation is currently being implemented.

## Local Backend Development

```powershell
cd backend

python -m venv .venv

.\.venv\Scripts\activate

pip install -r requirements-dev.txt

uvicorn app.main:app --reload

Open:

Application: http://127.0.0.1:8000
Swagger API: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/api/v1/health/live
Readiness check: http://127.0.0.1:8000/api/v1/health/ready
Metrics: http://127.0.0.1:8000/metrics
Author

Marwan
Cubic Engineering Consultancy


---

# Run the Phase 1 backend

Open PowerShell inside the project:

```powershell
cd "C:\Users\Dell\Desktop\MaCubic\FINAL PROJECT - CubicDocs AI\backend"