"""
Main Runner Script
主运行脚本
"""

import sys
import logging
from pathlib import Path

from .config import Config
from .batch_process import batch_process, process_single_file


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mortar_extraction.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main(args):
    """
    Main execution function.
    
    Args:
        args: Command line arguments (from argparse)
    """
    try:
        logger.info("Starting mortar strength extraction")
        
        # Initialize configuration
        config = Config()
        
        # Get output formats
        if args.format == 'all':
            output_formats = ['json', 'csv', 'excel']
        else:
            output_formats = [args.format]
        
        # Process files
        if len(args.files) == 1:
            logger.info(f"Processing single file: {args.files[0]}")
            result = process_single_file(
                file_path=args.files[0],
                output_path=args.output,
                model=getattr(args, 'model', None),
                config=config
            )
            logger.info(f"Result: {result.get('status', 'unknown')}")
        else:
            logger.info(f"Processing {len(args.files)} files in batch")
            result = batch_process(
                file_paths=args.files,
                output_dir=args.output,
                output_formats=output_formats,
                model=getattr(args, 'model', None),
                config=config
            )
            logger.info(
                f"Completed: {result['successful']}/{result['total_processed']} successful"
            )
        
        logger.info("Extraction completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    # For direct execution
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract structured data from mortar strength inspection reports"
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='PDF or image files to process'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='data/output',
        help='Output directory (default: data/output)'
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['json', 'csv', 'excel', 'all'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--model',
        '-m',
        choices=['claude', 'qwen'],
        help='Model to use for extraction (overrides env config)'
    )
    
    args = parser.parse_args()
    sys.exit(main(args))
