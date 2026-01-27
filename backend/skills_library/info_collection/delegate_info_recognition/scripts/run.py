"""
Main Run Script
"""

import logging
from .config import Config
from .batch_process import process_batch_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(args):
    config = Config()
    is_valid, errors = config.validate()
    if not is_valid:
        for error in errors:
            print(error)
        return 1

    model = args.model if args.model else config.default_model

    try:
        stats = process_batch_files(
            file_paths=args.files,
            model=model,
            config=config,
            output_dir=args.output,
            output_format=args.format,
        )
        return 1 if stats.get('error', 0) > 0 else 0
    except Exception as e:
        print(f"Processing failed: {e}")
        return 1
