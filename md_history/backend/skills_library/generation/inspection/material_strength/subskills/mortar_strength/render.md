# Render Specification: 砂浆强度检测描述

skill: mortar_strength
version: 1.0.0

# ==================== 写作风格 ====================

writing_style:
  tone: 客观、专业
  voice: 陈述式
  forbidden_phrases: [安全, 危险, 符合要求, 不符合要求, 合格, 不合格]
  preferred_phrases: [检测结果表明, 强度推定值为, 依据××规范]

# ==================== 结构 ====================

structure:
  sections:
    - name: overview
      order: 1
      description: 检测概述（方法、数量）
    - name: results
      order: 2
      description: 检测结果（强度值、等级）
    - name: code_ref
      order: 3
      description: 规范依据

# ==================== 内容规则 ====================

content_rules:
  
  # 检测概述（注意：砂浆用"测点"而非"构件"或"部位"）
  overview:
    templates:
      default: |
        砂浆强度采用{test_method}检测，检测{test_count}个测点。
  
  # 检测结果
  results:
    conditions:
      - if: strength_grade
        template: with_grade
      - if: strength_range
        template: range_based
      - default: true
        template: simple
    
    templates:
      with_grade: |
        强度等级推定为{strength_grade}，强度推定值为{avg_strength}MPa。
      
      range_based: |
        砂浆强度推定值在{strength_range.min}~{strength_range.max}MPa之间，平均值为{avg_strength}MPa。
      
      simple: |
        强度推定值为{avg_strength}MPa。
  
  # 规范依据
  code_ref:
    templates:
      default: |
        相关检测及结果判定依据{code_list}执行。
    
    variables:
      code_list:
        type: natural_language_list
        source: code_reference
        connector: "、"
        default: "JGJ/T 70-2009"

# ==================== 数值格式化规则 ====================

number_formatting:
  strength_value:
    decimal_places: 1
    unit: MPa
    example: "5.2MPa"

# ==================== 示例输出 ====================

examples:
  
  # 示例1：有强度等级
  example_with_grade:
    input:
      test_method: 回弹法
      test_count: 6
      avg_strength: 5.2
      strength_grade: M5.0
      code_reference: [JGJ/T 70-2009]
    
    output: |
      砂浆强度采用回弹法检测，检测6个测点，强度等级推定为M5.0，强度推定值为5.2MPa。
      相关检测及结果判定依据JGJ/T 70-2009执行。
  
  # 示例2：有强度范围
  example_with_range:
    input:
      test_method: 回弹法
      test_count: 8
      strength_range: {min: 4.8, max: 6.5}
      avg_strength: 5.5
      code_reference: [JGJ/T 70-2009]
    
    output: |
      砂浆强度采用回弹法检测，检测8个测点。砂浆强度推定值在4.8~6.5MPa之间，平均值为5.5MPa。
      相关检测及结果判定依据JGJ/T 70-2009执行。
