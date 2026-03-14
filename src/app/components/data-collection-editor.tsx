import { useCallback, useEffect, useMemo, useState } from 'react';
import { Edge, Node } from 'reactflow';
import { Database } from 'lucide-react';
import CollectionDetailModal from './collection-detail-modal';

interface DataCollectionEditorProps {
  projectId: string;
  initialNodes: Node[];
  initialEdges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
}

interface TemplateField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'file';
  required: boolean;
}

interface NodeTemplate {
  type: string;
  label: string;
  description: string;
  fields: TemplateField[];
}

interface NodeTemplateCategory {
  title: string;
  nodes: NodeTemplate[];
}

const getStorageKey = (projectId: string, type: string) => `project_${projectId}_${type}`;

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

const saveToStorage = (key: string, data: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error('Failed to save to storage:', e);
  }
};

const serializeFileData = (files: Record<string, any[]>): Record<string, any[]> => {
  const serialized: Record<string, any[]> = {};
  Object.keys(files).forEach((nodeId) => {
    serialized[nodeId] = files[nodeId].map((file) => {
      const { file: _file, ...rest } = file;
      return rest;
    });
  });
  return serialized;
};

const FALLBACK_TEMPLATE_CATEGORIES: NodeTemplateCategory[] = [
  {
    title: '智能采集',
    nodes: [
      {
        type: 'multi-doc-upload',
        label: '多文档智能上传',
        description: '批量上传 PDF/图片并执行智能解析。',
        fields: [
          { name: 'batch_name', label: '批次名称', type: 'text', required: true },
          { name: 'upload_time', label: '上传时间', type: 'date', required: true },
        ],
      },
    ],
  },
  {
    title: '检测前信息',
    nodes: [
      {
        type: 'delegate-info',
        label: '委托方资料',
        description: '记录委托单位与项目基础信息。',
        fields: [
          { name: 'project_name', label: '项目名称', type: 'text', required: true },
          { name: 'delegate_unit', label: '委托单位', type: 'text', required: true },
          { name: 'contact_person', label: '联系人', type: 'text', required: true },
        ],
      },
    ],
  },
  {
    title: '检测中数据',
    nodes: [
      {
        type: 'mortar-strength',
        label: '砂浆强度',
        description: '砂浆强度检测数据。',
        fields: [
          { name: 'test_location', label: '测试位置', type: 'text', required: true },
          { name: 'strength_value', label: '强度值(MPa)', type: 'number', required: true },
        ],
      },
      {
        type: 'concrete-strength',
        label: '混凝土强度',
        description: '混凝土抗压强度检测数据。',
        fields: [
          { name: 'specimen_number', label: '试块编号', type: 'text', required: true },
          { name: 'compressive_strength', label: '抗压强度(MPa)', type: 'number', required: true },
        ],
      },
      {
        type: 'brick-strength',
        label: '砖强度',
        description: '砖块强度检测数据。',
        fields: [
          { name: 'strength_grade', label: '强度等级', type: 'text', required: true },
          { name: 'compressive_strength', label: '抗压强度(MPa)', type: 'number', required: true },
        ],
      },
      {
        type: 'rebar-diameter',
        label: '钢筋直径',
        description: '钢筋直径测量数据。',
        fields: [
          { name: 'location', label: '位置', type: 'text', required: true },
          { name: 'diameter', label: '直径(mm)', type: 'number', required: true },
        ],
      },
      {
        type: 'inclination',
        label: '倾斜测量',
        description: '建筑倾斜度测量数据。',
        fields: [
          { name: 'measurement_point', label: '测量点', type: 'text', required: true },
          { name: 'inclination_angle', label: '倾斜角度', type: 'number', required: true },
        ],
      },
      {
        type: 'material-test',
        label: '材料检测',
        description: '通用材料检测数据。',
        fields: [
          { name: 'material_name', label: '材料名称', type: 'text', required: true },
          { name: 'test_result', label: '检测结果', type: 'text', required: true },
        ],
      },
      {
        type: 'site-inspection',
        label: '现场情况检查',
        description: '现场检查记录。',
        fields: [
          { name: 'inspection_location', label: '检查位置', type: 'text', required: true },
          { name: 'site_condition', label: '现场情况', type: 'text', required: true },
        ],
      },
    ],
  },
  {
    title: '检测后数据',
    nodes: [
      {
        type: 'software-calculation',
        label: '软件计算结果',
        description: '结构计算软件结果。',
        fields: [
          { name: 'mortar_strength_mpa', label: '砂浆强度取值', type: 'number', required: false },
          { name: 'brick_strength_grade', label: '砖强度等级', type: 'text', required: false },
        ],
      },
    ],
  },
];

const normalizeTemplateCategories = (input: any): NodeTemplateCategory[] | null => {
  if (!Array.isArray(input)) return null;
  const categories: NodeTemplateCategory[] = input
    .filter((category) => category && typeof category.title === 'string' && Array.isArray(category.nodes))
    .map((category) => ({
      title: category.title,
      nodes: category.nodes
        .filter((node: any) => node && typeof node.type === 'string' && typeof node.label === 'string')
        .map((node: any) => ({
          type: node.type,
          label: node.label,
          description: typeof node.description === 'string' ? node.description : '',
          fields: Array.isArray(node.fields)
            ? node.fields
                .filter((field: any) => field && typeof field.name === 'string')
                .map((field: any) => ({
                  name: field.name,
                  label: typeof field.label === 'string' ? field.label : field.name,
                  type: field.type === 'number' || field.type === 'date' || field.type === 'file' ? field.type : 'text',
                  required: !!field.required,
                }))
            : [],
        })),
    }))
    .filter((category) => category.nodes.length > 0);

  return categories.length > 0 ? categories : null;
};

const flattenTemplates = (categories: NodeTemplateCategory[]): NodeTemplate[] => categories.flatMap((category) => category.nodes);

const buildNormalizedNodes = (sourceNodes: Node[], templates: NodeTemplate[]): Node[] => {
  const byType = new Map<string, Node>();
  sourceNodes.forEach((node) => {
    const type = String(node.data?.type || '');
    if (type && !byType.has(type)) {
      byType.set(type, node);
    }
  });

  return templates.map((template) => {
    const existing = byType.get(template.type);
    if (existing) {
      return {
        ...existing,
        type: 'collection',
        position: { x: 0, y: 0 },
        data: {
          ...existing.data,
          label: template.label,
          type: template.type,
          fields: template.fields,
        },
      } as Node;
    }

    return {
      id: `collection-${template.type}`,
      type: 'collection',
      position: { x: 0, y: 0 },
      data: {
        label: template.label,
        type: template.type,
        fields: template.fields,
      },
    } as Node;
  });
};

export default function DataCollectionEditor({
  projectId,
  initialNodes,
  initialEdges,
  onNodesChange: onNodesChangeProp,
  onEdgesChange: onEdgesChangeProp,
}: DataCollectionEditorProps) {
  const [templateCategories, setTemplateCategories] = useState<NodeTemplateCategory[]>(FALLBACK_TEMPLATE_CATEGORIES);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const [uploadedFiles, setUploadedFiles] = useState<Record<string, any[]>>(() =>
    loadFromStorage(getStorageKey(projectId, 'collectionUploadedFiles'), {})
  );
  const [analysisResults, setAnalysisResults] = useState<Record<string, any>>(() =>
    loadFromStorage(getStorageKey(projectId, 'collectionAnalysisResults'), {})
  );

  const templateList = useMemo(() => flattenTemplates(templateCategories), [templateCategories]);
  const normalizedNodes = useMemo(() => buildNormalizedNodes(initialNodes || [], templateList), [initialNodes, templateList]);

  const selectedNode = useMemo(() => {
    const uploadNode = normalizedNodes.find((node) => String(node.data?.type) === 'multi-doc-upload');
    if (uploadNode) return uploadNode;
    return normalizedNodes.find((node) => node.id === selectedNodeId) || normalizedNodes[0] || null;
  }, [normalizedNodes, selectedNodeId]);

  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const response = await fetch('/api/collection/node-templates');
        if (!response.ok) return;
        const payload = await response.json();
        const normalized = normalizeTemplateCategories(payload?.categories);
        if (normalized) {
          setTemplateCategories(normalized);
        }
      } catch {
        // keep fallback templates
      }
    };
    loadTemplates();
  }, []);

  useEffect(() => {
    if (normalizedNodes.length === 0) {
      setSelectedNodeId(null);
      return;
    }
    const uploadNode = normalizedNodes.find((node) => String(node.data?.type) === 'multi-doc-upload');
    if (uploadNode) {
      if (selectedNodeId !== uploadNode.id) {
        setSelectedNodeId(uploadNode.id);
      }
      return;
    }
    if (!selectedNodeId || !normalizedNodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(normalizedNodes[0].id);
    }
  }, [normalizedNodes, selectedNodeId]);

  useEffect(() => {
    const source = JSON.stringify(initialNodes || []);
    const normalized = JSON.stringify(normalizedNodes);
    if (source !== normalized) {
      onNodesChangeProp(normalizedNodes);
    }
  }, [initialNodes, normalizedNodes, onNodesChangeProp]);

  useEffect(() => {
    if ((initialEdges || []).length > 0) {
      onEdgesChangeProp([]);
    }
  }, [initialEdges, onEdgesChangeProp]);

  useEffect(() => {
    const savedFiles = loadFromStorage(getStorageKey(projectId, 'collectionUploadedFiles'), {});
    const savedResults = loadFromStorage(getStorageKey(projectId, 'collectionAnalysisResults'), {});
    setUploadedFiles(savedFiles);
    setAnalysisResults(savedResults);
  }, [projectId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const serialized = serializeFileData(uploadedFiles);
      saveToStorage(getStorageKey(projectId, 'collectionUploadedFiles'), serialized);
    }, 500);
    return () => clearTimeout(timer);
  }, [uploadedFiles, projectId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      saveToStorage(getStorageKey(projectId, 'collectionAnalysisResults'), analysisResults);
    }, 500);
    return () => clearTimeout(timer);
  }, [analysisResults, projectId]);

  const handleDataAnalysis = useCallback(
    async (
      nodeId: string,
      nodeData: any,
      options?: { prompt?: string; skillName?: string; targetFileId?: string; targetFiles?: any[] }
    ) => {
      const existingFiles = uploadedFiles[nodeId] || [];
      const processingFiles = options?.targetFiles || existingFiles;
      if (processingFiles.length === 0) {
        return;
      }

      const skillName = options?.skillName;

      const targetFiles = options?.targetFileId
        ? processingFiles.filter((fileItem: any) => fileItem.id === options.targetFileId)
        : processingFiles;

      const uploadResults = await Promise.all(
        targetFiles.map(async (fileItem: any) => {
          if (!fileItem.file) {
            return { id: fileItem.id, skipped: true };
          }

          try {
            let response: Response;
            if (skillName) {
              const formData = new FormData();
              formData.append('file', fileItem.file);
              formData.append('format', 'json');
              formData.append('project_id', projectId);
              formData.append('node_id', nodeId);
              formData.append('persist_result', 'false');

              response = await fetch(`/api/skill/${encodeURIComponent(skillName)}/run`, {
                method: 'POST',
                body: formData,
              });
            } else {
              const orchestrateData = new FormData();
              orchestrateData.append('files', fileItem.file);
              orchestrateData.append('project_id', projectId);
              orchestrateData.append('node_id', nodeId);
              orchestrateData.append('persist_result', 'false');
              orchestrateData.append('use_llm_classification', 'true');

              response = await fetch('/api/skill/orchestrate', {
                method: 'POST',
                body: orchestrateData,
              });
            }

            if (!response.ok) {
              let errorMessage = `Skill failed: ${response.statusText}`;
              try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
              } catch {
                const text = await response.text().catch(() => '');
                if (text) {
                  errorMessage = `Skill failed: ${text.substring(0, 100)}`;
                }
              }
              throw new Error(errorMessage);
            }

            const result = await response.json();
            if (!skillName) {
              const matched = Array.isArray(result?.results)
                ? result.results.find((item: any) => item?.file_name === fileItem.name)
                : null;
              if (!matched) {
                return { id: fileItem.id, error: '未匹配到自动识别结果' };
              }
              return { id: fileItem.id, result: matched };
            }
            return { id: fileItem.id, result };
          } catch (error: any) {
            console.error('Skill execution failed:', error);
            const errorMessage = error?.message || error?.toString() || 'Skill execution failed';
            return { id: fileItem.id, error: errorMessage };
          }
        })
      );

      const resultMap = new Map(uploadResults.map((item: any) => [item.id, item]));

      const mergedBaseFiles = [...existingFiles];
      processingFiles.forEach((item: any) => {
        if (!mergedBaseFiles.some((existingItem: any) => existingItem.id === item.id)) {
          mergedBaseFiles.push(item);
        }
      });

      const nextFiles = mergedBaseFiles.map((item: any) => {
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
        const autoSkillName = result.classification?.skill_name;
        const autoData = Array.isArray(result.data) ? result.data : [];

        return {
          ...item,
          status: success ? 'uploaded' : 'failed',
          error: success ? undefined : result.error || 'Skill execution failed',
          skill_result: result,
          commit_results: records,
          confirmed: false,
          skill_name: skillName || autoSkillName,
          file_type: result.classification?.file_type,
          source_hash: result.source_hash || item.source_hash,
          parse_result: autoData,
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
            data: Array.isArray(data)
              ? data
              : Array.isArray(item.parse_result)
                ? item.parse_result
                : data
                  ? [data]
                  : [],
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
    },
    [uploadedFiles, projectId]
  );

  const handleFileUpload = useCallback(async (nodeId: string, nodeLabel: string, _customPrompt?: string) => {
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
        setUploadedFiles((prev) => ({
          ...prev,
          [nodeId]: [...(prev[nodeId] || []), ...localFiles],
        }));

        await handleDataAnalysis(nodeId, { label: nodeLabel }, { targetFiles: localFiles });
      }
    };

    input.click();
  }, [handleDataAnalysis]);

  const handleUpdateAnalysisResult = useCallback((nodeId: string, fileId: string, data: any[]) => {
    setAnalysisResults((prev) => {
      const current = prev[nodeId];
      if (!current || !Array.isArray(current.jsonData)) {
        return prev;
      }
      const nextJsonData = current.jsonData.map((item: any) => (item.fileId === fileId ? { ...item, data } : item));
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
    setUploadedFiles((prev) => {
      const nextFiles = (prev[nodeId] || []).filter((file: any) => {
        if (file.id === fileId && file.url?.startsWith('blob:')) {
          URL.revokeObjectURL(file.url);
        }
        return file.id !== fileId;
      });
      return {
        ...prev,
        [nodeId]: nextFiles,
      };
    });
  }, []);

  return (
    <div className="h-full bg-slate-50 overflow-hidden">
      {selectedNode ? (
        <CollectionDetailModal
          embedded
          projectId={projectId}
          node={selectedNode}
          onClose={() => setSelectedNodeId(null)}
          uploadedFiles={uploadedFiles[selectedNode.id] || []}
          analysisResult={analysisResults[selectedNode.id] || null}
          onUpload={handleFileUpload}
          onAnalyze={handleDataAnalysis}
          onRemoveFile={(fileId) => handleRemoveFile(selectedNode.id, fileId)}
          onUpdateAnalysisResult={(fileId, data) => handleUpdateAnalysisResult(selectedNode.id, fileId, data)}
        />
      ) : (
        <div className="h-full flex items-center justify-center text-slate-400">
          <div className="text-center">
            <Database className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm">未找到可用的上传节点</p>
          </div>
        </div>
      )}
    </div>
  );
}
