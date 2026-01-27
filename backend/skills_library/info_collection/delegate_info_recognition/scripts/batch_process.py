"""
Batch processing for Delegate Info Check
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from .config import Config
from .qwen_client import QwenClient
from .pdf_processor import PDFProcessor
from .formatter import Formatter
from skills.extractor import DelegateInfoExtractor


def process_single_file(file_path: str, model: str, config: Config):
    pdf_processor = PDFProcessor(poppler_path=config.poppler_path, temp_dir=str(config.temp_dir))
    model_config = config.get_model_config(model)

    if model == 'qwen':
        model_client = QwenClient(
            api_key=model_config['api_key'],
            model=model_config['model_name'],
            max_retries=model_config['max_retries'],
            timeout=model_config['timeout'],
        )
    else:
        raise NotImplementedError(f"Model {model} not implemented")

    extractor = DelegateInfoExtractor()

    results = []
    if pdf_processor.is_pdf(file_path):
        images = pdf_processor.convert_pdf_to_images(file_path)
        for idx, image_path in enumerate(images):
            schema = extractor.extract_from_image(image_path, model_client)
            schema.source_file = f"{file_path} (page {idx + 1})"
            results.append(schema)
    elif pdf_processor.is_image(file_path):
        schema = extractor.extract_from_image(file_path, model_client)
        results.append(schema)
    else:
        from skills.schema import DelegateInfoSchema
        schema = DelegateInfoSchema(source_file=file_path, status="error", notes="Unsupported file type")
        results.append(schema)

    return results


def process_batch_files(file_paths: List[str], model: str, config: Config,
                        output_dir: Optional[str] = None,
                        output_format: str = 'json') -> Dict[str, Any]:
    output_dir = Path(output_dir or str(config.output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'total': len(file_paths),
        'success': 0,
        'error': 0,
        'warnings': []
    }

    per_file_results: list[tuple[str, list]] = []

    for file_path in file_paths:
        try:
            results = process_single_file(file_path, model, config)
            per_file_results.append((file_path, results))

            for result in results:
                if result.status == 'success':
                    stats['success'] += 1
                else:
                    stats['error'] += 1
                    if result.notes:
                        stats['warnings'].append(f"{file_path}: {result.notes}")

            # Save per-file outputs
            base_name = Path(file_path).stem
            Formatter.to_json([r.to_dict() for r in results], str(output_dir / f"{base_name}.json"))
        except Exception as e:
            stats['error'] += 1
            stats['warnings'].append(f"{file_path}: {e}")

    # Brick-compatible report
    report_entries: list[dict[str, Any]] = []
    for file_path, results in per_file_results:
        success = any(r.status == "success" for r in results)
        data_items = [r.to_dict() for r in results if r.status == "success"]
        error_notes = [r.notes for r in results if r.status != "success" and r.notes]
        report_entries.append(
            {
                "file": file_path,
                "success": success,
                "type": None,
                "data": data_items,
                "error": "; ".join(error_notes) if error_notes else None,
            }
        )

    report_path = output_dir / "processing_report.json"
    Formatter.to_json(report_entries, str(report_path))

    return stats
