import React, { useState, useRef, useEffect } from 'react';
import { X, Upload, Image as ImageIcon, FileText, Download, BarChart3, CheckCircle, AlertCircle, Loader2, Move, Settings, Database, Trash2, MessageSquare, ZoomIn, ZoomOut, RotateCcw, Sparkles, Code, LayoutList } from 'lucide-react';
import SkillSelector from './skill-selector';

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
  skill_name?: string;
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
  skill_result?: any;
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
    jsonData: any; // 鍘熷JSON format is preserved on save
  } | null;
  onUpload: (nodeId: string, nodeLabel: string, prompt?: string) => void;
  onAnalyze: (
    nodeId: string,
    nodeData: any,
    options?: { prompt?: string; skillName?: string; targetFileId?: string }
  ) => Promise<void>;
  onRemoveFile: (fileId: string) => void;
  onUpdateAnalysisResult?: (fileId: string, data: any[]) => void;
  projectId?: string; // 椤圭洰ID
}

export default function CollectionDetailModal({
  node,
  onClose,
  uploadedFiles,
  analysisResult,
  onUpload,
  onAnalyze,
  onRemoveFile,
  onUpdateAnalysisResult,
  projectId,
}: CollectionDetailModalProps) {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(uploadedFiles[0] || null);
  const [middlePanelOffset, setMiddlePanelOffset] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef(false);
  const [pdfZoom, setPdfZoom] = useState(1); // PDF缂╂斁姣斾緥锛岄粯璁?00%
  const [selectedSkill, setSelectedSkill] = useState<string>('');
  const [isExecutingSkill, setIsExecutingSkill] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [editedJsonByFile, setEditedJsonByFile] = useState<Record<string, string>>({});
  const [jsonErrorsByFile, setJsonErrorsByFile] = useState<Record<string, string | null>>({});
  const [viewMode, setViewMode] = useState<'form' | 'json'>('form');

  const skillAllowlistByNodeType: Record<string, string[]> = {
    'mortar-strength': ['mortar_table_recognition'],
    'brick-strength': ['brick_table_recognition'],
    'software-calculation': ['software_calculation_recognition'],
  };
  const preferredSkillByNodeType: Record<string, string> = {
    'mortar-strength': 'mortar_table_recognition',
    'brick-strength': 'brick_table_recognition',
    'software-calculation': 'software_calculation_recognition',
  };
  const allowedSkillsForNode = skillAllowlistByNodeType[node?.data?.type] || [];
  const preferredSkillForNode = preferredSkillByNodeType[node?.data?.type];

  // 褰撴枃浠跺垪琛ㄥ彉鍖栨椂锛屾洿鏂伴€変腑鏂囦欢
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

  // 褰撳垏鎹㈡枃浠舵椂锛岄噸缃甈DF缂╂斁姣斾緥
  useEffect(() => {
    setPdfZoom(1);
  }, [selectedFile?.id]);

  useEffect(() => {
    if (!preferredSkillForNode) return;
    if (!selectedSkill || (allowedSkillsForNode.length > 0 && !allowedSkillsForNode.includes(selectedSkill))) {
      setSelectedSkill(preferredSkillForNode);
    }
  }, [preferredSkillForNode, selectedSkill, node?.id]);

  const MIDDLE_PANEL_WIDTH = 340; // 涓棿鏍忓浐瀹氬搴?
  const MIN_SIDE_MARGIN = 100; // 宸﹀彸涓や晶鏈€灏忕暀鐧借窛绂?

  // 鍒濆鍖栦腑闂存爮浣嶇疆
  useEffect(() => {
    if (containerRef.current && middlePanelOffset === 0) {
      const containerWidth = containerRef.current.offsetWidth;
      // 灞呬腑璁＄畻: (鎬诲搴?- 闈㈡澘瀹藉害) / 2
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
    onUpload(node.id, node.data.label, undefined);
  };


  const handleExecuteSkill = async () => {
    if (!selectedSkill || !selectedFile?.file) {
      alert('Please select a skill and file.');
      return;
    }
    if (allowedSkillsForNode.length > 0 && !allowedSkillsForNode.includes(selectedSkill)) {
      alert(`褰撳墠鑺傜偣浠呮敮鎸侊細${allowedSkillsForNode.join(' / ')}`);
      return;
    }

    setIsExecutingSkill(true);
    try {
      await onAnalyze(node.id, node.data, {
        skillName: selectedSkill,
        targetFileId: selectedFile.id,
      });
    } finally {
      setIsExecutingSkill(false);
    }
  };


  const handleClose = () => {
    // Check if there are parsed but unconfirmed files.
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
      
      const message = `有 ${unconfirmedFiles.length} 个文件已解析但尚未确认：\n${fileListText}\n\n确定要关闭吗？未确认的文件不会保存到数据库。`;
      
      if (window.confirm(message)) {
        onClose();
      }
    } else {
      // All files are confirmed, or no confirmation is required.
      onClose();
    }
  };

  const handleDeleteFile = (fileId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 闃绘瑙﹀彂鏂囦欢閫夋嫨
    onRemoveFile(fileId);
    // selectedFile 浼氶€氳繃 useEffect 鑷姩鏇存柊
  };

  const getParseStatus = (status?: string) => {
    if (status === 'uploaded') return { text: '已解析', className: 'bg-emerald-100 text-emerald-700' };
    if (status === 'failed') return { text: '澶辫触', className: 'bg-rose-100 text-rose-700' };
    return { text: '未解析', className: 'bg-slate-100 text-slate-600' };
  };

  const selectedJsonItem = Array.isArray(analysisResult?.jsonData) && selectedFile
    ? analysisResult?.jsonData.find((item: any) => item.fileId === selectedFile.id)
    : null;

  const getJsonText = (fileId: string, data: any) => {
    if (editedJsonByFile[fileId] !== undefined) {
      return editedJsonByFile[fileId];
    }
    return JSON.stringify(data ?? null, null, 2);
  };

  const handleJsonChange = (fileId: string, value: string) => {
    setEditedJsonByFile((prev) => ({ ...prev, [fileId]: value }));
    setJsonErrorsByFile((prev) => ({ ...prev, [fileId]: null }));
  };

  const handleJsonSave = (fileId: string, rawValue: string) => {
    if (!onUpdateAnalysisResult) {
      return;
    }
    try {
      const parsed = JSON.parse(rawValue);
      const normalized = Array.isArray(parsed) ? parsed : [parsed];
      onUpdateAnalysisResult(fileId, normalized);
      setJsonErrorsByFile((prev) => ({ ...prev, [fileId]: null }));
    } catch (error: any) {
      setJsonErrorsByFile((prev) => ({
        ...prev,
        [fileId]: error?.message || 'Invalid JSON',
      }));
    }
  };

  const handleConfirmResult = async () => {
    if (!selectedFile) {
      return;
    }
    const skillName = selectedFile.skill_name || selectedSkill;
    if (!skillName) {
      alert('请先选择技能');
      return;
    }
    const jsonText = getJsonText(selectedFile.id, selectedJsonItem?.data);
    let parsed: any;
    try {
      parsed = JSON.parse(jsonText);
    } catch (error: any) {
      alert(`JSON 格式错误：${error?.message || '无法解析'}`);
      return;
    }

    const records = Array.isArray(parsed) ? parsed : [parsed];
    const payload = {
      project_id: projectId || node.id,
      node_id: node.id,
      run_id: selectedFile.run_id,
      source_hash: selectedFile.source_hash,
      skill_name: skillName,
      records,
    };

    setIsConfirming(true);
    try {
      const response = await fetch('/api/skill/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || errorData.message || '纭澶辫触');
      }
      setSelectedFile({ ...selectedFile, confirmed: true });
    } catch (error: any) {
      console.error('Confirm failed:', error);
      alert(`确认失败：${error?.message || '未知错误'}`);
    } finally {
      setIsConfirming(false);
    }
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
    // Adapter for both 0-1 and 0-100 scales
    const score = confidence <= 1 ? confidence : confidence / 100;
    
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const renderFormView = (fileId: string, jsonString: string) => {
    let data: any;
    try {
      data = JSON.parse(jsonString);
    } catch (e) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-slate-400 bg-slate-50 rounded-lg border border-slate-200 border-dashed">
           <AlertCircle className="w-8 h-8 mb-2 text-rose-400"/>
           <p className="text-sm">数据格式错误，无法显示表单视图。</p>
           <button onClick={() => setViewMode('json')} className="mt-2 text-blue-600 hover:underline text-xs">切换到代码模式修复</button>
        </div>
      );
    }
    
    // Support single object or array of objects
    const items = Array.isArray(data) ? data : (typeof data === 'object' && data !== null ? [data] : []);

    if (items.length === 0) {
         return <div className="p-8 text-center text-slate-400 text-sm bg-slate-50 rounded-lg border border-slate-200 border-dashed">鏆傛棤鏁版嵁缁撴瀯</div>;
    }

    const handleFieldUpdate = (itemIndex: number, key: string, value: string) => {
        const newData = JSON.parse(JSON.stringify(Array.isArray(data) ? data : [data]));
        newData[itemIndex][key] = value;
        const finalData = Array.isArray(data) ? newData : newData[0];
        handleJsonChange(fileId, JSON.stringify(finalData, null, 2));
    };

    const handleRowUpdate = (itemIndex: number, arrayKey: string, rowIndex: number, rowValKey: string, value: string) => {
        const newData = JSON.parse(JSON.stringify(Array.isArray(data) ? data : [data]));
        if (newData[itemIndex] && newData[itemIndex][arrayKey] && Array.isArray(newData[itemIndex][arrayKey])) {
             if (newData[itemIndex][arrayKey][rowIndex]) {
                 newData[itemIndex][arrayKey][rowIndex][rowValKey] = value;
                 const finalData = Array.isArray(data) ? newData : newData[0];
                 handleJsonChange(fileId, JSON.stringify(finalData, null, 2));
             }
        }
    };
    
    // Save on blur using the current data in the closure (fresh on re-render)
    const handleSaveCurrent = () => {
         handleJsonSave(fileId, JSON.stringify(data, null, 2)); 
    };

    // Dictionary for label translation
    const labelMap: Record<string, string> = {
      table_id: '表格编号',
      commission_id: '委托单编号',
      test_date: '检测日期',
      instrument_id: '设备编号',
      brick_type: '砖块类型',
      strength_grade: '设计强度等级',
      rows: '回弹测区数据明细',
      items: '检测项明细',
      test_location: '测区位置/编号',
      estimated_strength_mpa: '推定强度 (MPa)',
      converted_strength_mpa: '换算强度 (MPa)',
      seq: '序号',
      meta: '表格元数据',
      control_id: '控制编号',
      record_no: '记录编号',
      house_name: '房屋名称',
      house_details: '房屋详情',
      client_org: '委托单位',
      inspection_reason: '检测原因',
      inspection_basis: '检测依据',
      inspection_date: '检测日期',
      table_type: '表格类型',
      test_location_text: '检测部位',
      design_strength_grade: '设计强度等级',
      modification_location: '拆改位置',
      modification_description: '拆改描述',
      photo_index: '照片编号',
      photo_no: '照片编号',
      damage_location: '损伤位置',
      damage_description: '损伤描述',
      mortar_strength_mpa: '砌筑砂浆抗压强度取值 (MPa)',
      brick_strength_grade: '砌墙砖抗压强度等级',
      live_loads: '活载',
      dead_loads: '恒载(含自重)',
      load_combination_type: '荷载基本组合类型',
      wind_snow_terrain: '风雪及场地参数',
      non_accessible_roof: '不上人屋面',
      living_room_bedroom_kitchen_wc: '客厅/卧室/厨房/卫生间',
      stair_and_balcony: '楼梯/阳台',
      roof: '屋面',
      floor_prefab: '楼面(预制板)',
      stair_room: '楼梯间',
    };

    const getLabel = (k: string) => labelMap[k] || k;

    return (
      <div className="space-y-4">
        {items.map((item: any, idx: number) => {
          // Try to get confidence from item (if exists) or mock it for design if missing (optional)
          const confidence = item.confidence !== undefined ? Number(item.confidence) : null;
          
          return (
          <div key={idx} className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition-all duration-200">
            <div className="bg-slate-50/80 px-4 py-2 border-b border-slate-100 flex justify-between items-center backdrop-blur-sm">
                 <span className="text-xs font-bold text-slate-600 flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 ring-2 ring-blue-100"></div>
                    璁板綍 #{idx + 1}
                 </span>
                 {/* Confidence Badge */}
                 {confidence !== null && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium flex items-center gap-1 ${getConfidenceColor(confidence)}`}>
                        <Sparkles className="w-3 h-3" />
                        {confidence <= 1 ? Math.round(confidence * 100) : confidence}% 缃俊搴?
                    </span>
                 )}
            </div>
            <div className="divide-y divide-slate-50">
               {/* 鍏堟覆鏌撻潪鏁扮粍瀛楁锛坢eta 淇℃伅锛?*/}
               {Object.entries(item).map(([key, val]) => {
                   const isSystem = key === 'file' || key === 'table_type' || key === '鍥剧墖搴忓彿' || key === 'box_2d' || key === 'confidence' || key === '__confidence' || key === 'image_index' || key === 'notes' || key === 'source_file' || key === 'parser' || key === 'signoff' || key === 'status';
                   if (isSystem) return null;
                   if (Array.isArray(val)) return null; // 璺宠繃鏁扮粍锛屽悗闈㈡覆鏌?
                   
                   // 鐗规畩澶勭悊 meta 瀵硅薄锛氬睍寮€鍏跺瓙瀛楁锛堥殣钘?source_file / parser锛?
                   if (key === 'meta' && typeof val === 'object' && val !== null && !Array.isArray(val)) {
                     const hiddenMetaKeys = new Set(['source_file', 'parser']);
                     const metaEntries = Object.entries(val).filter(([subKey]) => !hiddenMetaKeys.has(subKey));
                     if (metaEntries.length === 0) return null;
                     return (
                        <div key={key} className="border-t border-slate-100">
                          <div className="bg-slate-50/50 px-4 py-2 border-b border-slate-100">
                            <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">{getLabel(key)}</span>
                          </div>
                          {metaEntries.map(([subKey, subVal]) => (
                            <div key={subKey} className="flex flex-col sm:flex-row group hover:bg-slate-50/60 transition-colors">
                               <div className="sm:w-[35%] px-4 py-2 flex items-center bg-slate-50/10 border-r border-transparent sm:border-slate-50 group-hover:border-slate-100 transition-colors">
                                   <span className="text-[11px] font-medium text-slate-500 truncate select-none" title={getLabel(subKey)}>{getLabel(subKey)}</span>
                              </div>
                              <div className="sm:w-[65%] flex items-center relative">
                                 <div className="hidden sm:block absolute left-0 top-2 bottom-2 w-px bg-slate-100 group-hover:bg-slate-200 transition-colors"></div>
                                 {/* 鍒ゆ柇鏄惁涓洪暱鏂囨湰瀛楁 */}
                                 {subKey === 'house_details' || subKey === 'description' || subKey === 'notes' ? (
                                    <textarea
                                       className="w-full px-4 py-2 text-[11px] text-slate-900 bg-transparent border-none focus:ring-0 placeholder:text-slate-300 font-semibold resize-none overflow-hidden leading-relaxed"
                                       placeholder="-"
                                       rows={3}
                                       style={{ minHeight: '60px' }}
                                       value={String(subVal ?? '')}
                                       onInput={(e) => {
                                          const target = e.currentTarget;
                                          target.style.height = 'auto';
                                          target.style.height = target.scrollHeight + 'px';
                                       }}
                                       ref={(el) => {
                                          if (el) {
                                             el.style.height = 'auto';
                                             el.style.height = el.scrollHeight + 'px';
                                          }
                                       }}
                                       onChange={(e) => {
                                         const newData = JSON.parse(JSON.stringify(Array.isArray(data) ? data : [data]));
                                         if (newData[idx] && newData[idx][key]) {
                                           newData[idx][key][subKey] = e.target.value;
                                           const finalData = Array.isArray(data) ? newData : newData[0];
                                           handleJsonChange(fileId, JSON.stringify(finalData, null, 2));
                                         }
                                       }}
                                       onBlur={handleSaveCurrent}
                                    />
                                 ) : (
                                    <input 
                                       type="text" 
                                       className="w-full h-full px-4 py-2 text-[11px] text-slate-900 bg-transparent border-none focus:ring-0 placeholder:text-slate-300 font-semibold"
                                       placeholder="-"
                                       value={String(subVal ?? '')}
                                       onChange={(e) => {
                                         const newData = JSON.parse(JSON.stringify(Array.isArray(data) ? data : [data]));
                                         if (newData[idx] && newData[idx][key]) {
                                           newData[idx][key][subKey] = e.target.value;
                                           const finalData = Array.isArray(data) ? newData : newData[0];
                                           handleJsonChange(fileId, JSON.stringify(finalData, null, 2));
                                         }
                                       }}
                                       onBlur={handleSaveCurrent}
                                    /> 
                                 )}
                              </div>
                           </div>
                         ))}
                        </div>
                      );
                    }

                   // 閫氱敤瀵硅薄瀛楁灞曞紑锛堜緥濡?live_loads / dead_loads / wind_snow_terrain锛?
                   if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
                     const objectEntries = Object.entries(val as Record<string, any>);
                     if (objectEntries.length === 0) return null;
                     return (
                       <div key={key} className="border-t border-slate-100">
                         <div className="bg-slate-50/50 px-4 py-2 border-b border-slate-100">
                           <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">{getLabel(key)}</span>
                         </div>
                         {objectEntries.map(([subKey, subVal]) => (
                           <div key={`${key}.${subKey}`} className="flex flex-col sm:flex-row group hover:bg-slate-50/60 transition-colors">
                             <div className="sm:w-[35%] px-4 py-2 flex items-center bg-slate-50/10 border-r border-transparent sm:border-slate-50 group-hover:border-slate-100 transition-colors">
                               <span className="text-[11px] font-medium text-slate-500 truncate select-none" title={getLabel(subKey)}>{getLabel(subKey)}</span>
                             </div>
                             <div className="sm:w-[65%] flex items-center relative">
                               <div className="hidden sm:block absolute left-0 top-2 bottom-2 w-px bg-slate-100 group-hover:bg-slate-200 transition-colors"></div>
                               <input
                                 type="text"
                                 className="w-full h-full px-4 py-2 text-[11px] text-slate-900 bg-transparent border-none focus:ring-0 placeholder:text-slate-300 font-semibold"
                                 placeholder="-"
                                 value={String(subVal ?? '')}
                                 onChange={(e) => {
                                   const newData = JSON.parse(JSON.stringify(Array.isArray(data) ? data : [data]));
                                   if (newData[idx] && newData[idx][key]) {
                                     newData[idx][key][subKey] = e.target.value;
                                     const finalData = Array.isArray(data) ? newData : newData[0];
                                     handleJsonChange(fileId, JSON.stringify(finalData, null, 2));
                                   }
                                 }}
                                 onBlur={handleSaveCurrent}
                               />
                             </div>
                           </div>
                         ))}
                       </div>
                     );
                   }

                   return ( 
                      <div key={key} className="flex flex-col sm:flex-row group hover:bg-slate-50/60 transition-colors">
                        <div className="sm:w-[35%] px-4 py-2 flex items-center bg-slate-50/10 border-r border-transparent sm:border-slate-50 group-hover:border-slate-100 transition-colors">
                            <span className="text-[11px] font-medium text-slate-500 truncate select-none" title={getLabel(key)}>{getLabel(key)}</span>
                        </div>
                        <div className="sm:w-[65%] flex items-center relative">
                           <div className="hidden sm:block absolute left-0 top-2 bottom-2 w-px bg-slate-100 group-hover:bg-slate-200 transition-colors"></div>
                           {/* 鍒ゆ柇鏄惁涓洪暱鏂囨湰瀛楁 */}
                           {key === 'house_details' || key === 'modification_description' || key === 'damage_description' || key === 'description' ? (
                              <textarea
                                 className="w-full px-4 py-2 text-[11px] text-slate-900 bg-transparent border-none focus:ring-0 placeholder:text-slate-300 font-semibold resize-none overflow-hidden leading-relaxed"
                                 placeholder="-"
                                 rows={3}
                                 style={{ minHeight: '60px' }}
                                 value={val as string ?? ''}
                                 onInput={(e) => {
                                    const target = e.currentTarget;
                                    target.style.height = 'auto';
                                    target.style.height = target.scrollHeight + 'px';
                                 }}
                                 ref={(el) => {
                                    if (el) {
                                       el.style.height = 'auto';
                                       el.style.height = el.scrollHeight + 'px';
                                    }
                                 }}
                                 onChange={(e) => handleFieldUpdate(idx, key, e.target.value)}
                                 onBlur={handleSaveCurrent}
                              />
                           ) : (
                              <input 
                                 type="text" 
                                 className="w-full h-full px-4 py-2 text-[11px] text-slate-900 bg-transparent border-none focus:ring-0 placeholder:text-slate-300 font-semibold"
                                 placeholder="-"
                                 value={val as string ?? ''}
                                 onChange={(e) => handleFieldUpdate(idx, key, e.target.value)}
                                 onBlur={handleSaveCurrent}
                              />
                           )}
                        </div>
                     </div>
                   );
               })}
               
               {/* 鐒跺悗娓叉煋鏁扮粍瀛楁锛堣〃鏍兼暟鎹級 */}
               {Object.entries(item).map(([key, val]) => {
                   if (!Array.isArray(val)) return null;
                   if (val.length === 0) return null;
                   
                   // Check if it's an array of objects to render as table
                   if (typeof val[0] === 'object') {
                      // 杩囨护鎺?seq 鍒?
                      const subHeaders = Object.keys(val[0]).filter(h => h !== 'seq');
                      return (
                        <div key={key} className="flex flex-col border-t border-slate-100 mt-1">
                          <div className="bg-slate-50/50 px-4 py-2 border-b border-slate-100 flex items-center gap-2">
                            <LayoutList className="w-3.5 h-3.5 text-slate-400" />
                            <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">{getLabel(key)}</span>
                          </div>
                          <div className="overflow-x-auto">
                             <table className="w-full text-left border-collapse table-fixed">
                               <thead>
                                 <tr className="bg-slate-50/30 border-b border-slate-100">
                                   <th className="px-2 py-1.5 w-8 text-[10px] font-medium text-slate-400 text-center bg-slate-50/20">#</th>
                                   {subHeaders.map(h => {
                                     let widthClass = '';
                                     if (h === 'modification_location') widthClass = 'w-24';
                                     else if (h === 'photo_no') widthClass = 'w-16';
                                     else if (h === 'test_location') widthClass = 'w-24';
                                     else if (h === 'modification_description') widthClass = 'w-auto'; 
                                     else widthClass = 'w-24'; // Default narrow for others to give space to description
                                     
                                     return (
                                       <th key={h} className={`px-2 py-1.5 text-[10px] font-bold text-slate-500 whitespace-normal bg-slate-50/20 ${widthClass}`}>{getLabel(h)}</th>
                                     );
                                   })}
                                 </tr>
                               </thead>
                               <tbody className="divide-y divide-slate-50">
                                 {val.map((row: any, rIdx: number) => (
                                   <tr key={rIdx} className="hover:bg-slate-50/50 transition-colors group/row">
                                     <td className="px-2 py-1 text-[10px] text-slate-400 text-center font-mono select-none align-top pt-2">{rIdx + 1}</td>
                                     {subHeaders.map(h => {
                                       const cellVal = row[h] ?? '';
                                       const isLongText = h === 'modification_description' || h === 'damage_description';
                                       
                                       return (
                                       <td key={h} className="px-1 py-0.5 align-top">
                                         {isLongText ? (
                                            <textarea
                                                className="w-full bg-transparent hover:bg-white border border-transparent hover:border-slate-200 focus:bg-white focus:border-blue-400 rounded px-1.5 py-1 text-[10px] text-slate-700 font-medium transition-all focus:outline-none placeholder:text-slate-300 resize-none overflow-hidden leading-relaxed"
                                                placeholder="-"
                                                value={String(cellVal)}
                                                rows={1}
                                                style={{ minHeight: '28px' }}
                                                onInput={(e) => {
                                                    const target = e.currentTarget;
                                                    target.style.height = 'auto';
                                                    target.style.height = target.scrollHeight + 'px';
                                                }}
                                                ref={(el) => {
                                                    if (el) {
                                                        el.style.height = 'auto';
                                                        el.style.height = el.scrollHeight + 'px';
                                                    }
                                                }}
                                                onChange={(e) => handleRowUpdate(idx, key, rIdx, h, e.target.value)}
                                                onBlur={handleSaveCurrent}
                                            />
                                         ) : (
                                            <input 
                                                type="text" 
                                                placeholder="-"
                                                className="w-full bg-transparent hover:bg-white border border-transparent hover:border-slate-200 focus:bg-white focus:border-blue-400 rounded px-1.5 py-0.5 text-[10px] text-slate-700 font-medium transition-all focus:outline-none placeholder:text-slate-300 h-7"
                                                value={String(cellVal)}
                                                onChange={(e) => handleRowUpdate(idx, key, rIdx, h, e.target.value)}
                                                onBlur={handleSaveCurrent}
                                            />
                                         )}
                                       </td>
                                     )})}
                                   </tr>
                                 ))}
                               </tbody>
                             </table>
                          </div>
                        </div>
                      );
                   }
                   return null;
               })}
            </div>
          </div>
        )})}
      </div>
    );
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
                placeholder="鍦ㄦ杈撳叆鑺傜偣鎻忚堪淇℃伅..."
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
                杈撳叆鏁版嵁
                <span className="text-xs text-slate-500 ml-auto">
                  {uploadedFiles.length} 涓枃浠?
                </span>
              </h3>
            </div>

            {uploadedFiles.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-6">
                <div className="w-24 h-24 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                  <ImageIcon className="w-12 h-12 text-slate-300" />
                </div>
                <p className="font-medium mb-1">鏆傛棤杈撳叆鏁版嵁</p>
                <p className="text-xs text-center">
                  鍦ㄤ腑闂撮潰鏉夸笂浼犳枃浠?
                </p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto">
                {/* File List */}
                <div className="p-3 space-y-2">
                  {uploadedFiles.map((file) => {
                    const statusBadge = getParseStatus(file.status);
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
                                {file.confirmed && (
                                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                                    宸茬‘璁?
                                  </span>
                                )}
                                {file.error && (
                                  <span className="text-[10px] text-rose-600 truncate">
                                    {file.error}
                                  </span>
                                )}
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
                                title="鍒犻櫎鏂囦欢"
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
                      <h4 className="text-sm font-medium text-slate-700">鏂囦欢棰勮</h4>
                      {(selectedFile.type === 'application/pdf' || selectedFile.name?.toLowerCase().endsWith('.pdf')) && (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => setPdfZoom(Math.max(0.5, pdfZoom - 0.25))}
                            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-600 hover:text-slate-800"
                            title="缂╁皬"
                          >
                            <ZoomOut className="w-4 h-4" />
                          </button>
                          <span className="text-xs text-slate-500 min-w-[3rem] text-center">
                            {Math.round(pdfZoom * 100)}%
                          </span>
                          <button
                            onClick={() => setPdfZoom(Math.min(2, pdfZoom + 0.25))}
                            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-600 hover:text-slate-800"
                            title="鏀惧ぇ"
                          >
                            <ZoomIn className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setPdfZoom(1)}
                            className="p-1.5 hover:bg-slate-100 rounded-md transition-colors text-slate-600 hover:text-slate-800 ml-1"
                            title="閲嶇疆缂╂斁"
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
                閰嶇疆涓庢搷浣?
              </h3>
              <Move className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {/* File Upload Section - 绉诲埌杩欓噷 */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                  <div className="w-1 h-4 bg-blue-600 rounded-full"></div>
                  鏂囦欢涓婁紶
                </h4>
                
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-3 text-center hover:border-blue-400 hover:bg-blue-50/30 transition-all cursor-pointer flex flex-col items-center">
                  <div className="flex items-center justify-center gap-3 mb-2">
                     <Upload className="w-5 h-5 text-slate-400" />
                     <span className="text-xs text-slate-600">鐐瑰嚮涓婁紶鎴栨嫋鎷芥枃浠?(PDF/鍥剧墖)</span>
                  </div>
                  <button
                    onClick={handleUploadClick}
                    className="w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors text-xs font-medium inline-flex items-center justify-center gap-2"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    閫夋嫨鏂囦欢
                  </button>
                </div>

                {uploadedFiles.length > 0 && (
                  <div className="mt-1.5 text-xs text-slate-500 text-center">
                    宸查€夋嫨 {uploadedFiles.length} 涓枃浠?
                  </div>
                )}
              </div>

                            {/* Analysis Control Section - 移到这里 */}
              <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-2">
                <p className="text-[11px] text-blue-700">
                  自动识别文件类型并路由到对应技能。
                </p>
              </div>

              {/* Declarative Skill Section - 手动选择技能 */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                  <div className="w-1 h-4 bg-indigo-600 rounded-full"></div>
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  鎵嬪姩閫夋嫨鎶€鑳?
                </h4>

                <div className="border border-indigo-200 rounded-lg p-3 bg-gradient-to-br from-indigo-50 to-purple-50">
                  <div className="mb-2">
                    <SkillSelector
                      selectedSkill={selectedSkill}
                      onSkillSelect={(skillName) => setSelectedSkill(skillName)}
                      showOnlyDeclarative={true}
                      groupFilter="info_collection"
                      allowedSkills={allowedSkillsForNode}
                    />
                  </div>

                  <button
                    onClick={handleExecuteSkill}
                    disabled={isExecutingSkill || !selectedSkill || !selectedFile?.file}
                    className="w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded shadow-sm transition-colors text-xs font-medium flex items-center justify-center gap-2"
                  >
                    {isExecutingSkill ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        鎵ц涓?..
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        鎵ц鎶€鑳?
                      </>
                    )}
                  </button>

                  {!selectedSkill && (
                    <p className="text-[10px] text-amber-600 mt-1.5 text-center">
                      璇烽€夋嫨涓€涓妧鑳戒互缁х画
                    </p>
                  )}
                </div>
              </div>


              {/* Custom Prompt Configuration */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                    <div className="w-1 h-4 bg-purple-600 rounded-full"></div>
                    <MessageSquare className="w-4 h-4 text-purple-600" />
                    鑷畾涔夋彁绀鸿瘝
                  </h4>
                  <span className="text-[10px] text-slate-500">
                    {customPrompt.trim() ? (
                      <span className="text-green-600">已启用</span>
                    ) : (
                      <span>可选</span>
                    )}
                  </span>
                </div>
                
                <div className="border border-slate-200 rounded-lg bg-white">
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="输入自定义提示词，用于指导AI解析数据。"
                    className="w-full px-3 py-2 text-xs text-slate-700 placeholder:text-slate-400 border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 resize-none leading-relaxed"
                    rows={3}
                  />
                </div>
              </div>

              {/* Additional Options */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                  <div className="w-1 h-4 bg-slate-600 rounded-full"></div>
                  鍏朵粬閫夐」
                </h4>
                
                <div className="space-y-1.5">
                  <label className="flex items-center gap-2 px-2 py-2 bg-slate-50 rounded border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                    <input type="checkbox" className="w-3 h-3 text-blue-600 rounded border-slate-300 focus:ring-0" />
                    <span className="text-xs text-slate-700">鑷姩淇濆瓨鍒嗘瀽缁撴灉</span>
                  </label>
                  
                  <label className="flex items-center gap-2 px-2 py-2 bg-slate-50 rounded border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                    <input type="checkbox" className="w-3 h-3 text-blue-600 rounded border-slate-300 focus:ring-0" />
                    <span className="text-xs text-slate-700">瀵煎嚭涓篍xcel鏍煎紡</span>
                  </label>

                  <label className="flex items-center gap-2 px-2 py-2 bg-slate-50 rounded border border-slate-200 cursor-pointer hover:bg-slate-100 transition-colors">
                    <input type="checkbox" className="w-3 h-3 text-blue-600 rounded border-slate-300 focus:ring-0" defaultChecked />
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
                杈撳嚭鏁版嵁
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
                <p className="font-medium mb-1">鏆傛棤杈撳嚭鏁版嵁</p>
                <p className="text-xs text-center">
                  执行数据分析后
                  <br />
                  结果将显示在此处
                </p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto">

                {selectedFile?.validation_result && (
                  <div className="p-4 pb-0">
                    <h4 className="text-sm font-medium text-slate-700 mb-3">鏍￠獙缁撴灉</h4>
                    {selectedFile.validation_result.errors?.length > 0 && (
                      <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 p-3">
                        <div className="text-xs font-medium text-rose-700 mb-2">閿欒</div>
                        <ul className="text-xs text-rose-700 space-y-1">
                          {selectedFile.validation_result.errors.map((err, idx) => (
                            <li key={idx}>- {err}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {selectedFile.validation_result.warnings?.length > 0 && (
                      <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
                        <div className="text-xs font-medium text-amber-700 mb-2">璀﹀憡</div>
                        <ul className="text-xs text-amber-700 space-y-1">
                          {selectedFile.validation_result.warnings.map((warn, idx) => (
                            <li key={idx}>- {warn}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* JSON Data Display */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium text-slate-700">璇嗗埆缁撴灉</h4>
                    <div className="flex bg-slate-100 rounded-lg p-0.5 border border-slate-200">
                        <button
                          onClick={() => setViewMode('form')}
                          className={`px-3 py-1 text-xs font-medium rounded-md flex items-center gap-1.5 transition-all ${
                            viewMode === 'form' 
                              ? 'bg-white text-blue-600 shadow-sm ring-1 ring-black/5' 
                              : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
                          }`}
                        >
                          <LayoutList className="w-3.5 h-3.5" />
                          琛ㄥ崟
                        </button>
                        <button
                          onClick={() => setViewMode('json')}
                          className={`px-3 py-1 text-xs font-medium rounded-md flex items-center gap-1.5 transition-all ${
                            viewMode === 'json' 
                              ? 'bg-white text-blue-600 shadow-sm ring-1 ring-black/5' 
                              : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
                          }`}
                        >
                          <Code className="w-3.5 h-3.5" />
                          浠ｇ爜
                        </button>
                    </div>
                  </div>
                  
                  {viewMode === 'form' ? (
                     <div className="space-y-4">
                        {Array.isArray(analysisResult.jsonData) && analysisResult.jsonData.length > 0 ? (
                           <>
                              {(selectedFile ? (selectedJsonItem ? [selectedJsonItem] : []) : analysisResult.jsonData)
                                .map((item: any, index: number) => (
                                   <div key={item.fileId || index}>
                                      {renderFormView(item.fileId || String(index), getJsonText(item.fileId || String(index), item.data))}
                                   </div>
                                ))}
                           </>
                        ) : (
                           <div className="text-center text-slate-400 py-8 text-xs bg-slate-50 rounded-lg border border-slate-200 border-dashed">暂无结构化数据</div>
                        )}
                     </div>
                  ) : (
                    <div className="bg-white rounded-lg p-4 border border-slate-200 overflow-x-auto space-y-4 shadow-inner bg-slate-50/30">
                        {Array.isArray(analysisResult.jsonData) && analysisResult.jsonData.length > 0 ? (
                        <>
                            {(selectedFile ? (selectedJsonItem ? [selectedJsonItem] : []) : analysisResult.jsonData)
                            .map((item: any, index: number) => {
                                const isConfirmed = selectedFile?.confirmed || false;
                                return (
                                <div key={item.fileId || index} className="border border-slate-200 rounded-md p-3 bg-white">
                                    <div className="flex items-center justify-between mb-2">
                                    <div className="text-xs text-slate-500">
                                        文件 {index + 1}：{item.fileName || '未命名文件'}
                                    </div>
                                    {isConfirmed && (
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-50 border border-emerald-200 rounded text-emerald-600 text-xs font-medium">
                                        <CheckCircle className="w-3 h-3" />
                                        已确认
                                        </div>
                                    )}
                                    </div>
                                    <div className="space-y-2">
                                    <textarea
                                        value={getJsonText(item.fileId || String(index), item.data)}
                                        onChange={(e) => handleJsonChange(item.fileId || String(index), e.target.value)}
                                        onBlur={() => handleJsonSave(item.fileId || String(index), getJsonText(item.fileId || String(index), item.data))}
                                        className="w-full min-h-[450px] text-[11px] leading-4 text-slate-800 font-mono whitespace-pre-wrap break-words bg-slate-50 border border-slate-200 rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                                    />
                                    {jsonErrorsByFile[item.fileId || String(index)] && (
                                        <div className="text-xs text-rose-500 mt-1">
                                        {jsonErrorsByFile[item.fileId || String(index)]}
                                        </div>
                                    )}
                                    </div>
                                </div>
                                );
                            })}
                            {selectedFile && Array.isArray(analysisResult.jsonData) && !selectedJsonItem && (
                                <div className="text-xs text-amber-500 mt-2">
                                    请运行声明式技能以处理此文件。
                                </div>
                            )}
                        </>
                        ) : (
                           <>
                           <pre className="text-xs text-slate-700 font-mono whitespace-pre-wrap break-words">
                            {analysisResult.jsonData 
                                ? JSON.stringify(analysisResult.jsonData, null, 2)
                                : '鏆傛棤鏁版嵁'}
                            </pre>
                            {selectedFile && (
                                <div className="text-xs text-amber-500 mt-2">
                                    璇疯繍琛屽０鏄庡紡鎶€鑳戒互澶勭悊姝ゆ枃浠躲€?
                                </div>
                            )}
                           </>
                        )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="mt-4 space-y-2">
                    <button 
                      onClick={handleConfirmResult}
                      disabled={isConfirming || selectedFile?.confirmed}
                      className="w-full px-3 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white border border-transparent rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2 shadow-sm shadow-emerald-200"
                    >
                      <CheckCircle className="w-4 h-4" />
                      {isConfirming
                          ? "淇濆瓨涓?.."
                          : "纭鏃犺"}
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


