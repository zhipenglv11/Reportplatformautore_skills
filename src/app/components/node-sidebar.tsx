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
  Search,
  Users,
  FileBox,
  X,
  ArrowRight,
  ListTree,
  LayoutTemplate,
  Star,
  Calculator,
  HelpCircle,
  Square,
  Loader2,
  PenLine,
  ClipboardCheck,
  FileText,
  UploadCloud,
  Sparkles,
} from "lucide-react";
import { useState, useMemo, useEffect, useRef } from "react";
import { Node } from "reactflow";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "./ui/accordion";
import { cn } from "./ui/utils";

interface NodeSidebarProps {
  onAddNode: (type: string) => void;
  mode: "collection" | "report";
  nodes?: Node[];
  onNodeSelect?: (nodeId: string) => void;
  onGenerateReport?: () => void;
  onStopGeneration?: () => void;
  isGenerating?: boolean;
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
  onStopGeneration,
  isGenerating = false,
}: NodeSidebarProps) {
  const [chapterNumber, setChapterNumber] = useState("");
  const [chapterTitle, setChapterTitle] = useState("");
  const [showTemplates, setShowTemplates] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const [isGenerateReportClicked, setIsGenerateReportClicked] = useState(false);
  const [activeCategory, setActiveCategory] = useState<"recommended" | "shared" | "favorites">("recommended");
  // 每个类别的搜索词
  const [categorySearchTerms, setCategorySearchTerms] = useState<Record<number, string>>({});
  // 收藏的模板列表（存储模板标题）
  const [favoriteTemplates, setFavoriteTemplates] = useState<string[]>(() => {
    // 从 localStorage 读取收藏列表
    const saved = localStorage.getItem('favoriteTemplates');
    return saved ? JSON.parse(saved) : [];
  });

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

      // 使用 e.clientX 计算新的宽度
      // 假设侧边栏在左侧：新宽度 = 鼠标当前 X 坐标
      // 假设侧边栏在右侧：新宽度 = 窗口宽度 - 鼠标当前 X 坐标
      // 根据提供的 DOM 路径，该侧边栏在右侧 (right-0)，所以应该是：
      // 但根据 UI 上下文，NodeSidebar 通常在左侧或右侧。
      // 这里的 resize handle 是 absolute top-0 right-0，说明它在组件的右边缘。
      // 这意味着这个 Sidebar 是靠左放置的，向右拖动增加宽度。
      
      // 用户反馈鼠标跳动问题，通常是因为基于 clientX 的计算没有考虑到容器的偏移
      // 或者在拖动过程中触发了其他布局变化。
      // 让我们更仔细地检查计算逻辑。
      
      // 原逻辑：
      // const newWidth = e.clientX;
      // 这意味着 sidebar 是绝对定位或固定定位在屏幕左边缘的，或者它的左边缘就在 x=0 处。
      // 如果 sidebar 前面有其他元素（比如 ProjectSidebar），那么 e.clientX 就不等于 sidebar 的宽度。
      
      // 修正逻辑：
      // 1. 获取 sidebar 左边缘的 X 坐标
      // 2. 新宽度 = 鼠标 X - sidebar 左边缘 X
      
      if (sidebarRef.current) {
         const sidebarRect = sidebarRef.current.getBoundingClientRect();
         const newWidth = e.clientX - sidebarRect.left;
         
         if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
           setSidebarWidth(newWidth);
         }
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

  // 解析章节编号为数组（支持多种格式：1, 1.1, 1.1.1, 一, 一.1）
  const parseChapterNumber = (number: string): number[] => {
    if (!number || number.trim() === "") return [999999]; // 无编号的放到最后

    const cleaned = number.trim();
    // 替换中文顿号、句号为点
    const normalized = cleaned.replace(/[、。]/g, '.');
    
    const parts = normalized.split(".").map((part) => {
      // 尝试解析中文数字
      const cnNum = chineseToNumber(part);
      if (cnNum > 0) return cnNum;

      // 解析阿拉伯数字
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
      // 将章节加入映射表，使用标准化后的 key (如 "1.2.3")
      const normalizedKey = chapter.sortKey.join('.');
      map.set(normalizedKey, chapter);

      // 同时尝试保存原始编号作为 key，以防万一
      if (chapter.number && chapter.number !== normalizedKey) {
      map.set(chapter.number, chapter);
      }
    });

    chapters.forEach((chapter) => {
      if (chapter.sortKey[0] === 999999 || chapter.level === 1) {
        // 无编号或顶层章节（如 "1", "2", "3"）
        tree.push(chapter);
      } else {
        // 子章节（如 "1.1", "1.2.1"）
        const parentKey = chapter.sortKey.slice(0, -1).join('.');
        const parent = map.get(parentKey);

        if (parent) {
          parent.children.push(chapter);
        } else {
          // 如果找不到父章节，尝试向上查找
          let found = false;
          // ... 向上查找逻辑需要基于 normalizedKey ...
          // 这里的向上查找逻辑可能比较复杂，先简化处理：
          // 如果找不到直接父节点，尝试找 "1" 这样的父节点 (对于 "1.1")
          // 实际上 parentKey 已经是直接父节点的 normalizedKey 了

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

  const collectionCategories = [
    {
      title: "智能采集",
      nodes: [
        {
          type: "multi-doc-upload",
          label: "多文档智能上传",
          icon: UploadCloud,
          color: "sky",
          description: "批量上传文档，AI自动识别并分发",
        },
      ],
    },
    {
      title: "检测前信息",
      nodes: [
        {
          type: "delegate-info",
          label: "委托方资料",
          icon: FileText,
          color: "purple",
          description: "项目及委托单位基本信息",
        },
      ],
    },
    {
      title: "检测中数据",
      nodes: [
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
    {
      type: "site-inspection",
      label: "现场情况检查",
      icon: ClipboardCheck,
      color: "teal",
      description: "现场情况检查与记录",
        },
      ],
    },
    {
      title: "检测后数据",
      nodes: [
    {
      type: "software-calculation",
      label: "软件计算结果",
      icon: Calculator,
      color: "cyan",
      description: "结构计算软件分析结果",
        },
      ],
    },
  ];

  // Recommended Templates
  const recommendedTemplates = [
    { title: "民用建筑可靠性鉴定", desc: "依据《民用建筑可靠性鉴定标准》对安全性与使用性进行评估", color: "from-indigo-500 to-purple-600", nodes: 8 },
    { title: "工业建筑可靠性鉴定", desc: "针对厂房等工业建筑结构系统、构件及材料的综合鉴定", color: "from-slate-500 to-slate-700", nodes: 10 },
    { title: "危险房屋鉴定", desc: "依照《危险房屋鉴定标准》评定房屋危险性等级", color: "from-red-500 to-red-700", nodes: 8 },
    { title: "抗震鉴定", desc: "既有建筑抗震性能评估及抗震承载力验算", color: "from-orange-500 to-amber-600", nodes: 7 },
    { title: "主体结构施工质量鉴定", desc: "混凝土结构、砌体结构等主体工程施工质量验收与评估", color: "from-blue-600 to-cyan-600", nodes: 6 },
  ];

  // Team Shared Templates
  const sharedTemplates = [
    { title: "标准结构检测报告", desc: "包含外观质量、强度检测、钢筋配置等全套流程", color: "from-blue-500 to-indigo-600", nodes: 6 },
    { title: "混凝土专项检测", desc: "专注混凝土强度、回弹法及钻芯法检测流程", color: "from-emerald-500 to-teal-600", nodes: 4 },
    { title: "钢筋保护层厚度检测", desc: "针对梁板墙柱的钢筋位置及保护层厚度专项", color: "from-orange-500 to-rose-600", nodes: 3 },
    { title: "建筑物沉降观测", desc: "沉降观测点布设及周期性观测数据分析", color: "from-violet-500 to-purple-600", nodes: 5 },
    { title: "装配式结构验收", desc: "预制构件进场、连接节点及灌浆质量验收", color: "from-cyan-500 to-blue-600", nodes: 7 },
    { title: "节能工程检测", desc: "墙体保温、门窗气密性及系统节能性能检测", color: "from-pink-500 to-rose-500", nodes: 4 },
  ];

  // 切换收藏状态
  const toggleFavorite = (templateTitle: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止触发模板卡片的点击事件
    setFavoriteTemplates((prev) => {
      const isFavorite = prev.includes(templateTitle);
      const newFavorites = isFavorite
        ? prev.filter((title) => title !== templateTitle)
        : [...prev, templateTitle];
      // 保存到 localStorage
      localStorage.setItem('favoriteTemplates', JSON.stringify(newFavorites));
      return newFavorites;
    });
  };

  // 检查模板是否已收藏
  const isFavorite = (templateTitle: string): boolean => {
    return favoriteTemplates.includes(templateTitle);
  };

  // 获取所有模板（推荐 + 共享）
  const getAllTemplates = () => {
    return [...recommendedTemplates, ...sharedTemplates];
  };

  const getActiveTemplates = () => {
    switch (activeCategory) {
      case "shared":
        return sharedTemplates;
      case "favorites":
        // 从所有模板中筛选出收藏的模板
        return getAllTemplates().filter((template) => 
          favoriteTemplates.includes(template.title)
        );
      default:
        return recommendedTemplates;
    }
  };

  const getActiveTitle = () => {
    switch (activeCategory) {
      case "shared":
        return { title: "团队共享模板", desc: "团队成员共享的标准报告模板，统一规范" };
      case "favorites":
        return { title: "我的收藏", desc: "您收藏的常用模板" };
      default:
        return { title: "推荐报告模板", desc: "预设的标准工程检测报告结构，可直接使用" };
    }
  };

  const currentInfo = getActiveTitle();

  return (
    <div
      ref={sidebarRef}
      className="relative bg-white border-r border-slate-200 flex flex-col h-full shadow-sm"
      style={{ width: `${sidebarWidth}px` }}
    >
      {/* 拖动调整手柄 */}
      <div
        className={`absolute top-0 right-0 h-full w-1 cursor-col-resize hover:w-1.5 transition-all z-50 group ${isResizing ? 'w-1.5 bg-blue-500' : 'hover:bg-blue-400/50'
          }`}
        onMouseDown={handleMouseDown}
      >
        <div className={`absolute inset-y-0 right-0 w-4 ${isResizing ? 'bg-blue-500/10' : ''}`} />
      </div>

      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
      {mode === "collection" ? (
        <div className="space-y-1">
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200">
            <h4 className="text-xs font-semibold text-slate-600">数据采集节点</h4>
            <div className="relative group/help">
              <HelpCircle className="w-3.5 h-3.5 text-slate-400 cursor-help hover:text-slate-600 transition-colors" />
              <div className="absolute right-0 top-full mt-2 w-48 p-2 bg-slate-800 text-white text-[10px] rounded shadow-lg opacity-0 invisible group-hover/help:opacity-100 group-hover/help:visible transition-all z-50 pointer-events-none leading-relaxed">
                选择数据类型添加到画布，连接节点创建数据流程。
                <div className="absolute right-3 bottom-full w-2 h-2 bg-slate-800 rotate-45 translate-y-1" />
              </div>
            </div>
          </div>
          <Accordion type="multiple" className="w-full">
            {collectionCategories.map((category, index) => {
              const categoryValue = `category-${index}`;
              return (
                <AccordionItem key={index} value={categoryValue} className="border-b border-slate-100 last:border-b-0">
                  <AccordionTrigger className={cn(
                    "py-2 px-0 hover:no-underline [&>svg]:w-3.5 [&>svg]:h-3.5 [&>svg]:text-slate-500",
                    "focus-visible:ring-0 focus-visible:ring-offset-0"
                  )}>
                    <span className="text-xs font-semibold text-slate-700">{category.title}</span>
                  </AccordionTrigger>
                  <AccordionContent className="pt-1.5 pb-2">
                    <div className="space-y-1.5">
                      {/* 搜索输入框 */}
                      <div className="relative mb-1.5">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
                        <input
                          type="text"
                          placeholder="搜索节点..."
                          value={categorySearchTerms[index] || ''}
                          onChange={(e) => {
                            setCategorySearchTerms(prev => ({
                              ...prev,
                              [index]: e.target.value
                            }));
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="w-full pl-7 pr-2 py-1.5 text-xs border border-slate-200 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 placeholder:text-slate-400"
                        />
                      </div>
                      {/* 节点列表 */}
                      <div className="space-y-1">
                        {category.nodes
                          .filter((node) => {
                            const searchTerm = (categorySearchTerms[index] || '').toLowerCase().trim();
                            if (!searchTerm) return true;
                            return node.label.toLowerCase().includes(searchTerm) ||
                                   node.description.toLowerCase().includes(searchTerm);
                          })
                          .map((node) => {
            const Icon = node.icon;
            const hasNodeOnCanvas = nodes?.some((n) => n.type === node.type) || false;
            
            // Only enable specific skills as requested
            const enabledSkills = ["委托方资料", "砂浆强度", "混凝土强度", "砖强度", "现场情况检查", "多文档智能上传"];
            const isEnabled = enabledSkills.includes(node.label);

            return (
              <button
                key={node.type}
                disabled={!isEnabled}
                title={!isEnabled ? "该功能尚未开放" : ""}
                onClick={() => isEnabled && onAddNode(node.type)}
                                className={cn(
                                  "w-full px-2 py-1.5 rounded border transition-all text-left group",
                                  isEnabled && "hover:shadow-sm",
                                  !isEnabled && "opacity-50 cursor-not-allowed bg-slate-50",
                                  isEnabled && hasNodeOnCanvas
                                    ? "border-slate-300 bg-slate-100 hover:bg-slate-200"
                                    : isEnabled ? "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50" : "border-slate-200"
                                )}
              >
                                <div className="flex items-center gap-2">
                  <div
                                    className={cn(
                                      "p-1 rounded",
                                      hasNodeOnCanvas
                                        ? "bg-slate-200"
                                        : "bg-slate-100"
                                    )}
                  >
                                    <Icon className={cn(
                                      "w-3 h-3",
                                      !isEnabled ? "text-slate-300" : 
                                      hasNodeOnCanvas
                                        ? "text-slate-700"
                                        : "text-slate-500"
                                    )} />
                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className={cn(
                                      "text-xs font-medium truncate",
                                      !isEnabled ? "text-slate-400" :
                                      hasNodeOnCanvas
                                        ? "text-slate-800"
                                        : "text-slate-700"
                                    )}>
                      {node.label}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
                        {/* 无搜索结果提示 */}
                        {category.nodes.filter((node) => {
                          const searchTerm = (categorySearchTerms[index] || '').toLowerCase().trim();
                          if (!searchTerm) return false;
                          return node.label.toLowerCase().includes(searchTerm) ||
                                 node.description.toLowerCase().includes(searchTerm);
                        }).length === 0 && categorySearchTerms[index] && (
                          <div className="text-xs text-slate-400 text-center py-2">
                            未找到匹配的节点
                          </div>
                        )}
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Rapid Templates - Moved to Top */}
          <div className="mb-4">
            <button
              onClick={() => setShowTemplates(true)}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white hover:border-purple-300 hover:bg-purple-50 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-md group-hover:bg-indigo-100 group-hover:text-indigo-700 transition-colors">
                  <LayoutTemplate className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <div className="font-medium text-slate-700 group-hover:text-purple-700">快速模板库</div>
                  <div className="text-xs text-slate-400 group-hover:text-purple-500">浏览 20+ 个预制报告模板</div>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-400" />
            </button>
          </div>

          {/* Template Modal - Figma Style */}
          {showTemplates && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-8" onClick={() => setShowTemplates(false)}>
              <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl h-[700px] flex overflow-hidden animate-in fade-in zoom-in-95 duration-200" onClick={(e) => e.stopPropagation()}>
                {/* Modal Sidebar */}
                <div className="w-64 border-r border-slate-200 bg-slate-50 flex flex-col">
                  <div className="p-4 border-b border-slate-200">
                    <h2 className="font-semibold text-slate-800 mb-4">模板库</h2>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        placeholder="搜索模板..."
                        className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    <button
                      onClick={() => setActiveCategory("recommended")}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeCategory === "recommended"
                        ? "bg-white shadow-sm border border-slate-200 text-purple-700"
                        : "text-slate-600 hover:bg-slate-100"
                        }`}
                    >
                      <BookOpen className={`w-4 h-4 ${activeCategory === "recommended" ? "text-purple-600" : "text-slate-400"}`} />
                      <span>推荐模板</span>
                    </button>
                    <button
                      onClick={() => setActiveCategory("shared")}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeCategory === "shared"
                        ? "bg-white shadow-sm border border-slate-200 text-purple-700"
                        : "text-slate-600 hover:bg-slate-100"
                        }`}
                    >
                      <Users className={`w-4 h-4 ${activeCategory === "shared" ? "text-purple-600" : "text-slate-400"}`} />
                      <span>团队共享</span>
                    </button>
                    <button
                      onClick={() => setActiveCategory("favorites")}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeCategory === "favorites"
                        ? "bg-white shadow-sm border border-slate-200 text-purple-700"
                        : "text-slate-600 hover:bg-slate-100"
                        }`}
                    >
                      <FileBox className={`w-4 h-4 ${activeCategory === "favorites" ? "text-purple-600" : "text-slate-400"}`} />
                      <span>我的收藏</span>
                    </button>
                  </div>
                  <div className="p-4 border-t border-slate-200">
                    <button className="w-full py-2 border border-dashed border-slate-300 rounded-lg text-sm text-slate-500 hover:border-purple-400 hover:text-purple-600 hover:bg-purple-50 transition-all flex items-center justify-center gap-2">
                      <Plus className="w-4 h-4" />
                      <span>新建模板</span>
                    </button>
                  </div>
                </div>

                {/* Modal Content */}
                <div className="flex-1 flex flex-col bg-white">
                  <div className="p-6 border-b border-slate-200 flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-bold text-slate-800">{currentInfo.title}</h3>
                      <p className="text-sm text-slate-500">{currentInfo.desc}</p>
                    </div>
                    <button
                      onClick={() => setShowTemplates(false)}
                      className="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
                    <div className="grid grid-cols-3 gap-6">
                      {/* Template Cards */}
                      {getActiveTemplates().length > 0 ? (
                        getActiveTemplates().map((item, i) => (
                          <div key={i} className="group bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-xl hover:border-purple-300 transition-all cursor-pointer flex flex-col h-64"
                            onClick={() => {
                              // 传递模板信息，格式：TEMPLATE:模板名称
                              onAddNode(`TEMPLATE:${item.title}`);
                              setShowTemplates(false);
                            }}
                          >
                            <div className={`h-32 bg-gradient-to-br ${item.color} p-4 flex items-start justify-end relative overflow-hidden`}>
                              <div className="absolute inset-0 bg-white/10 group-hover:bg-transparent transition-colors" />
                              {/* Abstract Shapes */}
                              <div className="absolute -bottom-8 -left-8 w-24 h-24 bg-white/20 rounded-full blur-xl" />
                              
                              {/* 收藏按钮 - 左上角 */}
                              <button
                                onClick={(e) => toggleFavorite(item.title, e)}
                                className={`absolute top-3 left-3 p-2 rounded-lg backdrop-blur-md transition-all z-10 ${
                                  isFavorite(item.title)
                                    ? 'bg-yellow-400/90 text-yellow-900 hover:bg-yellow-500/90'
                                    : 'bg-white/20 text-white hover:bg-white/30'
                                }`}
                                title={isFavorite(item.title) ? '取消收藏' : '收藏'}
                              >
                                <Star 
                                  className={`w-4 h-4 transition-all ${
                                    isFavorite(item.title) ? 'fill-current' : ''
                                  }`} 
                                />
                              </button>
                              
                              <div className="absolute top-4 right-4 bg-white/20 backdrop-blur-md px-2 py-1 rounded text-xs font-medium text-white border border-white/30">
                                {item.nodes} 个节点
                              </div>
                            </div>
                            <div className="p-4 flex-1 flex flex-col">
                              <h4 className="font-bold text-slate-800 group-hover:text-purple-700 transition-colors mb-2">{item.title}</h4>
                              <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{item.desc}</p>
                              <div className="mt-auto pt-3 flex items-center text-xs font-medium text-slate-400 group-hover:text-purple-600">
                                <span>点击应用</span>
                                <ArrowRight className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="col-span-3 flex flex-col items-center justify-center p-12 text-slate-400">
                          <FileBox className="w-12 h-12 mb-4 opacity-50" />
                          <p>暂无收藏模板</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 添加章节按钮 - 紧凑风格 */}
            <button
              onClick={handleAddChapter}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all mb-3 ${isClicked
              ? 'bg-purple-100 text-purple-700'
              : 'text-slate-500 hover:text-purple-600 hover:bg-purple-50'
              }`}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>添加章节</span>
            </button>

          {/* 报告结构预览 */}
          {chapterTree.length > 0 && (
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-semibold text-slate-700 flex items-center gap-2">
                <ListTree className="w-4 h-4" />
                当前报告结构
              </h4>
                {/* 帮助提示 */}
                <div className="relative group/help">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400 cursor-help hover:text-slate-600 transition-colors" />
                  <div className="absolute right-0 top-full mt-2 w-48 p-2 bg-slate-800 text-white text-[10px] rounded shadow-lg opacity-0 invisible group-hover/help:opacity-100 group-hover/help:visible transition-all z-50 pointer-events-none leading-relaxed">
                    双击章节标题可定位到画布节点。配置 LLM 和提示词生成报告内容。
                    <div className="absolute right-3 bottom-full w-2 h-2 bg-slate-800 rotate-45 translate-y-1" />
                  </div>
                </div>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {renderChapterTree(chapterTree)}
              </div>
              <div className="mt-3 pt-3 border-t border-slate-200">
                <p className="text-xs text-slate-500">
                  共{" "}
                  {chapterTree.length}{" "}
                  个章节
                </p>
              </div>
            </div>
          )}

        </div>
      )}
      </div>

      {/* 底部区域 */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/50">
          {/* 生成报告按钮 / 停止生成按钮 */}
          {mode === "report" && onGenerateReport && (
            <>
              {isGenerating ? (
                /* 停止生成按钮 - 与生成报告按钮风格一致 */
                <button
                  onClick={() => {
                    if (onStopGeneration) {
                      onStopGeneration();
                    }
                    setIsGenerateReportClicked(false);
                  }}
                  className="group w-full p-4 rounded-lg border border-amber-300 bg-amber-50/50 hover:border-red-400 hover:bg-red-50 transition-all duration-300 overflow-hidden relative shadow-sm hover:shadow-md"
                >
                  {/* 按钮内容 */}
                  <div className="relative flex items-center justify-center gap-3">
                    {/* 书本+笔组合图标 - 写字中 */}
                    <div className="relative w-8 h-8">
                      {/* 书本图标 */}
                      <BookOpen className="w-7 h-7 text-amber-700 absolute bottom-0 left-0" />
                      {/* 笔图标 - 持续写字动画 */}
                      <div className="absolute -top-0.5 right-1 animate-writing-active">
                        <PenLine className="w-4 h-4 text-amber-600 transform -rotate-45" />
                      </div>
                      {/* 写字时的小墨点效果 - 持续显示 */}
                      <div className="absolute bottom-1 right-2 flex gap-0.5">
                        <span className="w-0.5 h-0.5 bg-amber-500 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                        <span className="w-0.5 h-0.5 bg-amber-500 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                        <span className="w-0.5 h-0.5 bg-amber-500 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                    <div className="flex flex-col items-start flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-amber-800">正在生成</span>
                        <Loader2 className="w-3.5 h-3.5 text-amber-600 animate-spin" />
                      </div>
                      <span className="text-[10px] text-amber-600">AI 正在撰写报告内容...</span>
                    </div>
                    {/* 停止按钮 */}
                    <div className="flex items-center gap-1 px-2 py-1 rounded bg-red-100 text-red-600 group-hover:bg-red-500 group-hover:text-white transition-colors">
                      <Square className="w-3 h-3 fill-current" />
                      <span className="text-xs font-medium">停止</span>
                    </div>
                  </div>
                </button>
              ) : (
                /* 生成报告按钮 - 书本+笔动效 */
            <button
              onClick={() => {
                setIsGenerateReportClicked(true);
                onGenerateReport();
              }}
                  className="group w-full p-4 rounded-lg border border-slate-200 bg-white hover:border-amber-300 hover:bg-amber-50/50 transition-all duration-300 overflow-hidden relative shadow-sm hover:shadow-md"
                >
                  {/* 按钮内容 */}
                  <div className="relative flex items-center justify-center gap-3">
                    {/* 书本+笔组合图标 */}
                    <div className="relative w-8 h-8">
                      {/* 书本图标 */}
                      <BookOpen className="w-7 h-7 text-slate-600 group-hover:text-amber-700 transition-colors absolute bottom-0 left-0" />
                      {/* 笔图标 - 带写字动画 */}
                      <div className="absolute -top-0.5 right-1 group-hover:animate-writing">
                        <PenLine className="w-4 h-4 text-amber-500 group-hover:text-amber-600 transition-colors transform -rotate-45" />
                      </div>
                      {/* 写字时的小墨点效果 */}
                      <div className="absolute bottom-1 right-2 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="w-0.5 h-0.5 bg-amber-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                        <span className="w-0.5 h-0.5 bg-amber-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                        <span className="w-0.5 h-0.5 bg-amber-400 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                    <div className="flex flex-col items-start">
                      <span className="font-semibold text-slate-700 group-hover:text-amber-800 transition-colors">生成报告</span>
                      <span className="text-[10px] text-slate-400 group-hover:text-amber-600 transition-colors">AI 智能撰写</span>
                  </div>
              </div>
            </button>
          )}
            </>
      )}

      </div>
    </div>
  );
}
