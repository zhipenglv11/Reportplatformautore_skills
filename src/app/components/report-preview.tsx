import React from 'react';
import { FileText, Share2, Download, Copy, X } from 'lucide-react';

interface ReportPreviewProps {
    isGenerating?: boolean;
    chapters?: Array<{
        chapter_id: string;
        title: string;
        chapter_content: {
            blocks: Array<any>;
        };
    }>;
    onClose?: () => void;
}

export function ReportPreview({ isGenerating = false, chapters = [], onClose }: ReportPreviewProps) {
    return (
        <div className="h-full flex flex-col bg-slate-50 min-h-0 w-full relative">
            <style>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 8px;
                    height: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #cbd5e1;
                    border-radius: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #94a3b8;
                }
            `}</style>

            <div className="flex-none flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white z-10">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-slate-100 rounded-md">
                        <FileText className="w-4 h-4 text-slate-600" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-slate-800">
                            {isGenerating ? 'AI 正在生成报告...' : '报告预览'}
                        </h3>
                        <p className="text-xs text-slate-500">
                            {isGenerating ? '请稍候' : '展示表格与文本块'}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                    {!isGenerating && (
                        <>
                            <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="复制">
                                <Copy className="w-4 h-4" />
                            </button>
                            <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="下载">
                                <Download className="w-4 h-4" />
                            </button>
                            <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="分享">
                                <Share2 className="w-4 h-4" />
                            </button>
                        </>
                    )}
                    {onClose && (
                        <>
                            <div className="h-4 w-px bg-slate-200 mx-1" />
                            <button
                                onClick={onClose}
                                className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors"
                                title="关闭预览"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto bg-white min-h-0 custom-scrollbar">
                <div className="w-full bg-white min-h-full px-8 py-8">
                    {isGenerating ? (
                        <div className="space-y-4">
                            <div className="h-5 bg-slate-100 rounded w-1/3 animate-pulse"></div>
                            <div className="h-24 bg-slate-100 rounded animate-pulse"></div>
                            <div className="h-24 bg-slate-100 rounded animate-pulse"></div>
                        </div>
                    ) : chapters.length > 0 ? (
                        <div className="space-y-8">
                            {chapters.map((chapter) => (
                                <section key={chapter.chapter_id} className="space-y-3">
                                    <h2 className="text-base font-semibold text-slate-800">
                                        {chapter.title}
                                    </h2>
                                    <div className="space-y-4">
                                        {(chapter.chapter_content?.blocks || []).map((block: any, index: number) => {
                                            if (block.type === "note") {
                                                return (
                                                    <div
                                                        key={`${chapter.chapter_id}-note-${index}`}
                                                        className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700"
                                                    >
                                                        {block.text || "暂无提示"}
                                                    </div>
                                                );
                                            }

                                            if (block.type === "table") {
                                                const columns = block.columns || [];
                                                const rows = block.rows || [];
                                                return (
                                                    <div key={`${chapter.chapter_id}-table-${index}`} className="space-y-2">
                                                        <div className="text-xs font-medium text-slate-600">
                                                            {block.title || "表格"}
                                                        </div>
                                                        <div className="overflow-x-auto">
                                                            <table className="w-full text-xs border-collapse border border-slate-200">
                                                                <thead>
                                                                    <tr className="bg-slate-100">
                                                                        {columns.map((col: any) => (
                                                                            <th
                                                                                key={col.key}
                                                                                className="border border-slate-200 px-2 py-1 text-left font-semibold text-slate-600"
                                                                            >
                                                                                {col.label}
                                                                            </th>
                                                                        ))}
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    {rows.length > 0 ? (
                                                                        rows.map((row: any, rowIndex: number) => (
                                                                            <tr key={rowIndex} className="odd:bg-white even:bg-slate-50">
                                                                                {columns.map((col: any) => (
                                                                                    <td key={col.key} className="border border-slate-200 px-2 py-1 text-slate-700">
                                                                                        {row[col.key] ?? ""}
                                                                                    </td>
                                                                                ))}
                                                                            </tr>
                                                                        ))
                                                                    ) : (
                                                                        <tr>
                                                                            <td colSpan={columns.length || 1} className="border border-slate-200 px-2 py-3 text-center text-slate-400">
                                                                                暂无数据
                                                                            </td>
                                                                        </tr>
                                                                    )}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </div>
                                                );
                                            }

                                            if (block.type === "text") {
                                                return (
                                                    <p
                                                        key={`${chapter.chapter_id}-text-${index}`}
                                                        className="text-xs leading-6 text-slate-900"
                                                    >
                                                        {block.text || "暂无文本"}
                                                    </p>
                                                );
                                            }

                                            return null;
                                        })}
                                    </div>
                                </section>
                            ))}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center text-slate-400 py-16">
                            <div className="text-sm font-medium">暂无预览数据</div>
                            <div className="text-xs mt-1">请先生成报告章节</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
