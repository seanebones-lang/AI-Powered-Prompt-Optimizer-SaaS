"""
Batch optimization module for processing multiple prompts at once.
"""
import logging
import json
import time
from typing import List, Dict, Any, Optional, Callable
from agents import OrchestratorAgent
from database import db, BatchJob
from input_validation import sanitize_and_validate_prompt, validate_prompt_type

logger = logging.getLogger(__name__)


class BatchOptimizer:
    """Handles batch optimization of multiple prompts."""

    def __init__(self, max_workers: int = 10):
        """
        Initialize batch optimizer.
        
        Args:
            max_workers: Maximum number of concurrent optimizations
        """
        self.max_workers = max_workers
        self.orchestrator = OrchestratorAgent()

    async def optimize_batch(
        self,
        prompts: List[Dict[str, Any]],
        user_id: Optional[int] = None,
        job_id: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Optimize a batch of prompts.
        
        Args:
            prompts: List of prompt dictionaries with 'prompt' and 'type' keys
            user_id: User ID for tracking
            job_id: Batch job ID for updating progress
            
        Returns:
            List of optimization results
        """
        results = []
        completed = 0
        failed = 0

        async def optimize_single(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
            """Optimize a single prompt."""
            try:
                prompt_text = prompt_data.get("prompt", "")
                prompt_type_str = prompt_data.get("type", "creative")

                # Validate and sanitize
                is_valid, sanitized_prompt, validation_error = sanitize_and_validate_prompt(prompt_text)
                if not is_valid:
                    return {
                        "success": False,
                        "error": validation_error,
                        "original_prompt": prompt_text
                    }

                is_valid_type, prompt_type_enum, type_error = validate_prompt_type(prompt_type_str)
                if not is_valid_type:
                    return {
                        "success": False,
                        "error": type_error,
                        "original_prompt": prompt_text
                    }

                # Optimize
                start_time = time.time()
                result = await self.orchestrator.optimize_prompt(sanitized_prompt, prompt_type_enum)
                processing_time = time.time() - start_time

                result["processing_time"] = processing_time
                result["original_prompt"] = sanitized_prompt
                result["prompt_type"] = prompt_type_str
                result["success"] = True

                return result
            except Exception as e:
                logger.error(f"Error optimizing prompt: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "original_prompt": prompt_data.get("prompt", "")
                }

        # Process prompts asynchronously
        import asyncio
        tasks = [optimize_single(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing batch item: {str(result)}")
                failed += 1
                results.append({
                    "success": False,
                    "error": str(result),
                    "original_prompt": ""
                })
            else:
                results.append(result)
                if result.get("success"):
                    completed += 1
                else:
                    failed += 1

            # Update job progress if job_id provided
            if job_id:
                db.update_batch_job(
                    job_id,
                    completed_prompts=completed,
                    failed_prompts=failed
                )
            # Call progress callback if provided
            if progress_callback:
                progress_callback(len(prompts), completed, failed)

        return results

    async def create_and_process_batch(
        self,
        prompts: List[Dict[str, Any]],
        user_id: Optional[int] = None,
        name: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> Optional[BatchJob]:
        """
        Create a batch job and process it.
        
        Args:
            prompts: List of prompt dictionaries
            user_id: User ID
            name: Optional job name
            
        Returns:
            BatchJob object
        """
        try:
            # Create batch job
            prompts_json = json.dumps(prompts)
            job = db.create_batch_job(user_id, prompts_json, name)

            if not job:
                logger.error("Failed to create batch job")
                return None

            # Update status to processing
            db.update_batch_job(job.id, status="processing")

            # Process batch
            results = await self.optimize_batch(prompts, user_id, job.id, progress_callback)

            # Save results
            results_json = json.dumps(results)
            db.update_batch_job(
                job.id,
                status="completed",
                results_json=results_json
            )

            # Refresh job
            db_session = db.get_session()
            db_session.refresh(job)
            db_session.close()

            return job
        except Exception as e:
            logger.error(f"Error creating and processing batch: {str(e)}")
            if job:
                db.update_batch_job(job.id, status="failed")
            return None
