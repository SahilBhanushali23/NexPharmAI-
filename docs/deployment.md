# NexPharmAI Deployment Guide

## Architecture Targets
- **Frontend**: Vercel (Next.js Node runtime / static edge)
- **Backend**: Railway / Docker container
- **Database**: Managed PostgreSQL 16 (Neon / Supabase / Railway Postgres / AWS RDS)

## Environment Variables
### Backend
- `DATABASE_URL`: PostgreSQL connection string (`postgresql+psycopg2://...`)
- `JWT_SECRET`: 64-character hex cryptographic secret
- `CORS_ORIGINS`: Comma-separated allowed frontend domains
- `MODEL_PATH`: Filesystem directory housing serialized `.pkl` models and metadata

### Frontend
- `NEXT_PUBLIC_API_URL`: Public HTTPS URL of the backend API service

## Railway Deployment
Backend entrypoint command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
