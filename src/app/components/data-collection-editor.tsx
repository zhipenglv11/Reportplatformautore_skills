import { useCallback, useState, useEffect, useRef } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Database } from 'lucide-react';
import CollectionNode from './nodes/collection-node';
import NodeSidebar from './node-sidebar';
import CollectionDetailModal from './collection-detail-modal';

const nodeTypes: NodeTypes = {
  collection: CollectionNode,
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

interface DataCollectionEditorProps {
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
}

export default function DataCollectionEditor({ 
  initialNodes, 
  initialEdges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp 
}: DataCollectionEditorProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  
  // 文件上传和分析状态
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, any[]>>({});
  const [analysisResults, setAnalysisResults] = useState<Record<string, any>>({});

  // 使用 ref 来跟踪是否是内部更新，避免循环同步
  const isInternalUpdateRef = useRef(false);
  const initialNodesRef = useRef(initialNodes);
  const initialEdgesRef = useRef(initialEdges);

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
    
    // 使用 requestAnimationFrame 确保在下一帧更新，避免阻塞渲染
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

  const onNodeDoubleClick = useCallback((_: React.MouseEvent, node: any) => {
    setSelectedNode(node);
  }, []);

  // 处理文件上传
  const handleFileUpload = useCallback((nodeId: string, nodeLabel: string) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'image/*,.pdf,.doc,.docx,.xls,.xlsx';
    
    input.onchange = (e: any) => {
      const files = Array.from(e.target.files || []) as File[];
      const newFiles = files.map((file: File) => ({
        id: `${nodeId}-file-${Date.now()}-${Math.random()}`,
        name: file.name,
        type: file.type,
        size: file.size,
        url: URL.createObjectURL(file),
        uploadDate: new Date().toLocaleString('zh-CN'),
      }));
      
      setUploadedFiles(prev => ({
        ...prev,
        [nodeId]: [...(prev[nodeId] || []), ...newFiles]
      }));
    };
    
    input.click();
  }, []);

  // 处理数据分析
  const handleDataAnalysis = useCallback((nodeId: string, nodeData: any) => {
    const files = uploadedFiles[nodeId] || [];
    
    if (files.length === 0) {
      return;
    }

    // 模拟数据分析过程
    const mockAnalysisResult = {
      nodeId,
      nodeLabel: nodeData.label,
      analyzedAt: new Date().toLocaleString('zh-CN'),
      totalFields: nodeData.fields?.length || 0,
      successCount: Math.floor((nodeData.fields?.length || 0) * 0.85),
      data: (nodeData.fields || []).map((field: any) => ({
        fieldName: field.name,
        fieldLabel: field.label,
        extractedValue: field.type === 'number' 
          ? (Math.random() * 100).toFixed(2)
          : field.type === 'date'
          ? new Date().toISOString().split('T')[0]
          : `示例${field.label}`,
        unit: field.label.includes('强度') ? 'MPa' : 
              field.label.includes('直径') ? 'mm' : 
              field.label.includes('角度') ? '°' : 
              field.label.includes('高度') ? 'm' : undefined,
        confidence: Math.floor(Math.random() * 20) + 80,
        status: Math.random() > 0.15 ? 'success' : 'warning',
      })),
      summary: {
        avgConfidence: Math.floor(Math.random() * 10) + 85,
        recommendations: [
          '数据质量良好，建议确认后保存',
          '部分字段置信度较低，请人工核对',
        ],
      },
    };
    
    setAnalysisResults(prev => ({
      ...prev,
      [nodeId]: mockAnalysisResult
    }));
  }, [uploadedFiles]);

  const handleRemoveFile = useCallback((nodeId: string, fileId: string) => {
    setUploadedFiles(prev => ({
      ...prev,
      [nodeId]: (prev[nodeId] || []).filter(f => f.id !== fileId)
    }));
  }, []);

  const addNode = useCallback((type: string) => {
    // 为不同数据类型定义预设字段
    const getDefaultFields = (dataType: string) => {
      switch (dataType) {
        case 'mortar-strength':
          return [
            { name: 'test_location', label: '测试位置', type: 'text', required: true },
            { name: 'strength_value', label: '强度值(MPa)', type: 'number', required: true },
            { name: 'test_date', label: '测试日期', type: 'date', required: true },
            { name: 'tester', label: '检测人员', type: 'text', required: true },
          ];
        case 'concrete-strength':
          return [
            { name: 'specimen_number', label: '试块编号', type: 'text', required: true },
            { name: 'compressive_strength', label: '抗压强度(MPa)', type: 'number', required: true },
            { name: 'curing_days', label: '养护天数', type: 'number', required: true },
            { name: 'test_date', label: '测试日期', type: 'date', required: true },
          ];
        case 'rebar-diameter':
          return [
            { name: 'location', label: '位置', type: 'text', required: true },
            { name: 'diameter', label: '直径(mm)', type: 'number', required: true },
            { name: 'specification', label: '规格型号', type: 'text', required: true },
            { name: 'quantity', label: '数量', type: 'number', required: true },
          ];
        case 'brick-strength':
          return [
            { name: 'batch_number', label: '批次号', type: 'text', required: true },
            { name: 'strength_grade', label: '强度等级', type: 'text', required: true },
            { name: 'compressive_strength', label: '抗压强度(MPa)', type: 'number', required: true },
            { name: 'sample_count', label: '样本数量', type: 'number', required: true },
          ];
        case 'inclination':
          return [
            { name: 'measurement_point', label: '测量点', type: 'text', required: true },
            { name: 'inclination_angle', label: '倾斜角度(°)', type: 'number', required: true },
            { name: 'direction', label: '倾斜方向', type: 'text', required: true },
            { name: 'height', label: '测量高度(m)', type: 'number', required: true },
          ];
        case 'material-test':
          return [
            { name: 'material_name', label: '材料名称', type: 'text', required: true },
            { name: 'test_item', label: '检测项目', type: 'text', required: true },
            { name: 'test_result', label: '检测结果', type: 'text', required: true },
            { name: 'standard', label: '检测标准', type: 'text', required: false },
          ];
        default:
          return [];
      }
    };

    const getDefaultLabel = (dataType: string) => {
      const labels: Record<string, string> = {
        'mortar-strength': '砂浆强度',
        'concrete-strength': '混凝土强度',
        'rebar-diameter': '钢筋直径',
        'brick-strength': '砖强度',
        'inclination': '倾斜测量',
        'material-test': '材料检测',
      };
      return labels[dataType] || '数据节点';
    };

    const newNode = {
      id: `collection-${Date.now()}`,
      type: 'collection',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
      data: { 
        label: getDefaultLabel(type),
        type,
        fields: getDefaultFields(type)
      },
    };
    
    // 标记为内部更新，避免触发循环同步
    isInternalUpdateRef.current = true;
    setNodes((nds) => [...nds, newNode]);
  }, [setNodes]);

  return (
    <div className="flex h-full bg-slate-50">
      {/* Sidebar */}
      <NodeSidebar onAddNode={addNode} mode="collection" nodes={nodes} />

      {/* Flow Editor */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={[]}
          onNodesChange={onNodesChange}
          onNodeDoubleClick={onNodeDoubleClick}
          nodeTypes={nodeTypes}
          className="bg-slate-50"
          nodesDraggable={true}
          nodesConnectable={false}
          elementsSelectable={true}
          panOnDrag={[1, 2]}
          zoomOnScroll={true}
          selectionOnDrag
          selectionMode="partial"
          multiSelectionKeyCode="Shift"
        >
          <Background color="#e2e8f0" gap={16} />
          <Controls className="bg-white border border-slate-200 rounded-lg shadow-sm" />
          <MiniMap 
            className="bg-white border border-slate-200 rounded-lg shadow-sm"
            nodeColor="#3b82f6"
            maskColor="rgba(241, 245, 249, 0.8)"
            pannable
            zoomable
          />
          <FitView />
        </ReactFlow>

        {/* 空白画布提示 */}
        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center">
              <Database className="w-16 h-16 text-slate-200 mx-auto mb-4" />
              <p className="text-slate-400 text-sm">请从左侧选择一个数据类型以创建节点</p>
            </div>
          </div>
        )}
      </div>

      {/* Collection Detail Panel */}
      {selectedNode && (
        <CollectionDetailModal 
          node={selectedNode} 
          onClose={() => setSelectedNode(null)}
          uploadedFiles={uploadedFiles[selectedNode.id] || []}
          analysisResult={analysisResults[selectedNode.id] || null}
          onUpload={handleFileUpload}
          onAnalyze={handleDataAnalysis}
          onRemoveFile={(fileId) => handleRemoveFile(selectedNode.id, fileId)}
        />
      )}
    </div>
  );
}