import { useCallback, useState, useEffect, useRef } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Edge,
  Node,
  NodeTypes,
  useReactFlow,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";
import ReportNode from "./nodes/report-node";
import NodeSidebar from "./node-sidebar";
import { ProjectSidebar } from "./project-sidebar";
import ReportNodeEditor from "./report-node-editor";
import { ReportPreview } from "./report-preview"; // Import the new component
import { FileText, Sparkles, X } from "lucide-react";

const nodeTypes: NodeTypes = {
  report: ReportNode,
};

// FitView 组件：只在初始加载时调用 fitView
function FitView() {
  const { fitView } = useReactFlow();
  const hasFittedRef = useRef(false);

  useEffect(() => {
    if (!hasFittedRef.current) {
      // 延迟执行，确保节点已渲染
      const timer = setTimeout(() => {
        fitView({ duration: 400, padding: 0.2 });
        hasFittedRef.current = true;
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [fitView]);

  return null;
}

interface ReportEditorProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
}

function ReportEditorContent({
  initialNodes,
  initialEdges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp,
}: ReportEditorProps) {
  const [nodes, setNodes, onNodesChange] =
    useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] =
    useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [showGenerateModal, setShowGenerateModal] =
    useState(false);
  const [previewHeight, setPreviewHeight] = useState(55); // 预览面板高度百分比，默认55%
  const [isResizingPreview, setIsResizingPreview] =
    useState(false);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const { setCenter, getNode, fitView, getViewport } = useReactFlow();

  const [editorPosition, setEditorPosition] = useState({ x: -1, y: 100 });
  const [isDraggingEditor, setIsDraggingEditor] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const [isReportGenerating, setIsReportGenerating] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 使用 ref 来跟踪是否是内部更新，避免循环同步
  const isInternalUpdateRef = useRef(false);
  const initialNodesRef = useRef(initialNodes);
  const initialEdgesRef = useRef(initialEdges);

  // 处理编辑器拖动
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingEditor) return;

      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;

      // 简单的边界检查
      const maxX = window.innerWidth - 480;
      const maxY = window.innerHeight - 100;

      setEditorPosition({
        x: Math.max(0, Math.min(maxX, newX)),
        y: Math.max(0, Math.min(maxY, newY))
      });
    };

    const handleMouseUp = () => {
      setIsDraggingEditor(false);
    };

    if (isDraggingEditor) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
    };
  }, [isDraggingEditor, dragOffset]);

  const handleEditorHeaderMouseDown = useCallback((e: React.MouseEvent) => {
    setDragOffset({
      x: e.clientX - editorPosition.x,
      y: e.clientY - editorPosition.y
    });
    setIsDraggingEditor(true);
  }, [editorPosition]);


  // 当父组件传入的初始数据改变时（比如切换项目），同步到本地状态
  useEffect(() => {
    // 使用深度比较，避免不必要的更新
    const nodesChanged = JSON.stringify(initialNodes) !== JSON.stringify(initialNodesRef.current);
    if (nodesChanged && !isInternalUpdateRef.current) {
      initialNodesRef.current = initialNodes;
      setNodes(initialNodes);
    }
  }, [initialNodes, setNodes]);

  useEffect(() => {
    const edgesChanged = JSON.stringify(initialEdges) !== JSON.stringify(initialEdgesRef.current);
    if (edgesChanged && !isInternalUpdateRef.current) {
      initialEdgesRef.current = initialEdges;
      setEdges(initialEdges);
    }
  }, [initialEdges, setEdges]);

  // 同步本地状态到父组件（使用防抖避免频繁更新）
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

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: any) => {
      setSelectedNode(node);
      // Close editor on single click if selecting a different node
      // Or keep it open if you want "sticky" behavior, but requirement implies explicitly double click to open
      // We'll keep it simple: Single click selects, doesn't toggle editor.
    },
    [],
  );

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: any) => {
      setSelectedNode(node);
      setIsEditorOpen(true);

      const { x, y, zoom } = getViewport();
      // Calculate node's position in screen coordinates relative to the container
      // node.position is the top-left of the node in flow coordinates
      const nodeX = node.position.x * zoom + x;
      const nodeY = node.position.y * zoom + y;

      // Place editor to the right of the node (width approx 320px)
      // Add some buffer (e.g. 20px)
      const buffer = 20;
      const nodeWidth = 320 * zoom;

      setEditorPosition({
        x: nodeX + nodeWidth + buffer,
        y: nodeY
      });
    },
    [getViewport]
  );

  // Template chapters mapping
  const templateChapters: Record<string, string[]> = {
    "危险房屋鉴定": [
      "一、基本情况",
      "二、房屋概况",
      "三、鉴定内容和方法、主要检测仪器设备及原始记录一览",
      "四、检测鉴定依据",
      "五、检查和检测情况",
      "六、复核验算",
      "七、分析说明",
      "八、鉴定意见及处理建议"
    ],
    "标准结构检测报告": [
      "一、工程概况",
      "二、检测依据",
      "三、检测内容和方法",
      "四、检测结果",
      "五、检测结论",
      "六、建议"
    ],
    "混凝土专项检测": [
      "一、工程概况",
      "二、检测方法",
      "三、检测结果",
      "四、结论与建议"
    ],
    "钢筋保护层厚度检测": [
      "一、工程概况",
      "二、检测方法",
      "三、检测结果"
    ],
    "建筑物沉降观测": [
      "一、工程概况",
      "二、观测点布设",
      "三、观测方法",
      "四、观测数据",
      "五、数据分析"
    ],
    "装配式结构验收": [
      "一、工程概况",
      "二、预制构件进场验收",
      "三、连接节点验收",
      "四、灌浆质量验收",
      "五、结构性能检测",
      "六、验收结论",
      "七、建议"
    ],
    "节能工程检测": [
      "一、工程概况",
      "二、检测内容",
      "三、检测方法",
      "四、检测结果"
    ],
    "民用建筑可靠性鉴定": [
      "一、工程概况",
      "二、鉴定依据",
      "三、鉴定内容",
      "四、现场检查与检测",
      "五、结构安全性评估",
      "六、结构使用性评估",
      "七、鉴定结论",
      "八、处理建议"
    ],
    "工业建筑可靠性鉴定": [
      "一、工程概况",
      "二、鉴定依据",
      "三、鉴定内容",
      "四、现场检查与检测",
      "五、结构系统鉴定",
      "六、构件鉴定",
      "七、材料鉴定",
      "八、结构安全性评估",
      "九、结构使用性评估",
      "十、鉴定结论与建议"
    ],
    "抗震鉴定": [
      "一、工程概况",
      "二、鉴定依据",
      "三、现场检查",
      "四、抗震承载力验算",
      "五、抗震构造措施检查",
      "六、抗震性能评估",
      "七、鉴定结论"
    ],
    "主体结构施工质量鉴定": [
      "一、工程概况",
      "二、鉴定依据",
      "三、检查内容",
      "四、检测结果",
      "五、质量评估",
      "六、鉴定结论"
    ]
  };

  const addNode = useCallback(
    (chapterTitle: string) => {
      // 检查是否是模板
      if (chapterTitle.startsWith("TEMPLATE:")) {
        const templateName = chapterTitle.replace("TEMPLATE:", "");
        const chapters = templateChapters[templateName];
        
        if (chapters && chapters.length > 0) {
          // 创建多个节点
          const newNodes = chapters.map((chapter, index) => {
            // 从章节标题中提取编号（如"一、"、"二、"等）
            const chapterMatch = chapter.match(/^([一二三四五六七八九十]+)、/);
            const chapterNumber = chapterMatch ? chapterMatch[1] : `${index + 1}`;
            const title = chapter.replace(/^[一二三四五六七八九十]+、/, "");

            return {
              id: `report-${Date.now()}-${index}`,
              type: "report",
              position: {
                x: 100 + (index % 3) * 400,
                y: 100 + Math.floor(index / 3) * 150,
              },
              data: {
                label: title || chapter,
                chapterNumber: chapterNumber,
                llmModel: "",
                prompt: "",
                references: [],
                templates: [],
                status: 'idle',
              },
            };
          });
          
          // 标记为内部更新，避免触发循环同步
          isInternalUpdateRef.current = true;
          setNodes((nds) => [...nds, ...newNodes]);
          return;
        }
      }

      // 原有的单个节点创建逻辑
      // 从标题中提取章节编号
      const match = chapterTitle.match(/第(.+?)章\s*(.+)/);
      const chapterNumber = match
        ? match[1]
        : `${nodes.length + 1}`;
      const title = match ? match[2] : chapterTitle;

      const newNode = {
        id: `report-${Date.now()}`,
        type: "report",
        position: {
          x: Math.random() * 400 + 100,
          y: Math.random() * 400 + 100,
        },
        data: {
          label: title,
          chapterNumber: chapterNumber,
          llmModel: "",
          prompt: "",
          references: [],
          templates: [],
          status: 'idle', // idle, running, completed
        },
      };
      
      // 标记为内部更新，避免触发循环同步
      isInternalUpdateRef.current = true;
      setNodes((nds) => [...nds, newNode]);
    },
    [nodes.length, setNodes],
  );

  // 处理章节选中和定位
  const handleNodeSelect = useCallback(
    (nodeId: string) => {
      const node = getNode(nodeId);
      if (node) {
        setSelectedNode(node);
        setCenter(node.position.x + 100, node.position.y + 50, {
          zoom: 1.2,
          duration: 800,
        });
        // 选中状态更新不需要标记为内部更新，这是用户操作
        setNodes((nds) =>
          nds.map((n) => ({
            ...n,
            selected: n.id === nodeId,
          })),
        );
      }
    },
    [getNode, setCenter, setNodes],
  );

  // 停止报告生成
  const handleStopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsReportGenerating(false);
    // 将所有 running 状态的节点重置为 idle
    // 这是用户操作，应该同步到父组件
    setNodes((nds) => nds.map(n => 
      n.data.status === 'running' ? { ...n, data: { ...n.data, status: 'idle' } } : n
    ));
  }, [setNodes]);

  // 模拟报告生成过程
  const handleGenerateReport = async () => {
    // 创建新的 AbortController
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setShowGenerateModal(true);
    setIsReportGenerating(true);

    // 重置所有节点状态
    setNodes((nds) => nds.map(n => ({ ...n, data: { ...n.data, status: 'idle' } })));

    // 按顺序执行每个节点
    // 这里简单假设节点顺序就是数组顺序，实际上可能需要按照边连接顺序排序
    const sortedNodes = [...nodes].sort((a, b) => {
      // 简单的根据y坐标排序，或者根据chapterNumber排序
      return parseFloat(a.data.chapterNumber) - parseFloat(b.data.chapterNumber);
    });

    for (const node of sortedNodes) {
      // 检查是否被终止
      if (signal.aborted) {
        break;
      }

      // 1. 设置当前节点为运行中
      setNodes((nds) => nds.map(n =>
        n.id === node.id ? { ...n, data: { ...n.data, status: 'running' } } : n
      ));

      // 聚焦到当前运行的节点
      setCenter(node.position.x + 100, node.position.y + 50, { zoom: 1.2, duration: 500 });

      // 模拟生成耗时（支持中断）
      try {
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(resolve, 1500);
          signal.addEventListener('abort', () => {
            clearTimeout(timeout);
            reject(new Error('Generation aborted'));
          });
        });
      } catch {
        // 被终止，跳出循环
        break;
      }

      // 再次检查是否被终止
      if (signal.aborted) {
        break;
      }

      // 2. 设置当前节点为完成
      setNodes((nds) => nds.map(n =>
        n.id === node.id ? { ...n, data: { ...n.data, status: 'completed' } } : n
      ));
    }

    // 全部完成（或被终止）
    if (!signal.aborted) {
      setIsReportGenerating(false);
      // 最后再fitView一下
      setTimeout(() => fitView({ duration: 800, padding: 0.2 }), 500);
    }
    
    abortControllerRef.current = null;
  };

  // MiniMap 节点颜色函数
  const getMiniMapNodeColor = (node: Node) => {
    if (node.type !== "report") return "#8b5cf6";

    const chapterNumber = node.data?.chapterNumber || "";
    if (!chapterNumber || chapterNumber.trim() === "")
      return "#3b82f6";

    // 提取第一个数字
    const match = chapterNumber.match(/^(\d+)/);
    if (match) {
      const topLevel = parseInt(match[1], 10);
      const colorMap = [
        "#3b82f6", // blue
        "#8b5cf6", // purple
        "#6366f1", // indigo
        "#7c3aed", // violet
        "#c026d3", // fuchsia
        "#ec4899", // pink
        "#f43f5e", // rose
        "#06b6d4", // cyan
        "#14b8a6", // teal
        "#10b981", // emerald
      ];
      return colorMap[(topLevel - 1) % colorMap.length];
    }

    return "#3b82f6"; // 默认蓝色
  };

  // 磁吸功能 - 节点拖动结束时对齐
  const handleNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const SNAP_DISTANCE = 50; // 吸附检测距离
      const SNAP_GAP = 30; // 对齐后保持的间距
      const ALIGNMENT_THRESHOLD = 20; // 对齐阈值

      const nodeWidth = 320; // 节点宽度
      const nodeHeight = 92; // 节点高度（估算）

      const draggedNode = node;
      let snappedX = draggedNode.position.x;
      let snappedY = draggedNode.position.y;

      // 遍历所有其他节点，寻找吸附目标
      nodes.forEach((otherNode) => {
        if (otherNode.id === draggedNode.id) return;

        const dx = Math.abs(
          draggedNode.position.x - otherNode.position.x,
        );
        const dy = Math.abs(
          draggedNode.position.y - otherNode.position.y,
        );

        // 水平对齐检测（上下排列）
        if (dx < ALIGNMENT_THRESHOLD) {
          const bottomOfOther =
            otherNode.position.y + nodeHeight;
          const topOfDragged = draggedNode.position.y;
          const bottomOfDragged =
            draggedNode.position.y + nodeHeight;
          const topOfOther = otherNode.position.y;

          if (
            Math.abs(topOfDragged - bottomOfOther) <
            SNAP_DISTANCE
          ) {
            snappedX = otherNode.position.x;
            snappedY = bottomOfOther + SNAP_GAP;
          }
          else if (
            Math.abs(bottomOfDragged - topOfOther) <
            SNAP_DISTANCE
          ) {
            snappedX = otherNode.position.x;
            snappedY = topOfOther - nodeHeight - SNAP_GAP;
          }
        }

        // 垂直对齐检测（左右排列）
        if (dy < ALIGNMENT_THRESHOLD) {
          const rightOfOther = otherNode.position.x + nodeWidth;
          const leftOfDragged = draggedNode.position.x;
          const rightOfDragged =
            draggedNode.position.x + nodeWidth;
          const leftOfOther = otherNode.position.x;

          if (
            Math.abs(leftOfDragged - rightOfOther) <
            SNAP_DISTANCE
          ) {
            snappedX = rightOfOther + SNAP_GAP;
            snappedY = otherNode.position.y;
          }
          else if (
            Math.abs(rightOfDragged - leftOfOther) <
            SNAP_DISTANCE
          ) {
            snappedX = leftOfOther - nodeWidth - SNAP_GAP;
            snappedY = otherNode.position.y;
          }
        }

        // 中心对齐检测
        const centerXDragged =
          draggedNode.position.x + nodeWidth / 2;
        const centerYDragged =
          draggedNode.position.y + nodeHeight / 2;
        const centerXOther =
          otherNode.position.x + nodeWidth / 2;
        const centerYOther =
          otherNode.position.y + nodeHeight / 2;

        if (
          Math.abs(centerXDragged - centerXOther) <
          ALIGNMENT_THRESHOLD &&
          dy < SNAP_DISTANCE
        ) {
          snappedX = otherNode.position.x;
        }

        if (
          Math.abs(centerYDragged - centerYOther) <
          ALIGNMENT_THRESHOLD &&
          dx < SNAP_DISTANCE
        ) {
          snappedY = otherNode.position.y;
        }
      });

      if (
        snappedX !== draggedNode.position.x ||
        snappedY !== draggedNode.position.y
      ) {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === draggedNode.id
              ? { ...n, position: { x: snappedX, y: snappedY } }
              : n,
          ),
        );
      }
    },
    [nodes, setNodes],
  );

  // Ref for the main content area to calculate precise resize widths
  const containerRef = useRef<HTMLDivElement>(null);

  // 处理预览面板高度调整
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingPreview || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      // Calculate height from the top of the container
      const newHeightPixels = e.clientY - containerRect.top;
      const newHeightPercent = (newHeightPixels / containerRect.height) * 100;

      // 限制高度在30%到80%之间
      const clampedHeight = Math.max(
        30,
        Math.min(80, newHeightPercent),
      );
      setPreviewHeight(clampedHeight);
    };

    const handleMouseUp = () => {
      setIsResizingPreview(false);
    };

    if (isResizingPreview) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "row-resize";
      document.body.style.userSelect = "none";
    }

    return () => {
      document.removeEventListener(
        "mousemove",
        handleMouseMove,
      );
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizingPreview]);

  // 当预览面板显示状态改变时，自动调整视图以展示所有节点
  useEffect(() => {
    if (showGenerateModal) {
      // 稍微延迟以等待布局更新
      const timer = setTimeout(() => {
        fitView({ duration: 600, padding: 0.2 });
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [showGenerateModal, fitView]);

  return (
    <div className="flex h-full w-full bg-slate-50 relative">
      {/* Sidebar */}
      <NodeSidebar
        onAddNode={addNode}
        mode="report"
        nodes={nodes}
        onNodeSelect={handleNodeSelect}
        onGenerateReport={handleGenerateReport}
        onStopGeneration={handleStopGeneration}
        isGenerating={isReportGenerating}
      />

      {/* Main Content Area (Vertical Split Pane) */}
      <div className="flex-1 flex flex-col relative overflow-hidden" ref={containerRef}>
        {/* Preview Panel - Top (above canvas) */}
        {showGenerateModal && (
          <div
            className={`relative bg-white border-b border-slate-200 shadow-sm z-10 flex flex-col w-full ${isResizingPreview ? '' : 'transition-all duration-300 ease-in-out'
              }`}
            style={{ height: `${previewHeight}%` }}
          >
            {/* The Report Preview Component */}
            <div className="flex-1 overflow-hidden min-h-0 flex flex-col">
              <ReportPreview 
                isGenerating={isReportGenerating} 
                onClose={() => setShowGenerateModal(false)}
              />
            </div>

            {/* Resizer Handle - Horizontal */}
            <div
              className="absolute left-0 right-0 bottom-0 h-2 cursor-row-resize hover:bg-blue-100 transition-colors z-20 flex items-center justify-center group"
              onMouseDown={() => setIsResizingPreview(true)}
            >
              {/* 中间的拖动指示器 - 拉到底时消失 */}
              <div 
                className={`flex flex-col items-center gap-0.5 transition-opacity duration-200 ${previewHeight >= 78 ? 'opacity-0' : 'opacity-100'}`}
              >
                <div className="w-8 h-0.5 bg-slate-300 rounded-full group-hover:bg-blue-400 transition-colors" />
                <svg 
                  className="w-3 h-3 text-slate-400 group-hover:text-blue-500 transition-colors" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2"
                >
                  <path d="M7 10l5 5 5-5" />
                </svg>
              </div>
            </div>
          </div>
        )}

        {/* Flow Editor - takes remaining space */}
        <div className="flex-1 relative w-full min-h-0">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onNodeDoubleClick={onNodeDoubleClick}
            nodeTypes={nodeTypes}
            className="bg-slate-50"
            selectionOnDrag
            panOnDrag={[1, 2]}
            selectionMode="partial"
            multiSelectionKeyCode="Shift"
            nodesConnectable={false}
            edgesUpdatable={false}
            edgesFocusable={false}
            onNodeDragStop={handleNodeDragStop}
          >
            <Background color="#e2e8f0" gap={16} />
            <Controls className="bg-white border border-slate-200 rounded-lg shadow-sm" />
            <MiniMap
              className="bg-white border border-slate-200 rounded-lg shadow-sm"
              nodeColor={getMiniMapNodeColor}
              maskColor="rgba(241, 245, 249, 0.8)"
              pannable
              zoomable
            />
            <FitView />
          </ReactFlow>

          {/* 空白画布提示 */}
          {nodes.length === 0 && !showGenerateModal && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <FileText className="w-16 h-16 text-slate-200 mx-auto mb-4" />
                <p className="text-slate-400 text-sm">请从左侧选择报告模板或添加章节节点</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Report Node Editor Panel (Floating Draggable) */}
      {selectedNode && isEditorOpen && (
        <div
          style={{
            position: 'absolute',
            left: editorPosition.x,
            top: editorPosition.y,
            height: '600px', // Fixed height for better UX
            zIndex: 50
          }}
          className="shadow-2xl rounded-lg overflow-hidden border border-slate-200"
        >
          <ReportNodeEditor
            node={selectedNode}
            onClose={() => setIsEditorOpen(false)}
            onUpdate={(updatedNode) => {
              setNodes((nds) =>
                nds.map((n) =>
                  n.id === updatedNode.id ? updatedNode : n,
                ),
              );
            }}
            onHeaderMouseDown={handleEditorHeaderMouseDown}
          />
        </div>
      )}
    </div>
  );
}

export default function ReportEditor(props: ReportEditorProps) {
  return (
    <ReactFlowProvider>
      <ReportEditorContent {...props} />
    </ReactFlowProvider>
  );
}
