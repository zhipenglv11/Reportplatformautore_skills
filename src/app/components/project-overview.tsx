import { useState } from "react";
import {
    TrendingUp,
    FileText,
    Clock,
    BarChart3,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from "recharts";

interface ProjectOverviewProps {
    isCollapsed?: boolean;
}

const projectData = [
    { name: '1月', value: 12 },
    { name: '2月', value: 19 },
    { name: '3月', value: 15 },
    { name: '4月', value: 25 },
    { name: '5月', value: 32 },
    { name: '6月', value: 30 },
];

const typeData = [
    { name: '结构安全性', value: 45, color: '#6366f1' },
    { name: '抗震鉴定', value: 30, color: '#ec4899' },
    { name: '施工验收', value: 15, color: '#10b981' },
    { name: '其他', value: 10, color: '#f59e0b' },
];

const recentProjects = [
    { id: 1, name: '某商业中心结构安全性鉴定', type: '结构安全性', date: '2024-12-30', status: '进行中' },
    { id: 2, name: '工业厂房抗震鉴定项目', type: '抗震鉴定', date: '2024-12-28', status: '已完成' },
    { id: 3, name: '住宅楼裂缝专项检测', type: '专项检测', date: '2024-12-25', status: '审核中' },
    { id: 4, name: '钢结构施工质量验收', type: '施工验收', date: '2024-12-22', status: '已完成' },
    { id: 5, name: '历史建筑保护性监测', type: '监测', date: '2024-12-20', status: '进行中' },
];

export function ProjectOverview({ isCollapsed = false }: ProjectOverviewProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (isCollapsed) {
        return null;
    }

    const totalProjects = 156;
    const activeProjects = 23;
    const completedProjects = 98;
    const avgCompletionTime = 12;

    return (
        <div className="mb-3">
            {/* Overview Card */}
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                {/* Header */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full flex items-center justify-between p-3 hover:bg-slate-50 transition-colors"
                >
                    <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-slate-600" />
                        <span className="text-sm font-semibold text-slate-700">项目概览</span>
                    </div>
                    {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                </button>

                {/* Stats Summary - Always Visible */}
                <div className="px-3 pb-3 grid grid-cols-2 gap-2">
                    <div className="bg-slate-50 rounded-md p-2">
                        <div className="flex items-center gap-1.5 mb-1">
                            <FileText className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-xs text-slate-500">总项目</span>
                        </div>
                        <div className="text-lg font-bold text-slate-800">{totalProjects}</div>
                    </div>
                    <div className="bg-slate-50 rounded-md p-2">
                        <div className="flex items-center gap-1.5 mb-1">
                            <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                            <span className="text-xs text-slate-500">进行中</span>
                        </div>
                        <div className="text-lg font-bold text-emerald-600">{activeProjects}</div>
                    </div>
                    <div className="bg-slate-50 rounded-md p-2">
                        <div className="flex items-center gap-1.5 mb-1">
                            <Clock className="w-3.5 h-3.5 text-blue-500" />
                            <span className="text-xs text-slate-500">已完成</span>
                        </div>
                        <div className="text-lg font-bold text-blue-600">{completedProjects}</div>
                    </div>
                    <div className="bg-slate-50 rounded-md p-2">
                        <div className="flex items-center gap-1.5 mb-1">
                            <Clock className="w-3.5 h-3.5 text-amber-500" />
                            <span className="text-xs text-slate-500">平均周期</span>
                        </div>
                        <div className="text-lg font-bold text-amber-600">{avgCompletionTime}天</div>
                    </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                    <div className="border-t border-slate-200 p-3 space-y-4 animate-in slide-in-from-top-2 duration-200">
                        {/* Mini Bar Chart */}
                        <div>
                            <h4 className="text-xs font-semibold text-slate-700 mb-2">项目趋势</h4>
                            <div className="h-32">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={projectData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                        <XAxis
                                            dataKey="name"
                                            axisLine={false}
                                            tickLine={false}
                                            tick={{ fill: '#64748b', fontSize: 10 }}
                                            dy={5}
                                        />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: '#fff',
                                                borderRadius: '6px',
                                                border: '1px solid #e2e8f0',
                                                fontSize: '12px',
                                                padding: '4px 8px',
                                            }}
                                            cursor={{ fill: '#f1f5f9' }}
                                        />
                                        <Bar dataKey="value" fill="#6366f1" radius={[2, 2, 0, 0]} barSize={20} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Mini Pie Chart */}
                        <div>
                            <h4 className="text-xs font-semibold text-slate-700 mb-2">报告类型分布</h4>
                            <div className="h-32">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={typeData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={25}
                                            outerRadius={45}
                                            paddingAngle={2}
                                            dataKey="value"
                                        >
                                            {typeData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: '#fff',
                                                borderRadius: '6px',
                                                border: '1px solid #e2e8f0',
                                                fontSize: '12px',
                                            }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="flex flex-wrap gap-2 mt-2">
                                {typeData.map((item, index) => (
                                    <div key={index} className="flex items-center gap-1.5">
                                        <div
                                            className="w-2 h-2 rounded-full"
                                            style={{ backgroundColor: item.color }}
                                        />
                                        <span className="text-xs text-slate-600">{item.name}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Recent Projects Table */}
                        <div>
                            <h4 className="text-xs font-semibold text-slate-700 mb-2">最近项目</h4>
                            <div className="space-y-1.5 max-h-32 overflow-y-auto">
                                {recentProjects.slice(0, 3).map((project) => (
                                    <div
                                        key={project.id}
                                        className="flex items-center justify-between p-2 bg-slate-50 rounded-md hover:bg-slate-100 transition-colors cursor-pointer"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <div className="text-xs font-medium text-slate-700 truncate">
                                                {project.name}
                                            </div>
                                            <div className="flex items-center gap-2 mt-0.5">
                                                <span className="text-[10px] text-slate-500">{project.type}</span>
                                                <span className="text-[10px] text-slate-400">•</span>
                                                <span className="text-[10px] text-slate-500">{project.date}</span>
                                            </div>
                                        </div>
                                        <span
                                            className={`text-[10px] px-1.5 py-0.5 rounded ${
                                                project.status === '已完成'
                                                    ? 'bg-emerald-100 text-emerald-700'
                                                    : project.status === '进行中'
                                                    ? 'bg-blue-100 text-blue-700'
                                                    : 'bg-amber-100 text-amber-700'
                                            }`}
                                        >
                                            {project.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

