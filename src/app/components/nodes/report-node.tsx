import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const chapterColors = [
  { border: 'border-blue-200', bg: 'bg-blue-50', text: 'text-blue-700', icon: 'text-blue-500', hover: 'hover:border-blue-300' },
  { border: 'border-purple-200', bg: 'bg-purple-50', text: 'text-purple-700', icon: 'text-purple-500', hover: 'hover:border-purple-300' },
  { border: 'border-emerald-200', bg: 'bg-emerald-50', text: 'text-emerald-700', icon: 'text-emerald-500', hover: 'hover:border-emerald-300' },
  { border: 'border-orange-200', bg: 'bg-orange-50', text: 'text-orange-700', icon: 'text-orange-500', hover: 'hover:border-orange-300' },
  { border: 'border-pink-200', bg: 'bg-pink-50', text: 'text-pink-700', icon: 'text-pink-500', hover: 'hover:border-pink-300' },
  { border: 'border-cyan-200', bg: 'bg-cyan-50', text: 'text-cyan-700', icon: 'text-cyan-500', hover: 'hover:border-cyan-300' },
];

function getTopLevelChapterIndex(chapterNumber: string): number {
  if (!chapterNumber) return 0;
  
  // 提取第一个数字
  const match = chapterNumber.match(/^(\d+)/);
  if (match) {
    const num = parseInt(match[1], 10);
    return (num - 1) % chapterColors.length;
  }
  
  // 处理中文数字 (简单处理一到十)
  const cnNums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
  const firstChar = chapterNumber.charAt(0);
  const index = cnNums.indexOf(firstChar);
  if (index !== -1) {
    return index % chapterColors.length;
  }

  return 0; // 默认第一个颜色
}

function ReportNode({ data }: any) {
  // 获取规范和文档信息
  // 优先使用新的数据结构（systemReferenceCode/userReferenceCode），兼容旧的数据结构（referenceCode/referenceTab）
  const systemReferenceCode = data.systemReferenceCode || (data.referenceTab === 'system' ? (data.referenceCode || data.referenceSpec) : '');
  const userReferenceCode = data.userReferenceCode || (data.referenceTab === 'user' ? (data.referenceCode || data.referenceSpec) : '');
  
  // 构建显示标签列表
  const referenceLabels: string[] = [];
  if (systemReferenceCode) {
    referenceLabels.push(`规范：${systemReferenceCode}`);
  }
  if (userReferenceCode) {
    referenceLabels.push(`文档：${userReferenceCode}`);
  }

  const status = data.status || 'idle'; // idle, running, completed

  // 根据章节编号获取颜色
  const colorIndex = getTopLevelChapterIndex(data.chapterNumber);
  const colors = chapterColors[colorIndex];

  return (
    <div className={`relative bg-white rounded-xl shadow-lg border min-w-[320px] overflow-hidden transition-all duration-300
      ${status === 'running' ? 'border-transparent shadow-red-100' : ''}
      ${status === 'completed' ? 'border-green-500 shadow-green-100' : colors.border}
      ${status === 'idle' ? `${colors.hover} hover:shadow-xl` : ''}
    `}>
      {/* Running Animation: SVG Marquee Effect */}
      {status === 'running' && (
        <div className="absolute inset-0 z-0 pointer-events-none rounded-xl overflow-visible">
          <svg className="absolute inset-0 w-full h-full overflow-visible">
            <rect
              x="2"
              y="2"
              width="calc(100% - 4px)"
              height="calc(100% - 4px)"
              rx="10"
              ry="10"
              fill="none"
              stroke="#ef4444"
              strokeWidth="3"
              strokeDasharray="12 8"
              strokeLinecap="round"
              className="animate-[dash_1s_linear_infinite]"
            />
          </svg>
          <style>{`
            @keyframes dash {
              to {
                stroke-dashoffset: -20;
              }
            }
          `}</style>
        </div>
      )}

      {/* Status Indicators Overlay */}
      {status === 'running' && (
        <div className="absolute top-2 right-2 z-10 bg-white/90 backdrop-blur px-2 py-1 rounded-full shadow-sm border border-slate-100 flex items-center gap-1.5 animate-pulse">
          <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
          <span className="text-[10px] font-medium text-slate-600">生成中...</span>
        </div>
      )}
      {status === 'completed' && (
        <div className="absolute top-2 right-2 z-10 bg-emerald-50 px-2 py-1 rounded-full border border-emerald-100 flex items-center gap-1.5">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          <span className="text-[10px] font-medium text-emerald-700">已生成</span>
        </div>
      )}

      {/* Header */}
      <div className={`px-4 py-3 border-b flex items-center justify-between ${status === 'completed' ? 'bg-emerald-50/50 border-emerald-100' : `${colors.bg} ${colors.border}`}`}>
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-white shadow-sm ${status === 'completed' ? 'text-emerald-600' : colors.icon}`}>
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-1.5 py-0.5 rounded bg-white/60 ${status === 'completed' ? 'text-emerald-700' : colors.text}`}>
                {data.chapterNumber || '1.0'}
              </span>
              <h3 className="font-bold text-slate-800 text-sm">
                {data.label || '未命名章节'}
              </h3>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5 font-medium">
              报告生成节点
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      {referenceLabels.length > 0 && (
        <div className="px-4 py-2.5 space-y-1.5">
          {referenceLabels.map((label, index) => (
            <div key={index} className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 px-2 py-1.5 rounded border border-slate-100">
              <div className="w-1 h-3 bg-slate-300 rounded-full"></div>
              <span className="truncate flex-1" title={label}>
                {label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-slate-400 !border-2 !border-white shadow-sm"
      />
      {/* 
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-slate-400 !border-2 !border-white shadow-sm"
      />
      */}
    </div>
  );
}

export default memo(ReportNode);
