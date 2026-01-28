# Render Specification: 材料强度检测描述
# 定义如何将结构化数据转换为专业的技术报告文字

skill: material_strength_description
version: 1.0.0

# ==================== 写作风格 ====================

writing_style:
  language: 中文
  tone: 客观、专业
  voice: 第三人称、陈述式
  register: 工程技术报告语体
  
  forbidden_phrases:
    - 安全 / 危险 / 不安全
    - 符合要求 / 不符合要求（除非有明确判定依据）
    - 合格 / 不合格（这是结论章节的职责）
    - 良好 / 较差 / 优秀（主观评价词）
    - 可能 / 大概 / 估计（不确定表述）
  
  preferred_phrases:
    - 检测结果表明
    - 根据检测数据
    - 强度推定值为
    - 依据××规范
    - 检测方法为

# ==================== 章节结构 ====================

structure:
  type: sequential
  sections:
    
    # 第1部分：检测概述
    - name: overview
      required: true
      order: 1
      content_type: summary
      description: 说明检测对象、方法、数量
      
    # 第2部分：检测结果（按材料类型分组）
    - name: results_by_material
      required: true
      order: 2
      content_type: data_presentation
      grouping: by_material_type
      description: 逐一描述各类材料的检测结果
      
    # 第3部分：规范依据
    - name: code_reference
      required: true
      order: 3
      content_type: reference
      description: 说明检测和判定依据的规范

# ==================== 内容生成规则 ====================

content_rules:
  
  # ---------- 检测概述部分 ----------
  overview:
    conditions:
      - if: material_types.length == 1
        template: "single_material"
      - if: material_types.length > 1
        template: "multiple_materials"
      - if: test_count == 0
        template: "no_test"
    
    templates:
      single_material: |
        采用{test_method}对现场{material_type}强度进行检测，共检测{test_count}个{unit_name}。
      
      multiple_materials: |
        现场材料强度检测采用{test_method}，共检测{material_types_list}等材料，
        合计{total_count}个检测点。
      
      no_test: |
        本次检测未对材料强度进行检测。
    
    variables:
      unit_name:
        rules:
          - if: material_type == "混凝土"
            value: "构件"
          - if: material_type in ["砌体砖", "砌块"]
            value: "部位"
          - if: material_type == "砂浆"
            value: "测点"
      
      material_types_list:
        type: natural_language_list
        source: material_types
        example: "混凝土、砌体砖"
  
  # ---------- 检测结果部分 ----------
  results_by_material:
    grouping_strategy: by_material_type
    
    # 混凝土材料的描述模板
    concrete_template:
      conditions:
        - if: strength_grade is not None and carbonation_depth is not None
          template: "full_with_carbonation"
        - if: strength_grade is not None
          template: "full_without_carbonation"
        - if: strength_range is not None
          template: "range_based"
        - default: true
          template: "simple"
      
      templates:
        full_with_carbonation: |
          检测结果表明，混凝土强度推定值在{strength_range.min}~{strength_range.max}MPa之间，
          平均值为{avg_strength}MPa，设计强度等级为{strength_grade}。
          碳化深度平均值为{carbonation_depth}mm。
        
        full_without_carbonation: |
          检测结果表明，混凝土强度推定值为{avg_strength}MPa，
          设计强度等级为{strength_grade}。
        
        range_based: |
          混凝土强度检测结果显示，各检测构件强度推定值在{strength_range.min}~{strength_range.max}MPa之间，
          平均值为{avg_strength}MPa。
        
        simple: |
          混凝土强度检测结果为{avg_strength}MPa。
    
    # 砌体材料的描述模板
    masonry_template:
      conditions:
        - if: strength_grade is not None
          template: "with_grade"
        - default: true
          template: "simple"
      
      templates:
        with_grade: |
          砌体{material_type}采用{test_method}检测，检测{test_count}个部位，
          强度等级推定为{strength_grade}，强度推定值为{avg_strength}MPa。
        
        simple: |
          砌体{material_type}强度检测结果，强度推定值为{avg_strength}MPa。
    
    # 砂浆材料的描述模板
    mortar_template:
      templates:
        default: |
          砂浆强度采用{test_method}检测，检测{test_count}个测点，
          强度推定值为{avg_strength}MPa。
  
  # ---------- 规范依据部分 ----------
  code_reference:
    conditions:
      - if: code_reference.length > 0
        template: "with_codes"
      - default: true
        template: "generic"
    
    templates:
      with_codes: |
        相关检测及结果判定依据{code_list}执行。
      
      generic: |
        检测方法和结果判定依据国家相关规范执行。
    
    variables:
      code_list:
        type: natural_language_list
        source: code_reference
        connector: "、"
        example: "JGJ/T 23-2011、GB 50010-2010"

# ==================== 数值格式化规则 ====================

number_formatting:
  strength_value:
    decimal_places: 1
    unit: MPa
    unit_position: after
    space_before_unit: false
    example: "28.5MPa"
  
  carbonation_depth:
    decimal_places: 1
    unit: mm
    unit_position: after
    space_before_unit: false
    example: "2.3mm"
  
  test_count:
    type: integer
    chinese_number_below: 10  # 10以下用中文数字
    example: "五个构件" # 如果count=5

# ==================== 条件逻辑 ====================

conditional_logic:
  
  # 当没有设计强度等级时，不提及"设计强度"
  - condition: strength_grade is None
    action: omit_phrase
    phrases: ["设计强度等级", "设计强度"]
  
  # 当只有一个检测点时，不提及"平均值"
  - condition: test_count == 1
    action: replace
    from: "平均值为"
    to: "强度推定值为"
  
  # 当碳化深度缺失时，不单独说明碳化深度
  - condition: carbonation_depth is None
    action: omit_section
    section: carbonation_description
  
  # 当检测日期缺失时，不单独说明检测日期
  - condition: test_date is None
    action: omit_phrase
    phrases: ["检测日期为", "于××日"]

# ==================== 句式范式（Sentence Patterns） ====================

sentence_patterns:
  
  # 开头句式（引出检测方法）
  opening:
    - "采用{method}对{object}进行检测……"
    - "现场{object}采用{method}检测……"
    - "{object}强度检测采用{method}……"
  
  # 结果陈述句式
  result_presentation:
    - "检测结果表明，{object}强度推定值为{value}……"
    - "根据检测数据，{object}强度为{value}……"
    - "{object}强度检测结果显示，强度推定值{value}……"
  
  # 范围描述句式
  range_description:
    - "强度推定值在{min}~{max}{unit}之间"
    - "各检测点强度值范围为{min}~{max}{unit}"
  
  # 规范引用句式
  code_citation:
    - "相关检测及结果判定依据{codes}执行"
    - "检测方法依据{codes}进行"
    - "按照{codes}的要求进行检测和判定"

# ==================== 示例输出 ====================

examples:
  
  # 示例1：混凝土单一材料，完整信息
  example_1:
    input:
      material_type: 混凝土
      test_method: 回弹法
      test_count: 5
      strength_range: {min: 25.8, max: 31.2}
      avg_strength: 28.5
      strength_grade: C25
      carbonation_depth: 2.3
      code_reference: [JGJ/T 23-2011, GB 50010-2010]
    
    output: |
      采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，
      混凝土强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25。
      碳化深度平均值为2.3mm。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。
  
  # 示例2：砌体砖，有强度等级
  example_2:
    input:
      material_type: 砌体砖
      test_method: 回弹法
      test_count: 3
      avg_strength: 8.5
      strength_grade: MU10
      code_reference: [GB/T 50315-2011]
    
    output: |
      砌体砖采用回弹法检测，检测3个部位，强度等级推定为MU10，
      强度推定值为8.5MPa。相关检测及结果判定依据GB/T 50315-2011执行。
  
  # 示例3：混凝土+砌体，多材料
  example_3:
    input:
      materials:
        - material_type: 混凝土
          avg_strength: 28.5
          test_count: 5
        - material_type: 砌体砖
          avg_strength: 8.5
          test_count: 3
      test_method: 回弹法
      code_reference: [JGJ/T 23-2011, GB/T 50315-2011]
    
    output: |
      现场材料强度检测采用回弹法，共检测混凝土、砌体砖等材料，合计8个检测点。
      混凝土强度检测结果显示，各检测构件强度推定值平均值为28.5MPa。
      砌体砖强度检测结果，强度推定值为8.5MPa。
      相关检测及结果判定依据JGJ/T 23-2011、GB/T 50315-2011执行。

# ==================== 生成策略 ====================

generation_strategy:
  
  # LLM提示词构建策略
  prompt_construction:
    system_role: |
      你是建筑工程质量检测领域的专业技术人员，负责撰写结构安全鉴定报告中的
      材料强度检测章节。你的写作必须客观、准确、符合工程技术规范。
    
    user_instruction: |
      请根据以下检测数据，生成"材料强度检测情况"章节内容。
      
      要求：
      1. 使用工程技术报告语体，客观陈述
      2. 不做安全性或符合性结论
      3. 数值精度保留1位小数
      4. 必须注明检测方法和规范依据
      5. 按"检测概述→检测结果→规范依据"的结构组织
    
    include_render_rules: true
    include_examples: true
  
  # 后处理规则
  post_processing:
    - remove_redundant_spaces
    - check_punctuation
    - validate_number_format
    - verify_code_references

# ==================== 质量检查 ====================

quality_checks:
  
  # 必须包含的关键信息
  required_elements:
    - test_method
    - material_type
    - strength_value
    - code_reference
  
  # 禁止出现的内容
  forbidden_content:
    - pattern: "(安全|危险|合格|不合格)"
      severity: error
      message: 不得出现结论性判断
    
    - pattern: "(可能|大概|估计|推测)"
      severity: warning
      message: 避免不确定表述
  
  # 格式检查
  format_checks:
    - type: number_precision
      field: strength_value
      expected_decimal: 1
    
    - type: unit_consistency
      field: strength_value
      expected_unit: MPa
    
    - type: paragraph_length
      max_words: 200
      message: 单个段落不宜超过200字
