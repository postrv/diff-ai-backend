# backend/app/tasks/background_tasks.py
import asyncio
import logging
from typing import Any, Dict, Optional
import time
import traceback
from backend.app.services.diff_merge import compute_enhanced_diff
from backend.app.services.ai_service import ai_service, AIRequest

# Setup logging
logger = logging.getLogger(__name__)

# In-memory store for task results (for demo purposes)
# In production, use Redis, database, or another persistent storage
task_results = {}

# Task status constants
TASK_PENDING = "pending"
TASK_PROCESSING = "processing"
TASK_COMPLETED = "completed"
TASK_FAILED = "failed"


async def run_diff_merge_task(document_a: str, document_b: str, task_id: str = None) -> Dict[str, Any]:
    """
    Background task for diff and merge processing with AI enhancement.

    Args:
        document_a: Content of the first document
        document_b: Content of the second document
        task_id: Optional identifier for the task

    Returns:
        Dictionary with task results
    """
    logger.info(f"Starting diff processing task {task_id if task_id else '(unnamed)'}")

    # Update task status to "processing"
    if task_id:
        task_results[task_id] = {
            "status": TASK_PROCESSING,
            "progress": 0,
            "message": "Task started",
            "start_time": time.time()
        }

    try:
        # First phase: compute diff (30% of work)
        if task_id:
            await _update_task_status(task_id, 10, "Computing document differences")

        # Compute enhanced diff with AI summary
        diff_result = await compute_enhanced_diff(document_a, document_b)

        if task_id:
            await _update_task_status(task_id, 30, "Basic diff completed, performing AI analysis")

        # Second phase: AI analysis if needed (70% of work)
        if diff_result.ai_summary is None:
            # If AI summary wasn't generated during diff (possible error/timeout),
            # make another attempt here
            try:
                if task_id:
                    await _update_task_status(task_id, 40, "Generating AI-powered analysis")

                diff_stats = diff_result.stats
                ai_summary = await ai_service.analyze_diff(document_a, document_b, diff_stats)
                diff_result.ai_summary = ai_summary

                if task_id:
                    await _update_task_status(task_id, 70, "AI analysis completed")
            except Exception as e:
                logger.error(f"AI analysis failed in background task: {str(e)}")
                if task_id:
                    await _update_task_status(task_id, 70, "AI analysis unavailable, using basic summary")

        # Final phase: completing task
        if task_id:
            await _update_task_status(task_id, 90, "Finalizing results")

        # Prepare final result
        result = {
            "status": TASK_COMPLETED,
            "result": diff_result.to_dict(),
            "processing_time": time.time() - task_results[task_id]["start_time"] if task_id else None
        }

        # Store result if task_id is provided
        if task_id:
            task_results[task_id] = {
                **result,
                "progress": 100,
                "message": "Task completed successfully",
                "completed_at": time.time()
            }

        logger.info(f"Completed diff processing task {task_id if task_id else '(unnamed)'}")
        return result

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in diff processing task: {str(e)}\n{error_trace}")

        error_result = {
            "status": TASK_FAILED,
            "error": str(e),
            "error_trace": error_trace,
            "processing_time": time.time() - task_results[task_id]["start_time"] if task_id else None
        }

        if task_id:
            task_results[task_id] = {
                **error_result,
                "progress": 100,
                "message": f"Task failed: {str(e)}",
                "completed_at": time.time()
            }

        return error_result


async def run_merge_task(request: AIRequest, task_id: str) -> Dict[str, Any]:
    """
    Background task for document merging with detailed progress tracking.

    Args:
        request: AIRequest with documents and merge parameters
        task_id: Task identifier

    Returns:
        Dictionary with merge results
    """
    logger.info(f"Starting merge task {task_id}")

    # Initialize task status
    task_results[task_id] = {
        "status": TASK_PROCESSING,
        "progress": 0,
        "message": "Preparing document merge",
        "start_time": time.time()
    }

    try:
        # Phase 1: Preparation
        await _update_task_status(task_id, 10, "Analyzing document differences")

        # Phase 2: AI processing
        await _update_task_status(task_id, 30, "Applying AI-powered merge strategy")

        # Perform the merge
        merge_result = await ai_service.smart_merge(request)

        # Phase 3: Post-processing
        await _update_task_status(task_id, 80, "Finalizing merged document")

        # Phase 4: Completion
        result = {
            "status": TASK_COMPLETED,
            "result": merge_result,
            "processing_time": time.time() - task_results[task_id]["start_time"]
        }

        task_results[task_id] = {
            **result,
            "progress": 100,
            "message": "Merge completed successfully",
            "completed_at": time.time()
        }

        logger.info(f"Completed merge task {task_id}")
        return result

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in merge task: {str(e)}\n{error_trace}")

        error_result = {
            "status": TASK_FAILED,
            "error": str(e),
            "error_trace": error_trace,
            "processing_time": time.time() - task_results[task_id]["start_time"]
        }

        task_results[task_id] = {
            **error_result,
            "progress": 100,
            "message": f"Merge failed: {str(e)}",
            "completed_at": time.time()
        }

        return error_result


async def _update_task_status(task_id: str, progress: int, message: str) -> None:
    """
    Update the status of a task with progress information.

    Args:
        task_id: The task identifier
        progress: Percentage progress (0-100)
        message: Status message
    """
    if task_id in task_results:
        task_results[task_id].update({
            "progress": progress,
            "message": message,
            "last_updated": time.time()
        })
        # Small delay to ensure updates are visible in rapid succession
        await asyncio.sleep(0.1)


def get_task_result(task_id: str) -> Dict[str, Any]:
    """
    Retrieve the result of a background task by its ID.

    Args:
        task_id: The identifier of the task

    Returns:
        Task result or status
    """
    if task_id not in task_results:
        return {"status": "not_found", "message": f"No task found with ID {task_id}"}

    return task_results[task_id]


def clean_old_tasks(max_age_hours: int = 24):
    """
    Clean up old task results to prevent memory leaks.

    Args:
        max_age_hours: Maximum age of tasks to keep in hours
    """
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    tasks_to_remove = []
    for task_id, result in task_results.items():
        # Check if task has completion timestamp
        if "completed_at" in result and current_time - result["completed_at"] > max_age_seconds:
            tasks_to_remove.append(task_id)
        # Check if task has start time but never completed (zombie tasks)
        elif "start_time" in result and current_time - result["start_time"] > max_age_seconds:
            tasks_to_remove.append(task_id)

    # Remove old tasks
    for task_id in tasks_to_remove:
        task_results.pop(task_id, None)

    if tasks_to_remove:
        logger.info(f"Cleaned up {len(tasks_to_remove)} old task results")