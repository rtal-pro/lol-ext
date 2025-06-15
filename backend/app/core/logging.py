import logging
import sys
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward Loguru
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class LogConfig(BaseModel):
    """Logging configuration"""
    
    LOGGER_NAME: str = "lol_extension_api"
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    LOG_LEVEL: str = settings.LOG_LEVEL

    # Class vars
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, Any]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: Dict[str, Dict[str, Any]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: Dict[str, Dict[str, Any]] = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


def setup_logging() -> None:
    """Configure logging with Loguru"""
    # Remove default loguru handler
    logger.remove()
    
    # Create an instance of LogConfig
    log_config = LogConfig()
    
    # Add stderr handler with custom format
    logger.add(
        sys.stderr,
        format=log_config.LOG_FORMAT,
        level=log_config.LOG_LEVEL,
        enqueue=True,
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Update logging levels for some noisy loggers
    for logger_name in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy.engine.Engine",
    ]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False
    
    logger.info("Logging configured successfully")