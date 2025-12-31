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
    Cell
} from 'recharts';
import { 
    TrendingUp, 
    Users, 
    FileText, 
    Clock, 
    ArrowUpRight,
    ArrowDownRight,
    MoreHorizontal
} from 'lucide-react';

const projectData = [
    { name: '1月', value: 12 },
    { name: '2月', value: 19 },
    { name: '3月', value: 15 },
    { name: '4月', value: 25 },
    { name: '5月', value: 32 },
    { name: '6月', value: 30 },
];

const typeData = [
    { name: '结构安全性', value: 45, color: '#6366f1' }, // Indigo-500
    { name: '抗震鉴定', value: 30, color: '#ec4899' }, // Pink-500
    { name: '施工验收', value: 15, color: '#10b981' }, // Emerald-500
    { name: '其他', value: 10, color: '#f59e0b' }, // Amber-500
];

const recentProjects = [
    { id: 1, name: '某商业中心结构安全性鉴定', type: '结构安全性', date: '2023-06-20', status: '进行中' },
    { id: 2, name: '工业厂房抗震鉴定项目', type: '抗震鉴定', date: '2023-06-18', status: '已完成' },
    { id: 3, name: '住宅楼裂缝专项检测', type: '专项检测', date: '2023-06-15', status: '审核中' },
    { id: 4, name: '钢结构施工质量验收', type: '施工验收', date: '2023-06-12', status: '已完成' },
    { id: 5, name: '历史建筑保护性监测', type: '监测', date: '2023-06-10', status: '进行中' },
];

export default function Dashboard() {
    return (
        <div className="flex-1 overflow-y-auto bg-slate-50 p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">项目概览</h1>
                        <p className="text-slate-500 mt-1">欢迎回来，王工程师。这里是您的项目统计数据。</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-slate-500">统计周期：本月</span>
                        <button className="px-3 py-1.5 bg-white border border-slate-200 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50">
                            导出报表
                        </button>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-slate-500 text-sm font-medium">总项目数</span>
                            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                                <FileText className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-slate-900">128</span>
                            <span className="text-xs font-medium text-green-600 flex items-center">
                                <ArrowUpRight className="w-3 h-3 mr-0.5" />
                                +12%
                            </span>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-slate-500 text-sm font-medium">进行中</span>
                            <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                                <Clock className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-slate-900">12</span>
                            <span className="text-xs font-medium text-slate-400">当前活跃</span>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-slate-500 text-sm font-medium">已完成报告</span>
                            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                                <TrendingUp className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-slate-900">1,024</span>
                            <span className="text-xs font-medium text-green-600 flex items-center">
                                <ArrowUpRight className="w-3 h-3 mr-0.5" />
                                +8%
                            </span>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-slate-500 text-sm font-medium">团队成员</span>
                            <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                                <Users className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-slate-900">8</span>
                            <span className="text-xs font-medium text-slate-400">活跃用户</span>
                        </div>
                    </div>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Bar Chart */}
                    <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h3 className="text-lg font-bold text-slate-800 mb-6">项目趋势</h3>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={projectData}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        cursor={{ fill: '#f1f5f9' }}
                                    />
                                    <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Pie Chart */}
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <h3 className="text-lg font-bold text-slate-800 mb-6">报告类型分布</h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={typeData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
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
                        <div className="space-y-3 mt-4">
                            {typeData.map((item, index) => (
                                <div key={index} className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                        <span className="text-sm text-slate-600">{item.name}</span>
                                    </div>
                                    <span className="text-sm font-medium text-slate-900">{item.value}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Recent Projects Table */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-200 flex items-center justify-between">
                        <h3 className="text-lg font-bold text-slate-800">最近项目</h3>
                        <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">查看全部</button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-50 text-slate-500">
                                <tr>
                                    <th className="px-6 py-3 font-medium">项目名称</th>
                                    <th className="px-6 py-3 font-medium">类型</th>
                                    <th className="px-6 py-3 font-medium">日期</th>
                                    <th className="px-6 py-3 font-medium">状态</th>
                                    <th className="px-6 py-3 font-medium text-right">操作</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200">
                                {recentProjects.map((project) => (
                                    <tr key={project.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-slate-900">{project.name}</td>
                                        <td className="px-6 py-4 text-slate-500">{project.type}</td>
                                        <td className="px-6 py-4 text-slate-500">{project.date}</td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                project.status === '已完成' ? 'bg-green-100 text-green-800' :
                                                project.status === '进行中' ? 'bg-blue-100 text-blue-800' :
                                                'bg-amber-100 text-amber-800'
                                            }`}>
                                                {project.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="text-slate-400 hover:text-slate-600">
                                                <MoreHorizontal className="w-5 h-5" />
                                            </button>
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
