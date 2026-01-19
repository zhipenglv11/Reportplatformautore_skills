import json
import sys
import os

def validate_json(file_path):
    # Load schema
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output_schema.json')
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found at {schema_path}")
        return False

    # Load output file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to load JSON file {file_path}. {str(e)}")
        return False

    # Simple validation (You can use 'jsonschema' library if installed, but here we do manual check for portability)
    errors = []
    
    # Check overall_status
    if "overall_status" not in data:
        errors.append("Missing field: overall_status")
    elif data["overall_status"] not in schema["properties"]["overall_status"]["enum"]:
        errors.append(f"Invalid overall_status: {data.get('overall_status')}")

    # Check issues
    if "issues" not in data:
        errors.append("Missing field: issues")
    elif not isinstance(data["issues"], list):
        errors.append("Field 'issues' must be a list")
    else:
        for idx, issue in enumerate(data["issues"]):
            required_fields = ["issue_type", "severity", "page", "fix_suggestion"]
            for field in required_fields:
                if field not in issue:
                    errors.append(f"Issue #{idx} missing field: {field}")
            
            if "issue_type" in issue and issue["issue_type"] not in schema["properties"]["issues"]["items"]["properties"]["issue_type"]["enum"]:
                errors.append(f"Issue #{idx} has invalid issue_type: {issue['issue_type']}")

    if errors:
        print("Validation Failed:")
        for err in errors:
            print(f"- {err}")
        return False
    else:
        print("Validation Passed!")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <path_to_output.json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = validate_json(file_path)
    if not success:
        sys.exit(1)
