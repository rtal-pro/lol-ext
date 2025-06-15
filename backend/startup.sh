#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
python -c "
import time
import psycopg2

while True:
    try:
        conn = psycopg2.connect(
            dbname='lol_extension',
            user='postgres',
            password='postgres',
            host='db',
            port=5432
        )
        conn.close()
        break
    except psycopg2.OperationalError:
        print('Database not ready yet. Waiting...')
        time.sleep(1)
"
echo "Database is ready!"

# Initialize database schema and sync data
echo "Initializing database..."
python /app/init_db.py || echo "Database initialization skipped, tables may already exist"

# Let's start the application using uvicorn
cd /app
echo "Starting the application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload