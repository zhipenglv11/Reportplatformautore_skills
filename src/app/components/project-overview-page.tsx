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
import {
    TrendingUp,
    FileText,
    Clock,
    ArrowUpRight,
    ArrowLeft,
} from "lucide-react";

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

interface ProjectOverviewPageProps {
    onBack?: () => void;
}

export function ProjectOverviewPage({ onBack }: ProjectOverviewPageProps) {
    const totalProjects = 156;
    const activeProjects = 23;
    const completedProjects = 98;
    const avgCompletionTime = 12;

    return (
        <div className="flex-1 overflow-y-auto bg-slate-50 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        {onBack && (
                            <button
                                onClick={onBack}
                                className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-colors shadow-sm"
                                title="返回"
                            >
                                <ArrowLeft className="w-4 h-4" />
                            </button>
                        )}
                        <div>
                            <h1 className="text-lg font-bold text-slate-900">项目概览</h1>
                            <p className="text-xs text-slate-500 mt-0.5">欢迎回来，王工程师。这里是您的项目统计数据。</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">统计周期：本月</span>
                        <button className="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-50">
                            导出报表
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-slate-500 text-xs font-medium">总项目数</span>
                            <div className="p-1.5 bg-blue-50 text-blue-600 rounded-md">
                                <FileText className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold text-slate-900">{totalProjects}</span>
                            <span className="text-[10px] font-medium text-green-600 flex items-center">
                                <ArrowUpRight className="w-2.5 h-2.5 mr-0.5" />
                                +12%
                            </span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-slate-500 text-xs font-medium">进行中</span>
                            <div className="p-1.5 bg-amber-50 text-amber-600 rounded-md">
                                <Clock className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold text-slate-900">{activeProjects}</span>
                            <span className="text-[10px] font-medium text-slate-400">当前活跃</span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-slate-500 text-xs font-medium">已完成报告</span>
                            <div className="p-1.5 bg-emerald-50 text-emerald-600 rounded-md">
                                <TrendingUp className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold text-slate-900">{completedProjects}</span>
                            <span className="text-[10px] font-medium text-green-600 flex items-center">
                                <ArrowUpRight className="w-2.5 h-2.5 mr-0.5" />
                                +8%
                            </span>
                        </div>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                            <span className="text-slate-500 text-xs font-medium">平均周期</span>
                            <div className="p-1.5 bg-purple-50 text-purple-600 rounded-md">
                                <Clock className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold text-slate-900">{avgCompletionTime}</span>
                            <span className="text-[10px] font-medium text-slate-400">天</span>
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Bar Chart */}
                    <div className="lg:col-span-2 bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <h3 className="text-sm font-bold text-slate-800 mb-4">项目趋势</h3>
                        <div className="h-56">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={projectData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} dy={8} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#fff', borderRadius: '6px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '12px' }}
                                        cursor={{ fill: '#f1f5f9' }}
                                    />
                                    <Bar dataKey="value" fill="#6366f1" radius={[3, 3, 0, 0]} barSize={28} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Pie Chart */}
                    <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                        <h3 className="text-sm font-bold text-slate-800 mb-4">报告类型分布</h3>
                        <div className="h-44">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={typeData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={45}
                                        outerRadius={60}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {typeData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="space-y-2 mt-3">
                            {typeData.map((item, index) => (
                                <div key={index} className="flex items-center justify-between">
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                                        <span className="text-xs text-slate-600">{item.name}</span>
                                    </div>
                                    <span className="text-xs font-medium text-slate-900">{item.value}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Recent Projects Table */}
                <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                        <h3 className="text-sm font-bold text-slate-800">最近项目</h3>
                        <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">查看全部</button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-50 text-slate-500">
                                <tr>
                                    <th className="px-4 py-2.5 font-medium">项目名称</th>
                                    <th className="px-4 py-2.5 font-medium">类型</th>
                                    <th className="px-4 py-2.5 font-medium">日期</th>
                                    <th className="px-4 py-2.5 font-medium">状态</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200">
                                {recentProjects.map((project) => (
                                    <tr key={project.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-4 py-3 font-medium text-slate-900">{project.name}</td>
                                        <td className="px-4 py-3 text-slate-500">{project.type}</td>
                                        <td className="px-4 py-3 text-slate-500">{project.date}</td>
                                        <td className="px-4 py-3">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                                                project.status === '已完成' ? 'bg-green-100 text-green-800' :
                                                project.status === '进行中' ? 'bg-blue-100 text-blue-800' :
                                                'bg-amber-100 text-amber-800'
                                            }`}>
                                                {project.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

