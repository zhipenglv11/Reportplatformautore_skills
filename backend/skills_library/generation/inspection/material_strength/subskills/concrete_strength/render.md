# Render Specification: 混凝土强度检测描述

skill: concrete_strength
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
      description: 检测结果（强度值、等级、碳化深度）
    - name: code_ref
      order: 3
      description: 规范依据

# ==================== 内容规则 ====================

content_rules:
  
  # 检测概述
  overview:
    templates:
      default: |
        采用{test_method}对现场混凝土强度进行检测，共检测{test_count}个构件。
  
  # 检测结果
  results:
    conditions:
      - if: strength_grade and carbonation_depth
        template: full_with_carbonation
      - if: strength_grade
        template: full_without_carbonation
      - if: strength_range
        template: range_based
      - default: true
        template: simple
    
    templates:
      full_with_carbonation: |
        检测结果表明，混凝土强度推定值在{strength_range.min}~{strength_range.max}MPa之间，平均值为{avg_strength}MPa，设计强度等级为{strength_grade}。碳化深度平均值为{carbonation_depth}mm。
      
      full_without_carbonation: |
        检测结果表明，混凝土强度推定值为{avg_strength}MPa，设计强度等级为{strength_grade}。
      
      range_based: |
        混凝土强度检测结果显示，各检测构件强度推定值在{strength_range.min}~{strength_range.max}MPa之间，平均值为{avg_strength}MPa。
      
      simple: |
        混凝土强度检测结果为{avg_strength}MPa。
  
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

# ==================== 数值格式 ====================

number_formatting:
  strength_value:
    decimal_places: 1
    unit: MPa
  carbonation_depth:
    decimal_places: 1
    unit: mm

# ==================== 示例输出 ====================

examples:
  example_1:
    input:
      test_method: 回弹法
      test_count: 5
      strength_range: {min: 25.8, max: 31.2}
      avg_strength: 28.5
      strength_grade: C25
      carbonation_depth: 2.3
    
    output: |
      采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，混凝土强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25。碳化深度平均值为2.3mm。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。
