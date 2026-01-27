"""
Mortar Strength Data Extractor
砂浆强度数据抽取器

Main extraction logic for mortar strength inspection data.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .schema import MortarSchema
from .prompt import (
    get_system_prompt,
    get_extraction_prompt,
    get_validation_prompt
)
from .utils import validate_extraction, clean_json_response


logger = logging.getLogger(__name__)


class MortarExtractor:
    """
    Extractor for mortar strength inspection data.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the extractor.
        
        Args:
            llm_client: LLM client instance (Claude or Qwen)
        """
        self.llm_client = llm_client
        self.schema = MortarSchema
        
    def extract(
        self, 
        image_path: str,
        validate: bool = True,
        retry_on_error: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Extract structured data from mortar strength inspection image.
        
        Args:
            image_path: Path to the image file
            validate: Whether to validate the extracted data
            retry_on_error: Whether to retry on extraction errors
            max_retries: Maximum number of retries
            
        Returns:
            Extracted data as dictionary
            
        Raises:
            ValueError: If extraction fails after all retries
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")
        
        # Get prompts
        system_prompt = get_system_prompt()
        field_descriptions = self.schema.get_field_descriptions()
        extraction_prompt = get_extraction_prompt(field_descriptions)
        
        # Attempt extraction with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Extraction attempt {attempt + 1}/{max_retries}")
                
                # Call LLM for extraction
                response = self.llm_client.extract(
                    image_path=image_path,
                    system_prompt=system_prompt,
                    user_prompt=extraction_prompt
                )
                
                # Clean and parse response
                cleaned_response = clean_json_response(response)
                extracted_data = json.loads(cleaned_response)
                
                # Validate if requested
                if validate:
                    validation_result = validate_extraction(
                        extracted_data,
                        self.schema
                    )
                    
                    if not validation_result['valid']:
                        if retry_on_error and attempt < max_retries - 1:
                            logger.warning(
                                f"Validation failed: {validation_result['errors']}"
                            )
                            continue
                        else:
                            extracted_data['validation_errors'] = validation_result['errors']
                
                logger.info("Extraction successful")
                return extracted_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                if not retry_on_error or attempt == max_retries - 1:
                    raise ValueError(f"Failed to parse extraction result: {e}")
                    
            except Exception as e:
                logger.error(f"Extraction error: {e}")
                if not retry_on_error or attempt == max_retries - 1:
                    raise ValueError(f"Extraction failed: {e}")
        
        raise ValueError("Extraction failed after all retries")
    
    def extract_batch(
        self,
        image_paths: List[str],
        validate: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract data from multiple images in batch.
        
        Args:
            image_paths: List of image file paths
            validate: Whether to validate extracted data
            **kwargs: Additional arguments for extract()
            
        Returns:
            List of extracted data dictionaries
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
            
            try:
                result = self.extract(
                    image_path=image_path,
                    validate=validate,
                    **kwargs
                )
                result['source_file'] = image_path
                result['status'] = 'success'
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                results.append({
                    'source_file': image_path,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the extraction schema.
        
        Returns:
            Dictionary with schema information
        """
        return {
            'fields': self.schema.get_field_names(),
            'required_fields': self.schema.get_required_fields(),
            'field_descriptions': self.schema.get_field_descriptions()
        }
