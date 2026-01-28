# Render Specification: 材料强度章节（父Skill）
# 定义如何组装多个子skills的输出

skill: material_strength_description
version: 2.0.0
architecture: parent-child

# ==================== 写作风格 ====================

writing_style:
  tone: 客观、专业
  voice: 陈述式
  note: 父skill不直接生成文字，由子skills负责

# ==================== 章节结构 ====================

structure:
  type: sequential
  description: 按材料类型顺序组织
  
  sections:
    - name: overview
      order: 0
      optional: true
      condition: context.include_overview == true
      description: 总述段落（可选）
    
    - name: material_sections
      order: 1
      required: true
      description: 各材料类型的子段落
      source: subskills

# ==================== 组装规则 ====================

assembly_rules:
  
  # 段落分隔
  paragraph_separator: "\n\n"
  
  # 无数据时的输出
  empty_message:
    template: "本次检测未对材料强度进行检测。"
  
  # 总述生成（如果启用）
  overview_generation:
    enabled_when: context.include_overview == true
    template: "本次检测对{material_list}等材料强度进行了检测，共计{total_count}个检测点。"
    variables:
      material_list:
        type: natural_language_list
        source: summary.material_types
        mapping:
          concrete: 混凝土
          brick: 砌体砖
          mortar: 砂浆
        connector: "、"
      total_count:
        type: integer
        source: summary.total_test_count
  
  # 子段落排序
  section_order:
    source: context.material_order
    default: [concrete, brick, mortar]
  
  # 子段落组装
  section_assembly:
    method: sequential
    separator: "\n\n"
    preserve_content: true
    description: 保持子skills输出的原始内容，不做修改

# ==================== 质量检查 ====================

quality_checks:
  
  # 检查子skills输出格式
  subskill_output_validation:
    required_fields:
      - material_type
      - content
      - test_count
    
    content_checks:
      - type: not_empty
        field: content
        severity: error
      
      - type: min_length
        field: content
        value: 10
        severity: warning

# ==================== 示例输出 ====================

examples:
  
  # 示例1：单一材料
  example_single_material:
    input:
      sections:
        - material_type: concrete
          content: "采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，混凝土强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25。碳化深度平均值为2.3mm。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。"
    
    output: |
      采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，混凝土强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25。碳化深度平均值为2.3mm。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。
  
  # 示例2：多材料（含总述）
  example_multiple_materials:
    input:
      include_overview: true
      sections:
        - material_type: concrete
          content: "采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，混凝土强度推定值平均为28.5MPa，设计强度等级为C25。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。"
          test_count: 5
        - material_type: brick
          content: "砌体砖采用回弹法检测，检测3个部位，强度等级推定为MU10，强度推定值为8.5MPa。相关检测及结果判定依据GB/T 50315-2011执行。"
          test_count: 3
    
    output: |
      本次检测对混凝土、砌体砖等材料强度进行了检测，共计8个检测点。
      
      采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，混凝土强度推定值平均为28.5MPa，设计强度等级为C25。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。
      
      砌体砖采用回弹法检测，检测3个部位，强度等级推定为MU10，强度推定值为8.5MPa。相关检测及结果判定依据GB/T 50315-2011执行。

# ==================== 实现指导 ====================

implementation_notes: |
  父skill的render逻辑在 impl/assemble.py 中实现：
  
  1. assemble_content() 函数负责组装段落
  2. generate_overview() 函数生成总述（可选）
  3. 保持子skills输出的原始性，不做实质性修改
  4. 使用 "\n\n" 作为段落分隔符

    
    - type: paragraph_length
      max_words: 200
      message: 单个段落不宜超过200字
