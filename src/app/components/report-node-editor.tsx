import React, { useEffect, useMemo, useState } from 'react';
import { X, FileText, Search, Check, Eye } from 'lucide-react';

interface ReportNodeEditorProps {
  node: any;
  onClose: () => void;
  onUpdate: (node: any) => void;
  onHeaderMouseDown?: (e: React.MouseEvent) => void;
  collectionNodes: any[];
  reportType?: string;
}

const getStandardType = (code: string) => {
  const c = (code || '').toUpperCase();
  if (c.startsWith('GB')) return { text: '国标', color: 'bg-blue-50 text-blue-600' };
  if (c.startsWith('JGJ')) return { text: '行标', color: 'bg-orange-50 text-orange-600' };
  if (c.startsWith('DB')) return { text: '地标', color: 'bg-purple-50 text-purple-600' };
  if (c.startsWith('Q/')) return { text: '企标', color: 'bg-slate-100 text-slate-500' };
  return { text: '其他', color: 'bg-slate-100 text-slate-500' };
};

const formatDocumentDate = (dateCode: string): string => {
  if (!dateCode || !dateCode.startsWith('D')) return dateCode;
  const match = dateCode.match(/^D(\d{2})(\d{2})(\d{2})$/);
  if (!match) return dateCode;
  const [, yy, mm, dd] = match;
  return `20${yy}-${mm}-${dd}`;
};

const SYSTEM_REFERENCES = [
  { id: 's1', code: 'JGJ/T 23-2011', name: '回弹法检测混凝土抗压强度技术规程' },
  { id: 's2', code: 'GB 50204-2015', name: '混凝土结构工程施工质量验收规范' },
  { id: 's3', code: 'GB 50010-2010', name: '混凝土结构设计规范' },
  { id: 's4', code: 'GB 50367-2013', name: '混凝土结构加固设计规范' },
  { id: 's5', code: 'JGJ 106-2014', name: '建筑基桩检测技术规范' },
  { id: 's6', code: 'GB 50202-2018', name: '建筑地基基础工程施工质量验收标准' },
  { id: 's7', code: 'DB11/T 637-2015', name: '房屋结构综合安全性鉴定标准' },
  { id: 's8', code: 'JGJ 125-2016', name: '危险房屋鉴定标准' },
  { id: 's9', code: 'GB 50292-2015', name: '民用建筑可靠性鉴定标准' },
];

const USER_REFERENCES = [
  { id: 'u1', code: '混凝土强度 v1.0', name: 'D260102', content: '用于混凝土强度相关项目的补充规则。' },
  { id: 'u2', code: '钢筋保护层 v1.0', name: 'D260102', content: '用于钢筋保护层检测的补充规则。' },
  { id: 'u3', code: '外观缺陷 v1.1', name: 'D260105', content: '用于外观缺陷评估的企业补充规则。' },
  { id: 'u4', code: '植筋拉拔 v2.0', name: 'D260201', content: '用于植筋拉拔相关检测的补充规则。' },
];

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
    fields: ['委托方', '鉴定对象', '委托鉴定事项', '受理日期', '查勘日期'],
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
    fields: ['楼层数量', '主要构件（承重墙）', '一般构件（自承重墙）', '承载能力', '结论', '备注（建成年代/房屋类别/φ）'],
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

const getDefaultSystemReferenceIdByReportType = (type?: string): string => {
  const mapping: Record<string, string> = {
    民标安全性: 's9',
    危险房屋鉴定: 's8',
  };
  return mapping[type || ''] || 's8';
};

const chineseToNumber = (cn: string): number => {
  const map: { [key: string]: number } = {
    一: 1,
    二: 2,
    三: 3,
    四: 4,
    五: 5,
    六: 6,
    七: 7,
    八: 8,
    九: 9,
    十: 10,
  };
  if (map[cn]) return map[cn];
  if (cn.startsWith('十')) return 10 + (map[cn.replace('十', '')] || 0);
  if (cn.includes('十')) {
    const [a, b] = cn.split('十');
    return (map[a] || 1) * 10 + (map[b] || 0);
  }
  return 0;
};

const convertChineseToArabic = (input: string): string => {
  if (!input) return '';
  const normalized = input.replace(/[、。？]/g, '.');
  return normalized
    .split('.')
    .map((part) => {
      const t = part.trim();
      if (!t) return '';
      const cnNum = chineseToNumber(t);
      return cnNum > 0 ? String(cnNum) : t;
    })
    .join('.');
};

export default function ReportNodeEditor({
  node,
  onClose,
  onUpdate,
  onHeaderMouseDown,
  collectionNodes = [],
  reportType,
}: ReportNodeEditorProps) {
  const [label, setLabel] = useState(node.data.label || '');
  const [chapterNumber, setChapterNumber] = useState(node.data.chapterNumber || '');
  const [templateStyle, setTemplateStyle] = useState(node.data.templateStyle || 'concrete_strength_table');
  const [sourceNodeId, setSourceNodeId] = useState(node.data.sourceNodeId || '');

  const [referenceTab, setReferenceTab] = useState<'system' | 'user'>(node.data.referenceTab || 'system');
  const [systemReferenceId, setSystemReferenceId] = useState<string>(() => {
    if (node.data.systemReferenceId) return node.data.systemReferenceId;
    if (node.data.referenceTab === 'system' && node.data.referenceId) return node.data.referenceId;
    return '';
  });
  const [userReferenceId, setUserReferenceId] = useState<string>(() => {
    if (node.data.userReferenceId) return node.data.userReferenceId;
    if (node.data.referenceTab === 'user' && node.data.referenceId) return node.data.referenceId;
    return '';
  });

  const [searchKeyword, setSearchKeyword] = useState('');
  const [previewDoc, setPreviewDoc] = useState<{ title: string; content: string } | null>(null);

  const DATA_TYPE_OPTIONS = useMemo(() => {
    const scopePrefix = sourceNodeId.startsWith('scope_') ? sourceNodeId : '';
    const allOptions = [
      { value: 'concrete_strength_full', label: '混凝土强度检测', category: 'scope_concrete_strength' },
      { value: 'concrete_strength_table', label: '混凝土强度表格（旧）', category: 'scope_concrete_strength', deprecated: true },
      { value: 'concrete_strength_desc', label: '混凝土强度描述（旧）', category: 'scope_concrete_strength', deprecated: true },
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
    if (!scopePrefix) return allOptions;
    return allOptions.filter((opt) => opt.category === scopePrefix);
  }, [sourceNodeId]);

  useEffect(() => {
    if (DATA_TYPE_OPTIONS.length > 0 && !DATA_TYPE_OPTIONS.find((opt) => opt.value === templateStyle)) {
      setTemplateStyle(DATA_TYPE_OPTIONS[0].value);
    }
  }, [DATA_TYPE_OPTIONS, templateStyle]);

  useEffect(() => {
    if (sourceNodeId === 'scope_basic_situation') setTemplateStyle('basic_situation');
    if (sourceNodeId === 'scope_house_overview') setTemplateStyle('house_overview');
    if (sourceNodeId === 'scope_inspection_content_and_methods') setTemplateStyle('inspection_content_and_methods');
    if (sourceNodeId === 'scope_inspection_basis') setTemplateStyle('inspection_basis');
    if (sourceNodeId === 'scope_detailed_inspection') setTemplateStyle('detailed_inspection');
    if (sourceNodeId === 'scope_load_calc_params') setTemplateStyle('load_calc_params');
    if (sourceNodeId === 'scope_bearing_capacity_review') setTemplateStyle('bearing_capacity_review');
    if (sourceNodeId === 'scope_analysis_explanation') setTemplateStyle('analysis_explanation');
    if (sourceNodeId === 'scope_opinion_and_suggestions') setTemplateStyle('opinion_and_suggestions');
  }, [sourceNodeId]);

  useEffect(() => {
    if (templateStyle === 'inspection_basis' && !systemReferenceId) {
      setSystemReferenceId(getDefaultSystemReferenceIdByReportType(reportType));
      setReferenceTab('system');
    }
  }, [templateStyle, systemReferenceId, reportType]);

  useEffect(() => {
    setLabel(node.data.label || '');
    setChapterNumber(convertChineseToArabic(node.data.chapterNumber || ''));
    setTemplateStyle(node.data.templateStyle || 'concrete_strength_table');
    setSourceNodeId(node.data.sourceNodeId || '');
  }, [node.id, node.data.label, node.data.chapterNumber, node.data.templateStyle, node.data.sourceNodeId]);

  useEffect(() => {
    if (node.data.systemReferenceId) setSystemReferenceId(node.data.systemReferenceId);
    if (node.data.userReferenceId) setUserReferenceId(node.data.userReferenceId);
  }, [node.data.systemReferenceId, node.data.userReferenceId]);

  const selectedReferenceId = referenceTab === 'system' ? systemReferenceId : userReferenceId;
  const setSelectedReferenceId = referenceTab === 'system' ? setSystemReferenceId : setUserReferenceId;

  const baseReferences = referenceTab === 'system' ? SYSTEM_REFERENCES : USER_REFERENCES;
  const filteredReferences = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase();
    if (!keyword) return baseReferences;
    return baseReferences.filter((ref) => ref.code.toLowerCase().includes(keyword) || ref.name.toLowerCase().includes(keyword));
  }, [baseReferences, searchKeyword]);

  const handleChapterNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setChapterNumber(convertChineseToArabic(e.target.value));
  };

  const handleSave = () => {
    const systemRef = SYSTEM_REFERENCES.find((ref) => ref.id === systemReferenceId);
    const userRef = USER_REFERENCES.find((ref) => ref.id === userReferenceId);
    const currentRef = referenceTab === 'system' ? systemRef : userRef;
    const currentRefId = referenceTab === 'system' ? systemReferenceId : userReferenceId;

    onUpdate({
      ...node,
      data: {
        ...node.data,
        label,
        chapterNumber,
        templateStyle,
        sourceNodeId: sourceNodeId || null,
        systemReferenceId: systemReferenceId || null,
        systemReferenceCode: systemRef ? systemRef.code : '',
        userReferenceId: userReferenceId || null,
        userReferenceCode: userRef ? userRef.code : '',
        referenceId: currentRefId || null,
        referenceTab,
        referenceCode: currentRef ? currentRef.code : '',
      },
    });

    onClose();
  };

  return (
    <div className="w-full bg-white border-l border-slate-200 shadow-xl flex flex-col h-full relative">
      {previewDoc && (
        <div className="absolute inset-0 z-50 bg-white/95 backdrop-blur-sm flex flex-col animate-in fade-in duration-200">
          <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-white shadow-sm flex-shrink-0">
            <h3 className="font-semibold text-slate-800 text-sm truncate flex-1 pr-4" title={previewDoc.title}>{previewDoc.title}</h3>
            <button onClick={() => setPreviewDoc(null)} className="p-1 hover:bg-slate-100 rounded-md transition-colors text-slate-500"><X className="w-5 h-5" /></button>
          </div>
          <div className="flex-1 overflow-y-auto p-5">
            <pre className="whitespace-pre-wrap font-sans text-sm text-slate-600 leading-relaxed">{previewDoc.content}</pre>
          </div>
        </div>
      )}

      <div className="bg-white border-b border-slate-200 p-4 flex items-center justify-between cursor-move select-none flex-shrink-0" onMouseDown={onHeaderMouseDown}>
        <h3 className="text-slate-800 font-semibold flex items-center gap-2"><FileText className="w-4 h-4 text-slate-500" />章节配置</h3>
        <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded transition-colors" onMouseDown={(e) => e.stopPropagation()}><X className="w-5 h-5 text-slate-500" /></button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        <div className="space-y-4">
          <div className="grid grid-cols-[2fr_1fr] gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">章节标题</label>
              <input type="text" value={label} onChange={(e) => setLabel(e.target.value)} className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all" placeholder="输入标题" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">编号</label>
              <input type="text" value={chapterNumber} onChange={handleChapterNumberChange} className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all" placeholder="如: 1.1" />
            </div>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2"><div className="w-1 h-3 bg-indigo-500 rounded-full" /><h4 className="text-xs font-semibold text-slate-700">数据范围筛选（Scope）</h4></div>
            </div>

            <div>
              <label className="block text-[10px] font-medium text-slate-500 mb-1.5">检测大类（必选）</label>
              <select value={sourceNodeId} onChange={(e) => setSourceNodeId(e.target.value)} className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-indigo-400 bg-white">
                <option value="">-- 请选择 --</option>
                <option value="scope_concrete_strength">混凝土强度检测</option>
                <option value="scope_mortar_strength">砂浆强度检测</option>
                <option value="scope_brick_strength">砖强度检测</option>
                <option value="scope_steel_hardness">钢材里氏硬度检测</option>
                <option value="scope_basic_situation">基本情况</option>
                <option value="scope_house_overview">房屋概况</option>
                <option value="scope_inspection_content_and_methods">鉴定内容和方法及原始记录一览表</option>
                <option value="scope_inspection_basis">检测鉴定依据</option>
                <option value="scope_detailed_inspection">详细检查情况</option>
                <option value="scope_load_calc_params">荷载及计算参数取值</option>
                <option value="scope_bearing_capacity_review">承载能力复核验算</option>
                <option value="scope_analysis_explanation">分析说明</option>
                <option value="scope_opinion_and_suggestions">鉴定意见及处理建议</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-medium text-slate-500 mb-1.5">数据用途</label>
              <select value={templateStyle} onChange={(e) => setTemplateStyle(e.target.value)} disabled={!sourceNodeId} className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-indigo-400 bg-white disabled:bg-slate-50 disabled:text-slate-400">
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

        <div className="space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100"><div className="w-1 h-4 bg-emerald-600 rounded-full" /><h4 className="text-sm font-semibold text-slate-700">参考规范</h4></div>

          <div className="bg-slate-50 rounded-xl p-1">
            <div className="flex p-0.5 bg-white rounded-lg shadow-sm mb-3">
              <button onClick={() => setReferenceTab('system')} className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${referenceTab === 'system' ? 'bg-emerald-50 text-emerald-600' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'}`}>参考的规范标准</button>
              <button onClick={() => setReferenceTab('user')} className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${referenceTab === 'user' ? 'bg-emerald-50 text-emerald-600' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'}`}>参考的专家知识库</button>
            </div>

            <div className="relative mb-2 px-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
              <input type="text" value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} placeholder={referenceTab === 'system' ? '搜索规范编号或名称...' : '搜索参考的专家知识库...'} className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-emerald-400 bg-white" />
            </div>

            <div className="space-y-0.5 max-h-[280px] overflow-y-auto px-1">
              {filteredReferences.length > 0 ? (
                filteredReferences.map((ref) => {
                  const isSelected = ref.id === selectedReferenceId;
                  const typeInfo = getStandardType(ref.code);
                  return (
                    <div key={ref.id} className={`flex items-center justify-between p-2 rounded-md transition-all group border min-h-[56px] ${isSelected ? 'bg-white shadow-sm border-emerald-100' : 'hover:bg-white border-transparent'}`} onClick={() => setSelectedReferenceId(ref.id)}>
                      <div className="flex-1 min-w-0 pr-2 cursor-pointer flex flex-col justify-center">
                        <div className={`text-xs font-medium truncate leading-4 ${isSelected ? 'text-emerald-700' : 'text-slate-700'}`}>{ref.code}</div>
                        <div className={`text-xs truncate leading-4 mt-1 ${isSelected ? 'text-emerald-600/70' : 'text-slate-400'}`}>
                          {referenceTab === 'user' ? (ref.name.startsWith('D') ? formatDocumentDate(ref.name) : ref.name) : ref.name}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className={`text-[10px] px-1.5 rounded-sm ${referenceTab === 'system' ? typeInfo.color : 'bg-blue-50 text-blue-600'}`}>{referenceTab === 'system' ? typeInfo.text : '文档'}</span>
                        {referenceTab === 'user' && (
                          <button onClick={(e) => { e.stopPropagation(); setPreviewDoc({ title: `${ref.code} ${ref.name}`, content: (ref as any).content || '暂无内容' }); }} className="p-1 rounded-full hover:bg-slate-100 text-slate-400 hover:text-blue-500 transition-colors" title="查看详情">
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {isSelected && <Check className="w-3.5 h-3.5 text-emerald-500" />}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center"><p className="text-xs text-slate-400">未找到匹配项</p></div>
              )}
            </div>
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
