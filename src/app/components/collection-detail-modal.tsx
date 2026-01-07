import React, { useState, useRef, useEffect } from 'react';
import { X, Upload, Image as ImageIcon, FileText, Download, BarChart3, CheckCircle, AlertCircle, Loader2, Move, Settings, Database, Trash2, MessageSquare, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  uploadDate: string;
  file?: File;
  status?: 'pending' | 'uploaded' | 'failed';
  error?: string;
  object_key?: string;
  source_hash?: string;
  file_type?: string;
  parse_result?: any;
  validation_result?: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    policy?: any;
  };
  mapping_payload?: any;
  run_id?: string;
  record_id?: string;
  confirmed?: boolean;
  preview_chunks?: any[];
  commit_results?: any[];
}

interface AnalysisData {
  fieldName: string;
  fieldLabel: string;
  extractedValue: string | number;
  unit?: string;
  confidence: number;
  status: 'success' | 'warning' | 'error';
}

interface CollectionDetailModalProps {
  node: any;
  onClose: () => void;
  uploadedFiles: FileItem[];
  analysisResult: {
    nodeId: string;
    nodeLabel: string;
    analyzedAt: string;
    jsonData: any; // 原始JSON数据
  } | null;
  onUpload: (nodeId: string, nodeLabel: string, prompt?: string) => void;
  onAnalyze: (nodeId: string, nodeData: any, prompt?: string, templateMap?: Record<string, string>) => Promise<void>;
  onConfirm: (nodeId: string, file: FileItem) => Promise<void>;
  onRetryChunks?: (nodeId: string, file: FileItem, chunkIds: string[]) => Promise<void>;
  onRemoveFile: (fileId: string) => void;
  templateSelections?: Record<string, Record<string, string>>;
  onTemplateSelectionChange?: (fileId: string, chunkId: string, templateId: string) => void;
}

export default function CollectionDetailModal({
  node,
  onClose,
  uploadedFiles,
  analysisResult,
  onUpload,
  onAnalyze,
  onConfirm,
  onRetryChunks,
  onRemoveFile,
  templateSelections = {},
  onTemplateSelectionChange,
}: CollectionDetailModalProps) {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(uploadedFiles[0] || null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [middlePanelOffset, setMiddlePanelOffset] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [pdfZoom, setPdfZoom] = useState(1); // PDF缩放比例，默认100%

  const [fileTemplateMap, setFileTemplateMap] = useState<Record<string, string>>({});

  const templateOptions = [
    { value: 'concrete_strength_v1', label: '混凝土强度结果表', controlCode: 'KSQR-4.13-XC-10' },
    { value: 'rebound_record_v1', label: '回弹原始记录表', controlCode: 'KJQR-056-215' },
  ];

  const handleTemplateChange = (fileId: string, value: string) => {
    setFileTemplateMap((prev) => ({ ...prev, [fileId]: value }));
  };

  const getTemplateLabel = (value: string) => {
    const match = templateOptions.find((option) => option.value === value);
    return match ? match.label : '请选择识别模板';
  };

  const getTemplateCode = (value: string) => {
    const match = templateOptions.find((option) => option.value === value);
    return match ? match.controlCode : '';
  };

  // 当文件列表变化时，更新选中文件
  useEffect(() => {
    if (uploadedFiles.length === 0) {
      setSelectedFile(null);
      return;
    }

    const matched = uploadedFiles.find((file) => file.id === selectedFile?.id);
    if (!selectedFile) {
      setSelectedFile(uploadedFiles[0] || null);
      return;
    }

    if (!matched) {
      setSelectedFile(uploadedFiles[0] || null);
      return;
    }

    if (matched !== selectedFile) {
      setSelectedFile(matched);
    }
  }, [uploadedFiles, selectedFile?.id]);

  // 当切换文件时，重置PDF缩放比例
  useEffect(() => {
    setPdfZoom(1);
  }, [selectedFile?.id]);

  const MIDDLE_PANEL_WIDTH = 450; // 中间栏固定宽度
  const MIN_SIDE_MARGIN = 100; // 左右两侧最小留白距离

  // 初始化中间栏位置
  useEffect(() => {
    if (containerRef.current && middlePanelOffset === 0) {
      const containerWidth = containerRef.current.offsetWidth;
      // 居中计算: (总宽度 - 面板宽度) / 2
      const initialOffset = Math.floor((containerWidth - MIDDLE_PANEL_WIDTH) / 2);
      setMiddlePanelOffset(initialOffset);
    }
  }, []);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <ImageIcon className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const handleUploadClick = () => {
    onUpload(node.id, node.data.label, customPrompt.trim() || undefined);
  };

  const handleAnalyzeClick = async () => {
    if (uploadedFiles.length === 0) {
      alert('请先上传文件');
      return;
    }

    // 检查是否有未选择模板的文件
    const missingTemplateFiles = uploadedFiles.filter(file => !fileTemplateMap[file.id]);
    if (missingTemplateFiles.length > 0) {
      alert(`请先为以下文件选择识别模板：\n${missingTemplateFiles.map(f => f.name).join('\n')}`);
      return;
    }

    setIsAnalyzing(true);
    try {
      // 传递 fileTemplateMap 给父组件处理
      await onAnalyze(node.id, node.data, customPrompt.trim() || undefined, fileTemplateMap as any);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleConfirmClick = async () => {
    if (!selectedFile) {
      alert('请选择一个文件');
      return;
    }
    if (!selectedFile.preview_chunks || selectedFile.preview_chunks.length === 0) {
      alert('??????????????????????????????????????????');
      return;
    }
    if (selectedFile.confirmed) {
      alert('该文件已经确认过了');
      return;
    }
    setIsConfirming(true);
    try {
      await onConfirm(node.id, selectedFile);
    } finally {
      setIsConfirming(false);
    }
  };

  const handleClose = () => {
    // 检查是否有已解析但未确认的文件
    const unconfirmedFiles = uploadedFiles.filter(
      (file) => file.preview_chunks && file.preview_chunks.length > 0 && !file.confirmed
    );

    if (unconfirmedFiles.length > 0) {
      const fileNames = unconfirmedFiles
        .slice(0, 3)
        .map((file) => file.name)
        .join('、');
      const fileListText = unconfirmedFiles.length > 3
        ? `${fileNames} 等 ${unconfirmedFiles.length} 个文件`
        : fileNames;
      
      const message = `有 ${unconfirmedFiles.length} 个文件已解析但尚未确认：\n${fileListText}\n\n确定要关闭吗？未确认的文件将不会被保存到数据库。`;
      
      if (window.confirm(message)) {
        onClose();
      }
    } else {
      // 全部已确认或没有需要确认的文件，直接关闭
      onClose();
    }
  };

  const handleDeleteFile = (fileId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止触发文件选择
    onRemoveFile(fileId);
    // selectedFile 会通过 useEffect 自动更新
  };

  const getParseStatus = (status?: string) => {
    if (status === 'uploaded') return { text: '已解析', className: 'bg-emerald-100 text-emerald-700' };
    if (status === 'failed') return { text: '失败', className: 'bg-rose-100 text-rose-700' };
    return { text: '未解析', className: 'bg-slate-100 text-slate-600' };
  };

  const getChunkTemplateValue = (file: FileItem, chunk: any) => {
    const fileSelections = templateSelections[file.id] || {};
    return fileSelections[chunk.chunk_id] || chunk.suggested_template_id || '';
  };

  const selectedJsonItem = Array.isArray(analysisResult?.jsonData) && selectedFile
    ? analysisResult?.jsonData.find((item: any) => item.fileId === selectedFile.id)
    : null;
  const hasMissingSelection = !!(selectedFile?.preview_chunks || []).find(
    (chunk: any) => !getChunkTemplateValue(selectedFile as FileItem, chunk)
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-amber-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-slate-50 border-slate-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600 bg-green-100';
    if (confidence >= 70) return 'text-amber-600 bg-amber-100';
    return 'text-red-600 bg-red-100';
  };

  const handleMiddlePanelDragStart = (e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    const startX = e.clientX;
    const startOffset = middlePanelOffset;

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current || !containerRef.current) return;
      
      const containerWidth = containerRef.current.offsetWidth;
      const diff = e.clientX - startX;
      const newOffset = startOffset + diff;
      
      const minOffset = MIN_SIDE_MARGIN;
      const maxOffset = containerWidth - MIDDLE_PANEL_WIDTH - MIN_SIDE_MARGIN;
      
      setMiddlePanelOffset(Math.max(minOffset, Math.min(newOffset, maxOffset)));
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-8 bg-white rounded-xl shadow-2xl z-50 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="h-16 border-b border-slate-200 flex items-center justify-between px-6 bg-gradient-to-r from-slate-50 to-slate-100 flex-shrink-0">
          <div className="flex items-center gap-6 flex-1 mr-6">
            <div className="flex-shrink-0">
              <h2 className="font-semibold text-slate-800">{node.data.label}</h2>
              <p className="text-xs text-slate-500">数据采集与分析配置</p>
            </div>
            
            <div className="h-8 w-px bg-slate-300/50 flex-shrink-0" />
            
            <div className="w-1/2">
              <input
                type="text"
                placeholder="在此输入节点描述信息..."
                className="w-full bg-white border border-slate-300 hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg px-4 py-2 text-sm text-slate-700 placeholder:text-slate-400 shadow-sm hover:shadow transition-all outline-none"
              />
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors flex-shrink-0"
          >
            <X className="w-5 h-5 text-slate-600" />
          </button>
        </div>

        {/* Main Content - Three Panel Layout */}
        <div className="flex-1 overflow-hidden min-h-0 relative" ref={containerRef}>
          {/* Left Panel - Input Data */}
          <div 
            className="absolute top-0 left-0 bottom-0 flex flex-col bg-slate-50 border-r border-slate-200 overflow-hidden"
            style={{ 
              width: `${middlePanelOffset}px`,
            }}
          >
            <div className="p-4 border-b border-slate-200 bg-white flex-shrink-0">
              <h3 className="font-medium text-slate-700 flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-600" />
                输入数据
                <span className="text-xs text-slate-500 ml-auto">
                  {uploadedFiles.length} 个文件
                </span>
              </h3>
            </div>

            {uploadedFiles.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-6">
                <div className="w-24 h-24 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                  <ImageIcon className="w-12 h-12 text-slate-300" />
                </div>
                <p className="font-medium mb-1">暂无输入数据</p>
                <p className="text-xs text-center">
                  在中间面板上传文件
                </p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto">
                {/* File List */}
                <div className="p-3 space-y-2">
                  {uploadedFiles.map((file) => {
                    const statusBadge = getParseStatus(file.status);
                      const selectedTemplate = fileTemplateMap[file.id] || '';
                      return (
                        <div
                          key={file.id}
                          onClick={() => setSelectedFile(file)}
                          className={`p-3 rounded-lg border transition-all cursor-pointer group ${
                            selectedFile?.id === file.id
                              ? 'border-blue-300 bg-blue-50 shadow-sm'
                              : 'border-slate-200 hover:border-blue-200 hover:bg-white'
                          }`}
                        >
                          <div className="flex items-start gap-2">
                            <div className={`p-2 rounded-md flex-shrink-0 ${
                              selectedFile?.id === file.id ? 'bg-blue-100' : 'bg-slate-100'
                            }`}>
                              {getFileIcon(file.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-800 truncate">
                                {file.name}
                              </p>
                              <div className="mt-1 flex flex-wrap items-center gap-2">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${statusBadge.className}`}>
                                  {statusBadge.text}
                                </span>
                                {selectedTemplate && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                                    {getTemplateLabel(selectedTemplate)}
                                  </span>
                                )}
                                {getTemplateCode(selectedTemplate) && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                                    控制编号 {getTemplateCode(selectedTemplate)}
                                  </span>
                                )}
                                {file.confirmed && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                                    已确认
                                  </span>
                                )}
                                {file.error && (
                                  <span className="text-[10px] text-rose-600 truncate">
                                    {file.error}
                                  </span>
                                )}
                              </div>
                              
                              <div className="mt-2">
                                <select
                                  className="text-[10px] border border-slate-200 rounded px-2 py-1 bg-white text-slate-600 w-full"
                                  value={selectedTemplate}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={(e) => handleTemplateChange(file.id, e.target.value)}
                                >
                                  <option value="">请选择模板</option>
                                  {templateOptions.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              </div>

                              <div className="flex items-center justify-between mt-2">
                                <p className="text-xs text-slate-500">
                                  {formatFileSize(file.size)}
                                </p>
                                <p className="text-xs text-slate-400">
                                  {file.uploadDate}
                                </p>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <button
                                onClick={(e) => handleDeleteFile(file.id, e)}
                                className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 rounded-md transition-all flex-shrink-0 text-slate-400 hover:text-red-600"
                                title="删除文件"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                    </div>
                  )})}
                </div>

                {/* File Preview */}
                {selectedFile && middlePanelOffset > 250 && (
                  <div className="p-4 border-t border-slate-200 bg-white">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium text-slate-700">文件预览</h4>
                      {(selectedFile.type === 'application/pdf' || selectedFile.name?.toLowerCase().endsWith('.pdf')) && (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => setPdfZoom(Math.max(0.5, pdfZoom - 0.25))}
                            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-600 hover:text-slate-800"
                            title="缩小"
                          >
                            <ZoomOut className="w-4 h-4" />
                          </button>
                          <span className="text-xs text-slate-500 min-w-[3rem] text-center">
                            {Math.round(pdfZoom * 100)}%
                          </span>
                          <button
                            onClick={() => setPdfZoom(Math.min(2, pdfZoom + 0.25))}
                            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-600 hover:text-slate-800"
                            title="放大"
                          >
                            <ZoomIn className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setPdfZoom(1)}
                            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-600 hover:text-slate-800 ml-1"
                            title="重置缩放"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50">
                      {selectedFile.type.startsWith('image/') ? (
                        <img 
                          src={selectedFile.url} 
                          alt={selectedFile.name}
                          className="w-full object-contain max-h-64"
                        />
                      ) : selectedFile.type === 'application/pdf' || selectedFile.name?.toLowerCase().endsWith('.pdf') ? (
                        <div className="overflow-auto bg-slate-100" style={{ height: '384px' }}>
                          <div 
                            style={{ 
                              transform: `scale(${pdfZoom})`,
                              transformOrigin: 'top left',
                              width: `${100 / pdfZoom}%`,
                              height: `${384 / pdfZoom}px`
                            }}
                          >
                            <iframe
                              src={selectedFile.url}
                              title={selectedFile.name}
                              className="w-full border-0"
                              style={{ height: '384px' }}
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="h-48 flex items-center justify-center bg-slate-100">
                          <div className="text-center">
                            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-2" />
                            <p className="text-xs text-slate-500">{selectedFile.name}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Middle Panel - Fixed Width, Draggable */}
          <div 
            className="absolute top-0 bottom-0 flex flex-col bg-white shadow-xl z-10"
            style={{ 
              width: `${MIDDLE_PANEL_WIDTH}px`,
              left: `${middlePanelOffset}px`,
            }}
          >
            {/* Compact Header with Drag Handle */}
            <div 
              className="h-10 border-b border-slate-200 bg-white hover:bg-slate-50 flex items-center justify-between px-4 flex-shrink-0 group cursor-move transition-colors"
              onMouseDown={handleMiddlePanelDragStart}
            >
              <h3 className="text-sm font-medium text-slate-700 flex items-center gap-2">
                <Settings className="w-4 h-4 text-slate-500" />
                配置与操作
              </h3>
              <Move className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* File Upload Section - 移到这里 */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <div className="w-1 h-4 bg-blue-600 rounded-full"></div>
                  文件上传
                </h4>
                
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-4 text-center hover:border-blue-400 hover:bg-blue-50/30 transition-all cursor-pointer">
                  <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-700 mb-1">
                    点击上传或拖拽文件
                  </p>
                  <p className="text-xs text-slate-500 mb-3">
                    支持图片、PDF格式
                  </p>
                  <button
                    onClick={handleUploadClick}
                    className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-xs font-medium inline-flex items-center gap-2"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    选择文件
                  </button>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="mt-2 text-xs text-slate-500">
                    已选择 {uploadedFiles.length} 个文件
                  </div>
                )}
              </div>

              {/* Analysis Control Section - 移到这里 */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <div className="w-1 h-4 bg-emerald-600 rounded-full"></div>
                  数据分析
                </h4>
                
                <div className="border border-emerald-200 rounded-lg p-4 bg-gradient-to-br from-emerald-50 to-teal-50">
                  <p className="text-xs text-slate-700 mb-3">
                    使用AI智能识别上传文件中的数据字段
                  </p>
                  
                  <button
                    onClick={handleAnalyzeClick}
                    disabled={isAnalyzing || uploadedFiles.length === 0}
                    className="w-full px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors text-xs font-medium flex items-center justify-center gap-2"
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        正在分析数据...
                      </>
                    ) : (
                      <>
                        <BarChart3 className="w-4 h-4" />
                        开始数据分析
                      </>
                    )}
                  </button>

                  {uploadedFiles.length === 0 && (
                    <p className="text-xs text-amber-600 mt-2 text-center">
                      请先上传文件
                    </p>
                  )}
                </div>
              </div>

              {/* Custom Prompt Configuration */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <div className="w-1 h-4 bg-purple-600 rounded-full"></div>
                    <MessageSquare className="w-4 h-4 text-purple-600" />
                    自定义提示词
                  </h4>
                  <span className="text-xs text-slate-500">
                    {customPrompt.trim() ? (
                      <span className="text-green-600">✓ 将使用自定义提示词</span>
                    ) : (
                      <span>留空则使用默认提示词</span>
                    )}
                  </span>
                </div>
                
                <div className="border border-slate-200 rounded-lg bg-white">
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="输入自定义提示词，用于指导AI解析数据。例如：&#10;&quot;从图片中提取混凝土强度数据，包括试块编号、抗压强度值（单位：MPa）、养护天数、测试日期等信息，以JSON格式输出。&quot;"
                    className="w-full px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 resize-none"
                    rows={5}
                  />
                </div>
              </div>

              {/* Additional Options */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <div className="w-1 h-4 bg-slate-600 rounded-full"></div>
                  其他选项
                </h4>
                
                <div className="space-y-2">
                  <label className="flex items-center gap-2.5 p-2.5 bg-slate-50 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                    <input type="checkbox" className="w-3.5 h-3.5 text-blue-600 rounded" />
                    <span className="text-xs text-slate-700">自动保存分析结果</span>
                  </label>
                  
                  <label className="flex items-center gap-2.5 p-2.5 bg-slate-50 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                    <input type="checkbox" className="w-3.5 h-3.5 text-blue-600 rounded" />
                    <span className="text-xs text-slate-700">导出为Excel格式</span>
                  </label>

                  <label className="flex items-center gap-2.5 p-2.5 bg-slate-50 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                    <input type="checkbox" className="w-3.5 h-3.5 text-blue-600 rounded" defaultChecked />
                    <span className="text-xs text-slate-700">显示置信度评分</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Output Data */}
          <div 
            className="absolute top-0 right-0 bottom-0 flex flex-col bg-slate-50 border-l border-slate-200 overflow-hidden"
            style={{ 
              left: `${middlePanelOffset + MIDDLE_PANEL_WIDTH}px`,
            }}
          >
            <div className="p-4 border-b border-slate-200 bg-white flex-shrink-0">
              <h3 className="font-medium text-slate-700 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-600" />
                输出数据
                {analysisResult && (
                  <span className="text-xs text-slate-500 ml-auto">
                    {analysisResult.analyzedAt}
                  </span>
                )}
              </h3>
            </div>

            {!analysisResult ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-6">
                <div className="w-24 h-24 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                  <BarChart3 className="w-12 h-12 text-slate-300" />
                </div>
                <p className="font-medium mb-1">暂无输出数据</p>
                <p className="text-xs text-center">
                  执行数据分析后<br />结果将在此显示
                </p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto">

                {selectedFile?.validation_result && (
                  <div className="p-4 pb-0">
                    <h4 className="text-sm font-medium text-slate-700 mb-3">校验结果</h4>
                    {selectedFile.validation_result.errors?.length > 0 && (
                      <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 p-3">
                        <div className="text-xs font-medium text-rose-700 mb-2">错误</div>
                        <ul className="text-xs text-rose-700 space-y-1">
                          {selectedFile.validation_result.errors.map((err, idx) => (
                            <li key={idx}>- {err}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {selectedFile.validation_result.warnings?.length > 0 && (
                      <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
                        <div className="text-xs font-medium text-amber-700 mb-2">警告</div>
                        <ul className="text-xs text-amber-700 space-y-1">
                          {selectedFile.validation_result.warnings.map((warn, idx) => (
                            <li key={idx}>- {warn}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {selectedFile?.commit_results?.length > 0 && (
                  <div className="p-4 pb-0">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium text-slate-700">????</h4>
                      {onRetryChunks && (
                        <button
                          onClick={() => {
                            const failed = selectedFile.commit_results
                              .filter((item: any) => item.status !== 'success')
                              .map((item: any) => item.chunk_id);
                            if (failed.length > 0) {
                              onRetryChunks(node.id, selectedFile, failed);
                            }
                          }}
                          className="text-xs text-slate-600 hover:text-slate-800"
                        >
                          ?????
                        </button>
                      )}
                    </div>
                    <div className="space-y-2">
                      {selectedFile.commit_results.map((item: any) => (
                        <div key={item.chunk_id} className="border border-slate-200 rounded-lg bg-white p-3">
                          <div className="flex items-center justify-between">
                            <div className="text-xs text-slate-600">{item.chunk_id}</div>
                            <div className="flex items-center gap-2">
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                item.status === 'success' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                              }`}>
                                {item.status === 'success' ? 'success' : 'failed'}
                              </span>
                              {item.deduped && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                                  deduped
                                </span>
                              )}
                              {onRetryChunks && item.status !== 'success' && (
                                <button
                                  onClick={() => onRetryChunks(node.id, selectedFile, [item.chunk_id])}
                                  className="text-[10px] text-slate-600 hover:text-slate-800"
                                >
                                  ??
                                </button>
                              )}
                            </div>
                          </div>
                          {item.validation_result?.errors?.length > 0 && (
                            <div className="mt-2 text-[10px] text-rose-600">
                              ??: {item.validation_result.errors.join(', ')}
                            </div>
                          )}
                          {item.validation_result?.warnings?.length > 0 && (
                            <div className="mt-1 text-[10px] text-amber-600">
                              ??: {item.validation_result.warnings.join(', ')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* JSON Data Display */}
                <div className="p-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-3">识别结果（JSON）</h4>
                  
                  <div className="bg-slate-900 rounded-lg p-4 border border-slate-700 overflow-x-auto space-y-4">
                    {Array.isArray(analysisResult.jsonData) && analysisResult.jsonData.length > 0 ? (
                      (selectedFile ? (selectedJsonItem ? [selectedJsonItem] : []) : analysisResult.jsonData)
                        .map((item: any, index: number) => {
                          const isConfirmed = selectedFile?.confirmed || false;
                          return (
                          <div key={item.fileId || index} className="border border-slate-700 rounded-md p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="text-xs text-slate-400">
                                文件 {index + 1}：{item.fileName || '未命名文件'}
                              </div>
                              {isConfirmed && (
                                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-600/20 border border-emerald-500/30 rounded text-emerald-400 text-xs font-medium">
                                  <CheckCircle className="w-3 h-3" />
                                  已确认
                                </div>
                              )}
                            </div>
                            <pre className="text-xs text-slate-100 font-mono whitespace-pre-wrap break-words">
                              {item.data ? JSON.stringify(item.data, null, 2) : '暂无数据'}
                            </pre>
                          </div>
                        )})
                    ) : (
                      <pre className="text-xs text-slate-100 font-mono whitespace-pre-wrap break-words">
                        {analysisResult.jsonData 
                          ? JSON.stringify(analysisResult.jsonData, null, 2)
                          : '暂无数据'}
                      </pre>
                    )}
                    {selectedFile && Array.isArray(analysisResult.jsonData) && !selectedJsonItem && (
                      <div className="text-xs text-amber-400 mt-2">
                        当前文件尚未解析，请先点击"开始数据分析"。
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-4 space-y-2">
                    {hasMissingSelection && (
                      <div className="text-xs text-amber-600">
                        请先为标记为“需要选择”的片段选择模板。
                      </div>
                    )}
                    <button
                      onClick={handleConfirmClick}
                      disabled={!selectedFile?.preview_chunks || selectedFile?.preview_chunks.length === 0 || selectedFile?.confirmed || isConfirming || hasMissingSelection}
                      className={`w-full px-3 py-2 rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2 ${
                        selectedFile?.confirmed
                          ? 'bg-slate-400 text-white cursor-not-allowed'
                          : 'bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white'
                      }`}
                    >
                      {isConfirming ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          确认中...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          {selectedFile?.confirmed ? '已确认' : '已确认无误'}
                        </>
                      )}
                    </button>
                    <button className="w-full px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2">
                      <Download className="w-4 h-4" />
                      导出结果
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
