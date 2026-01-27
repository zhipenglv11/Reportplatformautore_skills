"""
Batch Processing
批处理模块
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from .config import Config
from .qwen_client import QwenClient
from .pdf_processor import PDFProcessor
from .formatter import Formatter
from skills.extractor import StructureAlterationExtractor
from skills.schema import StructureAlterationSchema


def process_single_file(file_path: str, model: str, config: Config) -> List[StructureAlterationSchema]:
    """
    处理单个文件
    
    Args:
        file_path: 文件路径
        model: 模型名称
        config: 配置对象
        
    Returns:
        提取结果列表
    """
    print(f"正在处理: {file_path}")
    
    # 初始化组件
    pdf_processor = PDFProcessor(
        poppler_path=config.poppler_path,
        temp_dir=str(config.temp_dir)
    )
    
    # 获取模型配置
    model_config = config.get_model_config(model)
    
    # 初始化模型客户端
    if model == 'qwen':
        model_client = QwenClient(
            api_key=model_config['api_key'],
            model=model_config['model_name'],
            max_retries=model_config['max_retries'],
            timeout=model_config['timeout']
        )
    else:
        raise NotImplementedError(f"模型 {model} 暂未实现")
    
    # 初始化提取器
    extractor = StructureAlterationExtractor(config=config.__dict__)
    
    # 处理文件
    results = []
    
    if pdf_processor.is_pdf(file_path):
        # PDF文件
        results = extractor.extract_from_pdf(
            pdf_path=file_path,
            model_client=model_client,
            pdf_processor=pdf_processor
        )
    elif pdf_processor.is_image(file_path):
        # 图片文件
        # 验证图片
        is_valid, error = pdf_processor.validate_image(file_path)
        if not is_valid:
            print(f"图片验证失败: {error}")
            schema = StructureAlterationSchema(
                source_file=file_path,
                status="error",
                notes=f"图片验证失败: {error}"
            )
            results = [schema]
        else:
            result = extractor.extract_from_image(
                image_path=file_path,
                model_client=model_client
            )
            results = [result]
    else:
        print(f"不支持的文件类型: {file_path}")
        schema = StructureAlterationSchema(
            source_file=file_path,
            status="error",
            notes="不支持的文件类型"
        )
        results = [schema]
    
    return results


def process_batch_files(file_paths: List[str], model: str, config: Config,
                       output_dir: Optional[str] = None,
                       output_format: str = 'json') -> Dict[str, Any]:
    """
    批量处理文件
    
    Args:
        file_paths: 文件路径列表
        model: 模型名称
        config: 配置对象
        output_dir: 输出目录
        output_format: 输出格式
        
    Returns:
        处理结果统计
    """
    output_dir = output_dir or str(config.output_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    per_file_results: list[tuple[str, list[StructureAlterationSchema]]] = []
    stats = {
        'total': len(file_paths),
        'success': 0,
        'error': 0,
        'warnings': []
    }
    
    # 处理每个文件
    for file_path in file_paths:
        try:
            results = process_single_file(file_path, model, config)
            all_results.extend(results)
            per_file_results.append((file_path, results))
            
            # 统计结果
            for result in results:
                if result.status == 'success':
                    stats['success'] += 1
                else:
                    stats['error'] += 1
                    stats['warnings'].append(f"{file_path}: {result.notes}")
            
            # 保存结果
            file_name = Path(file_path).stem
            save_results(results, output_dir, file_name, output_format)
            
        except Exception as e:
            print(f"处理文件失败 {file_path}: {str(e)}")
            stats['error'] += 1
            stats['warnings'].append(f"{file_path}: {str(e)}")
    
    # 打印统计信息
    print(f"\n处理完成:")
    print(f"- 总文件数: {stats['total']}")
    print(f"- 成功: {stats['success']}")
    print(f"- 失败: {stats['error']}")
    
    if stats['warnings']:
        print(f"\n警告和错误:")
        for warning in stats['warnings']:
            print(f"  - {warning}")

    # Generate report in brick-compatible format
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
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_entries, f, ensure_ascii=False, indent=2)

    return stats


def save_results(results: List[StructureAlterationSchema],
                output_dir: Path, base_name: str,
                output_format: str) -> List[str]:
    """
    保存处理结果
    
    Args:
        results: 提取结果列表
        output_dir: 输出目录
        base_name: 基础文件名
        output_format: 输出格式
        
    Returns:
        保存的文件路径列表
    """
    saved_files = []
    
    if output_format == 'json':
        for i, result in enumerate(results):
            output_path = output_dir / f"{base_name}_{i+1}.json"
            Formatter.to_json(result, str(output_path))
            saved_files.append(str(output_path))
            print(f"  已保存: {output_path}")
    
    elif output_format == 'csv':
        output_path = output_dir / f"{base_name}.csv"
        Formatter.to_csv(results, str(output_path))
        saved_files.append(str(output_path))
        print(f"  已保存: {output_path}")
    
    elif output_format == 'excel':
        output_path = output_dir / f"{base_name}.xlsx"
        Formatter.to_excel(results, str(output_path))
        saved_files.append(str(output_path))
        print(f"  已保存: {output_path}")
    
    elif output_format == 'all':
        output_files = Formatter.format_all(results, str(output_dir), base_name)
        saved_files = list(output_files.values())
        for format_type, file_path in output_files.items():
            print(f"  已保存 ({format_type}): {file_path}")
    
    else:
        raise ValueError(f"不支持的输出格式: {output_format}")
    
    return saved_files
