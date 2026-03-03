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
  projectId: string;
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
}

// 获取项目存储的 key
const getStorageKey = (projectId: string, type: string) => `project_${projectId}_${type}`;

// 从 localStorage 加载数据
const loadFromStorage = <T,>(key: string, defaultValue: T): T => {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to load from storage:', e);
  }
  return defaultValue;
};

// 保存数据到 localStorage
const saveToStorage = (key: string, data: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error('Failed to save to storage:', e);
  }
};

// 序列化文件数据（移除不能序列化的字段）
const serializeFileData = (files: Record<string, any[]>): Record<string, any[]> => {
  const serialized: Record<string, any[]> = {};
  Object.keys(files).forEach(nodeId => {
    serialized[nodeId] = files[nodeId].map(file => {
      // 移除 File 对象和 blob URL，只保留可序列化的元数据
      const { file: _file, url: _url, ...rest } = file;
      return rest;
    });
  });
  return serialized;
};

export default function DataCollectionEditor({ 
  projectId,
  initialNodes, 
  initialEdges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp 
}: DataCollectionEditorProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  
  // 从 localStorage 加载文件上传和分析状态
  const [uploadedFiles, setUploadedFiles] = useState<Record<string, any[]>>(() => {
    return loadFromStorage(getStorageKey(projectId, 'collectionUploadedFiles'), {});
  });
  const [analysisResults, setAnalysisResults] = useState<Record<string, any>>(() => {
    return loadFromStorage(getStorageKey(projectId, 'collectionAnalysisResults'), {});
  });

  // 当项目切换时，重新加载状态
  useEffect(() => {
    const savedFiles = loadFromStorage(getStorageKey(projectId, 'collectionUploadedFiles'), {});
    const savedResults = loadFromStorage(getStorageKey(projectId, 'collectionAnalysisResults'), {});
    
    setUploadedFiles(savedFiles);
    setAnalysisResults(savedResults);
    isInitialMountRef.current = true; // 重置初始挂载标志
  }, [projectId]);

  // 使用 ref 来跟踪是否是内部更新，避免循环同步
  const isInternalUpdateRef = useRef(false);
  const initialNodesRef = useRef(initialNodes);
  const initialEdgesRef = useRef(initialEdges);
  const isInitialMountRef = useRef(true);

  // 自动保存文件上传状态到 localStorage（带防抖）
  useEffect(() => {
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      return;
    }
    const timer = setTimeout(() => {
      const serialized = serializeFileData(uploadedFiles);
      saveToStorage(getStorageKey(projectId, 'collectionUploadedFiles'), serialized);
    }, 500);
    return () => clearTimeout(timer);
  }, [uploadedFiles, projectId]);

  // 自动保存分析结果到 localStorage（带防抖）
  useEffect(() => {
    if (isInitialMountRef.current) {
      return;
    }
    const timer = setTimeout(() => {
      saveToStorage(getStorageKey(projectId, 'collectionAnalysisResults'), analysisResults);
    }, 500);
    return () => clearTimeout(timer);
  }, [analysisResults, projectId]);

  // 自动保存模板选择到 localStorage（带防抖）

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
  const handleFileUpload = useCallback(async (nodeId: string, nodeLabel: string, customPrompt?: string) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = 'image/*,.pdf';
    
    input.onchange = async (e: any) => {
      const files = Array.from(e.target.files || []) as File[];
      const maxFileSize = 50 * 1024 * 1024;
      const oversizedFiles = files.filter((file) => file.size > maxFileSize);
      if (oversizedFiles.length > 0) {
        alert(`以下文件超过50MB限制：${oversizedFiles.map((file) => file.name).join(', ')}`);
        return;
      }
      
      const localFiles = files.map((file: File) => ({
        id: `${nodeId}-file-${Date.now()}-${Math.random()}`,
        name: file.name,
        type: file.type,
        size: file.size,
        url: URL.createObjectURL(file),
        uploadDate: new Date().toLocaleString('zh-CN'),
        file,
        status: 'pending',
      }));
      
      if (localFiles.length > 0) {
        setUploadedFiles(prev => ({
          ...prev,
          [nodeId]: [...(prev[nodeId] || []), ...localFiles]
        }));
      }
    };
    
    input.click();
  }, [projectId]);

  // 处理数据分析（点击后才上传并解析）

  const handleDataAnalysis = useCallback(async (
    nodeId: string,
    nodeData: any,
    options?: { prompt?: string; skillName?: string; targetFileId?: string }
  ) => {
    const files = uploadedFiles[nodeId] || [];

    if (files.length === 0) {
      return;
    }

    const skillName = options?.skillName;
    if (!skillName) {
      alert('Select a skill first.');
      return;
    }

    const targetFiles = options?.targetFileId
      ? files.filter((fileItem: any) => fileItem.id === options.targetFileId)
      : files;

    const uploadResults = await Promise.all(targetFiles.map(async (fileItem: any) => {
      if (!fileItem.file) {
        return { id: fileItem.id, skipped: true };
      }

      const formData = new FormData();
      formData.append('file', fileItem.file);
      formData.append('format', 'json');
      formData.append('project_id', projectId);
      formData.append('node_id', nodeId);
      // 仅在用户点击“确认无误”后入库，解析阶段不自动入库
      formData.append('persist_result', 'false');

      try {
        const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '';
        const url = `${apiBase.replace(/\/$/, '')}/api/skill/${encodeURIComponent(skillName)}/run`;
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          let errorMessage = `Skill failed: ${response.statusText}`;
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
          } catch (e) {
            const text = await response.text().catch(() => '');
            if (text) {
              errorMessage = `Skill failed: ${text.substring(0, 100)}`;
            }
          }
          throw new Error(errorMessage);
        }

        const result = await response.json();
        return { id: fileItem.id, result };
      } catch (error: any) {
        console.error('Skill execution failed:', error);
        const errorMessage = error?.message || error?.toString() || 'Skill execution failed';
        return { id: fileItem.id, error: errorMessage };
      }
    }));

    const resultMap = new Map(uploadResults.map((item: any) => [item.id, item]));

    const nextFiles = files.map((item: any) => {
      const uploadResult = resultMap.get(item.id);
      if (!uploadResult || uploadResult.skipped) {
        return item;
      }
      if (uploadResult.error) {
        return { ...item, status: 'failed', error: uploadResult.error };
      }

      const result = uploadResult.result || {};
      const records = Array.isArray(result.records) ? result.records : [];
      const success = !!result.success;

      return {
        ...item,
        status: success ? 'uploaded' : 'failed',
        error: success ? undefined : (result.error || 'Skill execution failed'),
        skill_result: result,
        commit_results: records,
        // 解析完成后默认不自动确认，必须由用户手动点击“已确认无误”
        confirmed: false,
        skill_name: skillName,
        source_hash: result.source_hash || item.source_hash,
      };
    });

    setUploadedFiles((prev) => ({
      ...prev,
      [nodeId]: nextFiles,
    }));

    const structuredData = nextFiles
      .map((item: any) => {
        const data = item.skill_result?.data;
        return {
          fileId: item.id,
          fileName: item.name || 'Unnamed file',
          data: Array.isArray(data) ? data : (data ? [data] : []),
        };
      })
      .filter((item: any) => item.data !== undefined && item.data !== null);

    const analysisResult = {
      nodeId,
      nodeLabel: nodeData.label,
      analyzedAt: new Date().toLocaleString('zh-CN'),
      jsonData: structuredData,
      validation: null,
    };

    setAnalysisResults((prev) => ({
      ...prev,
      [nodeId]: analysisResult,
    }));
  }, [uploadedFiles, projectId]);

  const handleUpdateAnalysisResult = useCallback((nodeId: string, fileId: string, data: any[]) => {
    setAnalysisResults((prev) => {
      const current = prev[nodeId];
      if (!current || !Array.isArray(current.jsonData)) {
        return prev;
      }
      const nextJsonData = current.jsonData.map((item: any) =>
        item.fileId === fileId ? { ...item, data } : item
      );
      return {
        ...prev,
        [nodeId]: {
          ...current,
          jsonData: nextJsonData,
        },
      };
    });
  }, []);

  const handleRemoveFile = useCallback((nodeId: string, fileId: string) => {
    setUploadedFiles(prev => {
      const nextFiles = (prev[nodeId] || []).filter((file: any) => {
        if (file.id === fileId && file.url?.startsWith('blob:')) {
          URL.revokeObjectURL(file.url);
        }
        return file.id !== fileId;
      });
      return {
        ...prev,
        [nodeId]: nextFiles
      };
    });
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
        case 'delegate-info':
          return [
            { name: 'project_name', label: '项目名称', type: 'text', required: true },
            { name: 'delegate_unit', label: '委托单位', type: 'text', required: true },
            { name: 'contact_person', label: '联系人', type: 'text', required: true },
            { name: 'phone', label: '联系电话', type: 'text', required: true },
            { name: 'address', label: '工程地址', type: 'text', required: true },
            { name: 'purpose', label: '检测目的', type: 'text', required: true },
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
        case 'site-inspection':
          return [
            { name: 'inspection_location', label: '检查位置', type: 'text', required: true },
            { name: 'inspection_date', label: '检查日期', type: 'date', required: true },
            { name: 'inspector', label: '检查人员', type: 'text', required: true },
            { name: 'site_condition', label: '现场情况描述', type: 'text', required: true },
            { name: 'issues_found', label: '发现的问题', type: 'text', required: false },
            { name: 'weather', label: '天气情况', type: 'text', required: false },
          ];
        case 'multi-doc-upload':
          return [
            { name: 'batch_name', label: '批次名称', type: 'text', required: true },
            { name: 'upload_time', label: '上传时间', type: 'date', required: true },
            { name: 'doc_count', label: '文档数量', type: 'number', required: false },
            { name: 'status', label: '处理状态', type: 'text', required: false },
            { name: 'notes', label: '备注信息', type: 'text', required: false },
          ];
        case 'software-calculation':
          return [
            { name: 'mortar_strength_mpa', label: '砌筑砂浆抗压强度取值(MPa)', type: 'number', required: false },
            { name: 'brick_strength_grade', label: '砌墙砖抗压强度等级', type: 'text', required: false },
            { name: 'live_loads', label: '活载', type: 'text', required: false },
            { name: 'dead_loads', label: '恒载(含自重)', type: 'text', required: false },
            { name: 'load_combination_type', label: '荷载基本组合类型', type: 'text', required: false },
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
        'site-inspection': '现场情况检查',
        'delegate-info': '委托方资料',
        'multi-doc-upload': '多文档智能上传',
        'software-calculation': '软件计算结果',
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
          projectId={projectId} 
          node={selectedNode} 
          onClose={() => setSelectedNode(null)}
          uploadedFiles={uploadedFiles[selectedNode.id] || []}
          analysisResult={analysisResults[selectedNode.id] || null}
          onUpload={handleFileUpload}
          onAnalyze={handleDataAnalysis}
          onRemoveFile={(fileId) => handleRemoveFile(selectedNode.id, fileId)}
          onUpdateAnalysisResult={(fileId, data) => handleUpdateAnalysisResult(selectedNode.id, fileId, data)}
        />
      )}
    </div>
  );
}
