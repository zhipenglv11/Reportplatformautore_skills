import {
  Plus,
  FlaskConical,
  Cylinder,
  BrickWall,
  Cable,
  Ruler,
  TestTube,
  BookOpen,
  ChevronDown,
  ChevronRight,
  ListTree,
} from "lucide-react";
import { useState, useMemo, useEffect, useRef } from "react";
import { Node } from "reactflow";

interface NodeSidebarProps {
  onAddNode: (type: string) => void;
  mode: "collection" | "report";
  nodes?: Node[];
  onNodeSelect?: (nodeId: string) => void;
  onGenerateReport?: () => void;
}

interface ChapterNode {
  id: string;
  number: string;
  title: string;
  children: ChapterNode[];
  level: number;
  sortKey: number[];
}

export default function NodeSidebar({
  onAddNode,
  mode,
  nodes,
  onNodeSelect,
  onGenerateReport,
}: NodeSidebarProps) {
  const [chapterNumber, setChapterNumber] = useState("");
  const [chapterTitle, setChapterTitle] = useState("");
  const [showTemplates, setShowTemplates] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const [isGenerateReportClicked, setIsGenerateReportClicked] = useState(false);
  
  // 侧边栏宽度调整
  const [sidebarWidth, setSidebarWidth] = useState(288); // 默认 w-72 = 288px
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  
  const MIN_WIDTH = 240;
  const MAX_WIDTH = 480;

  // 开始调整宽度
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  // 监听鼠标移动和释放
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = e.clientX;
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // 处理点击动画
  const handleAddChapter = () => {
    setIsClicked(true);
    setTimeout(() => {
      onAddNode('新章节');
      setChapterNumber('');
      setChapterTitle('');
      setIsClicked(false);
    }, 400);
  };

  // 解析章节编号为数组（支持多种格式：1, 1.1, 1.1.1）
  const parseChapterNumber = (number: string): number[] => {
    if (!number || number.trim() === "") return [999999]; // 无编号的放到最后
    
    const cleaned = number.trim();
    const parts = cleaned.split(".").map((part) => {
      const num = parseInt(part.replace(/[^\d]/g, ""), 10);
      return isNaN(num) ? 0 : num;
    });
    
    return parts.length > 0 ? parts : [999999];
  };

  // 构建章节层级结构（使用 useMemo 优化性能）
  const chapterTree = useMemo(() => {
    if (!nodes || nodes.length === 0) return [];

    // 1. 提取并预处理所有报告节点
    const chapters: ChapterNode[] = nodes
      .filter((node) => node.type === "report")
      .map((node) => {
        const number = node.data.chapterNumber || "";
        const sortKey = parseChapterNumber(number);
        const level = sortKey[0] === 999999 ? 0 : sortKey.length;
        
        return {
          id: node.id,
          number,
          title: node.data.label || "未命名章节",
          children: [],
          level,
          sortKey,
        };
      });

    // 2. 按章节编号排序
    chapters.sort((a, b) => {
      const maxLength = Math.max(a.sortKey.length, b.sortKey.length);
      for (let i = 0; i < maxLength; i++) {
        const aVal = a.sortKey[i] || 0;
        const bVal = b.sortKey[i] || 0;
        if (aVal !== bVal) return aVal - bVal;
      }
      return 0;
    });

    // 3. 构建树形结构
    const tree: ChapterNode[] = [];
    const map = new Map<string, ChapterNode>();

    chapters.forEach((chapter) => {
      // 将章节加入映射表
      map.set(chapter.number, chapter);
      
      if (chapter.sortKey[0] === 999999 || chapter.level === 1) {
        // 无编号或顶层章节（如 "1", "2", "3"）
        tree.push(chapter);
      } else {
        // 子章节（如 "1.1", "1.2.1"）
        const parentKey = chapter.sortKey.slice(0, -1);
        const parentNumber = parentKey.join(".");
        const parent = map.get(parentNumber);
        
        if (parent) {
          parent.children.push(chapter);
        } else {
          // 如果找不到父章节，尝试向上查找
          let found = false;
          for (let i = parentKey.length - 1; i >= 1; i--) {
            const ancestorNumber = parentKey.slice(0, i).join(".");
            const ancestor = map.get(ancestorNumber);
            if (ancestor) {
              ancestor.children.push(chapter);
              found = true;
              break;
            }
          }
          
          // 如果仍然找不到父节点，放到顶层
          if (!found) {
            tree.push(chapter);
          }
        }
      }
    });

    return tree;
  }, [nodes]); // 依赖 nodes，当 nodes 变化时自动重新计算

  // 渲染章节树（使用 chapter.id 作为 key 确保 React 正确追踪）
  const renderChapterTree = (chapters: ChapterNode[], level = 0): JSX.Element[] => {
    return chapters.map((chapter) => (
      <div key={chapter.id} className="transition-all duration-200">
        <div
          className="flex items-start gap-2 py-1.5 px-2 rounded hover:bg-purple-50 transition-colors cursor-pointer group"
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onDoubleClick={() => {
            if (onNodeSelect) {
              onNodeSelect(chapter.id);
            }
          }}
          title="双击定位到节点"
        >
          {chapter.number ? (
            <div className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-mono min-w-[32px] text-center mt-0.5 font-medium group-hover:bg-purple-200 transition-colors">
              {chapter.number}
            </div>
          ) : (
            <div className="px-1.5 py-0.5 bg-slate-200 text-slate-500 rounded text-xs min-w-[32px] text-center mt-0.5 group-hover:bg-slate-300 transition-colors">
              --
            </div>
          )}
          <span className="text-sm text-slate-700 flex-1 leading-relaxed group-hover:text-purple-700 transition-colors">
            {chapter.title}
          </span>
          {chapter.children.length > 0 && (
            <span className="text-xs text-slate-400 mt-0.5 group-hover:text-purple-400 transition-colors">
              ({chapter.children.length})
            </span>
          )}
        </div>
        {chapter.children.length > 0 && (
          <div className="mt-0.5">
            {renderChapterTree(chapter.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  const collectionNodes = [
    {
      type: "mortar-strength",
      label: "砂浆强度",
      icon: FlaskConical,
      color: "blue",
      description: "检测砂浆强度数据",
    },
    {
      type: "concrete-strength",
      label: "混凝土强度",
      icon: Cylinder,
      color: "indigo",
      description: "混凝土抗压强度测试",
    },
    {
      type: "rebar-diameter",
      label: "钢筋直径",
      icon: Cable,
      color: "violet",
      description: "钢筋直径测量数据",
    },
    {
      type: "brick-strength",
      label: "砖强度",
      icon: BrickWall,
      color: "rose",
      description: "砖块强度检测",
    },
    {
      type: "inclination",
      label: "倾斜测量",
      icon: Ruler,
      color: "amber",
      description: "建筑倾斜度测量",
    },
    {
      type: "material-test",
      label: "材料检测",
      icon: TestTube,
      color: "emerald",
      description: "通用材料检测",
    },
  ];

  return (
    <div
      ref={sidebarRef}
      className="relative bg-white border-r border-slate-200 p-4 overflow-y-auto shadow-sm"
      style={{ width: `${sidebarWidth}px` }}
    >
      {/* 拖动调整手柄 */}
      <div
        className={`absolute top-0 right-0 h-full w-1 cursor-col-resize hover:w-1.5 transition-all z-50 group ${
          isResizing ? 'w-1.5 bg-blue-500' : 'hover:bg-blue-400/50'
        }`}
        onMouseDown={handleMouseDown}
      >
        <div className={`absolute inset-y-0 right-0 w-4 ${isResizing ? 'bg-blue-500/10' : ''}`} />
      </div>

      {mode === "collection" ? (
        <div className="space-y-2">
          {collectionNodes.map((node) => {
            const Icon = node.icon;
            // 检查画布上是否已有该类型节点
            const hasNodeOnCanvas = nodes?.some((n) => n.type === node.type) || false;
            
            return (
              <button
                key={node.type}
                onClick={() => onAddNode(node.type)}
                className={`w-full p-3 rounded-lg border transition-all text-left group shadow-sm hover:shadow-md ${
                  hasNodeOnCanvas
                    ? `border-${node.color}-200 bg-${node.color}-50 hover:border-${node.color}-300 hover:bg-${node.color}-100`
                    : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-md ${
                      hasNodeOnCanvas
                        ? `bg-${node.color}-100`
                        : `bg-${node.color}-50`
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${
                      hasNodeOnCanvas
                        ? `text-${node.color}-600`
                        : `text-${node.color}-400`
                    }`} />
                  </div>
                  <div className="flex-1">
                    <div className={`font-medium ${
                      hasNodeOnCanvas
                        ? 'text-slate-800'
                        : 'text-slate-600'
                    }`}>
                      {node.label}
                    </div>
                    <p className={`text-xs mt-0.5 ${
                      hasNodeOnCanvas
                        ? 'text-slate-500'
                        : 'text-slate-400'
                    }`}>
                      {node.description}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="space-y-4">
          {/* 添加章节表单 */}
          <div className="p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg border border-purple-200 hover:border-purple-300 transition-all overflow-hidden">
            <button
              onClick={handleAddChapter}
              className="w-full group relative"
            >
              <div className="flex flex-col items-center gap-3 py-2">
                {/* 聚能环容器 */}
                <div className="relative w-20 h-20 flex items-center justify-center">
                  {/* 外层脉冲环 - 最外圈 */}
                  <div className={`absolute inset-0 rounded-full bg-gradient-to-br from-purple-400/20 to-indigo-400/20 blur-xl transition-all duration-500 ${
                    isClicked 
                      ? 'scale-150 opacity-0' 
                      : 'group-hover:scale-110 group-hover:opacity-100 animate-pulse-slow'
                  }`} />
                  
                  {/* 能量聚集环 - 第二层 */}
                  <div className={`absolute inset-2 rounded-full border-2 border-purple-300/40 transition-all duration-700 ${
                    isClicked
                      ? 'scale-[2] opacity-0 rotate-180'
                      : 'group-hover:scale-95 group-hover:border-purple-400/60 group-hover:rotate-90 animate-spin-slow'
                  }`}>
                    {/* 环上的能量点 */}
                    <div className="absolute top-0 left-1/2 w-1 h-1 -ml-0.5 -mt-0.5 rounded-full bg-purple-400 group-hover:animate-particle-glow" />
                    <div className="absolute bottom-0 left-1/2 w-1 h-1 -ml-0.5 -mb-0.5 rounded-full bg-indigo-400 group-hover:animate-particle-glow" style={{ animationDelay: '0.3s' }} />
                  </div>
                  
                  {/* 内层聚能环 - 第三层 */}
                  <div className={`absolute inset-4 rounded-full border-2 border-indigo-400/50 transition-all duration-500 ${
                    isClicked
                      ? 'scale-[1.8] opacity-0 -rotate-90'
                      : 'group-hover:scale-90 group-hover:border-indigo-500/70 group-hover:-rotate-45 animate-spin-reverse'
                  }`}>
                    {/* 环上的能量点 */}
                    <div className="absolute top-1/2 right-0 w-1 h-1 -mr-0.5 -mt-0.5 rounded-full bg-indigo-400 group-hover:animate-particle-glow" style={{ animationDelay: '0.15s' }} />
                    <div className="absolute top-1/2 left-0 w-1 h-1 -ml-0.5 -mt-0.5 rounded-full bg-purple-400 group-hover:animate-particle-glow" style={{ animationDelay: '0.45s' }} />
                  </div>
                  
                  {/* 能量粒子 - 悬停时从外向内聚集 */}
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={i}
                      className={`absolute w-1.5 h-1.5 rounded-full transition-all duration-500 ${
                        isClicked 
                          ? 'scale-0 opacity-0' 
                          : 'opacity-0 group-hover:opacity-100 group-hover:animate-particle-glow'
                      }`}
                      style={{
                        background: i % 2 === 0 ? 'rgb(168, 85, 247)' : 'rgb(99, 102, 241)',
                        transform: `rotate(${i * 45}deg) translateY(${isClicked ? '0px' : '-28px'})`,
                        animationDelay: `${i * 0.1}s`,
                        transitionDelay: `${i * 0.05}s`,
                      }}
                    />
                  ))}
                  
                  {/* 核心按钮 */}
                  <div className={`relative w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 via-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/40 transition-all duration-300 ${
                    isClicked
                      ? 'scale-75 opacity-0'
                      : 'group-hover:shadow-2xl group-hover:shadow-purple-500/60 group-hover:scale-110'
                  }`}>
                    {/* 核心光晕 */}
                    <div className="absolute inset-0 rounded-full bg-gradient-to-br from-white/20 to-transparent group-hover:from-white/30 transition-all" />
                    
                    {/* 内部脉冲光环 */}
                    <div className="absolute inset-2 rounded-full border border-white/30 opacity-0 group-hover:opacity-100 group-hover:animate-ripple" />
                    
                    {/* Plus 图标 */}
                    <Plus className={`relative w-7 h-7 text-white transition-all duration-300 ${
                      isClicked 
                        ? 'rotate-90 scale-0' 
                        : 'group-hover:rotate-90 group-hover:scale-110'
                    }`} />
                    
                    {/* 点击时的爆裂粒子 */}
                    {isClicked && [...Array(12)].map((_, i) => (
                      <div
                        key={`burst-${i}`}
                        className="absolute w-1.5 h-1.5 rounded-full"
                        style={{
                          background: i % 3 === 0 ? 'rgb(168, 85, 247)' : i % 3 === 1 ? 'rgb(139, 92, 246)' : 'rgb(99, 102, 241)',
                          transform: `rotate(${i * 30}deg) translateY(0px)`,
                          animation: `burst 0.6s ease-out forwards`,
                          animationDelay: `${i * 0.02}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
                
                <div className={`text-center transition-all duration-300 ${
                  isClicked ? 'opacity-0 scale-95' : 'opacity-100'
                }`}>
                  <h4 className="text-sm font-semibold text-purple-900 mb-1 group-hover:text-purple-700 transition-colors">
                    添加章节节点
                  </h4>
                  <p className="text-xs text-purple-700/70 group-hover:text-purple-600 transition-colors">
                    点击添加到画布
                  </p>
                </div>
              </div>
            </button>
          </div>

          {/* 快速模板 */}
          <div>
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="w-full flex items-center justify-between text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wider hover:text-slate-800 transition-colors"
            >
              <span>快速模板</span>
              {showTemplates ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
            {showTemplates && (
              <div className="space-y-2">
                {[
                  { number: "1", title: "概述" },
                  { number: "2", title: "依据标准及规范" },
                  { number: "3", title: "检测内容与方法" },
                  { number: "4", title: "检测结果" },
                  { number: "5", title: "检测结论" },
                  { number: "6", title: "附录" },
                ].map((template) => (
                  <button
                    key={template.number}
                    onClick={() =>
                      onAddNode(
                        `第${template.number}章 ${template.title}`,
                      )
                    }
                    className="w-full p-2.5 rounded-lg border border-slate-200 bg-white hover:border-purple-300 hover:bg-purple-50 transition-all text-left group"
                  >
                    <div className="flex items-center gap-2">
                      <div className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono text-slate-600 group-hover:bg-purple-100 group-hover:text-purple-700">
                        {template.number}
                      </div>
                      <span className="text-sm text-slate-700 group-hover:text-purple-700">
                        {template.title}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 报告结构预览 */}
          {chapterTree.length > 0 && (
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-xs font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <ListTree className="w-4 h-4" />
                当前报告结构
              </h4>
              <div className="max-h-64 overflow-y-auto">
                {renderChapterTree(chapterTree)}
              </div>
              <div className="mt-3 pt-3 border-t border-slate-200">
                <p className="text-xs text-slate-500">
                  共{" "}
                  {nodes?.filter((n) => n.type === "report")
                    .length || 0}{" "}
                  个章节
                </p>
              </div>
            </div>
          )}

          {/* 生成报告按钮 */}
          {onGenerateReport && (
            <button
              onClick={() => {
                setIsGenerateReportClicked(true);
                onGenerateReport();
              }}
              className={`group w-full p-4 rounded-lg border-2 transition-all duration-500 overflow-hidden relative ${
                isGenerateReportClicked
                  ? 'border-transparent bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600'
                  : 'border-slate-300 bg-slate-100 hover:border-transparent'
              }`}
            >
              {/* 彩色渐变背景 - 点击后始终显示，未点击时悬停显示 */}
              <div className={`absolute inset-0 bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 transition-opacity duration-500 ${
                isGenerateReportClicked
                  ? 'opacity-100'
                  : 'opacity-0 group-hover:opacity-100'
              }`} />
              
              {/* 背景光效 */}
              <div className={`absolute inset-0 bg-gradient-to-r from-purple-400 via-indigo-400 to-blue-400 blur-xl transition-opacity duration-500 ${
                isGenerateReportClicked
                  ? 'opacity-30'
                  : 'opacity-0 group-hover:opacity-30'
              }`} />
              
              {/* 未点击时的吸引动画 - 轻微脉冲边框 */}
              {!isGenerateReportClicked && (
                <>
                  {/* 脉冲边框 */}
                  <div className="absolute inset-0 rounded-lg border-2 border-purple-300/40 animate-pulse-slow" />
                  
                  {/* 轻微光晕 */}
                  <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-purple-200/20 via-indigo-200/20 to-blue-200/20 animate-pulse-slow" />
                  
                  {/* 流动光效 */}
                  <div className="absolute inset-0 rounded-lg overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-200/30 to-transparent animate-shimmer" 
                         style={{ 
                           backgroundSize: '200% 100%',
                           animation: 'shimmer 3s infinite linear'
                         }} />
                  </div>
                </>
              )}
              
              {/* 按钮内容 */}
              <div className={`relative flex items-center justify-center gap-2 transition-colors duration-500 ${
                isGenerateReportClicked
                  ? 'text-white'
                  : 'text-slate-700 group-hover:text-white'
              }`}>
                <BookOpen className={`w-5 h-5 transition-all duration-500 ${
                  isGenerateReportClicked
                    ? 'animate-pulse'
                    : 'group-hover:animate-pulse'
                } ${!isGenerateReportClicked && 'animate-bounce-subtle'}`} />
                <span className="font-semibold">生成报告</span>
              </div>

              {/* 闪烁光点 */}
              <div className={`absolute top-1/2 left-1/4 w-1.5 h-1.5 bg-white rounded-full transition-opacity duration-500 ${
                isGenerateReportClicked || 'opacity-0'
              } group-hover:opacity-100 group-hover:animate-ping`} />
              <div className={`absolute top-1/3 right-1/4 w-1 h-1 bg-white rounded-full transition-opacity duration-500 ${
                isGenerateReportClicked || 'opacity-0'
              } group-hover:opacity-100 group-hover:animate-ping`} style={{ animationDelay: '0.2s' }} />
            </button>
          )}
        </div>
      )}

      <div className="mt-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
        <h4 className="text-xs text-slate-500 mb-2">
          使用提示
        </h4>
        <p className="text-xs text-slate-600">
          {mode === "collection"
            ? "选择数据类型添加到画布，连接节点创建数据流程"
            : "添加章节节点，配置LLM和提示词生成报告内容。双击章节标题可定位到画布节点。"}
        </p>
      </div>
    </div>
  );
}