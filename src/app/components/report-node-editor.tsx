import React, { useState, useEffect, useMemo } from 'react';
import { X, FileText, Search, Check, Eye } from 'lucide-react';

interface ReportNodeEditorProps {
  node: any;
  onClose: () => void;
  onUpdate: (node: any) => void;
  onHeaderMouseDown?: (e: React.MouseEvent) => void;
  collectionNodes: any[];
}

// 辅助函数：根据编号判断标准类型
const getStandardType = (code: string) => {
  const c = code.toUpperCase();
  if (c.startsWith('GB')) return { text: '国标', color: 'bg-blue-50 text-blue-600' };
  if (c.startsWith('JGJ')) return { text: '行标', color: 'bg-orange-50 text-orange-600' };
  if (c.startsWith('DB')) return { text: '地标', color: 'bg-purple-50 text-purple-600' };
  if (c.startsWith('Q/')) return { text: '企标', color: 'bg-slate-100 text-slate-500' };
  return { text: '其他', color: 'bg-slate-100 text-slate-500' };
};

// 辅助函数：将专家文档的日期编码转换为日期格式
// 格式：D260102 -> 2026-01-02 (D + YY + MM + DD)
const formatDocumentDate = (dateCode: string): string => {
  if (!dateCode || !dateCode.startsWith('D')) {
    return dateCode; // 如果不是日期编码格式，直接返回原值
  }
  
  const match = dateCode.match(/^D(\d{2})(\d{2})(\d{2})$/);
  if (!match) {
    return dateCode; // 格式不匹配，返回原值
  }
  
  const [, yy, mm, dd] = match;
  const year = `20${yy}`; // 假设是20xx年
  return `${year}-${mm}-${dd}`;
};

// 模拟规范数据
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

// 增加 content 字段模拟文档内容
const USER_REFERENCES = [
  { 
    id: 'u1', 
    code: '混凝土强度 v1.0', 
    name: 'D260102',
    content: `rule_id: concrete_strength_v1
version: 1.0
scope: 混凝土强度检测结果评价规则

inputs:
- strength_estimated_mpa: 混凝土强度推定值（MPa）
- design_grade: 设计强度等级（如C30）
- carbonation_depth_avg_mm: 碳化深度平均值（mm）
- age_days: 龄期（天）

rules:
- if: strength_estimated_mpa >= design_strength(design_grade)
  then: evaluation = "满足设计要求"
- else: evaluation = "不满足设计要求"

constraints:
- if: design_grade is null
  then: evaluation = "无法评价（缺少设计强度等级）"

output_policy:
- 评价结果基于强度推定值与设计强度的对比
- 当设计强度等级缺失时，评价结果设为"无法评价"`
  },
  { 
    id: 'u2', 
    code: '钢筋保护层 v1.0', 
    name: 'D260102',
    content: `针对本项目的特殊技术要求如下：

1. 重点关注区域：地下室外墙及顶板。
2. 检测频率：按规范要求的1.5倍执行。
3. 报告要求：需包含裂缝分布图及3D扫描点云数据。
4. 安全措施：进场需进行二级安全教育。
`
  },
  { 
    id: 'u3', 
    code: '外观缺陷 v1.1', 
    name: 'D260105',
    content: `企业内部高于国标的验收标准：

1. 混凝土强度：实测值需达到设计值的105%以上。
2. 钢筋保护层厚度：允许偏差为±3mm（国标为±5mm）。
3. 外观质量：不得有任何肉眼可见的蜂窝麻面。
`
  },
  { 
    id: 'u4', 
    code: '植筋拉拔 v2.0', 
    name: 'D260201',
    content: `2025年度安全检测专项规范：

1. 定期巡检：每月至少一次全覆盖巡检。
2. 隐患排查：重点排查高空坠物风险。
3. 应急预案：需制定台风、暴雨等极端天气应急预案。
`
  },
];

// 抓取规则定义
const EXTRACTION_RULES: Record<string, { title: string; fields: string[] }> = {
  'concrete_strength_table': {
    title: '表7 回弹法检测结果抓取规则',
    fields: [
      '检测部位',
      '设计强度等级',
      '混凝土强度推定值_MPa',
      '碳化深度计算值_mm (数组)',
      '碳化深度平均值_mm'
    ]
  },
  'concrete_strength_desc': {
    title: '混凝土强度描述文本抓取规则',
    fields: [
      '混凝土类型',
      '检测方法',
      '检测仪器',
      '设计强度等级',
      '强度推定值_MPa',
      '强度统计 (最小值/平均值/数量)',
      '碳化深度平均值_mm',
      '检测日期',
      '浇筑日期',
      '龄期_天',
      '修正规范编号',
      '强度修正系数',
      '评价结果文本'
    ]
  }
};

export default function ReportNodeEditor({
  node,
  onClose,
  onUpdate,
  onHeaderMouseDown,
  collectionNodes = [],
}: ReportNodeEditorProps) {
  // 基本信息
  const [label, setLabel] = useState(node.data.label || '');
  const [chapterNumber, setChapterNumber] = useState(node.data.chapterNumber || '');
  const [templateStyle, setTemplateStyle] = useState(node.data.templateStyle || 'concrete_strength_table');
  const [sourceNodeId, setSourceNodeId] = useState(node.data.sourceNodeId || '');

  const DATA_TYPE_OPTIONS = useMemo(() => {
    // 根据来源批次/检测大类筛选数据类型选项
    const scopePrefix = sourceNodeId.startsWith('scope_') ? sourceNodeId : '';
    
    const allOptions = [
      { value: 'concrete_strength_table', label: '混凝土强度表格', category: 'scope_concrete_strength' },
      { value: 'concrete_strength_desc', label: '混凝土强度描述', category: 'scope_concrete_strength' },
      { value: 'mortar_strength_data', label: '砂浆强度数据', category: 'scope_mortar_strength' },
      { value: 'mortar_strength_desc', label: '砂浆强度描述', category: 'scope_mortar_strength' },
      { value: 'brick_strength_table', label: '砖强度表格', category: 'scope_brick_strength' },
      { value: 'brick_strength_desc', label: '砖强度描述', category: 'scope_brick_strength' },
    ];

    if (!scopePrefix) return allOptions;
    
    return allOptions.filter(opt => opt.category === scopePrefix);
  }, [sourceNodeId]);

  // 当选项列表变化且当前值不在列表中时，自动重置为第一个有效选项
  useEffect(() => {
    if (DATA_TYPE_OPTIONS.length > 0 && !DATA_TYPE_OPTIONS.find(opt => opt.value === templateStyle)) {
      setTemplateStyle(DATA_TYPE_OPTIONS[0].value);
    }
  }, [DATA_TYPE_OPTIONS, templateStyle]);

  // 参考规范 - 分别跟踪系统规范和专家文档的选中状态
  const [referenceTab, setReferenceTab] = useState<'system' | 'user'>(node.data.referenceTab || 'system');
  const [systemReferenceId, setSystemReferenceId] = useState<string>(() => {
    // 优先使用新的数据结构
    if (node.data.systemReferenceId) {
      return node.data.systemReferenceId;
    }
    // 兼容旧数据结构
    if (node.data.referenceTab === 'system' && node.data.referenceId) {
      return node.data.referenceId;
    }
    return ''; // 新节点默认不选中
  });
  const [userReferenceId, setUserReferenceId] = useState<string>(() => {
    // 优先使用新的数据结构
    if (node.data.userReferenceId) {
      return node.data.userReferenceId;
    }
    // 兼容旧数据结构
    if (node.data.referenceTab === 'user' && node.data.referenceId) {
      return node.data.referenceId;
    }
    return ''; // 新节点默认不选中
  });
  // 当前标签页的选中ID（用于显示）
  const selectedReferenceId = referenceTab === 'system' ? systemReferenceId : userReferenceId;
  const setSelectedReferenceId = referenceTab === 'system' ? setSystemReferenceId : setUserReferenceId;
  const [searchKeyword, setSearchKeyword] = useState('');
  
  // 文档预览状态
  const [previewDoc, setPreviewDoc] = useState<{title: string, content: string} | null>(null);

  // 中文数字转阿拉伯数字
  const chineseToNumber = (cn: string): number => {
    const map: { [key: string]: number } = {
      '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
      '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    };
    
    if (map[cn]) return map[cn];
    
    if (cn.startsWith('十')) {
      const second = cn.replace('十', '');
      return 10 + (map[second] || 0);
    }
    
    if (cn.includes('十')) {
      const [first, second] = cn.split('十');
      const num1 = map[first] || 1;
      const num2 = map[second] || 0;
      return num1 * 10 + num2;
    }
    
    return 0;
  };

  const convertChineseToArabic = (input: string): string => {
    if (!input) return '';
    
    let normalized = input.replace(/[、。]/g, '.');
    const parts = normalized.split('.');
    
    const convertedParts = parts.map((part) => {
      const trimmed = part.trim();
      if (!trimmed) return '';
      
      const cnNum = chineseToNumber(trimmed);
      if (cnNum > 0) {
        return cnNum.toString();
      }
      
      return trimmed;
    });
    
    return convertedParts.join('.');
  };

  const handleChapterNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    const converted = convertChineseToArabic(inputValue);
    setChapterNumber(converted);
  };

  useEffect(() => {
    setLabel(node.data.label || '');
    setChapterNumber(convertChineseToArabic(node.data.chapterNumber || ''));
    setTemplateStyle(node.data.templateStyle || 'concrete_strength_table');
    // 如果 node.data 中有保存的状态，则恢复
    if (node.data.referenceTab) {
      setReferenceTab(node.data.referenceTab);
    }
  }, [node.id]);

  // 当 node 变化时，更新规范和文档的选中状态
  useEffect(() => {
    if (node.data.systemReferenceId) {
      setSystemReferenceId(node.data.systemReferenceId);
    } else if (node.data.referenceTab === 'system' && node.data.referenceId) {
      setSystemReferenceId(node.data.referenceId);
    } else {
      setSystemReferenceId('');
    }
    
    if (node.data.userReferenceId) {
      setUserReferenceId(node.data.userReferenceId);
    } else if (node.data.referenceTab === 'user' && node.data.referenceId) {
      setUserReferenceId(node.data.referenceId);
    } else {
      setUserReferenceId('');
    }
  }, [node.id, node.data.systemReferenceId, node.data.userReferenceId, node.data.referenceId, node.data.referenceTab]);

  // 根据标签页获取基础数据
  const baseReferences = referenceTab === 'system' ? SYSTEM_REFERENCES : USER_REFERENCES;

  // 过滤规范
  const filteredReferences = useMemo(() => {
    let result = baseReferences;

    if (searchKeyword.trim()) {
      const keyword = searchKeyword.toLowerCase();
      return result.filter(ref => 
        ref.code.toLowerCase().includes(keyword) || 
        ref.name.toLowerCase().includes(keyword)
      );
    }

    return result;
  }, [baseReferences, searchKeyword]);

  const handleSave = () => {
    // 获取系统规范和专家文档的引用对象
    const systemRef = SYSTEM_REFERENCES.find(ref => ref.id === systemReferenceId);
    const userRef = USER_REFERENCES.find(ref => ref.id === userReferenceId);
    
    // 构建更新数据，同时保存系统规范和专家文档
    const updateData: any = {
      ...node.data,
      label,
      chapterNumber,
      templateStyle,
      sourceNodeId: sourceNodeId || null,
      // 系统规范
      systemReferenceId: systemReferenceId || null,
      systemReferenceCode: systemRef ? systemRef.code : '',
      // 专家文档
      userReferenceId: userReferenceId || null,
      userReferenceCode: userRef ? userRef.code : '',
    };
    
    // 兼容旧数据结构（保留当前标签页的选中作为 referenceId/referenceTab/referenceCode）
    const currentRef = referenceTab === 'system' ? systemRef : userRef;
    const currentRefId = referenceTab === 'system' ? systemReferenceId : userReferenceId;
    updateData.referenceId = currentRefId || null;
    updateData.referenceTab = referenceTab;
    updateData.referenceCode = currentRef ? currentRef.code : '';
    
    onUpdate({
      ...node,
      data: updateData,
    });
    onClose();
  };

  const handleTabChange = (tab: 'system' | 'user') => {
    setReferenceTab(tab);
    // 切换标签页时不清空已选中的项，保持用户的选择
  };

  return (
    <div className="w-full bg-white border-l border-slate-200 shadow-xl flex flex-col h-full relative">
      {/* 文档预览模态框 */}
      {previewDoc && (
        <div className="absolute inset-0 z-50 bg-white/95 backdrop-blur-sm flex flex-col animate-in fade-in duration-200">
          <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-white shadow-sm flex-shrink-0">
            <h3 className="font-semibold text-slate-800 text-sm truncate flex-1 pr-4" title={previewDoc.title}>
              {previewDoc.title}
            </h3>
            <button
              onClick={() => setPreviewDoc(null)}
              className="p-1 hover:bg-slate-100 rounded-md transition-colors text-slate-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-5">
            <div className="prose prose-sm prose-slate max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm text-slate-600 leading-relaxed">
                {previewDoc.content}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div
        className="bg-white border-b border-slate-200 p-4 flex items-center justify-between cursor-move select-none flex-shrink-0"
        onMouseDown={onHeaderMouseDown}
      >
        <h3 className="text-slate-800 font-semibold flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-500" />
          章节配置
        </h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-100 rounded transition-colors"
          onMouseDown={(e) => e.stopPropagation()}
        >
          <X className="w-5 h-5 text-slate-500" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        
        {/* 基本信息 */}
        <div className="space-y-4">
          <div className="grid grid-cols-[2fr_1fr] gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">章节标题</label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all"
                placeholder="输入标题"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1.5">编号</label>
              <input
                type="text"
                value={chapterNumber}
                onChange={handleChapterNumberChange}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400 transition-all"
                placeholder="如: 1.1"
              />
            </div>
          </div>

          {/* 数据范围筛选 */}
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-1 h-3 bg-indigo-500 rounded-full"></div>
                <h4 className="text-xs font-semibold text-slate-700">数据范围筛选 (Scope)</h4>
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">
                * 先选择检测大类，再选择数据用途。
              </p>
            </div>
            
            {/* 采集批次/节点筛选 */}
            <div>
              <label className="block text-[10px] font-medium text-slate-500 mb-1.5">检测大类 (必选)</label>
              <select
                value={sourceNodeId}
                onChange={(e) => setSourceNodeId(e.target.value)}
                className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-indigo-400 bg-white"
              >
                <option value="">-- 请选择 --</option>
                <option value="scope_concrete_strength">混凝土强度检测</option>
                <option value="scope_mortar_strength">砂浆强度检测</option>
                <option value="scope_brick_strength">砖强度检测</option>
                <option value="scope_steel_hardness">钢材里氏硬度检测</option>
              </select>
            </div>

            {/* 数据类型选择 - 整合在此 */}
            <div>
              <label className="block text-[10px] font-medium text-slate-500 mb-1.5">数据用途</label>
              <select
                value={templateStyle}
                onChange={(e) => setTemplateStyle(e.target.value)}
                disabled={!sourceNodeId}
                className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-indigo-400 bg-white disabled:bg-slate-50 disabled:text-slate-400"
              >
                {DATA_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 抓取规则展示 - 集成在Scope面板内 */}
            {EXTRACTION_RULES[templateStyle] && (
              <div className="mt-3 pt-3 border-t border-slate-200/60">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-[10px] font-semibold text-slate-600">
                    数据抓取字段预览
                  </h4>
                  <span className="text-[9px] text-slate-400 bg-white px-1.5 py-0.5 rounded border border-slate-100">
                    自动映射
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-1.5">
                  {EXTRACTION_RULES[templateStyle].fields.map((field, idx) => (
                    <span 
                      key={idx}
                      className="inline-flex items-center px-1.5 py-0.5 rounded-sm bg-slate-100 text-[10px] text-slate-600 border border-slate-200/50"
                    >
                      {field.split(' ')[0]} {/* 简化显示，只取字段名 */}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 参考规范 */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <div className="w-1 h-4 bg-emerald-600 rounded-full"></div>
            <h4 className="text-sm font-semibold text-slate-700">参考规范</h4>
          </div>

          <div className="bg-slate-50 rounded-xl p-1">
            {/* Reference Tabs (System/User) */}
            <div className="flex p-0.5 bg-white rounded-lg shadow-sm mb-3">
              <button
                onClick={() => handleTabChange('system')}
                className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                  referenceTab === 'system'
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                参考的规范标准
              </button>
              <button
                onClick={() => handleTabChange('user')}
                className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                  referenceTab === 'user'
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                参考的专家知识库
              </button>
            </div>

            {/* Search Bar */}
            <div className="relative mb-2 px-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
              <input
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder={referenceTab === 'system' ? "搜索规范编号或名称..." : "搜索参考的专家知识库..."}
                className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:border-emerald-400 bg-white"
              />
            </div>

            {/* Reference List */}
            <div className="space-y-0.5 max-h-[360px] overflow-y-auto px-1">
              {filteredReferences.length > 0 ? (
                filteredReferences.map((ref) => {
                  const isSelected = ref.id === selectedReferenceId;
                  const typeInfo = getStandardType(ref.code);
                  const userTag = { text: '记录', color: 'bg-blue-50 text-blue-600' };
                  
                  return (
                    <div
                      key={ref.id}
                      className={`
                        flex items-center justify-between p-2 rounded-md transition-all group border min-h-[56px]
                        ${isSelected 
                          ? 'bg-white shadow-sm border-emerald-100' 
                          : 'hover:bg-white border-transparent'
                        }
                      `}
                      onClick={() => setSelectedReferenceId(ref.id)}
                    >
                      <div className="flex-1 min-w-0 pr-2 cursor-pointer flex flex-col justify-center">
                        <div className={`text-xs font-medium truncate leading-4 ${isSelected ? 'text-emerald-700' : 'text-slate-700'}`}>
                          {ref.code}
                        </div>
                        <div className={`text-xs truncate leading-4 mt-1 ${isSelected ? 'text-emerald-600/70' : 'text-slate-400'}`}>
                          {referenceTab === 'user' ? (ref.name.startsWith('D') ? formatDocumentDate(ref.name) : ref.name) : ref.name}
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-center justify-center gap-1 flex-shrink-0 min-w-[40px]">
                        <div className="flex items-center gap-1">
                          <span className={`text-[10px] px-1.5 rounded-sm ${referenceTab === 'system' ? typeInfo.color : userTag.color}`}>
                            {referenceTab === 'system' ? typeInfo.text : userTag.text}
                          </span>
                          {referenceTab === 'user' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setPreviewDoc({ 
                                  title: `${ref.code} ${ref.name}`, 
                                  content: (ref as any).content || '暂无内容' 
                                });
                              }}
                              className="p-1 rounded-full hover:bg-slate-100 text-slate-400 hover:text-blue-500 transition-colors"
                              title="查看详情"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>

                        <Check className={`w-3.5 h-3.5 text-emerald-600 flex-shrink-0 ${isSelected ? '' : 'opacity-0'}`} />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center">
                  <p className="text-xs text-slate-400">未找到匹配规范</p>
                </div>
              )}
            </div>
            
            {/* List Footer Hint */}
            {filteredReferences.length > 0 && (
              <div className="text-center pt-2 pb-1">
                <span className="text-[10px] text-slate-400">
                  共 {filteredReferences.length} 条
                </span>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Footer */}
      <div className="bg-slate-50 border-t border-slate-200 p-4 flex gap-3 flex-shrink-0">
        <button
          onClick={handleSave}
          className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors font-medium text-sm shadow-sm"
        >
          保存配置
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2.5 bg-white text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-sm font-medium"
        >
          取消
        </button>
      </div>
    </div>
  );
}
