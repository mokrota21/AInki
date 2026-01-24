from sqlalchemy.orm import DeclarativeBase
import logging

# Get a logger with a specific name
logger = logging.getLogger("tables.base")

# Configure the root logger (only if not already configured)
if not logging.root.handlers:
    logging.basicConfig(
        format="{asctime} - {name} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO
    )

def after_create(target, context, **kwargs):
    logger.info(f"Initialized table {target.name}")

class Base(DeclarativeBase):
    pass