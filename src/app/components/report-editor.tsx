import { useCallback, useState, useEffect, useRef } from "react";
import {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
} from "reactflow";
import { 
  FileText, 
  ChevronLeft, 
  ChevronRight,
  ChevronDown,
  Plus, 
  Trash2, 
  Settings,
  MoreVertical,
  Wand2,
  BookTemplate,
  ListTree,
  Loader2
} from "lucide-react";
import { cn } from "./ui/utils";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "./ui/dialog";
import ReportNodeEditor from "./report-node-editor";
import { ReportChapterTree } from "./report-chapter-tree";
import { ReportPreview } from "./report-preview";

interface ReportEditorProps {
  projectId: string;
  reportType?: string;
  collectionNodes: Node[];
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
}

interface TemplateChapter {
  label: string;
  chapterNumber: string;
  templateStyle?: string;
  sourceNodeId?: string;
}

interface ReportTemplate {
  id: string;
  category: string;
  name: string;
  description: string;
  chapters: TemplateChapter[];
}

export default function ReportEditor({
  projectId,
  reportType,
  collectionNodes,
  initialNodes,
  initialEdges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp,
}: ReportEditorProps) {
  
  const [nodes, setNodes] = useState<Node[]>(initialNodes || []);
  const [edges, setEdges] = useState<Edge[]>(initialEdges || []);
  
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [generatedChapters, setGeneratedChapters] = useState<any[]>([]);
  const [showReportPreview, setShowReportPreview] = useState(false);
  
  // 新增：模板弹窗与定制化状态
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [isCustomizingStructure, setIsCustomizingStructure] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // 章节配置箭头：追踪选中章节行的垂直中心位置
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedRowY, setSelectedRowY] = useState<number | null>(null);

  useEffect(() => {
    if (!selectedNodeId || !containerRef.current) {
      setSelectedRowY(null);
      return;
    }
    const measure = () => {
      const row = containerRef.current?.querySelector(`[data-nodeid="${selectedNodeId}"]`);
      if (row && containerRef.current) {
        const rowRect = row.getBoundingClientRect();
        const containerRect = containerRef.current.getBoundingClientRect();
        setSelectedRowY(rowRect.top - containerRect.top + rowRect.height / 2);
      }
    };
    // 稍作延迟确保展开/折叠动画后 DOM 稳定
    const id = requestAnimationFrame(measure);
    return () => cancelAnimationFrame(id);
  }, [selectedNodeId, nodes, edges, isSidebarCollapsed]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  // mock 模板数据
  const templates: ReportTemplate[] = [
    {
      id: "weifang-1",
      category: "危房鉴定模板",
      name: "危房鉴定标准报告",
      description: "依据相关危房鉴定标准，包含现状调查、检测数据、等级评定等核心内容结构。",
      chapters: [
        { label: "基本情况", chapterNumber: "1", templateStyle: "basic_situation", sourceNodeId: "scope_basic_situation" },
        { label: "房屋概况", chapterNumber: "2", templateStyle: "house_overview", sourceNodeId: "scope_house_overview" },
        { label: "鉴定内容和方法及原始记录一览表", chapterNumber: "3", templateStyle: "inspection_content_and_methods", sourceNodeId: "scope_inspection_content_and_methods" },
        { label: "检测鉴定依据", chapterNumber: "4", templateStyle: "inspection_basis", sourceNodeId: "scope_inspection_basis" },
        { label: "详细检查情况", chapterNumber: "5", templateStyle: "detailed_inspection", sourceNodeId: "scope_detailed_inspection" },
        { label: "鉴定意见及处理建议", chapterNumber: "6", templateStyle: "opinion_and_suggestions", sourceNodeId: "scope_opinion_and_suggestions" }
      ]
    },
    {
      id: "safety-1",
      category: "安全性鉴定模板",
      name: "民用建筑安全性鉴定",
      description: "针对民用建筑结构的安全性评估，包含地基基础与上部结构鉴定。",
      chapters: [
        { label: "第1章 概况", chapterNumber: "1" },
        { label: "第2章 鉴定依据", chapterNumber: "2" },
        { label: "第3章 结构布置及轴线尺寸复核", chapterNumber: "3" },
        { label: "第4章 材料强度检测", chapterNumber: "4" },
        { label: "第5章 结构承载力验算", chapterNumber: "5" },
        { label: "第6章 安全性评级", chapterNumber: "6" }
      ]
    },
    {
      id: "quake-1",
      category: "抗震鉴定模板",
      name: "现有建筑抗震鉴定",
      description: "评估现有建筑在规定烈度下的抗震能力，并提供相应的加固建议结构。",
      chapters: [
        { label: "1. 概述", chapterNumber: "1" },
        { label: "2. 抗震设防标准及鉴定要求", chapterNumber: "2" },
        { label: "3. 建筑场地及地基基础评价", chapterNumber: "3" },
        { label: "4. 第一级鉴定", chapterNumber: "4" },
        { label: "5. 第二级鉴定", chapterNumber: "5" },
        { label: "6. 综合抗震能力评定", chapterNumber: "6" },
        { label: "7. 抗震加固建议", chapterNumber: "7" }
      ]
    },
    {
      id: "industry-1",
      category: "工业建筑可靠性鉴定模板",
      name: "工业构筑物可靠性鉴定",
      description: "面向复杂工业厂房体系的完整可靠性鉴定框架，支持复杂结构层级。",
      chapters: [
        { label: "一、 建筑物概况", chapterNumber: "1" },
        { label: "二、 检测鉴定内容及方法", chapterNumber: "2" },
        { label: "三、 环境条件及使用历史调查", chapterNumber: "3" },
        { label: "四、 承重结构与构件检测", chapterNumber: "4" },
        { label: "五、 结构可靠性评级", chapterNumber: "5" },
        { label: "六、 结论与修缮建议", chapterNumber: "6" }
      ]
    }
  ];

  const categories = Array.from(new Set(templates.map(t => t.category)));
  const [selectedCategory, setSelectedCategory] = useState<string>(categories[0]);

  // 当弹窗打开时重置状态
  useEffect(() => {
     if (isTemplateModalOpen) {
         setSelectedCategory(categories[0]);
     }
  }, [isTemplateModalOpen]);

  const handleApplyTemplate = () => {
    if (!selectedTemplateId) return;
    const template = templates.find(t => t.id === selectedTemplateId);
    if (!template) return;

    isInternalUpdateRef.current = true;
    
    // 生成新的节点
    const newNodes: Node[] = template.chapters.map((ch, idx) => ({
      id: `chapter-${Date.now()}-${idx}`,
      type: 'report',
      position: { x: 0, y: idx * 100 }, 
      data: { 
        label: ch.label,
        chapterNumber: ch.chapterNumber,
        templateStyle: ch.templateStyle,
        sourceNodeId: ch.sourceNodeId ?? null,
      },
      width: 150,
      height: 40,
    }));

    setNodes(newNodes);
    setEdges([]); // 清空可能存在的父子连接，采用扁平结构做演示
    if (newNodes.length > 0) {
      setSelectedNodeId(newNodes[0].id);
    }
    
    setIsTemplateModalOpen(false);
  };

  // Sync with props
  const isInternalUpdateRef = useRef(false);
  const initialNodesRef = useRef(initialNodes);
  const initialEdgesRef = useRef(initialEdges);

  // Sync props -> state
  useEffect(() => {
    const nodesChanged = JSON.stringify(initialNodes) !== JSON.stringify(initialNodesRef.current);
    if (nodesChanged && !isInternalUpdateRef.current) {
        initialNodesRef.current = initialNodes;
        setNodes(initialNodes || []);
    }
  }, [initialNodes]);

  useEffect(() => {
    const edgesChanged = JSON.stringify(initialEdges) !== JSON.stringify(initialEdgesRef.current);
    if (edgesChanged && !isInternalUpdateRef.current) {
        initialEdgesRef.current = initialEdges;
        setEdges(initialEdges || []);
    }
  }, [initialEdges]);

  // Sync state -> props (debounce)
  useEffect(() => {
    if (isInternalUpdateRef.current) {
      isInternalUpdateRef.current = false;
      return;
    }
    const timer = setTimeout(() => {
        onNodesChangeProp(nodes);
    }, 50);
    return () => clearTimeout(timer);
  }, [nodes, onNodesChangeProp]);

  useEffect(() => {
     if (isInternalUpdateRef.current) {
      isInternalUpdateRef.current = false;
      return;
    }
    const timer = setTimeout(() => {
        onEdgesChangeProp(edges);
    }, 50);
    return () => clearTimeout(timer);
  }, [edges, onEdgesChangeProp]);


  // Actions
  const handleAddChapter = () => {
    isInternalUpdateRef.current = true;
    const currentEdges = edges || [];
    const currentNodes = nodes || [];
    
    const rootNodesCount = currentNodes.filter(n => !currentEdges.some(e => e.target === n.id)).length;
    
    const newNode: Node = {
      id: `chapter-${Date.now()}`,
      type: 'report',
      position: { x: 0, y: (currentNodes.length || 0) * 100 }, 
      data: { 
        label: '新章节',
        chapterNumber: `${rootNodesCount + 1}` 
      },
      width: 150,
      height: 40,
    };
    
    setNodes(prev => [...(prev || []), newNode]);
    setSelectedNodeId(newNode.id);
  };

  const handleAddSubChapter = (parentId: string) => {
    const parentNode = nodes.find(n => n.id === parentId);
    if (!parentNode) return;

    isInternalUpdateRef.current = true;

    const currentEdges = edges || [];
    const currentNodes = nodes || [];
    const existingChildIds = currentEdges
      .filter((edge) => edge.source === parentId)
      .map((edge) => edge.target);
    const existingChildren = currentNodes.filter((node) => existingChildIds.includes(node.id));
    const parentChapterNumber = String(parentNode.data?.chapterNumber || "").trim();

    const existingIndexes = existingChildren
      .map((child) => String(child.data?.chapterNumber || ""))
      .map((num) => {
        if (!num) return NaN;
        if (!parentChapterNumber || !num.startsWith(`${parentChapterNumber}.`)) return NaN;
        const lastSegment = num.split(".").pop();
        const parsed = Number.parseInt(lastSegment || "", 10);
        return Number.isFinite(parsed) ? parsed : NaN;
      })
      .filter((num) => Number.isFinite(num)) as number[];
    const nextChildIndex = (existingIndexes.length > 0 ? Math.max(...existingIndexes) : 0) + 1;
    const nextChildChapterNumber = parentChapterNumber
      ? `${parentChapterNumber}.${nextChildIndex}`
      : "";

    const newNode: Node = {
      id: `chapter-${Date.now()}`,
      type: 'report',
      position: { x: 0, y: 0 },
      data: { 
        label: '新子章节',
        chapterNumber: nextChildChapterNumber,
      },
      width: 150,
      height: 40,
    };

    const newEdge: Edge = {
      id: `edge-${Date.now()}`,
      source: parentId,
      target: newNode.id,
      type: 'smoothstep'
    };

    setNodes(prev => [...(prev || []), newNode]);
    setEdges(prev => [...(prev || []), newEdge]);
    setSelectedNodeId(newNode.id);
  };

  const traverseDelete = (nodeId: string, currentNodes: Node[], currentEdges: Edge[]) => {
    const nodesToDelete = new Set<string>();
    const edgesToDelete = new Set<string>();
    
    const stack = [nodeId];
    
    while (stack.length > 0) {
        const currentId = stack.pop()!;
        nodesToDelete.add(currentId);
        
        const outgoingEdges = currentEdges.filter(e => e.source === currentId);
        outgoingEdges.forEach(e => {
            edgesToDelete.add(e.id);
            if (!nodesToDelete.has(e.target)) {
                stack.push(e.target);
            }
        });

        const incomingEdges = currentEdges.filter(e => e.target === currentId);
        incomingEdges.forEach(e => edgesToDelete.add(e.id));
    }

    return { nodesToDelete, edgesToDelete };
  };

  const handleDeleteNode = (nodeId: string) => {
    isInternalUpdateRef.current = true;
    const { nodesToDelete, edgesToDelete } = traverseDelete(nodeId, nodes, edges);
    
    setNodes(prev => prev.filter(n => !nodesToDelete.has(n.id)));
    setEdges(prev => prev.filter(e => !edgesToDelete.has(e.id)));
    
    if (selectedNodeId && nodesToDelete.has(selectedNodeId)) {
        setSelectedNodeId(null);
    }
  };

  const handleNodeUpdate = (updatedNode: Node) => {
      isInternalUpdateRef.current = true;
      setNodes(prev => prev.map(n => n.id === updatedNode.id ? updatedNode : n));
  };

  const parseChapterNumber = (value: string): number[] => {
    if (!value || value.trim() === "") return [Number.MAX_SAFE_INTEGER];
    return value
      .split(".")
      .map((part) => Number.parseInt(part, 10))
      .map((num) => (Number.isFinite(num) ? num : Number.MAX_SAFE_INTEGER));
  };

  const sortByChapterNumber = (a: Node, b: Node): number => {
    const aKey = parseChapterNumber(String(a.data?.chapterNumber || ""));
    const bKey = parseChapterNumber(String(b.data?.chapterNumber || ""));
    const maxLen = Math.max(aKey.length, bKey.length);
    for (let i = 0; i < maxLen; i += 1) {
      const av = aKey[i] ?? 0;
      const bv = bKey[i] ?? 0;
      if (av !== bv) return av - bv;
    }
    return String(a.data?.label || "").localeCompare(String(b.data?.label || ""), "zh-CN");
  };

  const resolveDatasetKey = (templateStyle: string): string => {
    const mapping: Record<string, string> = {
      concrete_strength_full: "concrete_strength_comprehensive",
      concrete_strength_table: "concrete_strength",
      concrete_strength_desc: "concrete_strength",
      mortar_strength_data: "mortar_strength",
      brick_strength_table: "brick_strength",
      basic_situation: "basic_situation",
      house_overview: "house_overview",
      inspection_content_and_methods: "inspection_content_and_methods",
      inspection_basis: "inspection_basis",
      detailed_inspection: "detailed_inspection",
      load_calc_params: "load_calc_params",
      bearing_capacity_review: "bearing_capacity_review",
      analysis_explanation: "analysis_explanation",
      opinion_and_suggestions: "opinion_and_suggestions",
    };
    return mapping[templateStyle] || templateStyle || "concrete_strength";
  };

  const handleGenerateFinalReport = async () => {
    const chapterNodes = (nodes || []).filter((n) => n.type === "report");
    if (chapterNodes.length === 0) {
      alert("请先添加至少一个章节。");
      return;
    }

    setIsGeneratingReport(true);
    setShowReportPreview(true);
    setSelectedNodeId(null);
    setGeneratedChapters([]);

    const sortedNodes = [...chapterNodes].sort(sortByChapterNumber);
    const successChapters: any[] = [];
    const failedTitles: string[] = [];

    for (const node of sortedNodes) {
      const templateStyle = String(node.data?.templateStyle || "");
      const sourceNodeId = node.data?.sourceNodeId || null;
      const chapterConfig = {
        node_id: node.id,
        chapter_id: node.id,
        title: node.data?.label || "未命名章节",
        dataset_key: resolveDatasetKey(templateStyle),
        sourceNodeId,
        context: sourceNodeId
          ? { source_node_id: sourceNodeId, sourceNodeId }
          : {},
      };

      try {
        const response = await fetch("/api/report/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: projectId,
            chapter_config: chapterConfig,
            project_context: {},
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorData.detail || errorData.message || `章节生成失败: ${node.data?.label || node.id}`);
        }

        const result = await response.json();
        const chapters = Array.isArray(result?.chapters) ? result.chapters : [];
        if (chapters.length > 0) {
          successChapters.push(...chapters);
        } else {
          throw new Error(`章节无返回内容: ${node.data?.label || node.id}`);
        }
      } catch (err) {
        failedTitles.push(String(node.data?.label || node.id));
        console.error("Generate chapter failed:", err);
      }
    }

    setGeneratedChapters(successChapters);
    setIsGeneratingReport(false);

    if (successChapters.length === 0) {
      alert("报告生成失败：没有成功生成任何章节。请检查每个章节的数据范围配置和采集数据是否已确认。");
      return;
    }

    if (failedTitles.length > 0) {
      alert(`部分章节生成失败：${failedTitles.join("、")}。其余章节已生成并可预览。`);
    }
  };


  const selectedNode = nodes.find(n => n.id === selectedNodeId);

  // -----------------------------------------------------------------------
  // 可折叠目录树（非定制模式下展示）
  // -----------------------------------------------------------------------
  function ChapterOutlineTree({
    nodes,
    edges,
    selectedNodeId,
    onSelectNode,
    parentId = null,
    depth = 0,
  }: {
    nodes: Node[];
    edges: Edge[];
    selectedNodeId: string | null;
    onSelectNode: (id: string) => void;
    parentId?: string | null;
    depth?: number;
  }) {
    const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

    const items = parentId === null
      ? nodes.filter(n => !edges.some(e => e.target === n.id))
      : edges.filter(e => e.source === parentId).map(e => nodes.find(n => n.id === e.target)).filter(Boolean) as Node[];

    return (
      <div className={cn("space-y-0.5", depth === 0 ? "p-2" : "mt-0.5")}>
        {items.map(node => {
          const hasChildren = edges.some(e => e.source === node.id);
          const isOpen = !collapsed[node.id];
          const isSelected = selectedNodeId === node.id;

          return (
            <div key={node.id}>
              <div
                data-nodeid={node.id}
                className={cn(
                  "group flex items-center gap-2 p-1.5 pr-1 rounded-md cursor-pointer transition-colors",
                  isSelected
                    ? "bg-slate-200 text-slate-900"
                    : "hover:bg-slate-100 text-slate-700"
                )}
                style={{ paddingLeft: `${12 + depth * 24}px` }}
                onClick={() => onSelectNode(node.id)}
              >
                {/* 展开/折叠三角 - 仅在有子章节时显示 */}
                {hasChildren ? (
                  <button
                    className="flex-shrink-0 w-4 h-4 flex items-center justify-center rounded hover:bg-slate-300 text-slate-500 hover:text-slate-700 transition-colors"
                    onClick={e => {
                      e.stopPropagation();
                      setCollapsed(prev => ({ ...prev, [node.id]: !prev[node.id] }));
                    }}
                  >
                    {isOpen
                      ? <ChevronDown className="w-3.5 h-3.5" />
                      : <ChevronRight className="w-3.5 h-3.5" />
                    }
                  </button>
                ) : (
                  <span className="flex-shrink-0 w-4 h-4" />
                )}
                <div className="flex-1 min-w-0 pr-1 pl-1">
                  <div className="text-xs font-medium truncate text-slate-700 text-left">
                    {node.data?.chapterNumber && <span className="text-slate-400 mr-2 font-mono text-[10px]">{node.data.chapterNumber}</span>}
                    {node.data?.label || '未命名章节'}
                  </div>
                </div>
              </div>

              {/* 递归渲染子节点 */}
              {hasChildren && isOpen && (
                <ChapterOutlineTree
                  nodes={nodes}
                  edges={edges}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={onSelectNode}
                  parentId={node.id}
                  depth={depth + 1}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  }

  return (

    <div ref={containerRef} className="h-full bg-white flex flex-row overflow-hidden relative">
            {/* Left Sidebar: Structure Tree */}
            <div className={`shrink-0 bg-slate-50 flex flex-col h-full transition-all duration-200 ${isSidebarCollapsed ? 'w-10 border-r-0' : 'w-[280px] border-r border-slate-200'}`}>
              {/* 折叠时：显示结构图标 */}
              {isSidebarCollapsed ? (
                <div className="flex flex-col items-center py-3 gap-3 flex-1">
                  <button
                    onClick={() => setIsSidebarCollapsed(false)}
                    className="w-7 h-7 flex items-center justify-center rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-200 transition-colors"
                    title="展开面板"
                  >
                    <ListTree className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                {/* 强化：将模板库提升至顶部作为主要交互入口 */}
                <div className="p-4 border-b border-slate-200 bg-white shadow-sm z-10 shrink-0 space-y-3">
                    <div className="flex items-center justify-between mb-1">
                        <h2 className="font-semibold text-sm text-slate-800">快速模板</h2>
                        <button
                          onClick={() => setIsSidebarCollapsed(true)}
                          className="w-6 h-6 flex items-center justify-center rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
                          title="折叠面板"
                        >
                          <ChevronLeft className="w-3.5 h-3.5" />
                        </button>
                    </div>
                    
                    <Button 
                        variant="default" 
                        onClick={() => setIsTemplateModalOpen(true)}
                        className="w-full bg-slate-900 hover:bg-slate-800 text-white shadow-sm transition-all h-9 text-sm font-medium flex items-center justify-center gap-2">
                        <BookTemplate className="w-4 h-4" />
                        从模板库导入结构
                    </Button>
                    <p className="text-[10px] text-slate-500 text-center leading-relaxed">
                        浏览 20+ 个预制模板，一键导入标准章节
                    </p>
                </div>

                {/* 弱化：章节树作为次要的调整区域 */}
                <div className="flex-1 flex flex-col overflow-hidden bg-slate-50/50">
                    <div className="px-4 pt-4 pb-2 flex items-center justify-between shrink-0">
                        <h3 className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
                            <ListTree className="w-3.5 h-3.5" />
                            报告结构
                        </h3>
                        {/* 仅在定制模式下显示添加主章节的按钮，设计更简约 */}
                        {isCustomizingStructure && (
                            <button
                                onClick={handleAddChapter}
                                className="w-5 h-5 flex items-center justify-center rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200/50 transition-colors"
                                title="添加根章节"
                            >
                                <Plus className="w-3.5 h-3.5" />
                            </button>
                        )}
                    </div>
                    
                    <ScrollArea className="flex-1 px-2">
                        {nodes.length > 0 ? (
                            isCustomizingStructure ? (
                                <ReportChapterTree 
                                    nodes={nodes}
                                    edges={edges}
                                    selectedNodeId={selectedNodeId}
                                    onSelectNode={setSelectedNodeId}
                                    onAddSubChapter={handleAddSubChapter}
                                    onDeleteNode={handleDeleteNode}
                                />
                            ) : (
                                <ChapterOutlineTree
                                    nodes={nodes}
                                    edges={edges}
                                    selectedNodeId={selectedNodeId}
                                    onSelectNode={setSelectedNodeId}
                                />
                            )
                        ) : (
                            <div className="flex flex-col items-center justify-center h-40 text-center px-4">
                                <ListTree className="w-8 h-8 text-slate-200 mb-2" />
                                <p className="text-xs text-slate-400">目前没有报告结构，请从上面的“从模板库导入结构”开始。</p>
                            </div>
                        )}
                    </ScrollArea>
                </div>

                <div className="p-4 border-t border-slate-200 bg-white shrink-0 shadow-[0_-4px_10px_rgba(0,0,0,0.02)] space-y-3">
                    <button 
                        onClick={() => setIsCustomizingStructure(!isCustomizingStructure)} 
                        className={cn(
                            "w-full text-[11px] flex items-center justify-center gap-1 transition-colors",
                            isCustomizingStructure ? "text-slate-800 font-medium" : "text-slate-400 hover:text-slate-600"
                        )}
                    >
                        <Settings className="w-3 h-3" />
                        {isCustomizingStructure ? "完成定制" : "定制报告章节"}
                    </button>
                    
                    <Button
                        onClick={handleGenerateFinalReport}
                        disabled={isGeneratingReport || nodes.length === 0}
                        className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 disabled:cursor-not-allowed text-white shadow-sm transition-all hover:shadow-md h-10 text-sm font-medium flex items-center justify-center"
                    >
                        {isGeneratingReport ? (
                            <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> 生成中...</>
                        ) : (
                            <><Wand2 className="w-4 h-4 mr-2" /> 生成最终报告</>
                        )}
                    </Button>
                </div>
                </>
              )}
            </div>

            {/* Right Panel: Content Editor */}
            <div className="flex-1 bg-slate-50 relative flex flex-col h-full min-w-0">
                {/* 章节配置指示箭头：动态对齐至左侧选中章节行的垂直位置 */}
                {selectedNode && selectedRowY !== null && (
                  <div
                    className="absolute left-0 z-30 pointer-events-none transition-[top] duration-150"
                    style={{ top: selectedRowY }}
                  >
                    {/* 连接线 */}
                    <div className="absolute right-full top-1/2 -translate-y-1/2 w-2 h-px bg-slate-400" />
                    {/* 左指三角形 */}
                    <div
                      className="-translate-y-1/2"
                      style={{
                        width: 0,
                        height: 0,
                        borderTop: '5px solid transparent',
                        borderBottom: '5px solid transparent',
                        borderRight: '6px solid #94a3b8',
                      }}
                    />
                  </div>
                )}
                {showReportPreview ? (
                    <div className="h-full w-full">
                        <ReportPreview
                          isGenerating={isGeneratingReport}
                          chapters={generatedChapters}
                          onClose={() => setShowReportPreview(false)}
                        />
                    </div>
                ) : selectedNode ? (
                    <div className="flex-1 p-6 overflow-hidden flex flex-col h-full w-full">
                        <div className="flex items-center gap-2 mb-4 shrink-0">
                             <div className="w-1.5 h-6 bg-slate-800 rounded-full" />
                             <h2 className="text-lg font-bold text-slate-800 line-clamp-1">{selectedNode.data.label || '未命名章节'}</h2>
                             {selectedNode.data.chapterNumber && (
                                 <span className="px-2 py-0.5 rounded-full bg-slate-200 text-xs font-mono text-slate-600 font-medium ml-2">
                                     {selectedNode.data.chapterNumber}
                                 </span>
                             )}
                        </div>
                        
                         <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col relative animate-in fade-in zoom-in-95 duration-200">
                             <ReportNodeEditor 
                                node={selectedNode}
                                onClose={() => setSelectedNodeId(null)}
                                onUpdate={handleNodeUpdate}
                                onHeaderMouseDown={() => {}}
                                collectionNodes={collectionNodes}
                                reportType={reportType}
                             />
                         </div>
                    </div>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-400 select-none">
                        <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-slate-100">
                             <Settings className="w-10 h-10 text-slate-200" />
                        </div>
                        <h3 className="text-base font-semibold text-slate-600 mb-2">未选择章节</h3>
                        <p className="text-sm text-slate-400 max-w-xs text-center">
                            请先从左侧导入 <span className="font-medium text-slate-500">报告模板</span>，或点击“定制报告章节”手动创建。
                        </p>
                    </div>
                )}
            </div>

        {/* 模板选择弹窗 */}
        <Dialog open={isTemplateModalOpen} onOpenChange={setIsTemplateModalOpen}>
            <DialogContent className="sm:max-w-[700px] p-0 overflow-hidden flex flex-col h-[500px]">
                <div className="px-6 py-4 border-b border-slate-200 shrink-0 bg-white z-10 flex items-start justify-between">
                    <div>
                        <DialogTitle className="text-lg">选择报告模板</DialogTitle>
                        <DialogDescription className="mt-1">
                            按鉴定类别选择基准模板，快速导入结构。
                        </DialogDescription>
                    </div>
                </div>
                
                <div className="flex-1 flex overflow-hidden bg-slate-50/50">
                    {/* 左侧分类导航 */}
                    <div className="w-48 border-r border-slate-200 bg-white p-3 overflow-y-auto shrink-0 space-y-1">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={cn(
                                    "w-full text-left px-3 py-2.5 rounded-md text-sm transition-colors relative",
                                    selectedCategory === cat 
                                        ? "bg-slate-100 text-slate-900 font-semibold" 
                                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                                )}
                            >
                                {cat}
                                {selectedCategory === cat && (
                                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-4 bg-slate-800 rounded-r-full" />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* 右侧对应分类模板列表 */}
                    <div className="flex-1 p-6 overflow-y-auto">
                        <div className="flex flex-col gap-4">
                            {templates.filter(t => t.category === selectedCategory).map(template => (
                                <div 
                                    key={template.id}
                                    onClick={() => setSelectedTemplateId(template.id)}
                                    className={cn(
                                        "border rounded-xl p-5 cursor-pointer transition-all hover:shadow-md relative bg-white group",
                                        selectedTemplateId === template.id 
                                            ? "border-slate-800 ring-1 ring-slate-200 shadow-sm" 
                                            : "border-slate-200 hover:border-slate-400"
                                    )}
                                >
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <BookTemplate className={cn(
                                                "w-5 h-5",
                                                selectedTemplateId === template.id ? "text-slate-800" : "text-slate-500 group-hover:text-slate-700"
                                            )} />
                                            <h4 className="font-semibold text-slate-800 text-base">{template.name}</h4>
                                        </div>
                                        <div className={cn(
                                            "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                                            selectedTemplateId === template.id ? "border-slate-800 bg-slate-800" : "border-slate-300"
                                        )}>
                                            {selectedTemplateId === template.id && <div className="w-2 h-2 bg-white rounded-full flex-shrink-0" />}
                                        </div>
                                    </div>
                                    <p className="text-sm text-slate-500 leading-relaxed mb-4 pl-7">{template.description}</p>
                                    
                                    <div className="pl-7">
                                        <div className="text-[11px] text-slate-600 bg-slate-100 px-2.5 py-1 rounded inline-flex items-center gap-1.5 font-medium">
                                            <ListTree className="w-3 h-3" />
                                            包含 {template.chapters.length} 个基准章节
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {templates.filter(t => t.category === selectedCategory).length === 0 && (
                                <div className="text-center py-10 text-slate-400 text-sm">
                                    该类别下暂无预设模板
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="p-4 border-t border-slate-200 shrink-0 bg-white flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setIsTemplateModalOpen(false)}>
                        取消
                    </Button>
                    <Button 
                        onClick={handleApplyTemplate} 
                        disabled={!selectedTemplateId}
                        className="bg-slate-900 hover:bg-slate-800 text-white min-w-[100px]"
                    >
                        确认导入
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    </div>
  );
}


