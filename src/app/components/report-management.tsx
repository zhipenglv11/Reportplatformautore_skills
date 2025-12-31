import React, { useState } from 'react';
import { 
    FileText, 
    Eye, 
    Edit3, 
    Download, 
    Trash2, 
    Clock, 
    CheckCircle2, 
    AlertCircle,
    Search,
    MoreHorizontal,
    X,
    AlertTriangle
} from 'lucide-react';

interface Report {
    id: string;
    name: string;
    version: string;
    createdAt: string;
    updatedAt: string;
    status: 'draft' | 'completed' | 'reviewing';
    author: string;
    size: string;
}

interface ReportManagementProps {
    projectId?: string;
}

export default function ReportManagement({ projectId }: ReportManagementProps) {
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState<string>('all');
    const [deletingReport, setDeletingReport] = useState<Report | null>(null);
    
    // 模拟报告历史数据
    const [reports, setReports] = useState<Report[]>([
        {
            id: '1',
            name: '房屋安全鉴定报告',
            version: 'V1.0',
            createdAt: '2024-12-28 14:30',
            updatedAt: '2024-12-28 16:45',
            status: 'completed',
            author: '王工',
            size: '2.4 MB'
        },
        {
            id: '2',
            name: '房屋安全鉴定报告',
            version: 'V0.9',
            createdAt: '2024-12-27 10:15',
            updatedAt: '2024-12-27 15:20',
            status: 'completed',
            author: '王工',
            size: '2.1 MB'
        },
        {
            id: '3',
            name: '房屋安全鉴定报告',
            version: 'V0.8',
            createdAt: '2024-12-26 09:00',
            updatedAt: '2024-12-26 11:30',
            status: 'draft',
            author: '李工',
            size: '1.8 MB'
        },
        {
            id: '4',
            name: '结构检测分析报告',
            version: 'V1.0',
            createdAt: '2024-12-25 16:00',
            updatedAt: '2024-12-25 18:00',
            status: 'reviewing',
            author: '张工',
            size: '3.2 MB'
        },
        {
            id: '5',
            name: '抗震性能评估报告',
            version: 'V0.5',
            createdAt: '2024-12-20 11:00',
            updatedAt: '2024-12-22 14:30',
            status: 'draft',
            author: '王工',
            size: '1.5 MB'
        },
    ]);

    const getStatusBadge = (status: Report['status']) => {
        switch (status) {
            case 'completed':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                        <CheckCircle2 className="w-3 h-3" />
                        已完成
                    </span>
                );
            case 'draft':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200">
                        <Clock className="w-3 h-3" />
                        草稿
                    </span>
                );
            case 'reviewing':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                        <AlertCircle className="w-3 h-3" />
                        审核中
                    </span>
                );
        }
    };

    const filteredReports = reports.filter(report => {
        const matchesSearch = report.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             report.version.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filterStatus === 'all' || report.status === filterStatus;
        return matchesSearch && matchesFilter;
    });

    const handleView = (report: Report) => {
        console.log('查看报告:', report.name, report.version);
        // TODO: 实现查看功能
    };

    const handleEdit = (report: Report) => {
        console.log('编辑报告:', report.name, report.version);
        // TODO: 实现编辑功能
    };

    const handleDownload = (report: Report) => {
        console.log('下载报告:', report.name, report.version);
        // TODO: 实现下载功能
    };

    const handleDelete = (report: Report) => {
        setDeletingReport(report);
    };

    const confirmDelete = () => {
        if (deletingReport) {
            setReports(prev => prev.filter(r => r.id !== deletingReport.id));
            setDeletingReport(null);
        }
    };

    const cancelDelete = () => {
        setDeletingReport(null);
    };

    return (
        <div className="h-full flex flex-col bg-slate-50">
            {/* Header - 紧凑的单行布局 */}
            <div className="px-6 py-3 bg-white border-b border-slate-200 flex items-center justify-between">
                {/* 标题和数量 */}
                <div className="flex items-center gap-3 flex-shrink-0">
                    <h2 className="text-sm font-semibold text-slate-900">生成记录</h2>
                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                        {filteredReports.length} 份
                    </span>
                </div>

                {/* 右侧：搜索和筛选 */}
                <div className="flex items-center gap-3">
                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="搜索报告..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-48 pl-8 pr-3 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-slate-300 focus:border-slate-300"
                        />
                    </div>

                    {/* Filter */}
                    <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="px-2.5 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-slate-300 focus:border-slate-300 bg-white text-slate-600"
                    >
                        <option value="all">全部</option>
                        <option value="completed">已完成</option>
                        <option value="draft">草稿</option>
                        <option value="reviewing">审核中</option>
                    </select>
                </div>
            </div>

            {/* Report List */}
            <div className="flex-1 overflow-y-auto p-6">
                {filteredReports.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                        <FileText className="w-12 h-12 text-slate-300 mb-3" />
                        <p className="text-sm">暂无报告记录</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {filteredReports.map((report) => (
                            <div
                                key={report.id}
                                className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3">
                                        <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                                            <FileText className="w-5 h-5 text-slate-600" />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h3 className="text-sm font-medium text-slate-900">{report.name}</h3>
                                                <span className="text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{report.version}</span>
                                            </div>
                                            <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                                                <span>创建: {report.createdAt}</span>
                                                <span>更新: {report.updatedAt}</span>
                                                <span>作者: {report.author}</span>
                                                <span>{report.size}</span>
                                            </div>
                                            <div className="mt-2">
                                                {getStatusBadge(report.status)}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-1">
                                        <button
                                            onClick={() => handleView(report)}
                                            className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                            title="阅览"
                                        >
                                            <Eye className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleEdit(report)}
                                            className="p-2 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                                            title="编辑"
                                        >
                                            <Edit3 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDownload(report)}
                                            className="p-2 text-slate-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                            title="下载"
                                        >
                                            <Download className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(report)}
                                            className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                            title="删除"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                                            title="更多操作"
                                        >
                                            <MoreHorizontal className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* 删除确认弹窗 */}
            {deletingReport && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 animate-in fade-in zoom-in-95 duration-200">
                        {/* 弹窗头部 */}
                        <div className="flex items-center justify-between p-4 border-b border-slate-200">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                                    <AlertTriangle className="w-5 h-5 text-red-600" />
                                </div>
                                <h3 className="text-lg font-semibold text-slate-900">确认删除</h3>
                            </div>
                            <button
                                onClick={cancelDelete}
                                className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* 弹窗内容 */}
                        <div className="p-6">
                            <p className="text-slate-600 mb-4">
                                您确定要删除以下报告吗？此操作无法撤销。
                            </p>
                            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                                <div className="flex items-center gap-3">
                                    <FileText className="w-8 h-8 text-slate-400" />
                                    <div>
                                        <p className="font-medium text-slate-900">{deletingReport.name}</p>
                                        <p className="text-sm text-slate-500">
                                            {deletingReport.version} · {deletingReport.author} · {deletingReport.size}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 弹窗按钮 */}
                        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-200 bg-slate-50 rounded-b-xl">
                            <button
                                onClick={cancelDelete}
                                className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 rounded-lg transition-colors"
                            >
                                取消
                            </button>
                            <button
                                onClick={confirmDelete}
                                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                            >
                                确认删除
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

