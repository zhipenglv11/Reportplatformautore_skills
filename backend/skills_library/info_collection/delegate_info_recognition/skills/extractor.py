"""
Delegate Info Extractor
"""

from typing import Any
from .schema import DelegateInfoSchema, get_json_schema
from .prompt import get_system_prompt, get_extraction_prompt
from .utils import clean_extracted_data, validate_json_output


class DelegateInfoExtractor:
    def __init__(self):
        self.system_prompt = get_system_prompt()
        self.extraction_prompt = get_extraction_prompt()
        self.json_schema = get_json_schema()

    def extract_from_image(self, image_path: str, model_client: Any) -> DelegateInfoSchema:
        try:
            response = model_client.extract(
                image_path=image_path,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self.extraction_prompt},
                ],
                json_schema=self.json_schema,
            )

            ok, data, error = validate_json_output(response)
            if not ok:
                return DelegateInfoSchema(source_file=image_path, status="error", notes=f"JSON????: {error}")

            cleaned = clean_extracted_data(data)
            schema = DelegateInfoSchema.from_dict(cleaned)
            schema.source_file = image_path
            return schema
        except Exception as e:
            return DelegateInfoSchema(source_file=image_path, status="error", notes=f"????: {e}")
