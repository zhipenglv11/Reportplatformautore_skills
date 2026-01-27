"""
Structure Damage and Alterations Extractor
结构损伤及拆改检查数据抽取器
"""

import json
from typing import Optional, Dict, Any
from pathlib import Path

from .schema import StructureAlterationSchema, MetaData, ItemData, SignoffData, get_json_schema
from .prompt import get_system_prompt, get_extraction_prompt
from .utils import clean_extracted_data, validate_json_output


class StructureAlterationExtractor:
    """结构损伤及拆改检查数据抽取器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化抽取器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.system_prompt = get_system_prompt()
        self.extraction_prompt = get_extraction_prompt()
        self.json_schema = get_json_schema()
    
    def extract_from_image(self, image_path: str, model_client: Any) -> StructureAlterationSchema:
        """
        从图片中提取数据
        
        Args:
            image_path: 图片路径
            model_client: 模型客户端(Qwen或Claude)
            
        Returns:
            提取结果
        """
        try:
            # 调用模型提取数据
            response = self._call_model(image_path, model_client)
            
            # 解析响应
            schema = self._parse_response(response, image_path)
            
            return schema
            
        except Exception as e:
            # 返回错误状态的schema
            schema = StructureAlterationSchema(
                source_file=str(image_path),
                status="error",
                notes=f"提取失败: {str(e)}"
            )
            return schema
    
    def extract_from_pdf(self, pdf_path: str, model_client: Any, 
                        pdf_processor: Any) -> list[StructureAlterationSchema]:
        """
        从PDF中提取数据
        
        Args:
            pdf_path: PDF路径
            model_client: 模型客户端
            pdf_processor: PDF处理器
            
        Returns:
            提取结果列表(每页一个)
        """
        results = []
        
        try:
            # 将PDF转换为图片
            images = pdf_processor.convert_pdf_to_images(pdf_path)
            
            # 逐页提取
            for idx, image_path in enumerate(images):
                schema = self.extract_from_image(image_path, model_client)
                schema.source_file = f"{pdf_path} (page {idx + 1})"
                results.append(schema)
            
            return results
            
        except Exception as e:
            # 返回错误状态
            schema = StructureAlterationSchema(
                source_file=str(pdf_path),
                status="error",
                notes=f"PDF处理失败: {str(e)}"
            )
            return [schema]
    
    def _call_model(self, image_path: str, model_client: Any) -> str:
        """
        调用模型进行提取
        
        Args:
            image_path: 图片路径
            model_client: 模型客户端
            
        Returns:
            模型响应文本
        """
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": self.extraction_prompt
            }
        ]
        
        # 调用模型(具体实现依赖于model_client类型)
        response = model_client.extract(
            image_path=image_path,
            messages=messages,
            json_schema=self.json_schema
        )
        
        return response
    
    def _parse_response(self, response: str, source_file: str) -> StructureAlterationSchema:
        """
        解析模型响应
        
        Args:
            response: 模型响应文本
            source_file: 源文件路径
            
        Returns:
            结构化数据
        """
        # 验证JSON格式
        is_valid, data, error = validate_json_output(response)
        
        if not is_valid:
            return StructureAlterationSchema(
                source_file=source_file,
                status="error",
                notes=f"JSON解析失败: {error}"
            )
        
        # 清洗数据
        cleaned_data = clean_extracted_data(data)
        
        # 构建schema
        schema = StructureAlterationSchema.from_dict(cleaned_data)
        schema.source_file = source_file
        
        return schema
    
    def validate_extraction(self, schema: StructureAlterationSchema) -> tuple[bool, list[str]]:
        """
        验证提取结果
        
        Args:
            schema: 提取的数据
            
        Returns:
            (是否有效, 警告列表)
        """
        warnings = []
        
        # 检查关键字段
        if not schema.meta.control_id:
            warnings.append("缺失控制编号")
        
        if not schema.meta.record_no:
            warnings.append("缺失原始记录编号")
        
        if not schema.items:
            warnings.append("未提取到任何数据项")
        else:
            # 检查每项的关键字段
            for idx, item in enumerate(schema.items):
                if not item.modification_location:
                    warnings.append(f"第{idx+1}项缺失拆改部位")
                
                if not item.modification_description:
                    warnings.append(f"第{idx+1}项缺失拆改内容描述")
        
        is_valid = len(warnings) == 0
        
        return is_valid, warnings
    
    def export_to_json(self, schema: StructureAlterationSchema, 
                      output_path: str) -> None:
        """
        导出为JSON文件
        
        Args:
            schema: 提取的数据
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema.to_dict(), f, ensure_ascii=False, indent=2)
    
    def export_to_dict(self, schema: StructureAlterationSchema) -> Dict[str, Any]:
        """
        导出为字典
        
        Args:
            schema: 提取的数据
            
        Returns:
            字典格式的数据
        """
        return schema.to_dict()
