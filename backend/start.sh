#!/bin/bash
# Start script for production

# Generate a secure JWT secret if not set
if [ -z "$JWT_SECRET_KEY" ]; then
  export JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
fi

# Run migrations/initialization
python -c "from server import init_db; init_db()"

# Start the server
uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
