import { useCallback, useState, useEffect } from "react";
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
import ReportNodeEditor from "./report-node-editor";
import { FileText, Sparkles, X } from "lucide-react";

const nodeTypes: NodeTypes = {
  report: ReportNode,
};

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
  const [previewWidth, setPreviewWidth] = useState(50); // 预览面板宽度百分比，默认50%
  const [isResizingPreview, setIsResizingPreview] =
    useState(false);
  const { setCenter, getNode } = useReactFlow();

  // 同步本地状态到父组件
  useEffect(() => {
    onNodesChangeProp(nodes);
  }, [nodes, onNodesChangeProp]);

  useEffect(() => {
    onEdgesChangeProp(edges);
  }, [edges, onEdgesChangeProp]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: any) => {
      setSelectedNode(node);
    },
    [],
  );

  const addNode = useCallback(
    (chapterTitle: string) => {
      // 从标题中提取章节编号，格式如："第1章 概述" 或 "第2.1章 子章节"
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
        },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [nodes.length, setNodes],
  );

  // 处理章节选中和定位
  const handleNodeSelect = useCallback(
    (nodeId: string) => {
      const node = getNode(nodeId);
      if (node) {
        // 选中节点
        setSelectedNode(node);

        // 居中显示节点，带缩放动画
        setCenter(node.position.x + 100, node.position.y + 50, {
          zoom: 1.2,
          duration: 800,
        });

        // 高亮节点（通过更新节点样式）
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
          // 检测是否在垂直方向接近
          const bottomOfOther =
            otherNode.position.y + nodeHeight;
          const topOfDragged = draggedNode.position.y;
          const bottomOfDragged =
            draggedNode.position.y + nodeHeight;
          const topOfOther = otherNode.position.y;

          // 拖动节点在目标节点下方
          if (
            Math.abs(topOfDragged - bottomOfOther) <
            SNAP_DISTANCE
          ) {
            snappedX = otherNode.position.x;
            snappedY = bottomOfOther + SNAP_GAP;
          }
          // 拖动节点在目标节点上方
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
          // 检测是否在水平方向接近
          const rightOfOther = otherNode.position.x + nodeWidth;
          const leftOfDragged = draggedNode.position.x;
          const rightOfDragged =
            draggedNode.position.x + nodeWidth;
          const leftOfOther = otherNode.position.x;

          // 拖动节点在目标节点右侧
          if (
            Math.abs(leftOfDragged - rightOfOther) <
            SNAP_DISTANCE
          ) {
            snappedX = rightOfOther + SNAP_GAP;
            snappedY = otherNode.position.y;
          }
          // 拖动节点在目标节点左侧
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

        // 水平中心对齐
        if (
          Math.abs(centerXDragged - centerXOther) <
            ALIGNMENT_THRESHOLD &&
          dy < SNAP_DISTANCE
        ) {
          snappedX = otherNode.position.x;
        }

        // 垂直中心对齐
        if (
          Math.abs(centerYDragged - centerYOther) <
            ALIGNMENT_THRESHOLD &&
          dx < SNAP_DISTANCE
        ) {
          snappedY = otherNode.position.y;
        }
      });

      // 应用吸附位置
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

  // 处理预览面板宽度调整
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingPreview) return;

      const containerWidth = window.innerWidth;
      const rightEdge = containerWidth - e.clientX;
      const newWidthPercent =
        (rightEdge / containerWidth) * 100;

      // 限制宽度在33.33%到80%之间
      const clampedWidth = Math.max(
        33.33,
        Math.min(80, newWidthPercent),
      );
      setPreviewWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsResizingPreview(false);
    };

    if (isResizingPreview) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
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

  return (
    <div className="flex h-full bg-slate-50">
      {/* Sidebar */}
      <NodeSidebar
        onAddNode={addNode}
        mode="report"
        nodes={nodes}
        onNodeSelect={handleNodeSelect}
        onGenerateReport={() => setShowGenerateModal(true)}
      />

      {/* Flow Editor */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
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
        </ReactFlow>

        {/* 生成报告弹窗 */}
        {showGenerateModal && (
          <>
            {/* 背景遮罩 */}
            <div
              className="absolute inset-0 bg-black/20 backdrop-blur-sm z-20 transition-opacity duration-300"
              onClick={() => setShowGenerateModal(false)}
            />

            {/* 弹窗内容 - 从右侧滑入，宽度可调 */}
            <div
              className="absolute right-0 top-0 bottom-0 bg-white shadow-2xl z-30 overflow-hidden flex flex-col border-l border-slate-200 transition-transform duration-300 ease-out"
              style={{
                width: `${previewWidth}%`,
                transform: showGenerateModal
                  ? "translateX(0)"
                  : "translateX(100%)",
              }}
            >
              {/* 左侧拖拽手柄 */}
              <div
                className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-indigo-500 transition-colors group z-40"
                onMouseDown={() => setIsResizingPreview(true)}
              >
                <div className="absolute inset-y-0 -left-1 -right-1" />
                {/* 拖拽指示器 */}
                <div className="absolute top-1/2 -translate-y-1/2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="w-1 h-12 bg-indigo-500 rounded-full shadow-lg" />
                </div>
              </div>

              {/* 弹窗头部 */}
              <div className="relative bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 p-6 text-white">
                {/* 装饰性光效 */}
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />

                <div className="relative flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
                      <Sparkles className="w-6 h-6" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold">
                        报告预览
                      </h2>
                      <p className="text-sm text-white/80 mt-1">
                        智能生成完整工程报告文档
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setShowGenerateModal(false)}
                    className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* 弹窗主体内容 */}
              <div className="flex-1 overflow-y-auto p-6">
                <div className="h-full flex items-center justify-center">
                  {/* 报告生成动画 */}
                  <div className="text-center">
                    {/* 文档图标容器 */}
                    <div className="relative inline-block mb-8">
                      {/* 外层光环 */}
                      <div className="absolute inset-0 -m-8">
                        <div className="w-full h-full rounded-full bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 opacity-20 animate-ping" />
                      </div>

                      {/* 旋转光环 */}
                      <div className="absolute inset-0 -m-6 animate-spin-slow">
                        <div className="w-full h-full rounded-full border-4 border-transparent border-t-blue-500 border-r-indigo-500" />
                      </div>

                      {/* 文档图标 */}
                      <div className="relative bg-white rounded-3xl shadow-2xl p-12 border border-slate-200">
                        {/* 主文档图标 */}
                        <div className="relative">
                          <FileText
                            className="w-24 h-24 text-blue-600"
                            strokeWidth={1.5}
                          />

                          {/* 刷新图标 - 在文档中央旋转 */}
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full p-3 animate-spin-slow shadow-lg">
                              <Sparkles className="w-8 h-8 text-white" />
                            </div>
                          </div>
                        </div>

                        {/* 装饰性光点 */}
                        <div className="absolute top-4 right-4 w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                        <div
                          className="absolute bottom-4 left-4 w-2 h-2 bg-indigo-400 rounded-full animate-pulse"
                          style={{ animationDelay: "0.5s" }}
                        />
                        <div
                          className="absolute top-1/2 right-2 w-1.5 h-1.5 bg-purple-400 rounded-full animate-pulse"
                          style={{ animationDelay: "0.3s" }}
                        />
                      </div>
                    </div>

                    {/* 状态文字 */}
                    <div className="space-y-3">
                      <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                        正在生成智能报告
                      </h3>
                      <p className="text-slate-500">
                        依赖的工程数据已就绪，报告内容生成中...
                      </p>

                      {/* 进度指示点 */}
                      <div className="flex items-center justify-center gap-2 pt-4">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                        <div
                          className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        />
                        <div
                          className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        />
                      </div>
                    </div>

                    {/* 章节统计 - 简化版 */}
                    <div className="mt-12 inline-flex items-center gap-6 px-8 py-4 bg-slate-50 rounded-full border border-slate-200">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full" />
                        <span className="text-sm text-slate-600">
                          <span className="font-semibold text-slate-800">
                            {nodes.length}
                          </span>{" "}
                          个章节
                        </span>
                      </div>
                      <div className="w-px h-4 bg-slate-300" />
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-sm text-slate-600">
                          生成中
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 弹窗底部操作栏 */}
              <div className="border-t border-slate-200 p-6 bg-slate-50">
                <div className="flex items-center justify-between max-w-4xl mx-auto">
                  <div className="text-sm text-slate-600">
                    {nodes.filter(
                      (n) => n.data.llmModel && n.data.prompt,
                    ).length === nodes.length &&
                    nodes.length > 0 ? (
                      <span className="text-green-600 font-medium">
                        ✓ 所有章节配置完成，可以生成报告
                      </span>
                    ) : (
                      <span className="text-amber-600">
                        部分章节未配置完成，建议完善后再生成
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => setShowGenerateModal(false)}
                    className="px-6 py-2.5 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    取消
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Report Node Editor Panel */}
      {selectedNode && (
        <ReportNodeEditor
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onUpdate={(updatedNode) => {
            setNodes((nds) =>
              nds.map((n) =>
                n.id === updatedNode.id ? updatedNode : n,
              ),
            );
          }}
        />
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