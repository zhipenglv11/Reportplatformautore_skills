"""
Batch Processing for Mortar Strength Extraction
批量处理砂浆强度检测数据
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import Config
from .qwen_client import QwenVLClient
from .pdf_processor import PDFProcessor
from .formatter import DataFormatter
from skills.extractor import MortarExtractor


logger = logging.getLogger(__name__)


def batch_process(
    file_paths: List[str],
    output_dir: Optional[str] = None,
    output_formats: List[str] = ['json'],
    model: Optional[str] = None,
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """
    Process multiple files in batch.
    
    Args:
        file_paths: List of file paths (PDF or images)
        output_dir: Output directory (defaults to config output_dir)
        output_formats: List of output formats ('json', 'csv', 'excel')
        model: Model to use ('claude' or 'qwen'), defaults to config
        config: Configuration instance (will create default if not provided)
        
    Returns:
        Dictionary with processing results and output file paths
    """
    # Initialize configuration
    if config is None:
        config = Config()
    
    config.validate()
    
    # Set output directory
    if output_dir is None:
        output_dir = str(config.output_dir)
    
    # Initialize components
    logger.info(f"Initializing with model: {model or config.default_model}")
    
    model_config = config.get_model_config(model)
    
    if model_config['type'] == 'qwen':
        llm_client = QwenVLClient(
            api_key=model_config['api_key'],
            model_name=model_config['model_name'],
            timeout=model_config['timeout']
        )
    else:
        # TODO: Add Claude client support
        raise NotImplementedError("Claude client not yet implemented")
    
    pdf_processor = PDFProcessor(
        poppler_path=config.poppler_path
    )
    
    extractor = MortarExtractor(llm_client=llm_client)
    
    # Process files
    all_image_paths = []
    
    for file_path in file_paths:
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue
        
        # Convert PDF to images if necessary
        if pdf_processor.is_pdf(str(file_path)):
            logger.info(f"Converting PDF: {file_path}")
            image_paths = pdf_processor.pdf_to_images(
                str(file_path),
                output_dir=str(config.temp_dir)
            )
            all_image_paths.extend(image_paths)
        else:
            all_image_paths.append(str(file_path))
    
    logger.info(f"Processing {len(all_image_paths)} images")
    
    # Extract data from all images
    results = extractor.extract_batch(
        image_paths=all_image_paths,
        validate=True,
        retry_on_error=True,
        max_retries=config.max_retries
    )
    
    # Format and save results
    output_files = DataFormatter.format_batch_results(
        results=results,
        output_dir=output_dir,
        formats=output_formats,
        base_name='mortar_strength'
    )
    
    # Generate report in brick-compatible format
    report_entries: list[dict[str, Any]] = []
    for result in results:
        success = result.get("status") == "success"
        report_entries.append(
            {
                "file": result.get("source_file"),
                "success": success,
                "type": None,
                "data": result if success else None,
                "error": None if success else result.get("error"),
            }
        )

    report_path = Path(output_dir) / 'processing_report.json'
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_entries, f, ensure_ascii=False, indent=2)
    output_files['report'] = str(report_path)
    
    logger.info("Batch processing completed")
    
    return {
        'total_processed': len(results),
        'successful': sum(1 for r in results if r.get('status') == 'success'),
        'failed': sum(1 for r in results if r.get('status') == 'error'),
        'output_files': output_files,
        'results': results
    }


def process_single_file(
    file_path: str,
    output_path: Optional[str] = None,
    model: Optional[str] = None,
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """
    Process a single file.
    
    Args:
        file_path: Path to file (PDF or image)
        output_path: Optional output file path
        model: Model to use
        config: Configuration instance
        
    Returns:
        Extraction result dictionary
    """
    result = batch_process(
        file_paths=[file_path],
        output_dir=str(Path(output_path).parent) if output_path else None,
        model=model,
        config=config
    )
    
    if result['results']:
        return result['results'][0]
    else:
        return {'status': 'error', 'error': 'Processing failed'}
