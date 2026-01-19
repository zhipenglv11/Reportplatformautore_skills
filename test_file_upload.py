#!/usr/bin/env python3
"""
测试文件上传到混凝土表格识别技能
使用方法: python test_file_upload.py <文件路径> [--format json|csv|excel] [--output-dir <目录>]
"""

import argparse
import requests
import json
from pathlib import Path
from datetime import datetime


def test_file_upload(file_path: str, format: str = "json", output_dir: str = None, api_url: str = "http://localhost:8000"):
    """上传文件并测试混凝土表格识别技能"""
    
    # 检查文件是否存在
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ 错误: 文件不存在: {file_path}")
        return False
    
    print(f"📁 准备上传文件: {file_path}")
    print(f"📋 格式: {format}")
    
    # 准备表单数据
    url = f"{api_url}/api/skill/concrete-table-recognition"
    files = {
        'file': (file_path_obj.name, open(file_path, 'rb'), 'application/pdf')
    }
    data = {
        'format': format
    }
    if output_dir:
        data['output_dir'] = output_dir
    
    try:
        print("\n🚀 正在上传并处理文件...")
        
        response = requests.post(url, files=files, data=data, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        
        print("\n✅ 处理成功！")
        print("\n📊 结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 保存结果到文件
        output_file = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存到: {output_file}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 错误: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"详细信息: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
            except:
                print(f"响应内容: {e.response.text}")
        return False
    finally:
        files['file'][1].close()


def main():
    parser = argparse.ArgumentParser(description='测试文件上传到混凝土表格识别技能')
    parser.add_argument('file_path', help='要上传的文件路径')
    parser.add_argument('--format', choices=['json', 'csv', 'excel'], default='json',
                        help='输出格式 (默认: json)')
    parser.add_argument('--output-dir', help='输出目录（可选）')
    parser.add_argument('--api-url', default='http://localhost:8000',
                        help='API 服务器地址 (默认: http://localhost:8000)')
    
    args = parser.parse_args()
    
    success = test_file_upload(
        file_path=args.file_path,
        format=args.format,
        output_dir=args.output_dir,
        api_url=args.api_url
    )
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
