#!/usr/bin/env python3
"""
Script to retrieve database table schema information.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters - when running in Docker container
DB_PARAMS = {
    'dbname': 'lol_extension',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'db',  # Use the Docker service name
    'port': 5432   # Default PostgreSQL port inside container
}

def get_table_schema(table_name):
    """Get the schema for a specific table."""
    try:
        conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Query to get column information
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        
        print(f"Schema for table '{table_name}':")
        print("-" * 60)
        print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable':<10}")
        print("-" * 60)
        
        for col in columns:
            print(f"{col['column_name']:<30} {col['data_type']:<20} {col['is_nullable']:<10}")
        
        conn.close()
    
    except Exception as e:
        print(f"Error getting schema: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python get_table_schema.py <table_name>")
        sys.exit(1)
    
    table_name = sys.argv[1]
    get_table_schema(table_name)