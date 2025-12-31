import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Brain, FileText, BookOpen, LayoutTemplate } from 'lucide-react';

interface ReportNodeEditorProps {
  node: any;
  onClose: () => void;
  onUpdate: (node: any) => void;
  onHeaderMouseDown?: (e: React.MouseEvent) => void;
}

export default function ReportNodeEditor({ node, onClose, onUpdate, onHeaderMouseDown }: ReportNodeEditorProps) {
  const [label, setLabel] = useState(node.data.label);
  const [chapterNumber, setChapterNumber] = useState(node.data.chapterNumber || '');
  const [llmModel, setLlmModel] = useState(node.data.llmModel || '');
  const [prompt, setPrompt] = useState(node.data.prompt || '');
  const [references, setReferences] = useState(node.data.references || []);
  const [templates, setTemplates] = useState(node.data.templates || []);
  const [activeTab, setActiveTab] = useState<'llm' | 'prompt' | 'references' | 'templates'>('llm');

  // 中文数字转阿拉伯数字
  const chineseToNumber = (cn: string): number => {
    const map: { [key: string]: number } = {
      '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
      '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    };
    
    // 简单处理 1-99 的情况
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

  // 将章节编号中的中文数字转换为阿拉伯数字
  const convertChineseToArabic = (input: string): string => {
    if (!input) return '';
    
    // 替换中文顿号、句号为点
    let normalized = input.replace(/[、。]/g, '.');
    
    // 分割为各部分
    const parts = normalized.split('.');
    
    const convertedParts = parts.map((part) => {
      const trimmed = part.trim();
      if (!trimmed) return '';
      
      // 尝试解析中文数字
      const cnNum = chineseToNumber(trimmed);
      if (cnNum > 0) {
        return cnNum.toString();
      }
      
      // 如果不是中文数字，保持原样（可能是阿拉伯数字或其他字符）
      return trimmed;
    });
    
    return convertedParts.join('.');
  };

  // 处理章节编号输入变化
  const handleChapterNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    // 自动转换中文数字为阿拉伯数字
    const converted = convertChineseToArabic(inputValue);
    setChapterNumber(converted);
  };

  // 当node变化时，更新所有状态
  useEffect(() => {
    setLabel(node.data.label);
    // 如果章节编号包含中文数字，自动转换为阿拉伯数字
    const initialChapterNumber = node.data.chapterNumber || '';
    setChapterNumber(convertChineseToArabic(initialChapterNumber));
    setLlmModel(node.data.llmModel || '');
    setPrompt(node.data.prompt || '');
    setReferences(node.data.references || []);
    setTemplates(node.data.templates || []);
  }, [node]);

  const handleSave = () => {
    onUpdate({
      ...node,
      data: {
        ...node.data,
        label,
        chapterNumber,
        llmModel,
        prompt,
        references,
        templates,
      },
    });
    onClose();
  };

  return (
    <div className="w-[480px] bg-white border-l border-slate-200 shadow-xl flex flex-col h-full">
      {/* Header */}
      <div
        className="bg-white border-b border-slate-200 p-4 flex items-center justify-between cursor-move select-none"
        onMouseDown={onHeaderMouseDown}
      >
        <h3 className="text-slate-800">章节配置</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-100 rounded transition-colors"
          onMouseDown={(e) => e.stopPropagation()}
        >
          <X className="w-5 h-5 text-slate-500" />
        </button>
      </div>

      {/* Chapter Basic Info - Compact Row */}
      <div className="p-4 border-b border-slate-200 grid grid-cols-[2fr_1fr] gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">章节标题</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-shadow"
            placeholder="输入章节标题"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wider">章节编号</label>
          <input
            type="text"
            value={chapterNumber}
            onChange={handleChapterNumberChange}
            className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-shadow"
            placeholder="例如: 1.1 (支持中文数字自动转换)"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 px-4 flex gap-2">
        <button
          onClick={() => setActiveTab('llm')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'llm'
            ? 'border-purple-600 text-purple-600'
            : 'border-transparent text-slate-600 hover:text-slate-800'
            }`}
        >
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            LLM 选型
          </div>
        </button>
        <button
          onClick={() => setActiveTab('prompt')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'prompt'
            ? 'border-purple-600 text-purple-600'
            : 'border-transparent text-slate-600 hover:text-slate-800'
            }`}
        >
          <div className="flex items-center gap-2">
            <LayoutTemplate className="w-4 h-4" />
            Prompt
          </div>
        </button>
        <button
          onClick={() => setActiveTab('references')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'references'
            ? 'border-purple-600 text-purple-600'
            : 'border-transparent text-slate-600 hover:text-slate-800'
            }`}
        >
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4" />
            参考规范
          </div>
        </button>
        <button
          onClick={() => setActiveTab('templates')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'templates'
            ? 'border-purple-600 text-purple-600'
            : 'border-transparent text-slate-600 hover:text-slate-800'
            }`}
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            模板库
          </div>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'llm' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-600 mb-2">选择 LLM 模型</label>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">请选择模型</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-3">Claude 3</option>
                <option value="gemini-pro">Gemini Pro</option>
              </select>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-sm text-blue-800 mb-2">模型说明</h4>
              <p className="text-xs text-blue-600">
                选择合适的 LLM 模型来生成本章节内容。不同模型具有不同的特性和成本。
              </p>
            </div>
          </div>
        )}

        {activeTab === 'prompt' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-600 mb-2">专业级 Prompt 提示词</label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={12}
                placeholder="请输入提示词，用于指导 LLM 生成本章节内容..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              />
            </div>
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <h4 className="text-sm text-purple-800 mb-2">提示</h4>
              <p className="text-xs text-purple-600">
                使用专业术语和明确的指令，帮助 LLM 生成高质量的报告内容。
              </p>
            </div>
          </div>
        )}

        {activeTab === 'references' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-sm text-slate-600">参考规范列表</label>
              <button
                onClick={() => setReferences([...references, { name: '', url: '' }])}
                className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
              >
                <Plus className="w-4 h-4" />
                添加规范
              </button>
            </div>
            <div className="space-y-3">
              {references.map((ref: any, index: number) => (
                <div key={index} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-start justify-between mb-2">
                    <input
                      type="text"
                      placeholder="规范名称"
                      value={ref.name}
                      onChange={(e) => {
                        const newRefs = [...references];
                        newRefs[index] = { ...newRefs[index], name: e.target.value };
                        setReferences(newRefs);
                      }}
                      className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                    <button
                      onClick={() => setReferences(references.filter((_: any, i: number) => i !== index))}
                      className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder="规范文档路径或 URL"
                    value={ref.url}
                    onChange={(e) => {
                      const newRefs = [...references];
                      newRefs[index] = { ...newRefs[index], url: e.target.value };
                      setReferences(newRefs);
                    }}
                    className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
                  />
                </div>
              ))}
              {references.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-8">暂无参考规范</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'templates' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-sm text-slate-600">模板库</label>
              <button
                onClick={() => setTemplates([...templates, { name: '', content: '' }])}
                className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700"
              >
                <Plus className="w-4 h-4" />
                添加模板
              </button>
            </div>
            <div className="space-y-3">
              {templates.map((template: any, index: number) => (
                <div key={index} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-start justify-between mb-2">
                    <input
                      type="text"
                      placeholder="模板名称"
                      value={template.name}
                      onChange={(e) => {
                        const newTemplates = [...templates];
                        newTemplates[index] = { ...newTemplates[index], name: e.target.value };
                        setTemplates(newTemplates);
                      }}
                      className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                    <button
                      onClick={() => setTemplates(templates.filter((_: any, i: number) => i !== index))}
                      className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <textarea
                    placeholder="模板内容"
                    value={template.content}
                    onChange={(e) => {
                      const newTemplates = [...templates];
                      newTemplates[index] = { ...newTemplates[index], content: e.target.value };
                      setTemplates(newTemplates);
                    }}
                    rows={4}
                    className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-purple-500 resize-none"
                  />
                </div>
              ))}
              {templates.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-8">暂无模板</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-slate-200 p-4 flex gap-2">
        <button
          onClick={handleSave}
          className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          保存配置
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
        >
          取消
        </button>
      </div>
    </div>
  );
}