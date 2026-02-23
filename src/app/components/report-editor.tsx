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
  SelectionMode,
} from "reactflow";
import "reactflow/dist/style.css";
import ReportNode from "./nodes/report-node";
import NodeSidebar from "./node-sidebar";
import { ProjectSidebar } from "./project-sidebar";
import ReportNodeEditor from "./report-node-editor";
import { ReportPreview } from "./report-preview"; // Import the new component
import { FileText, ChevronLeft, ChevronRight, Eye, RotateCcw, Trash2 } from "lucide-react";

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
  nodeSnapshot: Node[];
  chapterCount: number;
}

function ReportEditorContent({
  projectId,
  reportType,
  collectionNodes,
  initialNodes,
  initialEdges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp,
}: ReportEditorProps) {
  const getDefaultReferenceByReportType = useCallback((type?: string) => {
    const mapping: Record<string, { code: string; name: string }> = {
      "民用建筑可靠性鉴定": { code: "GB 50292-2015", name: "民用建筑可靠性鉴定标准" },
      "危险房屋鉴定": { code: "JGJ 125-2016", name: "危险房屋鉴定标准" },
      "抗震鉴定": { code: "GB 50023-2009", name: "建筑抗震鉴定标准" },
      "主体结构施工质量鉴定": { code: "GB 50204-2015", name: "混凝土结构工程施工质量验收规范" },
    };
    return mapping[type || ""] || { code: "JGJ 125-2016", name: "危险房屋鉴定标准" };
  }, []);

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
  const [editorSize, setEditorSize] = useState({ width: 420, height: 600 });
  const [isDraggingEditor, setIsDraggingEditor] = useState(false);
  const [isResizingEditor, setIsResizingEditor] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [resizeStart, setResizeStart] = useState({ 
    mouseX: 0, 
    mouseY: 0, 
    width: 0, 
    height: 0 
  });

  const [isReportGenerating, setIsReportGenerating] = useState(false);
  const [reportChapters, setReportChapters] = useState<any[]>([]);
  const [reportHistory, setReportHistory] = useState<ReportGenerationSnapshot[]>([]);
  const [isHistorySidebarOpen, setIsHistorySidebarOpen] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 使用 ref 来跟踪是否是内部更新，避免循环同步
  const isInternalUpdateRef = useRef(false);
  const initialNodesRef = useRef(initialNodes);
  const initialEdgesRef = useRef(initialEdges);

  const historyStorageKey = `project_${projectId}_report_generation_history`;

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

  // 处理编辑器拖动
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDraggingEditor) {
        const newX = e.clientX - dragOffset.x;
        const newY = e.clientY - dragOffset.y;

        // 简单的边界检查
        const maxX = window.innerWidth - editorSize.width;
        const maxY = window.innerHeight - 50;

        setEditorPosition({
          x: Math.max(0, Math.min(maxX, newX)),
          y: Math.max(0, Math.min(maxY, newY))
        });
      } else if (isResizingEditor) {
        // 计算鼠标移动的距离
        const deltaX = e.clientX - resizeStart.mouseX;
        const deltaY = e.clientY - resizeStart.mouseY;
        
        // 基于初始尺寸和移动距离计算新尺寸
        const newWidth = Math.max(320, resizeStart.width + deltaX);
        const newHeight = Math.max(400, resizeStart.height + deltaY);
        
        setEditorSize({
          width: newWidth,
          height: newHeight
        });
      }
    };

    const handleMouseUp = () => {
      setIsDraggingEditor(false);
      setIsResizingEditor(false);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };

    if (isDraggingEditor || isResizingEditor) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = 'none';
      if (isResizingEditor) {
        document.body.style.cursor = 'nwse-resize';
      }
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isDraggingEditor, isResizingEditor, dragOffset, editorPosition, editorSize]);

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
      "三、鉴定内容和方法及原始记录一览表",
      "四、检测鉴定依据",
      "五、检查和检测情况",
      "六、复核验算",
      "七、分析评述",
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

  const getTemplateStyleForTitle = (title: string) => {
    if (title.includes("房屋概况")) {
      return "house_overview";
    }
    if (title.includes("基本情况")) {
      return "basic_situation";
    }
    if (title.includes("鉴定内容和方法") && title.includes("原始记录")) {
      return "inspection_content_and_methods";
    }
    if (title.includes("检测鉴定依据") || title.includes("鉴定依据") || title.includes("检测依据")) {
      return "inspection_basis";
    }
    if (title.includes("检查情况") || title.includes("现场检查") || title.includes("检查和检测情况")) {
      return "detailed_inspection";
    }
    if (title.includes("荷载及计算参数取值")) {
      return "load_calc_params";
    }
    if (title.includes("承载能力复核验算")) {
      return "bearing_capacity_review";
    }
    if (title.includes("分析说明") || title.includes("分析评述")) {
      return "analysis_explanation";
    }
    if (title.includes("鉴定意见") || title.includes("处理建议")) {
      return "opinion_and_suggestions";
    }
    return "text_table_1";
  };

  const getDefaultSourceForTitle = (title: string) => {
    if (title.includes("房屋概况")) {
      return "scope_house_overview";
    }
    if (title.includes("基本情况")) {
      return "scope_basic_situation";
    }
    if (title.includes("检测鉴定依据") || title.includes("鉴定依据") || title.includes("检测依据")) {
      return "scope_inspection_basis";
    }
    if (title.includes("检查情况") || title.includes("现场检查") || title.includes("检查和检测情况")) {
      return "scope_detailed_inspection";
    }
    if (title.includes("荷载及计算参数取值")) {
      return "scope_load_calc_params";
    }
    if (title.includes("承载能力复核验算")) {
      return "scope_bearing_capacity_review";
    }
    if (title.includes("分析说明") || title.includes("分析评述")) {
      return "scope_analysis_explanation";
    }
    if (title.includes("鉴定意见") || title.includes("处理建议")) {
      return "scope_opinion_and_suggestions";
    }
    return null;
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
            // 从章节标题中提取编号(如"一、"、"二、"等)
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
                templateStyle: getTemplateStyleForTitle(title || chapter),
                sourceNodeId: getDefaultSourceForTitle(title || chapter),
                referenceSpecType: "system",
                referenceSpec: (title || chapter).includes("检测鉴定依据")
                  ? getDefaultReferenceByReportType(reportType).code
                  : "JGJ/T 23-2011",
                systemReferenceCode: (title || chapter).includes("检测鉴定依据")
                  ? getDefaultReferenceByReportType(reportType).code
                  : "JGJ/T 23-2011",
                systemReferenceName: (title || chapter).includes("检测鉴定依据")
                  ? getDefaultReferenceByReportType(reportType).name
                  : "",
                status: 'idle',
              },
            };
          });
          
          // 标记为内部更新,避免触发循环同步
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
          templateStyle: getTemplateStyleForTitle(title),
          sourceNodeId: getDefaultSourceForTitle(title),
          referenceSpecType: "system",
          referenceSpec: title.includes("检测鉴定依据")
            ? getDefaultReferenceByReportType(reportType).code
            : "JGJ/T 23-2011",
          systemReferenceCode: title.includes("检测鉴定依据")
            ? getDefaultReferenceByReportType(reportType).code
            : "JGJ/T 23-2011",
          systemReferenceName: title.includes("检测鉴定依据")
            ? getDefaultReferenceByReportType(reportType).name
            : "",
          status: 'idle', // idle, running, completed
        },
      };
      
      // 标记为内部更新,避免触发循环同步
      isInternalUpdateRef.current = true;
      setNodes((nds) => [...nds, newNode]);
    },
    [nodes.length, setNodes, getDefaultReferenceByReportType, getDefaultSourceForTitle, reportType],
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
        // 閫変腑鐘舵€佹洿鏂颁笉闇€瑕佹爣璁颁负鍐呴儴鏇存柊锛岃繖鏄敤鎴锋搷浣?
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

  // 鍋滄鎶ュ憡鐢熸垚
  const handleStopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsReportGenerating(false);
    // 灏嗘墍鏈?running 鐘舵€佺殑鑺傜偣閲嶇疆涓?idle
    // 杩欐槸鐢ㄦ埛鎿嶄綔锛屽簲璇ュ悓姝ュ埌鐖剁粍浠?
    setNodes((nds) => nds.map(n => 
      n.data.status === 'running' ? { ...n, data: { ...n.data, status: 'idle' } } : n
    ));
  }, [setNodes]);

  // 妯℃嫙鎶ュ憡鐢熸垚杩囩▼
  const handleGenerateReport = async () => {
    // ???? AbortController
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setShowGenerateModal(true);
    setIsReportGenerating(true);
    setReportChapters([]);

    // ????????
    setNodes((nds) => nds.map(n => ({ ...n, data: { ...n.data, status: 'idle' } })));

    // ???????????
    const sortedNodes = [...nodes].sort((a, b) => {
      return parseFloat(a.data.chapterNumber) - parseFloat(b.data.chapterNumber);
    });

    const nextChapters: any[] = [];
    for (const node of sortedNodes) {
      if (signal.aborted) {
        break;
      }

      setNodes((nds) => nds.map(n =>
        n.id === node.id ? { ...n, data: { ...n.data, status: 'running' } } : n
      ));

      setCenter(node.position.x + 100, node.position.y + 50, { zoom: 1.2, duration: 500 });

      try {
        const referenceSpecType = node.data?.referenceSpecType || node.data?.referenceTab || "system";
        const referenceSpec =
          node.data?.referenceSpec ||
          node.data?.referenceCode ||
          node.data?.systemReferenceCode ||
          "JGJ/T 23-2011";
        // 鑾峰彇鏁版嵁婧愯妭鐐笽D锛堢敤浜庢煡璇㈡暟鎹級
        const sourceNodeId = node.data?.sourceNodeId || node.data?.source_node_id || null;
        
        const ruleId =
          node.data?.userReferenceCode ||
          (referenceSpecType === "user" ? referenceSpec : undefined);

        const templateStyle = node.data?.templateStyle || node.data?.template_style || "concrete_strength_table";
        
        // 根据 templateStyle 自动映射 dataset_key(已更新为新系统)
        const datasetKeyMap: Record<string, string> = {
          'concrete_strength_full': 'concrete_strength',  // 混凝土强度(新系统)
          'concrete_strength_table': 'concrete_strength',  // 混凝土强度表格(兼容旧系统)
          'concrete_strength_desc': 'concrete_strength',  // 混凝土强度描述(兼容旧系统)
          'mortar_strength_data': 'mortar_strength',  // 砂浆强度数据
          'mortar_strength_desc': 'mortar_strength',  // 砂浆强度描述
          'brick_strength_table': 'brick_strength',  // 砖强度表格
          'brick_strength_desc': 'brick_strength',  // 砖强度描述
          'inspection_content_and_methods': 'inspection_content_and_methods',  // 鉴定内容和方法及原始记录一览表
          'inspection_basis': 'inspection_basis',  // 检测鉴定依据
          'detailed_inspection': 'detailed_inspection',  // 详细检查情况
          'basic_situation': 'basic_situation',  // 基本情况
          'house_overview': 'house_overview',  // 房屋概况
          'load_calc_params': 'load_calc_params',  // 荷载及计算参数取值
          'bearing_capacity_review': 'bearing_capacity_review',  // 承载能力复核验算
          'analysis_explanation': 'analysis_explanation',  // 分析说明
          'opinion_and_suggestions': 'opinion_and_suggestions',  // 鉴定意见及处理建议
        };
        const datasetKey = node.data?.datasetKey || node.data?.dataset_key || datasetKeyMap[templateStyle] || "concrete_strength";

        const chapterNumber = node.data?.chapterNumber || "";
        const chapterTitle = node.data?.label || "";

        const payload = {
          project_id: projectId,
          chapter_config: {
            node_id: node.id, // 报告节点ID(用于标识章节)
            sourceNodeId: sourceNodeId, // 数据源节点ID或检测大类(scope_开头)
            title: chapterTitle,
            dataset_key: datasetKey,
            table_id: node.data?.tableId || node.data?.table_id || "table_7_rebound",
            template_style: templateStyle,
            reference_spec_type: referenceSpecType,
            reference_spec: referenceSpec,
            rule_id: ruleId,
            context: {
              report_type: reportType || "",
              reference_spec: referenceSpec,
              chapter_number: chapterNumber,
            },
          },
          project_context: {
            report_type: reportType || "",
          },
        };

        const response = await fetch("/api/report/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal,
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: response.statusText }));
          throw new Error(errorData.detail || errorData.message || response.statusText);
        }

        const result = await response.json();
        if (result?.chapters?.length) {
          nextChapters.push(...result.chapters);
        }
      } catch {
        break;
      }

      if (signal.aborted) {
        break;
      }

      setNodes((nds) => nds.map(n =>
        n.id === node.id ? { ...n, data: { ...n.data, status: 'completed' } } : n
      ));
    }

    if (!signal.aborted) {
      setIsReportGenerating(false);
      setReportChapters(nextChapters);
      const snapshot: ReportGenerationSnapshot = {
        id: `report-snapshot-${Date.now()}`,
        createdAt: new Date().toISOString(),
        reportType: reportType || "",
        chapters: nextChapters,
        nodeSnapshot: JSON.parse(JSON.stringify(nodes)),
        chapterCount: nextChapters.length,
      };
      setReportHistory((prev) => [snapshot, ...prev].slice(0, 50));
      setTimeout(() => fitView({ duration: 800, padding: 0.2 }), 500);
    }

    abortControllerRef.current = null;
  };

  // MiniMap 鑺傜偣棰滆壊鍑芥暟
  const getMiniMapNodeColor = (node: Node) => {
    if (node.type !== "report") return "#8b5cf6";

    const chapterNumber = node.data?.chapterNumber || "";
    if (!chapterNumber || chapterNumber.trim() === "")
      return "#3b82f6";

    // 鎻愬彇绗竴涓暟瀛?
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

    return "#3b82f6"; // 榛樿钃濊壊
  };

  // 纾佸惛鍔熻兘 - 鑺傜偣鎷栧姩缁撴潫鏃跺榻?
  const handleNodeDragStop = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const SNAP_DISTANCE = 50; // 鍚搁檮妫€娴嬭窛绂?
      const SNAP_GAP = 30; // 瀵归綈鍚庝繚鎸佺殑闂磋窛
      const ALIGNMENT_THRESHOLD = 20; // 瀵归綈闃堝€?

      const nodeWidth = 320; // 鑺傜偣瀹藉害
      const nodeHeight = 92; // 鑺傜偣楂樺害锛堜及绠楋級

      const draggedNode = node;
      let snappedX = draggedNode.position.x;
      let snappedY = draggedNode.position.y;

      // 閬嶅巻鎵€鏈夊叾浠栬妭鐐癸紝瀵绘壘鍚搁檮鐩爣
      nodes.forEach((otherNode) => {
        if (otherNode.id === draggedNode.id) return;

        const dx = Math.abs(
          draggedNode.position.x - otherNode.position.x,
        );
        const dy = Math.abs(
          draggedNode.position.y - otherNode.position.y,
        );

        // 姘村钩瀵归綈妫€娴嬶紙涓婁笅鎺掑垪锛?
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

        // 鍨傜洿瀵归綈妫€娴嬶紙宸﹀彸鎺掑垪锛?
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

        // 涓績瀵归綈妫€娴?
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

  // 澶勭悊棰勮闈㈡澘楂樺害璋冩暣
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingPreview || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      // Calculate height from the top of the container
      const newHeightPixels = e.clientY - containerRect.top;
      const newHeightPercent = (newHeightPixels / containerRect.height) * 100;

      // 闄愬埗楂樺害鍦?0%鍒?0%涔嬮棿
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

  // 褰撻瑙堥潰鏉挎樉绀虹姸鎬佹敼鍙樻椂锛岃嚜鍔ㄨ皟鏁磋鍥句互灞曠ず鎵€鏈夎妭鐐?
  useEffect(() => {
    if (showGenerateModal) {
      // 绋嶅井寤惰繜浠ョ瓑寰呭竷灞€鏇存柊
      const timer = setTimeout(() => {
        fitView({ duration: 600, padding: 0.2 });
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [showGenerateModal, fitView]);

  const handleLoadHistoryPreview = useCallback((snapshot: ReportGenerationSnapshot) => {
    setReportChapters(snapshot.chapters || []);
    setIsReportGenerating(false);
    setShowGenerateModal(true);
  }, []);

  const handleRestoreNodeConfig = useCallback((snapshot: ReportGenerationSnapshot) => {
    if (!Array.isArray(snapshot.nodeSnapshot)) return;
    isInternalUpdateRef.current = true;
    setNodes(snapshot.nodeSnapshot);
    setSelectedNode(null);
    setIsEditorOpen(false);
  }, [setNodes]);

  const handleClearHistory = useCallback(() => {
    setReportHistory([]);
  }, []);

  const handleDeleteHistoryItem = useCallback((itemId: string) => {
    setReportHistory((history) => history.filter((item) => item.id !== itemId));
  }, []);

  const historyCountLabel = reportHistory.length > 99 ? "99+" : String(reportHistory.length);

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
                chapters={reportChapters}
                onClose={() => setShowGenerateModal(false)}
              />
            </div>

            {/* Resizer Handle - Horizontal */}
            <div
              className="absolute left-0 right-0 bottom-0 h-2 cursor-row-resize hover:bg-blue-100 transition-colors z-20 flex items-center justify-center group"
              onMouseDown={() => setIsResizingPreview(true)}
            >
              {/* 涓棿鐨勬嫋鍔ㄦ寚绀哄櫒 - 鎷夊埌搴曟椂娑堝け */}
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
            selectionMode={SelectionMode.Partial}
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

      {/* Collapsible History Sidebar (inside 报告生成功能) */}
      <div
        className={`h-full border-l border-slate-200 bg-white transition-all duration-200 ${
          isHistorySidebarOpen ? "w-80" : "w-10"
        }`}
      >
        <div className="h-full flex flex-col">
          <div className="h-12 border-b border-slate-200 flex items-center justify-between px-2">
            {isHistorySidebarOpen && (
              <div className="text-sm font-semibold text-slate-700 px-1">报告回溯</div>
            )}
            <button
              className="p-1.5 rounded hover:bg-slate-100 text-slate-500"
              onClick={() => setIsHistorySidebarOpen((v) => !v)}
              title={isHistorySidebarOpen ? "收起" : "展开"}
            >
              {isHistorySidebarOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {isHistorySidebarOpen && (
            <>
              <div className="px-3 py-2 border-b border-slate-100">
                <span className="text-xs text-slate-500">共 {reportHistory.length} 份</span>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {reportHistory.length === 0 ? (
                  <div className="text-xs text-slate-400 px-2 py-4">暂无历史报告</div>
                ) : (
                  reportHistory.map((item, index) => (
                    <div key={item.id} className="border border-slate-200 rounded-lg p-2 space-y-2">
                      <div className="text-xs text-slate-700 font-medium">
                        第 {reportHistory.length - index} 次生成
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {new Date(item.createdAt).toLocaleString("zh-CN")}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        章节数：{item.chapterCount} {item.reportType ? `| 类型：${item.reportType}` : ""}
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          className="text-xs px-2 py-1 rounded bg-slate-900 text-white hover:bg-slate-800 inline-flex items-center gap-1"
                          onClick={() => handleLoadHistoryPreview(item)}
                        >
                          <Eye className="w-3 h-3" />
                          查看
                        </button>
                        <button
                          className="text-xs px-2 py-1 rounded border border-slate-200 text-slate-700 hover:bg-slate-50 inline-flex items-center gap-1"
                          onClick={() => handleRestoreNodeConfig(item)}
                        >
                          <RotateCcw className="w-3 h-3" />
                          恢复节点
                        </button>
                        <button
                          className="text-xs px-2 py-1 rounded border border-rose-200 text-rose-600 hover:bg-rose-50 inline-flex items-center gap-1"
                          onClick={() => handleDeleteHistoryItem(item.id)}
                          title="删除此记录"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}

          {!isHistorySidebarOpen && (
            <div className="flex-1 flex items-start justify-center pt-3">
              <div
                className="min-w-[22px] h-[22px] px-1 rounded-full bg-slate-900 text-white text-[10px] leading-[22px] text-center font-semibold"
                title={`已生成 ${reportHistory.length} 份报告`}
              >
                {historyCountLabel}
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
            width: editorSize.width,
            height: editorSize.height,
            zIndex: 50
          }}
          className="shadow-2xl rounded-lg overflow-hidden border border-slate-200 bg-white"
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
            collectionNodes={collectionNodes}
            reportType={reportType}
          />
          {/* Resize Handle - Bottom Right Corner */}
          <div
            className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize z-50 flex items-center justify-center hover:bg-slate-100 rounded-tl transition-colors"
            onMouseDown={(e) => {
              e.stopPropagation();
              e.preventDefault();
              // 璁板綍鍒濆榧犳爣浣嶇疆鍜岀獥鍙ｅ昂瀵?
              setResizeStart({
                mouseX: e.clientX,
                mouseY: e.clientY,
                width: editorSize.width,
                height: editorSize.height
              });
              setIsResizingEditor(true);
            }}
          >
            <div className="w-2 h-2 border-r-2 border-b-2 border-slate-400 transform translate-x-[-1px] translate-y-[-1px]"></div>
          </div>
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


