import { useEffect, useRef, useState } from "react";
import {
    MoreHorizontal,
    Clock,
    User,
    Hash,
    ChevronRight,
    Save,
    FileUp,
    Check,
    FileText
} from "lucide-react";

interface ProjectHeaderProps {
    projectName?: string;
    projectCode?: string;
    projectDate?: string;
    projectStatus?: string;
    engineer?: string;
    reportType?: string;
    isAnimating?: boolean;
    animatingProjectName?: string;
}

export function ProjectHeader({ 
    projectName = '某商业中心结构安全性鉴定项目', 
    projectCode = 'P-20241230-01',
    projectDate = '2024-12-30',
    projectStatus = '进行中',
    engineer = '王工',
    reportType = '民标安全性',
    isAnimating = false, 
    animatingProjectName = '' 
}: ProjectHeaderProps) {
    const [showAnimation, setShowAnimation] = useState(false);
    const [animationStyle, setAnimationStyle] = useState<React.CSSProperties>({});
    const headerRef = useRef<HTMLDivElement>(null);
    const projectNameRef = useRef<HTMLSpanElement>(null);
    
    // 自动保存开关状态，默认为开启
    const [autoSaveEnabled, setAutoSaveEnabled] = useState<boolean>(() => {
        const saved = localStorage.getItem('autoSaveEnabled');
        return saved !== null ? JSON.parse(saved) : true;
    });

    // 切换自动保存状态
    const toggleAutoSave = () => {
        setAutoSaveEnabled((prev) => {
            const newValue = !prev;
            localStorage.setItem('autoSaveEnabled', JSON.stringify(newValue));
            return newValue;
        });
    };

    // 下拉菜单状态
    const [showMenu, setShowMenu] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // 点击外部关闭菜单
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setShowMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 模板入库处理
    const handleTemplateImport = () => {
        // TODO: 实现模板入库逻辑
        setShowMenu(false);
        alert('模板入库功能开发中...');
    };

    useEffect(() => {
        if (isAnimating && animatingProjectName && projectNameRef.current) {
            // 获取对话框的位置
            const dialog = document.querySelector('[id*="radix-"][role="dialog"]') as HTMLElement;
            const input = document.getElementById('project-input') as HTMLElement;
            
            if (dialog && input && projectNameRef.current) {
                const dialogRect = dialog.getBoundingClientRect();
                const inputRect = input.getBoundingClientRect();
                const headerRect = projectNameRef.current.getBoundingClientRect();
                
                // 计算起始位置（输入框的位置）
                const startX = inputRect.left + inputRect.width / 2;
                const startY = inputRect.top + inputRect.height / 2;
                
                // 计算目标位置（header中项目名称的位置）
                const endX = headerRect.left;
                const endY = headerRect.top + headerRect.height / 2;
                
                // 设置动画样式
                setAnimationStyle({
                    position: 'fixed',
                    left: `${startX}px`,
                    top: `${startY}px`,
                    transform: 'translate(-50%, -50%)',
                    zIndex: 9999,
                    pointerEvents: 'none',
                });
                
                setShowAnimation(true);
                
                // 触发动画
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        setAnimationStyle({
                            position: 'fixed',
                            left: `${endX}px`,
                            top: `${endY}px`,
                            transform: 'translate(0, -50%)',
                            zIndex: 9999,
                            pointerEvents: 'none',
                            transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                        });
                    });
                });
                
                // 动画结束后隐藏动画元素
                const timer = setTimeout(() => {
                    setShowAnimation(false);
                }, 600);
                return () => clearTimeout(timer);
            } else {
                // 如果找不到对话框元素（比如在 dashboard 视图），直接显示项目名称，不执行动画
                // 确保 showAnimation 保持为 false，这样项目名称会正常显示
                setShowAnimation(false);
            }
        } else if (!isAnimating) {
            // 当动画结束时，确保 showAnimation 为 false
            setShowAnimation(false);
        }
    }, [isAnimating, animatingProjectName]);
    return (
        <div className="h-[50px] bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0 z-10">
            {/* Left: Project Info / Breadcrumbs */}
            <div className="flex items-center gap-4 justify-end">
                <div className="flex items-center gap-2 relative" ref={headerRef}>
                    {showAnimation && (
                        <div
                            className="font-semibold text-slate-800 whitespace-nowrap"
                            style={animationStyle}
                        >
                            {animatingProjectName}
                        </div>
                    )}
                    <span 
                        ref={projectNameRef}
                        className={`font-semibold text-slate-800 transition-opacity duration-300 ${isAnimating && showAnimation ? 'opacity-0' : 'opacity-100'}`}
                    >
                        {projectName}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        projectStatus === '已完成' ? 'bg-emerald-100 text-emerald-700' :
                        projectStatus === '进行中' ? 'bg-amber-100 text-amber-700' :
                        projectStatus === '审核中' ? 'bg-blue-100 text-blue-700' :
                        'bg-amber-100 text-amber-700'
                    }`}>
                        {projectStatus}
                    </span>
                </div>
            </div>

            {/* Middle: Spacer */}
            <div className="flex-1" />

            {/* Right: Meta Info & Actions */}
            <div className="flex items-center gap-6">
                {/* Meta Info moved from left */}
                <div className="flex items-center gap-4 text-xs text-slate-400">
                    {/* 报告类型显示 */}
                    <div className="flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        <span>{reportType || '未设置'}</span>
                    </div>
                    
                    <div className="h-4 w-px bg-slate-200" />
                    
                    <div className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        <span>{projectCode}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{projectDate}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        <span>{engineer}</span>
                    </div>
                </div>

                {/* Divider */}
                <div className="h-4 w-px bg-slate-200" />

                {/* Auto Save Status Indicator & More Menu */}
                <div className="flex items-center gap-2">
                    {/* 自动保存状态指示器 */}
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        <div className={`w-1.5 h-1.5 rounded-full ${autoSaveEnabled ? 'bg-green-500' : 'bg-slate-300'}`} />
                        <span>{autoSaveEnabled ? '自动保存' : '手动保存'}</span>
                    </div>

                    {/* More Menu */}
                    <div className="relative" ref={menuRef}>
                        <button 
                            onClick={() => setShowMenu(!showMenu)}
                            className={`p-2 rounded-lg text-slate-500 transition-colors ${showMenu ? 'bg-slate-100' : 'hover:bg-slate-100'}`}
                        >
                            <MoreHorizontal className="w-5 h-5" />
                        </button>

                        {/* Dropdown Menu */}
                        {showMenu && (
                            <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                                {/* 自动保存开关 */}
                                <button
                                    onClick={toggleAutoSave}
                                    className="w-full px-3 py-2 flex items-center justify-between hover:bg-slate-50 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <Save className="w-4 h-4 text-slate-500" />
                                        <span className="text-sm text-slate-700">自动保存</span>
                                    </div>
                                    {/* Toggle Switch */}
                                    <div className={`relative w-8 h-4 rounded-full transition-colors ${autoSaveEnabled ? 'bg-green-500' : 'bg-slate-300'}`}>
                                        <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full shadow-sm transition-all ${autoSaveEnabled ? 'left-4' : 'left-0.5'}`} />
                                    </div>
                                </button>

                                {/* 分隔线 */}
                                <div className="h-px bg-slate-100 my-1" />

                                {/* 模板入库 */}
                                <button
                                    onClick={handleTemplateImport}
                                    className="w-full px-3 py-2 flex items-center gap-2 hover:bg-slate-50 transition-colors"
                                >
                                    <FileUp className="w-4 h-4 text-slate-500" />
                                    <span className="text-sm text-slate-700">模板入库</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
