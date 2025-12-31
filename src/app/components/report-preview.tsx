import React from 'react';
import { Sparkles, FileText, Share2, Download, Copy, ThumbsUp, ThumbsDown, X } from 'lucide-react';


interface ReportPreviewProps {
    isGenerating?: boolean;
    onClose?: () => void;
}

export function ReportPreview({ isGenerating = false, onClose }: ReportPreviewProps) {
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
                @keyframes writing {
                    0% { width: 0; opacity: 0.5; }
                    50% { width: 100%; opacity: 1; }
                    100% { opacity: 0.5; }
                }
                .animate-writing {
                    animation: writing 2s ease-in-out infinite;
                }
            `}</style>

            {/* Toolbar */}
            <div className="flex-none flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white z-10">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-slate-100 rounded-md">
                        <FileText className="w-4 h-4 text-slate-600" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-slate-800">
                            {isGenerating ? 'AI 正在生成报告...' : '房屋安全鉴定报告'}
                        </h3>
                        <p className="text-xs text-slate-500">
                            {isGenerating ? '请稍候' : '生成于 2 分钟前'}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-1">
                {!isGenerating && (
                        <>
                            <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="历史记录">
                            <span className="sr-only">历史记录</span>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                        </button>
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

            {/* Document Content */}
            <div className="flex-1 overflow-y-auto bg-white min-h-0 custom-scrollbar">
                <div
                    className="w-full bg-white min-h-full px-8 py-10 transition-all duration-500"
                >
                    {isGenerating ? (
                        <div className="space-y-12 animate-in fade-in duration-700">
                            {/* Header Skeleton */}
                            <div className="space-y-4">
                                <div className="h-10 bg-slate-100 rounded-lg w-3/4 animate-pulse"></div>
                                <div className="flex gap-4">
                                    <div className="h-6 bg-slate-100 rounded-full w-24 animate-pulse"></div>
                                    <div className="h-6 bg-slate-100 rounded w-40 animate-pulse"></div>
                                </div>
                            </div>

                            {/* Writing Animation Lines */}
                            <div className="space-y-8">
                                {[1, 2, 3].map((section) => (
                                    <div key={section} className="space-y-4">
                                        <div className="h-8 bg-slate-100 rounded w-1/3 animate-pulse"></div>
                                        <div className="space-y-2">
                                            <div className="h-4 bg-slate-100 rounded w-full animate-writing" style={{ animationDelay: `${section * 0.2}s` }}></div>
                                            <div className="h-4 bg-slate-100 rounded w-11/12 animate-writing" style={{ animationDelay: `${section * 0.3}s` }}></div>
                                            <div className="h-4 bg-slate-100 rounded w-full animate-writing" style={{ animationDelay: `${section * 0.4}s` }}></div>
                                            <div className="h-4 bg-slate-100 rounded w-4/5 animate-writing" style={{ animationDelay: `${section * 0.5}s` }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="animate-in fade-in duration-500 prose prose-slate prose-sm max-w-none">
                            <h1 className="text-center text-xl font-bold mb-2">房屋安全鉴定报告</h1>
                            <p className="text-center text-sm text-slate-600 mb-1">房屋名称：丽华园 44 号楼</p>
                            <p className="text-center text-sm text-slate-600 mb-1">委托单位：昆山高新技术产业开发区青阳城市管理办事处</p>
                            <p className="text-center text-sm text-slate-600 mb-4">报告编号：FW-24-0279</p>
                            <p className="text-center text-sm text-slate-600 mb-8">昆山市房屋安全鉴定管理站</p>
                            
                            <hr className="my-6" />

                            <h2 className="text-base font-bold mt-6 mb-3">一、基本情况</h2>
                            <p className="text-sm leading-relaxed mb-2">委托方：昆山高新技术产业开发区青阳城市管理办事处</p>
                            <p className="text-sm leading-relaxed mb-2">鉴定对象：丽华园44号楼</p>
                            <p className="text-sm leading-relaxed mb-2">委托鉴定事项：对房屋现状危险性进行鉴定，为后续处理提供参考</p>
                            <p className="text-sm leading-relaxed mb-2">受理日期：2024年4月30日</p>
                            <p className="text-sm leading-relaxed mb-4">查勘日期：2024年7月9日~7月10日、9月6日、9月29日、10月12日</p>

                            <h2 className="text-base font-bold mt-6 mb-3">二、房屋概况</h2>
                            <p className="text-sm leading-relaxed mb-4">鉴定对象位于昆山市开发区同丰东路以南、顺帆北路以西丽华园小区内，一层作为商铺、车库使用，二层至六层作为住宅使用。据委托方提供资料，鉴定对象约建于1999年，建筑面积 3299.95m²，为六层（屋面设置阁楼）底框结构，屋盖采用现浇板坡屋面，楼面主要采用预应力混凝土空心板楼面，卫生间、厨房、阳台采用现浇混凝土板楼面，采用现浇混凝土楼梯，竖向承重构件为混凝土柱及烧结粘土砖实墙。委托方提供鉴定对象建筑及结构设计图纸一套（建设单位为昆山经济开发区动迁办公室，设计单位为苏州市民用建筑设计院，施工单位为昆山市开发区建筑公司，工程名称为丽华园44#、21#、25#商住房，设计证号：1011552，图纸日期为1997.02，盖有设计出图专用章、竣工图章及设计人员签字，扫描件）。</p>

                            <h2 className="text-base font-bold mt-6 mb-3">三、鉴定内容和方法、主要检测仪器设备及原始记录一览</h2>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（一）鉴定内容和方法</h3>
                            <p className="text-sm leading-relaxed mb-2">1. 对鉴定对象地基进行危险性鉴定，评定鉴定对象地基的危险性状态。通过分析鉴定对象倾斜观测资料和其不均匀沉降引起上部结构反应的检查结果进行判定。</p>
                            <p className="text-sm leading-relaxed mb-2">2. 对鉴定对象基础及上部结构进行危险性鉴定，评定鉴定对象基础及楼层的危险性等级。</p>
                            <p className="text-sm leading-relaxed mb-2 pl-4">（1）对鉴定对象基础进行危险性鉴定。通过分析鉴定对象倾斜观测资料和其不均匀沉降引起上部结构反应的检查结果进行判定。</p>
                            <p className="text-sm leading-relaxed mb-4 pl-4">（2）对鉴定对象上部结构进行危险性鉴定。依据设计图纸及国家相关规范标准要求对鉴定对象结构布置进行检查核对。</p>

                            <h2 className="text-base font-bold mt-6 mb-3">四、检测鉴定依据</h2>
                            <p className="text-sm leading-relaxed mb-4">依据国家及地方相关规范标准进行检测鉴定。</p>

                            <h2 className="text-base font-bold mt-6 mb-3">五、检查和检测情况</h2>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（一）检查情况</h3>
                            <p className="text-sm leading-relaxed mb-4">对鉴定对象进行现场检查，包括结构布置、构件状况等。</p>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（二）检测情况</h3>
                            <p className="text-sm leading-relaxed mb-2">1、上部结构构件截面尺寸</p>
                            <p className="text-sm leading-relaxed mb-2">2、钢筋配置</p>
                            <p className="text-sm leading-relaxed mb-2">3、材料强度</p>
                            <p className="text-sm leading-relaxed mb-4">4、房屋倾斜</p>

                            <h2 className="text-base font-bold mt-6 mb-3">六、复核验算</h2>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（一）荷载及计算参数取值</h3>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（二）承载能力复核验算</h3>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（三）墙体高厚比复核验算</h3>

                            <h2 className="text-base font-bold mt-6 mb-3">七、分析说明</h2>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（一）地基危险性评定</h3>
                            <h3 className="text-sm font-semibold mt-4 mb-2">（二）基础及上部结构危险性鉴定</h3>

                            <h2 className="text-base font-bold mt-6 mb-3">八、鉴定意见及处理建议</h2>
                            <p className="text-sm leading-relaxed mb-4">根据《危险房屋鉴定标准》（JGJ125-2016）危险性鉴定等级划分：</p>
                            <table className="w-full text-sm border-collapse border border-slate-300 mb-4">
                                <thead>
                                    <tr className="bg-slate-100">
                                        <th className="border border-slate-300 px-3 py-2 text-left">等级</th>
                                        <th className="border border-slate-300 px-3 py-2 text-left">分级标准</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td className="border border-slate-300 px-3 py-2">A</td>
                                        <td className="border border-slate-300 px-3 py-2">无危险构件，房屋结构能满足安全使用要求。</td>
                                    </tr>
                                    <tr>
                                        <td className="border border-slate-300 px-3 py-2">B</td>
                                        <td className="border border-slate-300 px-3 py-2">个别结构构件评定为危险构件，但不影响主体结构安全，基本能满足安全使用要求。</td>
                                    </tr>
                                    <tr>
                                        <td className="border border-slate-300 px-3 py-2">C</td>
                                        <td className="border border-slate-300 px-3 py-2">部分承重结构不能满足安全使用要求，房屋局部处于危险状态，构成局部危房。</td>
                                    </tr>
                                    <tr>
                                        <td className="border border-slate-300 px-3 py-2">D</td>
                                        <td className="border border-slate-300 px-3 py-2">承重结构已不能满足安全使用要求，房屋整体处于危险状态，构成整幢危房。</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Floating Action Component for Document */}
                {!isGenerating && (
                    <div className="flex justify-center py-8 gap-2 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
                        <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-full shadow-sm text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
                            <div className="flex -space-x-2">
                                <div className="w-5 h-5 rounded-full bg-indigo-500 border-2 border-white"></div>
                                <div className="w-5 h-5 rounded-full bg-rose-500 border-2 border-white"></div>
                            </div>
                            <span>参考资料</span>
                        </button>
                        <button className="p-2 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors">
                            <Copy className="w-4 h-4" />
                        </button>
                        <button className="p-2 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors">
                            <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button className="p-2 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-colors">
                            <ThumbsDown className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
