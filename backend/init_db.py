#!/usr/bin/env python3
"""
Script to initialize the database with all tables and sync data from Data Dragon.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

async def init_db():
    """Initialize database schema and sync data."""
    from app.db.models import Base
    from app.db.session import engine
    from app.services.data_dragon_service import DataDragonService
    
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")
    
    print("Syncing data from Data Dragon...")
    service = DataDragonService()
    
    # Sync champions
    print("Syncing champions...")
    await service.sync_champions()
    
    # Sync items
    print("Syncing items...")
    await service.sync_items()
    
    # Sync runes
    print("Syncing runes...")
    await service.sync_runes()
    
    print("Data sync completed successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())