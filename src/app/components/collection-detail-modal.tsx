import { useState, useRef, useEffect } from 'react';
import { X, Upload, Image as ImageIcon, FileText, Download, BarChart3, CheckCircle, AlertCircle, Loader2, Move, Settings, Database } from 'lucide-react';

interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  uploadDate: string;
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
    totalFields: number;
    successCount: number;
    data: AnalysisData[];
    summary?: {
      avgConfidence: number;
      recommendations: string[];
    };
  } | null;
  onUpload: (nodeId: string, nodeLabel: string) => void;
  onAnalyze: (nodeId: string, nodeData: any) => void;
  onRemoveFile: (fileId: string) => void;
}

export default function CollectionDetailModal({
  node,
  onClose,
  uploadedFiles,
  analysisResult,
  onUpload,
  onAnalyze,
  onRemoveFile,
}: CollectionDetailModalProps) {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(uploadedFiles[0] || null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [middlePanelOffset, setMiddlePanelOffset] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);

  const MIDDLE_PANEL_WIDTH = 450; // 中间栏固定宽度
  const MIN_SIDE_MARGIN = 100; // 左右两侧最小留白距离

  // 初始化中间栏位置
  useEffect(() => {
    if (containerRef.current && middlePanelOffset === 0) {
      const containerWidth = containerRef.current.offsetWidth;
      const initialOffset = Math.max(
        MIN_SIDE_MARGIN,
        Math.floor((containerWidth - MIDDLE_PANEL_WIDTH) / 3)
      );
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
    onUpload(node.id, node.data.label);
  };

  const handleAnalyzeClick = () => {
    if (uploadedFiles.length === 0) {
      alert('请先上传文件');
      return;
    }
    setIsAnalyzing(true);
    setTimeout(() => {
      onAnalyze(node.id, node.data);
      setIsAnalyzing(false);
    }, 1500);
  };

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
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-8 bg-white rounded-xl shadow-2xl z-50 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="h-16 border-b border-slate-200 flex items-center justify-between px-6 bg-gradient-to-r from-slate-50 to-slate-100 flex-shrink-0">
          <div>
            <h2 className="font-semibold text-slate-800">{node.data.label}</h2>
            <p className="text-xs text-slate-500">数据采集与分析配置</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
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
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      onClick={() => setSelectedFile(file)}
                      className={`p-3 rounded-lg border transition-all cursor-pointer ${
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
                          <p className="text-xs text-slate-500 mt-1">
                            {formatFileSize(file.size)}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {file.uploadDate}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* File Preview */}
                {selectedFile && middlePanelOffset > 250 && (
                  <div className="p-4 border-t border-slate-200 bg-white">
                    <h4 className="text-sm font-medium text-slate-700 mb-3">文件预览</h4>
                    <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50">
                      {selectedFile.type.startsWith('image/') ? (
                        <img 
                          src={selectedFile.url} 
                          alt={selectedFile.name}
                          className="w-full object-contain max-h-64"
                        />
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
            {/* Drag Handle */}
            <div 
              className="h-12 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-slate-200 flex items-center justify-center cursor-move hover:bg-gradient-to-r hover:from-blue-100 hover:to-indigo-100 transition-all flex-shrink-0 group"
              onMouseDown={handleMiddlePanelDragStart}
            >
              <Move className="w-5 h-5 text-slate-400 group-hover:text-blue-600 transition-colors" />
              <span className="ml-2 text-xs text-slate-500 group-hover:text-blue-700 font-medium">
                拖动调整位置
              </span>
            </div>

            <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-blue-50 to-indigo-50 flex-shrink-0">
              <h3 className="font-medium text-slate-700 flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-600" />
                节点配置与操作
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {/* Node Configuration Section */}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <div className="w-1 h-4 bg-blue-600 rounded-full"></div>
                  节点信息
                </h4>
                
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">
                      节点名称
                    </label>
                    <input
                      type="text"
                      value={node.data.label}
                      readOnly
                      className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">
                      节点类型
                    </label>
                    <input
                      type="text"
                      value={node.data.type}
                      readOnly
                      className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-600 mb-1.5">
                      描述信息
                    </label>
                    <textarea
                      placeholder="请输入节点描述..."
                      rows={2}
                      className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                </div>
              </div>

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
                    支持图片、PDF、Excel等格式
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
                    已上传 {uploadedFiles.length} 个文件
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

              {/* Data Fields Configuration - 移到后面 */}
              {node.data.fields && node.data.fields.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <div className="w-1 h-4 bg-indigo-600 rounded-full"></div>
                    数据字段配置
                  </h4>
                  
                  <div className="space-y-2">
                    {node.data.fields.map((field: any, index: number) => (
                      <div key={index} className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-medium text-slate-800">
                            {field.label}
                          </span>
                          {field.required && (
                            <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full">
                              必填
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-slate-500">
                          <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                            {field.name}
                          </span>
                          <span className="px-1.5 py-0.5 bg-slate-200 text-slate-700 rounded">
                            {field.type}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

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
                {/* Summary Stats */}
                <div className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 border-b border-slate-200">
                  <div className="grid grid-cols-1 gap-3">
                    <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-sm">
                      <p className="text-xs text-slate-500 mb-1">总字段</p>
                      <p className="text-xl font-semibold text-slate-800">{analysisResult.totalFields}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-sm">
                      <p className="text-xs text-slate-500 mb-1">成功识别</p>
                      <p className="text-xl font-semibold text-green-600">{analysisResult.successCount}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 border border-slate-200 shadow-sm">
                      <p className="text-xs text-slate-500 mb-1">平均准确率</p>
                      <p className="text-xl font-semibold text-blue-600">
                        {analysisResult.summary?.avgConfidence || 0}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Analysis Data */}
                <div className="p-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-3">识别字段详情</h4>
                  
                  <div className="space-y-3">
                    {analysisResult.data.map((item, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${getStatusColor(item.status)} transition-all`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              {getStatusIcon(item.status)}
                              <span className="text-sm font-medium text-slate-800">
                                {item.fieldLabel}
                              </span>
                            </div>
                            <p className="text-xs text-slate-500">
                              {item.fieldName}
                            </p>
                          </div>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getConfidenceColor(item.confidence)}`}>
                            {item.confidence}%
                          </span>
                        </div>
                        
                        <div className="bg-white rounded-lg px-3 py-2 border border-slate-200">
                          <div className="flex items-baseline gap-2">
                            <span className="font-semibold text-slate-900">
                              {item.extractedValue}
                            </span>
                            {item.unit && (
                              <span className="text-xs text-slate-500">{item.unit}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Recommendations */}
                  {analysisResult.summary?.recommendations && analysisResult.summary.recommendations.length > 0 && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h5 className="text-sm font-medium text-blue-900 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        建议
                      </h5>
                      <ul className="space-y-1">
                        {analysisResult.summary.recommendations.map((rec, index) => (
                          <li key={index} className="text-xs text-blue-700 flex items-start gap-2">
                            <span className="text-blue-400">•</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="mt-4 space-y-2">
                    <button className="w-full px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      确认并保存
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
