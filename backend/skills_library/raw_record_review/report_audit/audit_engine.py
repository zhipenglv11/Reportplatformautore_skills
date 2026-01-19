import re
import json
from collections import defaultdict

# --- Configuration & Rules Patterns ---

PATTERNS = {
    # R1: Consistency Entities (Simplistic regex for demonstration - needs tuning for real docs)
    "house_name": r"(?:项目名称|工程名称|房屋名称)[:：]\s*([^\n\r]+)",
    "floors": r"((?:地上|地下|共))\s*(\d+)\s*层", # Captures fragments like "地上", "3"
    "area": r"(\d+(?:\.\d+)?)\s*(?:m2|㎡|平方米)",
    "build_year": r"(\d{4})\s*年(?:建成|左右|上下)",
    
    # R2: Numeric Targets
    # Note: These regexes look for [Label] + [number]
    # Added (?<![a-zA-Z]) to avoid matching labels like C1, M1 as values.
    "mortar_strength": r"(?:砂浆|砌筑砂浆)抗压强度(?:换算|推定)值.*?(?<![a-zA-Z])(\d+(?:\.\d+)?)",
    "brick_strength": r"(?:烧结|普通)砖抗压强度(?:推定)值.*?(?<![a-zA-Z])(\d+(?:\.\d+)?)",
    "concrete_strength": r"(?:混凝土|砼)抗压强度(?:推定)值.*?(?<![a-zA-Z])(\d+(?:\.\d+)?)",
    "carbonation_depth": r"(?:碳化深度)(?:平均|实测)值.*?(?<![a-zA-Z])(\d+(?:\.\d+)?)"
}

# --- Helper Functions ---

def find_locations(text, pattern_key, pattern_str):
    """
    Finds all occurrences of a pattern and records their approximate location.
    Retuns list of dicts: {value: str, context: str, index: int}
    """
    matches = []
    # Use DOTALL to allow matching across newlines (common in tables/lists)
    # But be careful with greedy matching in patterns
    for match in re.finditer(pattern_str, text, re.IGNORECASE | re.DOTALL):
        start = max(0, match.start() - 20)
        end = min(len(text), match.end() + 20)
        context = text[start:end].replace('\n', ' ').strip()
        
        # Determine value.
        # If the regex has multiple groups, we need a strategy.
        # For 'floors', we might capture (Type, Value).
        # For simple fields, we expect just one capturing group for the value.
        
        # Default strategy: Last capturing group is the value, 
        # unless specific handling needed.
        if pattern_key == "floors":
            # pattern: ((?:地上|地下|共))\s*(\d+)\s*层
            # normalized key becomes "地上" or "地下"
            full_match = match.group(0)
            prefix = match.group(1) if match.lastindex >= 1 else "total"
            val = match.group(2) if match.lastindex >= 2 else match.group(0)
            
            matches.append({
                "sub_key": prefix, # Special field for multi-part consistency
                "value": val.strip(),
                "context": f"...{context}...",
                "index": match.start()
            })
        else:
            # Standard single value capture
            val = match.group(1) if match.lastindex else match.group(0)
            matches.append({
                "value": val.strip(),
                "context": f"...{context}...",
                "index": match.start()
            })

    return matches

def is_decimal_places(value_str, places=1):
    if '.' not in value_str:
        return False
    decimals = value_str.split('.')[1]
    return len(decimals) == places

def is_multiple_of_0_5(value_float):
    # Tolerance for float math
    x2 = value_float * 2
    return abs(x2 - round(x2)) < 1e-6

# --- Check Logic ---

def check_consistency(text):
    results = []
    
    # Define what we are checking
    fields = ["house_name", "floors", "area", "build_year"]
    
    extracted_data = {}

    for field in fields:
        matches = find_locations(text, field, PATTERNS[field])
        if not matches:
            continue
            
        # Group by Sub-Key (e.g. "地上" vs "Total") first
        # Structure: grouped_matches[sub_key] -> { value: [match_locations] }
        grouped_checks = defaultdict(lambda: defaultdict(list))
        
        for m in matches:
            sub_key = m.get('sub_key', 'default')
            # Normalize simplisticly (remove spaces)
            norm_val = m['value'].replace(" ", "")
            grouped_checks[sub_key][norm_val].append(m)
            
        # Pick a representative value for the main output profile (just the first valid one)
        # For floors, we might want to combine them, but for now just taking first available.
        first_group = list(grouped_checks.values())[0]
        extracted_data[field] = list(first_group.keys())[0]

        # Check consistency PER Sub-Key
        for sub_key, values_map in grouped_checks.items():
            if len(values_map) > 1:
                # Consistency Failure found in this group
                label = field if sub_key == 'default' else f"{field} ({sub_key})"
                
                detail_locations = []
                for val, locs in values_map.items():
                    for l in locs:
                        detail_locations.append({
                            "quote": f"Found '{val}': {l['context']}",
                            "index": l['index']
                        })
                
                results.append({
                    "check_type": "consistency",
                    "item": label,
                    "rule_id": f"R1-{field}",
                    "status": "fail",
                    "locations": detail_locations,
                    "expected": "Consistent values throughout document",
                    "found": f"Distinct values found: {list(values_map.keys())}",
                    "fix_suggestion": f"Unify to one of: {list(values_map.keys())}",
                    "severity": "major"
                })
    
    return results, extracted_data

def check_formatting(text):
    results = []
    
    # 1. R2-Mortar / Brick / Concrete (Expect 1 decimal)
    one_decimal_types = [
        ("mortar_strength", "R2-mortar"), 
        ("brick_strength", "R2-brick"), 
        ("concrete_strength", "R2-concrete")
    ]
    
    for pat_key, rule_id in one_decimal_types:
        matches = find_locations(text, pat_key, PATTERNS[pat_key])
        for m in matches:
            val_str = m['value']
            # validation
            if not is_decimal_places(val_str, 1):
                results.append({
                    "check_type": "format",
                    "item": pat_key,
                    "rule_id": rule_id,
                    "status": "fail",
                    "locations": [{"quote": m['context']}],
                    "expected": "1 decimal place (e.g., 5.0)",
                    "found": val_str,
                    "fix_suggestion": f"Format {val_str} to 1 decimal place",
                    "severity": "minor"
                })

    # 2. R2-Carbonation (Expect 1 decimal AND multiple of 0.5)
    carb_matches = find_locations(text, "carbonation_depth", PATTERNS["carbonation_depth"])
    for m in carb_matches:
        val_str = m['value']
        try:
            val_float = float(val_str)
        except:
            continue
            
        # Check 1: 0.5 multiple
        if not is_multiple_of_0_5(val_float):
            results.append({
                "check_type": "format",
                "item": "carbonation_depth",
                "rule_id": "R2-carbonation-step",
                "status": "fail",
                "locations": [{"quote": m['context']}],
                "expected": "Multiple of 0.5 (1.0, 1.5...)",
                "found": val_str,
                "fix_suggestion": "Round to nearest 0.5",
                "severity": "major"
            })
            
        # Check 2: 1 decimal place display (independent of value)
        if not is_decimal_places(val_str, 1):
            results.append({
                "check_type": "format",
                "item": "carbonation_depth",
                "rule_id": "R2-carbonation-format",
                "status": "fail",
                "locations": [{"quote": m['context']}],
                "expected": "Display with 1 decimal place",
                "found": val_str,
                "fix_suggestion": "Add/Truncate decimal places",
                "severity": "minor"
            })
            
    return results

# --- Main Entry Point ---

def run_audit(report_text):
    """
    Main function to execute the audit skill.
    """
    
    # 1. Run Consistency Checks
    consistency_issues, house_profile = check_consistency(report_text)
    
    # 2. Run Format Checks
    format_issues = check_formatting(report_text)
    
    all_checks = consistency_issues + format_issues
    
    # Determine overall status
    if any(c['severity'] == 'major' for c in all_checks):
        overall = 'fail'
    elif all_checks:
        overall = 'needs_review'
    else:
        overall = 'pass'
        
    # Generate Summary
    summary = f"Audit complete. Found {len(all_checks)} issues."
    if consistency_issues:
        summary += f" {len(consistency_issues)} consistency errors."
    if format_issues:
        summary += f" {len(format_issues)} formatting errors."
        
    return {
        "overall_status": overall,
        "house_profile": house_profile,
        "checks": all_checks,
        "summary": summary
    }

if __name__ == "__main__":
    # Test with a dummy string if run directly
    sample_text = """
    项目名称：幸福小区1#楼
    鉴定结论：幸福小区1号楼结构安全。
    
    房屋概况：
    地上3层，地下0层。总面积 5000.55m2。建于2008年左右。
    附录：建筑面积 5000.6m2。
    
    检测数据：
    砂浆抗压强度推定值：5.2 （不规范，不是5.0或5.5? 否，只是要保留1位）-> 5.2 ok
    砂浆抗压强度换算值：5  （不规范，应5.0）
    碳化深度平均值：1.3    （不规范，应1.0或1.5，且保留1位）
    """
    print(json.dumps(run_audit(sample_text), indent=2, ensure_ascii=False))
