import { memo } from 'react';
import { FileText, Brain, BookOpen, LayoutTemplate } from 'lucide-react';

// 定义章节颜色方案（高端商务配色）
const chapterColors = [
  {
    name: 'blue',
    gradient: 'from-blue-500 to-blue-600',
    handle: 'bg-blue-400',
    border: 'border-blue-200',
    hover: 'hover:shadow-blue-100',
  },
  {
    name: 'purple',
    gradient: 'from-purple-500 to-purple-600',
    handle: 'bg-purple-400',
    border: 'border-purple-200',
    hover: 'hover:shadow-purple-100',
  },
  {
    name: 'indigo',
    gradient: 'from-indigo-500 to-indigo-600',
    handle: 'bg-indigo-400',
    border: 'border-indigo-200',
    hover: 'hover:shadow-indigo-100',
  },
  {
    name: 'violet',
    gradient: 'from-violet-500 to-violet-600',
    handle: 'bg-violet-400',
    border: 'border-violet-200',
    hover: 'hover:shadow-violet-100',
  },
  {
    name: 'fuchsia',
    gradient: 'from-fuchsia-500 to-fuchsia-600',
    handle: 'bg-fuchsia-400',
    border: 'border-fuchsia-200',
    hover: 'hover:shadow-fuchsia-100',
  },
  {
    name: 'pink',
    gradient: 'from-pink-500 to-pink-600',
    handle: 'bg-pink-400',
    border: 'border-pink-200',
    hover: 'hover:shadow-pink-100',
  },
  {
    name: 'rose',
    gradient: 'from-rose-500 to-rose-600',
    handle: 'bg-rose-400',
    border: 'border-rose-200',
    hover: 'hover:shadow-rose-100',
  },
  {
    name: 'cyan',
    gradient: 'from-cyan-500 to-cyan-600',
    handle: 'bg-cyan-400',
    border: 'border-cyan-200',
    hover: 'hover:shadow-cyan-100',
  },
  {
    name: 'teal',
    gradient: 'from-teal-500 to-teal-600',
    handle: 'bg-teal-400',
    border: 'border-teal-200',
    hover: 'hover:shadow-teal-100',
  },
  {
    name: 'emerald',
    gradient: 'from-emerald-500 to-emerald-600',
    handle: 'bg-emerald-400',
    border: 'border-emerald-200',
    hover: 'hover:shadow-emerald-100',
  },
];

// 根据章节编号获取顶层章节索引
function getTopLevelChapterIndex(chapterNumber: string): number {
  if (!chapterNumber || chapterNumber.trim() === '') return 0;
  
  // 提取第一个数字（如 "1.1.2" -> 1, "3" -> 3）
  const match = chapterNumber.match(/^(\d+)/);
  if (match) {
    const topLevel = parseInt(match[1], 10);
    return (topLevel - 1) % chapterColors.length; // 循环使用颜色
  }
  
  return 0; // 默认第一个颜色
}

function ReportNode({ data }: any) {
  const hasLLM = data.llmModel && data.llmModel.length > 0;
  const hasPrompt = data.prompt && data.prompt.length > 0;
  const hasReferences = data.references && data.references.length > 0;
  const hasTemplates = data.templates && data.templates.length > 0;

  // 根据章节编号获取颜色
  const colorIndex = getTopLevelChapterIndex(data.chapterNumber);
  const colors = chapterColors[colorIndex];

  return (
    <div className={`bg-white rounded-xl shadow-lg border ${colors.border} min-w-[320px] overflow-hidden hover:shadow-xl ${colors.hover} transition-all`}>
      <div className={`bg-gradient-to-r ${colors.gradient} px-4 py-2 text-white flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4" />
          <span className="font-medium text-sm">{data.label}</span>
        </div>
        <div className="text-xs opacity-90 bg-white/20 px-2 py-0.5 rounded">章节 {data.chapterNumber}</div>
      </div>
      
      <div className="px-4 py-2.5 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {/* LLM Model */}
        <div className="flex items-center gap-1.5 text-xs">
          <Brain className={`w-3.5 h-3.5 flex-shrink-0 ${hasLLM ? 'text-green-500' : 'text-slate-300'}`} />
          <span className={`truncate ${hasLLM ? 'text-slate-700' : 'text-slate-400'}`}>
            {hasLLM ? data.llmModel : 'LLM 未配置'}
          </span>
        </div>
        
        {/* Prompt */}
        <div className="flex items-center gap-1.5 text-xs">
          <LayoutTemplate className={`w-3.5 h-3.5 flex-shrink-0 ${hasPrompt ? 'text-green-500' : 'text-slate-300'}`} />
          <span className={hasPrompt ? 'text-slate-700' : 'text-slate-400'}>
            {hasPrompt ? 'Prompt 已配置' : 'Prompt 未配置'}
          </span>
        </div>
        
        {/* References */}
        <div className="flex items-center gap-1.5 text-xs">
          <BookOpen className={`w-3.5 h-3.5 flex-shrink-0 ${hasReferences ? 'text-green-500' : 'text-slate-300'}`} />
          <span className={hasReferences ? 'text-slate-700' : 'text-slate-400'}>
            {hasReferences ? `${data.references.length} 个规范` : '参考规范'}
          </span>
        </div>
        
        {/* Templates */}
        <div className="flex items-center gap-1.5 text-xs">
          <FileText className={`w-3.5 h-3.5 flex-shrink-0 ${hasTemplates ? 'text-green-500' : 'text-slate-300'}`} />
          <span className={hasTemplates ? 'text-slate-700' : 'text-slate-400'}>
            {hasTemplates ? `${data.templates.length} 个模板` : '模板库'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default memo(ReportNode);