"""
Main Run Script
主运行脚本
"""

import sys
from pathlib import Path
from .config import Config
from .batch_process import process_batch_files


def main(args):
    """
    主函数
    
    Args:
        args: 命令行参数
    """
    # 加载配置
    config = Config()
    
    # 验证配置
    is_valid, errors = config.validate()
    if not is_valid:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # 确定使用的模型
    model = args.model if args.model else config.default_model
    
    print(f"使用模型: {model}")
    print(f"输出目录: {args.output}")
    print(f"输出格式: {args.format}\n")
    
    # 处理文件
    try:
        stats = process_batch_files(
            file_paths=args.files,
            model=model,
            config=config,
            output_dir=args.output,
            output_format=args.format
        )
        
        # 根据结果设置退出码
        if stats['error'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\n处理过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    print("请通过 parse.py 运行此脚本")
    sys.exit(1)
