from ..config.settings import settings
from ..config.tables import TaskStatus
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from fastapi import HTTPException, status
import uuid
import logging

logger = logging.getLogger("update_task")

async def create_task(task_id: uuid.UUID, task_status: str):
    """
    Creates a new task record.
    """
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            stmt = (
                insert(TaskStatus)
                .values(task_id=task_id, status=task_status)
                .on_conflict_do_nothing(index_elements=[TaskStatus.task_id])
            )
            session.execute(stmt)
            session.commit()
    except Exception as e:
        logger.error(f"Failed to create task: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create task: {str(e)}")

async def update_task(task_id: uuid.UUID, task_status: str):
    """
    Creates or updates the status of a background task (upsert).
    """
    try:
        engine = settings.get_pg_engine()
        with Session(engine) as session:
            # Check if task exists
            stmt = select(TaskStatus).where(TaskStatus.task_id == task_id)
            existing_task = session.execute(stmt).scalar_one_or_none()
            
            if existing_task:
                # Update existing task
                existing_task.status = task_status
            else:
                # Create new task
                new_task = TaskStatus(task_id=task_id, status=task_status)
                session.add(new_task)
            
            session.commit()
        return {"message": "Task updated successfully", "task_id": task_id, "status": task_status}
    except Exception as e:
        logger.error(f"Failed to update task: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update task: {str(e)}")