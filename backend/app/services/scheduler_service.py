import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db
from app.db.data_manager import DataDragonManager

# Set up logging
logger = logging.getLogger(__name__)


class ScheduledTask:
    """Represents a scheduled task with timing information"""
    
    def __init__(
        self, 
        name: str,
        func: Callable[[], Awaitable[Any]],
        interval_hours: int,
        last_run: Optional[datetime] = None,
        enabled: bool = True
    ):
        self.name = name
        self.func = func
        self.interval_hours = interval_hours
        self.last_run = last_run or datetime.min
        self.enabled = enabled
        self.running = False
        self.error = None
    
    @property
    def next_run(self) -> datetime:
        """Calculate the next scheduled run time"""
        if not self.last_run:
            return datetime.now()
        return self.last_run + timedelta(hours=self.interval_hours)
    
    @property
    def should_run(self) -> bool:
        """Check if task should run now"""
        return (
            self.enabled and 
            not self.running and 
            datetime.now() >= self.next_run
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for API responses"""
        return {
            "name": self.name,
            "interval_hours": self.interval_hours,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "enabled": self.enabled,
            "running": self.running,
            "error": str(self.error) if self.error else None
        }


class SchedulerService:
    """Service to manage scheduled tasks for data synchronization"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, poll_interval: int = 60):
        if self.initialized:
            return
            
        self.tasks: Dict[str, ScheduledTask] = {}
        self.poll_interval = poll_interval  # seconds
        self.running = False
        self.task = None
        self.initialized = True
        self.db_dependency = get_db
        logger.info("Scheduler service initialized")
    
    async def start(self):
        """Start the scheduler"""
        if self.running:
            return
            
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")
    
    def add_task(self, task: ScheduledTask):
        """Add a task to the scheduler"""
        self.tasks[task.name] = task
        logger.info(f"Added scheduled task: {task.name}")
    
    def remove_task(self, name: str):
        """Remove a task from the scheduler"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed scheduled task: {name}")
    
    def get_task(self, name: str) -> Optional[ScheduledTask]:
        """Get a task by name"""
        return self.tasks.get(name)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """Get all scheduled tasks"""
        return list(self.tasks.values())
    
    async def run_task(self, name: str) -> bool:
        """Run a task immediately"""
        task = self.get_task(name)
        if not task:
            return False
            
        return await self._execute_task(task)
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks and runs tasks"""
        while self.running:
            try:
                for task in self.tasks.values():
                    if task.should_run:
                        asyncio.create_task(self._execute_task(task))
                
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
    
    async def _execute_task(self, task: ScheduledTask) -> bool:
        """Execute a single task"""
        if task.running:
            return False
            
        task.running = True
        task.error = None
        
        try:
            logger.info(f"Running scheduled task: {task.name}")
            await task.func()
            task.last_run = datetime.now()
            logger.info(f"Completed scheduled task: {task.name}")
            return True
        except Exception as e:
            task.error = e
            logger.error(f"Error executing task {task.name}: {str(e)}", exc_info=True)
            return False
        finally:
            task.running = False


# Function to create data sync tasks
def create_data_sync_tasks(scheduler: SchedulerService, db_dependency):
    """Create and register data sync tasks"""
    
    async def sync_champions_task():
        """Task to sync champion data"""
        async for db in db_dependency():
            try:
                data_manager = DataDragonManager(db)
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("champions")
                
                updates_needed = await data_manager.check_for_updates()
                
                # Check if any updates are needed
                if any(updates_needed.values()):
                    logger.info(f"New version available: {latest_version}. Updates needed: {updates_needed}")
                
                # Always update champions if needed
                if current_version != latest_version:
                    logger.info(f"Scheduled sync: Champions from {current_version} to {latest_version}")
                    await data_manager.update_champions(latest_version)
                    await db.commit()
                    logger.info(f"Scheduled sync: Champions updated to version {latest_version}")
                else:
                    logger.info(f"Scheduled sync: Champions already at latest version {latest_version}")
                    
                # Always update summoner spells immediately if needed
                if updates_needed.get("summoner-spells", False):
                    logger.info(f"Scheduled sync: Summoner spells need update to version {latest_version}")
                    await data_manager.update_summoner_spells(latest_version)
                    await db.commit()
                    logger.info(f"Scheduled sync: Summoner spells updated to version {latest_version}")
            except Exception as e:
                logger.error(f"Error in champion sync task: {str(e)}", exc_info=True)
                raise
            finally:
                if 'data_manager' in locals():
                    await data_manager.close()
    
    async def sync_items_task():
        """Task to sync item data"""
        async for db in db_dependency():
            try:
                data_manager = DataDragonManager(db)
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("items")
                
                if current_version != latest_version:
                    logger.info(f"Scheduled sync: Items from {current_version} to {latest_version}")
                    await data_manager.update_items(latest_version)
                    await db.commit()
                    logger.info(f"Scheduled sync: Items updated to version {latest_version}")
                else:
                    logger.info(f"Scheduled sync: Items already at latest version {latest_version}")
            except Exception as e:
                logger.error(f"Error in item sync task: {str(e)}", exc_info=True)
                raise
            finally:
                if 'data_manager' in locals():
                    await data_manager.close()
    
    async def sync_runes_task():
        """Task to sync rune data"""
        async for db in db_dependency():
            try:
                data_manager = DataDragonManager(db)
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("runes")
                
                if current_version != latest_version:
                    logger.info(f"Scheduled sync: Runes from {current_version} to {latest_version}")
                    await data_manager.update_runes(latest_version)
                    await db.commit()
                    logger.info(f"Scheduled sync: Runes updated to version {latest_version}")
                else:
                    logger.info(f"Scheduled sync: Runes already at latest version {latest_version}")
            except Exception as e:
                logger.error(f"Error in rune sync task: {str(e)}", exc_info=True)
                raise
            finally:
                if 'data_manager' in locals():
                    await data_manager.close()
    
    async def sync_check_version_task():
        """Task to check for new Data Dragon versions"""
        async for db in db_dependency():
            try:
                data_manager = DataDragonManager(db)
                latest_version = await data_manager.get_latest_version()
                updates_needed = await data_manager.check_for_updates()
                
                if any(updates_needed.values()):
                    logger.info(f"New version available: {latest_version}. Updates needed: {updates_needed}")
                else:
                    logger.info(f"All data is at the latest version: {latest_version}")
            except Exception as e:
                logger.error(f"Error checking for updates: {str(e)}", exc_info=True)
                raise
            finally:
                if 'data_manager' in locals():
                    await data_manager.close()
    
    # Create and register tasks
    scheduler.add_task(ScheduledTask(
        name="check_versions",
        func=sync_check_version_task,
        interval_hours=1  # Check for new versions every hour
    ))
    
    scheduler.add_task(ScheduledTask(
        name="sync_champions",
        func=sync_champions_task,
        interval_hours=24  # Sync champions daily
    ))
    
    scheduler.add_task(ScheduledTask(
        name="sync_items",
        func=sync_items_task,
        interval_hours=24  # Sync items daily
    ))
    
    scheduler.add_task(ScheduledTask(
        name="sync_runes",
        func=sync_runes_task,
        interval_hours=24  # Sync runes daily
    ))
    
    logger.info("Created data sync tasks")
    return scheduler