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
  Plus, 
  Trash2, 
  Settings,
  MoreVertical,
  Wand2,
  BookTemplate
} from "lucide-react";
import { cn } from "./ui/utils";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "./ui/resizable";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
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

interface ReportGenerationSnapshot {
  id: string;
  createdAt: string;
  reportType: string;
  chapters: any[];
  chapterCount: number;
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
  const [reportHistory, setReportHistory] = useState<ReportGenerationSnapshot[]>([]);
  const [isHistorySidebarOpen, setIsHistorySidebarOpen] = useState(true);

  // Sync with props
  const isInternalUpdateRef = useRef(false);
  const initialNodesRef = useRef(initialNodes);
  const initialEdgesRef = useRef(initialEdges);
  const historyStorageKey = `project_${projectId}_report_generation_history`;

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

  useEffect(() => {
    try {
      const raw = localStorage.getItem(historyStorageKey);
      if (!raw) {
        setReportHistory([]);
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setReportHistory(parsed);
      } else {
        setReportHistory([]);
      }
    } catch {
      setReportHistory([]);
    }
  }, [historyStorageKey]);

  useEffect(() => {
    try {
      localStorage.setItem(historyStorageKey, JSON.stringify(reportHistory));
    } catch {
      // ignore storage write errors
    }
  }, [historyStorageKey, reportHistory]);


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

    setReportHistory((prev) => [
      {
        id: `snapshot-${Date.now()}`,
        createdAt: new Date().toISOString(),
        reportType: reportType || "",
        chapters: successChapters,
        chapterCount: successChapters.length,
      },
      ...prev,
    ]);

    if (failedTitles.length > 0) {
      alert(`部分章节生成失败：${failedTitles.join("、")}。其余章节已生成并可预览。`);
    }
  };

  const handleLoadHistoryPreview = (snapshot: ReportGenerationSnapshot) => {
    setGeneratedChapters(snapshot.chapters || []);
    setShowReportPreview(true);
    setSelectedNodeId(null);
  };

  const handleDeleteHistoryItem = (itemId: string) => {
    setReportHistory((history) => history.filter((item) => item.id !== itemId));
  };

  const historyCountLabel = reportHistory.length > 99 ? "99+" : String(reportHistory.length);


  const selectedNode = nodes.find(n => n.id === selectedNodeId);

  return (
    <div className="h-full bg-white flex flex-col overflow-hidden relative">
        <ResizablePanelGroup direction="horizontal" className="flex-1">
            {/* Left Sidebar: Structure Tree */}
            <ResizablePanel defaultSize={20} minSize={15} maxSize={30} className="bg-slate-50 border-r border-slate-200 flex flex-col h-full">
                <div className="p-4 border-b border-slate-200 flex items-center justify-between shrink-0 bg-white shadow-sm z-10">
                    <h2 className="font-semibold text-sm text-slate-800">结构层 - 章节树</h2>
                    <Button variant="default" size="sm" onClick={handleAddChapter} className="h-8 text-xs bg-slate-900 hover:bg-slate-800 shadow-sm transition-all hover:shadow pl-2 pr-3">
                        <Plus className="w-3.5 h-3.5 mr-1.5" />
                        新增章节
                    </Button>
                </div>
                
                <ScrollArea className="flex-1 p-2">
                    <ReportChapterTree 
                        nodes={nodes}
                        edges={edges}
                        selectedNodeId={selectedNodeId}
                        onSelectNode={setSelectedNodeId}
                        onAddSubChapter={handleAddSubChapter}
                        onDeleteNode={handleDeleteNode}
                    />
                </ScrollArea>

                <div className="p-4 border-t border-slate-200 bg-white space-y-3 shrink-0">
                    <div className="bg-blue-50/50 rounded-lg p-3 border border-blue-100 flex items-start gap-3">
                        <BookTemplate className="w-4 h-4 text-blue-600 mt-0.5" />
                        <div className="flex-1 min-w-0">
                             <h4 className="text-xs font-semibold text-blue-900 mb-1">快速模板库</h4>
                             <p className="text-[10px] text-blue-600/80 leading-relaxed mb-2">浏览 20+ 个预制报告模板，一键导入标准章节结构。</p>
                             <Button variant="outline" size="sm" className="w-full text-xs h-7 bg-white border-blue-200 hover:bg-blue-50 text-blue-700">浏览模板</Button>
                        </div>
                    </div>
                    
                    <Button
                        onClick={handleGenerateFinalReport}
                        disabled={isGeneratingReport || nodes.length === 0}
                        className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 disabled:cursor-not-allowed text-white shadow-sm transition-all hover:shadow-md h-10 text-sm font-medium"
                    >
                        <Wand2 className="w-4 h-4 mr-2" />
                        {isGeneratingReport ? "生成中..." : "生成最终报告"}
                    </Button>
                </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Right Panel: Content + History */}
            <ResizablePanel defaultSize={80} className="bg-slate-50 relative flex h-full">
                <div className="flex-1 h-full">
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
                                请从左侧 <span className="font-medium text-slate-500">结构层</span> 选择一个章节进行编辑，或创建新的章节。
                            </p>
                        </div>
                    )}
                </div>

                {isHistorySidebarOpen ? (
                  <div className="h-full w-80 border-l border-slate-200 bg-white transition-all duration-200">
                    <div className="h-full flex flex-col">
                      <div className="h-12 border-b border-slate-200 flex items-center justify-between px-2">
                        <div className="text-sm font-semibold text-slate-700 px-1">报告回溯</div>
                        <button
                          className="p-1.5 rounded hover:bg-slate-100 text-slate-500"
                          onClick={() => setIsHistorySidebarOpen(false)}
                          title="收起"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="px-3 py-2 border-b border-slate-100">
                        <span className="text-xs text-slate-500">当前项目共 {reportHistory.length} 份</span>
                      </div>
                      <div className="flex-1 overflow-y-auto p-2 space-y-2">
                        {reportHistory.length === 0 ? (
                          <div className="text-xs text-slate-400 px-2 py-4">暂无历史报告</div>
                        ) : (
                          reportHistory.map((item, index) => (
                            <div key={item.id} className="border border-slate-200 rounded-lg p-2 space-y-2">
                              <div className="text-xs text-slate-700 font-medium">第 {reportHistory.length - index} 次生成</div>
                              <div className="text-[11px] text-slate-500">{new Date(item.createdAt).toLocaleString("zh-CN")}</div>
                              <div className="text-[11px] text-slate-500">
                                章节数：{item.chapterCount} {item.reportType ? `| 类型：${item.reportType}` : ""}
                              </div>
                              <div className="flex items-center gap-2">
                                <button
                                  className="text-xs px-2 py-1 rounded bg-slate-900 text-white hover:bg-slate-800"
                                  onClick={() => handleLoadHistoryPreview(item)}
                                >
                                  查看
                                </button>
                                <button
                                  className="text-xs px-2 py-1 rounded border border-rose-200 text-rose-600 hover:bg-rose-50"
                                  onClick={() => handleDeleteHistoryItem(item.id)}
                                  title="删除此记录"
                                >
                                  删除
                                </button>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setIsHistorySidebarOpen(true)}
                    className="absolute right-2 top-2 z-20 bg-white border border-slate-200 rounded-lg shadow-sm w-[46px] py-2 hover:bg-slate-50 flex flex-col items-center"
                    title={`展开当前项目生成历史（${reportHistory.length}）`}
                  >
                    <div
                      className="text-[12px] font-medium text-slate-700 leading-none tracking-[1px]"
                      style={{ writingMode: "vertical-rl", textOrientation: "upright" }}
                    >
                      生成历史
                    </div>
                    <div className="mt-2 min-w-[24px] h-[20px] px-1 rounded-full bg-slate-900 text-white text-[11px] leading-[20px] text-center font-semibold">
                      {historyCountLabel}
                    </div>
                  </button>
                )}
            </ResizablePanel>
        </ResizablePanelGroup>
    </div>
  );
}


