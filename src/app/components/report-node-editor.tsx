import React, { useEffect, useState } from 'react';
import { X, FileText } from 'lucide-react';

interface ReportNodeEditorProps {
  node: any;
  onClose: () => void;
  onUpdate: (node: any) => void;
  onHeaderMouseDown?: (e: React.MouseEvent) => void;
  collectionNodes: any[];
  reportType?: string;
}

const EXTRACTION_RULES: Record<string, { title: string; fields: string[] }> = {
  concrete_strength_full: {
    title: '混凝土强度检测（完整报告）',
    fields: ['混凝土类型', '检测方法', '检测仪器', '强度统计', '碳化深度', '评价结果'],
  },
  concrete_strength_table: {
    title: '回弹法检测结果抓取规则',
    fields: ['检测部位', '设计强度等级', '混凝土强度推定值MPa', '碳化深度平均值mm'],
  },
  concrete_strength_desc: {
    title: '混凝土强度描述文本抓取规则',
    fields: ['混凝土类型', '检测方法', '检测仪器', '检测日期', '评价结果文本'],
  },
  basic_situation: {
    title: '基本情况',
    fields: ['委托方', '鉴定对象', '委托鉴定事项', '受理日期', '勘察日期'],
  },
  house_overview: {
    title: '房屋概况',
    fields: ['房屋概况（动态抽取并LLM润色）'],
  },
  inspection_content_and_methods: {
    title: '鉴定内容和方法及原始记录一览表',
    fields: ['鉴定内容和方法', '主要检测仪器设备', '原始记录一览表'],
  },
  inspection_basis: {
    title: '检测鉴定依据',
    fields: ['规范名称', '规范编号'],
  },
  detailed_inspection: {
    title: '详细检查情况',
    fields: ['房屋基本信息', '现场检查情况', '检查位置', '现状描述', '照片'],
  },
  load_calc_params: {
    title: '荷载及计算参数取值',
    fields: ['砌筑砂浆抗压强度取值', '砌墙砖抗压强度等级', '活载', '恒载（含自重）', '荷载基本组合类型'],
  },
  bearing_capacity_review: {
    title: '承载能力复核验算',
    fields: ['楼层数量', '主要构件（承重墙）', '一般构件（自承重墙）', '承载能力', '结论', '备注（建成年份/房屋类别）'],
  },
  analysis_explanation: {
    title: '分析说明',
    fields: ['地基危险性评定', '基础及上部结构危险性鉴定', '构件危险性评定表', '楼层危险性统计表', '整体危险性结论'],
  },
  opinion_and_suggestions: {
    title: '鉴定意见及处理建议',
    fields: ['综合评定结论', '主要存在问题', '处理建议'],
  },
};

type DataTypeOption = {
  value: string;
  label: string;
  category: string;
};

const DATA_TYPE_OPTIONS: DataTypeOption[] = [
  { value: 'concrete_strength_full', label: '混凝土强度检测', category: 'scope_concrete_strength' },
  { value: 'concrete_strength_table', label: '混凝土强度表格（旧）', category: 'scope_concrete_strength' },
  { value: 'concrete_strength_desc', label: '混凝土强度描述（旧）', category: 'scope_concrete_strength' },
  { value: 'mortar_strength_data', label: '砂浆强度（表格+描述）', category: 'scope_mortar_strength' },
  { value: 'brick_strength_table', label: '砖强度（表格+描述）', category: 'scope_brick_strength' },
  { value: 'basic_situation', label: '基本情况', category: 'scope_basic_situation' },
  { value: 'house_overview', label: '房屋概况', category: 'scope_house_overview' },
  { value: 'inspection_content_and_methods', label: '鉴定内容和方法及原始记录一览表', category: 'scope_inspection_content_and_methods' },
  { value: 'inspection_basis', label: '检测鉴定依据', category: 'scope_inspection_basis' },
  { value: 'detailed_inspection', label: '详细检查情况', category: 'scope_detailed_inspection' },
  { value: 'load_calc_params', label: '荷载及计算参数取值', category: 'scope_load_calc_params' },
  { value: 'bearing_capacity_review', label: '承载能力复核验算', category: 'scope_bearing_capacity_review' },
  { value: 'analysis_explanation', label: '分析说明（静态）', category: 'scope_analysis_explanation' },
  { value: 'opinion_and_suggestions', label: '鉴定意见及处理建议（静态）', category: 'scope_opinion_and_suggestions' },
];

const resolveSourceNodeIdByTemplateStyle = (templateStyle: string): string => {
  const matched = DATA_TYPE_OPTIONS.find((option) => option.value === templateStyle);
  return matched?.category || '';
};

const resolveTemplateStyleBySourceNodeId = (sourceNodeId: string): string => {
  const matched = DATA_TYPE_OPTIONS.find((option) => option.category === sourceNodeId);
  return matched?.value || '';
};

export default function ReportNodeEditor({
  node,
  onClose,
  onUpdate,
  onHeaderMouseDown,
}: ReportNodeEditorProps) {
  const [label, setLabel] = useState(node.data.label || '');
  const [templateStyle, setTemplateStyle] = useState(
    node.data.templateStyle || resolveTemplateStyleBySourceNodeId(String(node.data.sourceNodeId || '')) || 'concrete_strength_table'
  );

  useEffect(() => {
    setLabel(node.data.label || '');
    setTemplateStyle(
      node.data.templateStyle || resolveTemplateStyleBySourceNodeId(String(node.data.sourceNodeId || '')) || 'concrete_strength_table'
    );
  }, [node.id, node.data.label, node.data.templateStyle, node.data.sourceNodeId]);

  const handleSave = () => {
    const sourceNodeId = resolveSourceNodeIdByTemplateStyle(templateStyle);
    onUpdate({
      ...node,
      data: {
        ...node.data,
        label,
        templateStyle,
        sourceNodeId: sourceNodeId || null,
      },
    });

    onClose();
  };

  return (
    <div className="w-full bg-white border-l border-slate-200 shadow-xl flex flex-col h-full relative">
      <div className="bg-white border-b border-slate-200 p-4 flex items-center justify-between cursor-move select-none flex-shrink-0" onMouseDown={onHeaderMouseDown}>
        <h3 className="text-slate-800 font-semibold flex items-center gap-2"><FileText className="w-4 h-4 text-slate-500" />章节配置</h3>
        <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded transition-colors" onMouseDown={(e) => e.stopPropagation()}><X className="w-5 h-5 text-slate-500" /></button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1.5">章节标题</label>
            <input type="text" value={label} onChange={(e) => setLabel(e.target.value)} className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all" placeholder="输入标题" />
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2"><div className="w-1 h-3 bg-indigo-500 rounded-full" /><h4 className="text-xs font-semibold text-slate-700">数据范围筛选（Scope）</h4></div>
            </div>

            <div>
              <label className="block text-[10px] font-medium text-slate-500 mb-1.5">检测大类 / 数据用途（必选）</label>
              <select value={templateStyle} onChange={(e) => setTemplateStyle(e.target.value)} className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-indigo-400 bg-white">
                {DATA_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>

            {EXTRACTION_RULES[templateStyle] && (
              <div className="mt-3 pt-3 border-t border-slate-200/60">
                <h4 className="text-[10px] font-semibold text-slate-600 mb-2">数据抓取字段预览</h4>
                <div className="flex flex-wrap gap-1.5">
                  {EXTRACTION_RULES[templateStyle].fields.map((field, idx) => (
                    <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-sm bg-slate-100 text-[10px] text-slate-600 border border-slate-200/50">{field}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-slate-200 bg-white flex items-center justify-end gap-2">
        <button onClick={onClose} className="px-3 py-1.5 text-xs rounded-md border border-slate-200 text-slate-600 hover:bg-slate-50">取消</button>
        <button onClick={handleSave} className="px-3 py-1.5 text-xs rounded-md bg-slate-900 text-white hover:bg-slate-800">保存</button>
      </div>
    </div>
  );
}
