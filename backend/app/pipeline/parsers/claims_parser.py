"""Parser for claims files (CSV/Excel)."""
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from app.utils.logger import get_logger
from app.utils.error_handler import FileProcessingError

logger = get_logger(__name__)


class ClaimsParser:
    """Parse claims from CSV or Excel files."""

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        Parse claims file into DataFrame.
        
        Args:
            file_path: Path to the claims file
            
        Returns:
            DataFrame with claims data
        """
        path = Path(file_path)
        
        try:
            if path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            elif path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            else:
                raise FileProcessingError(
                    f"Unsupported file format: {path.suffix}",
                    error_code="UNSUPPORTED_FORMAT"
                )
            
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            
            logger.info(f"Parsed {len(df)} claims from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {str(e)}")
            raise FileProcessingError(
                f"Failed to parse file: {str(e)}",
                error_code="PARSE_ERROR"
            ) from e

    def to_dict_list(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to list of dictionaries."""
        return df.to_dict("records")

