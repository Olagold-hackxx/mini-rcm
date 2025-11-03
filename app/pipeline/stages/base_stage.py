"""Abstract base class for pipeline stages."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseStage(ABC):
    """Base class for all pipeline stages."""

    @abstractmethod
    async def execute(self, data: Any) -> Any:
        """
        Execute the stage processing.
        
        Args:
            data: Input data for the stage
            
        Returns:
            Processed data
        """
        pass

    def _log_stage_start(self, stage_name: str):
        """Log stage start."""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(f"Starting stage: {stage_name}")

    def _log_stage_complete(self, stage_name: str, result_count: int = None):
        """Log stage completion."""
        from utils.logger import get_logger
        logger = get_logger(__name__)
        if result_count is not None:
            logger.info(f"Completed stage: {stage_name} - Processed {result_count} items")
        else:
            logger.info(f"Completed stage: {stage_name}")

