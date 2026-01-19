import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, ArrowRight, FileCheck, FileX, Scale } from 'lucide-react';

interface FileUpload {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  category: 'raw_record' | 'inspection_report';
}

interface ReviewResult {
    summary: string;
    overall_status: string;
    details: any;
    mode: string;
}

export default function RawRecordReviewPanel() {
  const [rawFiles, setRawFiles] = useState<FileUpload[]>([]);
  const [reportFiles, setReportFiles] = useState<FileUpload[]>([]);
  const [isReviewing, setIsReviewing] = useState(false);
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);

  const rawInputRef = useRef<HTMLInputElement>(null);
  const reportInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, category: 'raw_record' | 'inspection_report') => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).map(file => ({
        file,
        id: Math.random().toString(36).substring(7),
        status: 'pending' as const,
        category
      }));
      
      if (category === 'raw_record') {
        setRawFiles(prev => [...prev, ...newFiles]);
      } else {
        setReportFiles(prev => [...prev, ...newFiles]);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent, category: 'raw_record' | 'inspection_report') => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files) {
      const newFiles = Array.from(e.dataTransfer.files).map(file => ({
        file,
        id: Math.random().toString(36).substring(7),
        status: 'pending' as const,
        category
      }));

      if (category === 'raw_record') {
        setRawFiles(prev => [...prev, ...newFiles]);
      } else {
        setReportFiles(prev => [...prev, ...newFiles]);
      }
    }
  };

  const removeFile = (id: string, category: 'raw_record' | 'inspection_report') => {
    if (category === 'raw_record') {
      setRawFiles(prev => prev.filter(f => f.id !== id));
    } else {
      setReportFiles(prev => prev.filter(f => f.id !== id));
    }
  };

  const startReview = async () => {
    if (rawFiles.length === 0 && reportFiles.length === 0) return;

    setIsReviewing(true);
    setReviewResult(null);

    const formData = new FormData();
    rawFiles.forEach(f => formData.append('raw_files', f.file));
    reportFiles.forEach(f => formData.append('report_files', f.file));

    try {
      const response = await fetch('/api/review/review', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Review failed');
      }

      const data = await response.json();
      setReviewResult(data);
    } catch (error) {
      console.error('Review error:', error);
      // Here you might want to set an error state to show to the user
    } finally {
      setIsReviewing(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4 relative min-h-[40px]">
        {/* Left: Description (Smaller font) */}
        <p className="text-xs text-slate-400 max-w-[200px] leading-relaxed">
          上传原始记录与鉴定报告，<br/>自动比对一致性及合规性
        </p>

        {/* Center: Upload Buttons (Centered Absolutely) */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center gap-4">
             {/* Raw Record Upload Button */}
            <div 
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border border-dashed border-indigo-300 cursor-pointer transition-colors
                ${rawFiles.length === 0 ? 'bg-indigo-50/50' : 'bg-white'}
                hover:bg-indigo-50 hover:border-indigo-400`}
              onClick={() => rawInputRef.current?.click()}
            >
              <input 
                type="file" 
                multiple 
                className="hidden" 
                ref={rawInputRef}
                onChange={(e) => handleFileSelect(e, 'raw_record')}
              />
              <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
                <Upload className="w-3 h-3 text-indigo-600" />
              </div>
              <span className="text-xs font-medium text-slate-700">上传原始记录</span>
             </div>

             {/* Inspection Report Upload Button */}
             <div 
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border border-dashed border-emerald-300 cursor-pointer transition-colors
                ${reportFiles.length === 0 ? 'bg-emerald-50/50' : 'bg-white'}
                hover:bg-emerald-50 hover:border-emerald-400`}
              onClick={() => reportInputRef.current?.click()}
            >
              <input 
                type="file" 
                multiple 
                className="hidden" 
                ref={reportInputRef}
                onChange={(e) => handleFileSelect(e, 'inspection_report')}
              />
              <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                <Upload className="w-3 h-3 text-emerald-600" />
              </div>
              <span className="text-xs font-medium text-slate-700">上传鉴定报告</span>
            </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center">
            <button
            onClick={startReview}
            disabled={isReviewing || (rawFiles.length === 0 && reportFiles.length === 0)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium text-white transition-all
                ${(isReviewing || (rawFiles.length === 0 && reportFiles.length === 0))
                ? 'bg-slate-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-200 hover:shadow-indigo-300 transform active:scale-95'
                }`}
            >
            {isReviewing ? (
                <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>审核中...</span>
                </>
            ) : (
                <>
                <FileCheck className="w-4 h-4" />
                <span>开始审核</span>
                </>
            )}
            </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-6 min-h-0 overflow-hidden">
        {/* Left Column: File Lists (Hidden when empty) */}
        {(rawFiles.length > 0 || reportFiles.length > 0) && (
            <div className="col-span-12 lg:col-span-3 flex flex-col gap-4 overflow-y-auto pr-2">
            
            {/* Raw Record List */}
            {rawFiles.length > 0 && (
                <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4">
                <div className="flex items-center gap-2 text-indigo-700 font-semibold mb-3">
                        <FileText className="w-4 h-4" />
                        <span className="text-sm">原始记录 ({rawFiles.length})</span>
                    </div>
                    <div className="space-y-2">
                        {rawFiles.map(file => (
                        <div key={file.id} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100 text-sm group">
                            <span className="truncate flex-1 text-slate-700">{file.file.name}</span>
                            <button 
                            onClick={() => removeFile(file.id, 'raw_record')}
                            className="text-slate-400 hover:text-red-500 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                            <FileX className="w-4 h-4" />
                            </button>
                        </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Inspection Report List */}
            {reportFiles.length > 0 && (
                <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-4">
                    <div className="flex items-center gap-2 text-emerald-700 font-semibold mb-3">
                        <FileText className="w-4 h-4" />
                        <span className="text-sm">鉴定报告 ({reportFiles.length})</span>
                    </div>
                    <div className="space-y-2">
                        {reportFiles.map(file => (
                        <div key={file.id} className="flex items-center justify-between p-2 bg-slate-50 rounded border border-slate-100 text-sm group">
                            <span className="truncate flex-1 text-slate-700">{file.file.name}</span>
                            <button 
                            onClick={() => removeFile(file.id, 'inspection_report')}
                            className="text-slate-400 hover:text-red-500 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                            <FileX className="w-4 h-4" />
                            </button>
                        </div>
                        ))}
                    </div>
                </div>
            )}
            </div>
        )}

        {/* Results Area (Full width when no files, else partial) */}
        <div className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col min-h-0
            ${rawFiles.length > 0 || reportFiles.length > 0 ? 'col-span-12 lg:col-span-9' : 'col-span-12'}`}>
          <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
            <h3 className="font-semibold text-slate-800 flex items-center gap-2">
              <Scale className="w-5 h-5 text-slate-500" />
              审核结果
            </h3>
            {reviewResult && (
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium border
                    ${reviewResult.overall_status === 'pass' 
                        ? 'bg-green-50 text-green-700 border-green-200' 
                        : reviewResult.overall_status === 'warning'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-red-50 text-red-700 border-red-200'
                    }`}>
                    {reviewResult.overall_status === 'pass' ? '通过' : reviewResult.overall_status === 'warning' ? '存在警告' : '不通过'}
                </span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {!reviewResult ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-4">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
                   <ArrowRight className="w-8 h-8 text-slate-300" />
                </div>
                <p>请上传文件并点击"开始审核"查看结果</p>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* Summary Section */}
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <h4 className="text-sm font-semibold text-slate-900 mb-2">执行摘要</h4>
                    <p className="text-slate-600 text-sm leading-relaxed">{reviewResult.summary}</p>
                    <div className="mt-2 text-xs text-slate-500">模式: {reviewResult.mode}</div>
                </div>

                {/* Details Section */}
                {reviewResult.details && (
                    <div className="space-y-4">
                        {reviewResult.mode === 'cross_check' ? (
                             // Cross Check specific view
                             <div className="grid grid-cols-1 gap-4">
                                {reviewResult.details.consistency_check?.length > 0 && (
                                    <div className="border border-red-100 bg-red-50 rounded-lg p-4">
                                        <h5 className="text-red-800 font-medium mb-2 flex items-center gap-2">
                                            <AlertCircle className="w-4 h-4"/> 一致性问题
                                        </h5>
                                        <ul className="space-y-2">
                                            {reviewResult.details.consistency_check.map((issue: any, idx: number) => (
                                                <li key={idx} className="text-sm text-red-700 bg-white/50 p-2 rounded">
                                                    {issue.message} (原始: <span className='font-mono'>{issue.raw_value}</span> vs 报告: <span className='font-mono'>{issue.report_value}</span>)
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {/* More details for raw and report findings... */}
                             </div>
                        ) : (
                            // Single mode view
                            <div className="space-y-3">
                                {Array.isArray(reviewResult.details) && reviewResult.details.map((fileRes: any, idx: number) => (
                                    <div key={idx} className="border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-slate-700">{fileRes.file_name}</span>
                                            {fileRes.issues?.length > 0 ? (
                                                <span className="text-amber-600 text-xs flex items-center gap-1"><AlertCircle className="w-3 h-3"/> {fileRes.issues.length} 个问题</span>
                                            ) : (
                                                <span className="text-green-600 text-xs flex items-center gap-1"><CheckCircle className="w-3 h-3"/> 通过</span>
                                            )}
                                        </div>
                                        {fileRes.issues?.length > 0 && (
                                            <ul className="space-y-1 mt-2">
                                                {fileRes.issues.map((issue: string, i: number) => (
                                                    <li key={i} className="text-xs text-slate-600 flex items-start gap-2">
                                                        <span className="w-1 h-1 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                                                        {issue}
                                                    </li>
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
                
                {/* Fallback JSON view for debugging or unhandled structure */}
                <details className="text-xs text-slate-400 mt-8">
                    <summary className="cursor-pointer hover:text-slate-600">查看原始JSON响应</summary>
                    <pre className="bg-slate-100 p-4 rounded mt-2 overflow-auto max-h-60">
                        {JSON.stringify(reviewResult, null, 2)}
                    </pre>
                </details>

              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
