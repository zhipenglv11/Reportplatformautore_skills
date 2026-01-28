# Render Specification: 砌体砖强度检测描述

skill: brick_strength
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
  
  # 检测概述（注意：砌体砖用"部位"而非"构件"）
  overview:
    templates:
      default: |
        砌体砖采用{test_method}检测，检测{test_count}个部位。
  
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
        砖强度推定值在{strength_range.min}~{strength_range.max}MPa之间，平均值为{avg_strength}MPa。
      
      simple: |
        砖强度推定值为{avg_strength}MPa。
  
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
        default: "GB/T 50315-2011、GB 50003-2011"

# ==================== 数值格式化规则 ====================

number_formatting:
  strength_value:
    decimal_places: 1
    unit: MPa
    example: "8.5MPa"

# ==================== 示例输出 ====================

examples:
  
  # 示例1：有强度等级
  example_with_grade:
    input:
      test_method: 回弹法
      test_count: 3
      avg_strength: 8.5
      strength_grade: MU10
      code_reference: [GB/T 50315-2011]
    
    output: |
      砌体砖采用回弹法检测，检测3个部位，强度等级推定为MU10，强度推定值为8.5MPa。
      相关检测及结果判定依据GB/T 50315-2011执行。
  
  # 示例2：有强度范围
  example_with_range:
    input:
      test_method: 回弹法
      test_count: 5
      strength_range: {min: 7.2, max: 9.8}
      avg_strength: 8.3
      code_reference: [GB/T 50315-2011, GB 50003-2011]
    
    output: |
      砌体砖采用回弹法检测，检测5个部位。砖强度推定值在7.2~9.8MPa之间，平均值为8.3MPa。
      相关检测及结果判定依据GB/T 50315-2011、GB 50003-2011执行。
