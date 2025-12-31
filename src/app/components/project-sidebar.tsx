import {
    LayoutGrid,
    Search,
    ChevronDown,
    ChevronRight,
    Building2,
    MoreHorizontal,
    Plus,
    PanelLeftClose,
    PanelLeftOpen,
    FileText,
    Pencil,
    LayoutDashboard,
    Folder
} from "lucide-react";
import { useState, useEffect } from "react";
import {
    CommandDialog,
    CommandInput,
    CommandList,
    CommandEmpty,
    CommandGroup,
    CommandItem,
    CommandSeparator,
} from "./ui/command";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Button } from "./ui/button";

export interface Project {
    id: string;
    name: string;
    code?: string; // 项目编号
    date?: string; // 项目日期
    status?: string; // 项目状态
    engineer?: string; // 工程师
    isActive?: boolean;
}

interface ProjectSidebarProps {
    onNavigate?: (view: 'workspace' | 'dashboard' | 'overview') => void;
    currentView?: 'workspace' | 'dashboard' | 'overview';
    onProjectCreated?: (projectName: string) => void;
    onProjectSelect?: (project: Project) => void;
    currentProjectId?: string;
}

export function ProjectSidebar({ onNavigate, currentView, onProjectCreated, onProjectSelect, currentProjectId }: ProjectSidebarProps) {
    const [isProjectsExpanded, setIsProjectsExpanded] = useState(true);
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [isNewProjectDialogOpen, setIsNewProjectDialogOpen] = useState(false);
    const [newProjectInput, setNewProjectInput] = useState('');
    const [showAllProjects, setShowAllProjects] = useState(false);
    
    // 根据 currentView 自动设置 activeItem
    const activeItem = currentView === 'overview' ? 'overview' : currentView === 'dashboard' ? 'overview' : 'project';
    const [projects, setProjects] = useState<Project[]>([
        { 
            id: '1', 
            name: '某商业中心结构安全性鉴定', 
            code: 'P-20241230-01',
            date: '2024-12-30',
            status: '进行中',
            engineer: '王工',
            isActive: true 
        },
        { 
            id: '2', 
            name: '工业厂房抗震鉴定项目',
            code: 'P-20241228-02',
            date: '2024-12-28',
            status: '已完成',
            engineer: '李工'
        },
        { 
            id: '3', 
            name: '住宅楼裂缝专项检测',
            code: 'P-20241225-03',
            date: '2024-12-25',
            status: '审核中',
            engineer: '张工'
        },
        { 
            id: '4', 
            name: '钢结构施工质量验收',
            code: 'P-20241222-04',
            date: '2024-12-22',
            status: '已完成',
            engineer: '赵工'
        },
        { 
            id: '5', 
            name: '历史建筑保护性监测',
            code: 'P-20241220-05',
            date: '2024-12-20',
            status: '进行中',
            engineer: '王工'
        },
        { 
            id: '6', 
            name: '丽华园44号楼危房鉴定',
            code: 'FW-24-0279',
            date: '2024-10-12',
            status: '已完成',
            engineer: '陈工'
        },
        { 
            id: '7', 
            name: '学校教学楼抗震评估',
            code: 'P-20241015-07',
            date: '2024-10-15',
            status: '已完成',
            engineer: '刘工'
        },
        { 
            id: '8', 
            name: '医院门诊楼安全鉴定',
            code: 'P-20241010-08',
            date: '2024-10-10',
            status: '进行中',
            engineer: '周工'
        },
        { 
            id: '9', 
            name: '老旧小区综合检测',
            code: 'P-20241005-09',
            date: '2024-10-05',
            status: '审核中',
            engineer: '吴工'
        },
        { 
            id: '10', 
            name: '商场加层可行性评估',
            code: 'P-20241001-10',
            date: '2024-10-01',
            status: '已完成',
            engineer: '郑工'
        },
    ]);
    
    // 默认显示的项目数量
    const defaultVisibleCount = 5;
    const visibleProjects = showAllProjects ? projects : projects.slice(0, defaultVisibleCount);
    const hiddenCount = projects.length - defaultVisibleCount;

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setIsSearchOpen((open) => !open);
            }
        };
        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    }, []);

    const toggleProjects = () => {
        if (isCollapsed) {
            // 折叠状态下点击"项目"，先展开侧边栏，然后展开项目列表
            setIsCollapsed(false);
            setIsProjectsExpanded(true);
            return;
        }
        setIsProjectsExpanded(!isProjectsExpanded);
    };

    const toggleSidebar = () => {
        setIsCollapsed(!isCollapsed);
    };

    const handleOverviewClick = () => {
        onNavigate?.('overview');
    };

    const handleProjectClick = (project?: Project) => {
        if (project) {
            // 更新项目激活状态
            setProjects(prev => prev.map(p => ({
                ...p,
                isActive: p.id === project.id
            })));
            // 通知父组件选中项目
            onProjectSelect?.(project);
        }
        onNavigate?.('workspace');
    };

    const handleNewProjectClick = () => {
        if (isCollapsed) {
            setIsCollapsed(false);
        }
        setIsNewProjectDialogOpen(true);
    };

    const handleCreateProject = () => {
        if (!newProjectInput.trim()) return;
        
        const projectName = newProjectInput.trim();
        
        // 生成项目编号和日期
        const now = new Date();
        const projectCode = `P-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${String(projects.length + 1).padStart(2, '0')}`;
        const projectDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        
        // 创建新项目
        const newProject: Project = {
            id: `project-${Date.now()}`,
            name: projectName,
            code: projectCode,
            date: projectDate,
            status: '进行中',
            engineer: '王工',
            isActive: true,
        };
        
        // 将之前的项目设为非激活状态
        setProjects(prev => prev.map(p => ({ ...p, isActive: false })));
        
        // 添加新项目并设为激活
        setProjects(prev => [newProject, ...prev]);
        
        // 触发项目创建动画（在关闭对话框之前）
        onProjectCreated?.(projectName);
        
        // 延迟关闭对话框，让动画先开始
        setTimeout(() => {
            // 重置输入并关闭对话框
            setNewProjectInput('');
            setIsNewProjectDialogOpen(false);
            
            // 导航到工作区并选中新项目
            handleProjectClick(newProject);
        }, 50);
    };

    return (
        <>
            <div className={`h-full flex flex-col bg-slate-50 border-r border-slate-200 flex-shrink-0 z-20 font-sans transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-[260px]'
                }`}>
                {/* Header / Logo Area */}
                <div className={`h-14 flex items-center mb-2 transition-all duration-300 ${isCollapsed ? 'justify-center px-0' : 'justify-between px-4'}`}>
                    {!isCollapsed ? (
                        <>
                            <div className="flex items-center gap-2 p-2 hover:bg-slate-200/50 rounded-lg transition-colors cursor-pointer flex-1 overflow-hidden" onClick={() => handleProjectClick(undefined)}>
                                <div className="w-6 h-6 flex items-center justify-center text-[#BFA15F] flex-shrink-0">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
                                        <path d="M7 12 L12 6 L17 9 L17 18" />
                                        <path d="M7 18 L7 12" />
                                        <path d="M12 18 L12 6" />
                                        <path d="M7 12 H17" />
                                        <path d="M7 18 H17" />
                                        <path d="M7 18 L12 12" />
                                        <path d="M17 18 L12 12" />
                                        <path d="M3 12 H7" opacity="0.5" />
                                        <path d="M17 12 H21" opacity="0.5" />
                                        <path d="M3 18 H7" opacity="0.5" />
                                        <path d="M17 18 H21" opacity="0.5" />
                                        <path d="M7 18 V22" opacity="0.5" />
                                        <path d="M12 18 V22" opacity="0.5" />
                                        <path d="M17 18 V22" opacity="0.5" />
                                        <circle cx="12" cy="6" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="17" cy="9" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="7" cy="12" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="7" cy="18" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="12" cy="18" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="17" cy="18" r="1.2" fill="currentColor" stroke="none" />
                                    </svg>
                                </div>
                                <span className={`font-semibold text-slate-700 text-sm whitespace-nowrap overflow-hidden transition-all duration-300 ml-2 ${isCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>智能报告平台</span>
                            </div>

                            <button
                                onClick={toggleSidebar}
                                className="p-1.5 hover:bg-slate-200/50 rounded-md text-slate-500 transition-colors ml-auto mr-0.5"
                                title="收起侧边栏"
                            >
                                <PanelLeftClose className="w-5 h-5" />
                            </button>
                        </>
                    ) : (
                        <div
                            className="relative w-8 h-8 flex items-center justify-center group cursor-pointer mt-2 mx-auto"
                            onClick={toggleSidebar}
                            title="展开侧边栏"
                        >
                            <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-200 group-hover:opacity-0 text-[#BFA15F]">
                                <div className="w-6 h-6">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
                                        <path d="M7 12 L12 6 L17 9 L17 18" />
                                        <path d="M7 18 L7 12" />
                                        <path d="M12 18 L12 6" />
                                        <path d="M7 12 H17" />
                                        <path d="M7 18 H17" />
                                        <path d="M7 18 L12 12" />
                                        <path d="M17 18 L12 12" />
                                        <path d="M3 12 H7" opacity="0.5" />
                                        <path d="M17 12 H21" opacity="0.5" />
                                        <path d="M3 18 H7" opacity="0.5" />
                                        <path d="M17 18 H21" opacity="0.5" />
                                        <path d="M7 18 V22" opacity="0.5" />
                                        <path d="M12 18 V22" opacity="0.5" />
                                        <path d="M17 18 V22" opacity="0.5" />
                                        <circle cx="12" cy="6" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="17" cy="9" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="7" cy="12" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="7" cy="18" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="12" cy="18" r="1.2" fill="currentColor" stroke="none" />
                                        <circle cx="17" cy="18" r="1.2" fill="currentColor" stroke="none" />
                                    </svg>
                                </div>
                            </div>

                            <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-200 opacity-0 group-hover:opacity-100 text-slate-500 bg-slate-200/50 rounded-md">
                                <PanelLeftOpen className="w-5 h-5" />
                            </div>
                        </div>
                    )}
                </div>

                {/* Main Navigation - Top Section */}
                <div className="px-3 pb-4 space-y-1">
                    <button
                        onClick={handleOverviewClick}
                        className={`w-full flex items-center py-2.5 rounded-lg transition-all duration-300 text-sm group ${
                            isCollapsed ? 'justify-center px-0' : 'pl-3'
                        } ${activeItem === 'overview' ? 'bg-slate-200 text-slate-900 font-medium' : 'text-slate-700 hover:bg-slate-200/50'}`}
                    >
                        <LayoutDashboard className={`w-4 h-4 flex-shrink-0 transition-all duration-300 ${isCollapsed ? 'mx-auto' : ''} ${activeItem === 'overview' ? 'text-slate-900' : 'text-slate-500 group-hover:text-slate-700'}`} />
                        <span className={`whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out ${isCollapsed ? 'w-0 opacity-0 ml-0' : 'w-auto opacity-100 ml-3'}`}>项目概览</span>
                    </button>

                    <button
                        onClick={() => setIsSearchOpen(true)}
                        className={`w-full flex items-center py-2.5 text-slate-700 hover:bg-slate-200/50 rounded-lg transition-all duration-300 text-sm group ${isCollapsed ? 'justify-center px-0' : 'pl-3'}`}
                    >
                        <Search className={`w-4 h-4 text-slate-500 group-hover:text-slate-700 flex-shrink-0 transition-all duration-300 ${isCollapsed ? 'mx-auto' : ''}`} />
                        <span className={`whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out ${isCollapsed ? 'w-0 opacity-0 ml-0' : 'w-auto opacity-100 ml-3'}`}>搜索项目</span>
                    </button>
                </div>

                {/* Projects Section */}
                <div className="flex-1 overflow-y-auto px-3 py-2">
                    {/* Section Header */}
                    <div
                        className={`flex items-center justify-between py-2 mb-1 transition-all duration-300 ${isCollapsed ? 'justify-center px-0' : 'px-3'}`}
                    >
                        <div
                            className={`text-xs font-medium text-slate-400 hover:text-slate-600 cursor-pointer ${isCollapsed ? 'flex items-center justify-center w-full' : 'flex items-center gap-1 flex-1'}`}
                            onClick={toggleProjects}
                            title={isCollapsed ? "项目" : undefined}
                        >
                            {!isCollapsed ? (
                                <>
                                    <Folder className="w-4 h-4" />
                                    {isProjectsExpanded ? (
                                        <ChevronDown className="w-3 h-3" />
                                    ) : (
                                        <ChevronRight className="w-3 h-3" />
                                    )}
                                </>
                            ) : (
                                <Folder className="w-4 h-4" />
                            )}
                        </div>
                        {!isCollapsed && (
                            <button 
                                onClick={handleNewProjectClick}
                                className="flex items-center gap-1.5 px-2 py-1 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-200/50 rounded transition-all duration-300"
                                title="新项目"
                            >
                                <Plus className="w-3.5 h-3.5" />
                                <span>新项目</span>
                            </button>
                        )}
                    </div>

                    {/* Projects List */}
                    {isProjectsExpanded && !isCollapsed && (
                        <div className="space-y-0.5 animate-in slide-in-from-top-2 duration-200">

                            {/* Existing Projects */}
                            {visibleProjects.map((project) => (
                                <button
                                    key={project.id}
                                    onClick={() => handleProjectClick(project)}
                                    className={`w-full flex items-center py-2.5 rounded-lg transition-all duration-300 text-sm group pl-3 ${
                                        (activeItem === 'project' && (project.isActive || project.id === currentProjectId))
                                            ? 'bg-slate-200 text-slate-900 font-medium'
                                            : 'text-slate-700 hover:bg-slate-200/50'
                                        }`}
                                >
                                    <Building2 className={`w-4 h-4 flex-shrink-0 ${activeItem === 'project' && project.isActive ? 'text-slate-900' : 'text-slate-500 group-hover:text-slate-700'}`} />
                                    <span className="whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out truncate max-w-[200px] opacity-100 ml-3">{project.name}</span>
                                </button>
                            ))}

                            {hiddenCount > 0 && (
                                <button 
                                    onClick={() => setShowAllProjects(!showAllProjects)}
                                    className="w-full flex items-center py-2.5 text-slate-500 hover:text-slate-700 hover:bg-slate-200/50 rounded-lg transition-all duration-300 text-sm mt-1 pl-3"
                                >
                                    {showAllProjects ? (
                                        <>
                                            <ChevronDown className="w-4 h-4 flex-shrink-0" />
                                            <span className="whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out truncate max-w-[200px] opacity-100 ml-3">收起项目</span>
                                        </>
                                    ) : (
                                        <>
                                    <MoreHorizontal className="w-4 h-4 flex-shrink-0" />
                                            <span className="whitespace-nowrap overflow-hidden transition-all duration-300 ease-in-out truncate max-w-[200px] opacity-100 ml-3">展开显示 ({hiddenCount})</span>
                                        </>
                                    )}
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer / User Profile */}
                <div className={`p-4 border-t border-slate-200 transition-all duration-300 ${isCollapsed ? 'px-2' : ''}`}>
                    <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center' : ''}`}>
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-xs flex-shrink-0 shadow-sm">
                            W
                        </div>
                        <div className={`flex flex-col overflow-hidden transition-all duration-300 ease-in-out ${isCollapsed ? 'w-0 opacity-0' : 'w-32 opacity-100'}`}>
                            <span className="text-sm font-medium text-slate-700 truncate">王工程师</span>
                            <span className="text-xs text-slate-500 truncate">专业版</span>
                        </div>
                    </div>
                </div>
            </div>

            <CommandDialog open={isSearchOpen} onOpenChange={setIsSearchOpen}>
                <CommandInput placeholder="搜索项目名称、项目关键词、项目编号..." />
                <CommandList>
                    <CommandEmpty>未找到相关项目。</CommandEmpty>
                    <CommandGroup heading="新聊天">
                        <CommandItem onSelect={() => {
                            setIsSearchOpen(false);
                            handleProjectClick();
                        }}>
                            <Pencil className="mr-2 h-4 w-4" />
                            <span>新对话</span>
                        </CommandItem>
                    </CommandGroup>
                    <CommandSeparator />
                    <CommandGroup heading="今天">
                        <CommandItem onSelect={() => {
                            setIsSearchOpen(false);
                            handleProjectClick();
                        }}>
                            <FileText className="mr-2 h-4 w-4" />
                            <span>绘制客户旅程工具</span>
                        </CommandItem>
                        {projects.slice(0, 1).map((project) => (
                            <CommandItem key={project.id} onSelect={() => {
                                setIsSearchOpen(false);
                                handleProjectClick();
                            }}>
                                <FileText className="mr-2 h-4 w-4" />
                                <span>{project.name}</span>
                            </CommandItem>
                        ))}
                    </CommandGroup>
                    <CommandSeparator />
                    <CommandGroup heading="昨天">
                        <CommandItem onSelect={() => {
                            setIsSearchOpen(false);
                            handleProjectClick();
                        }}>
                            <FileText className="mr-2 h-4 w-4" />
                            <span>模板报告生成方法</span>
                        </CommandItem>
                        {projects.slice(1, 2).map((project) => (
                            <CommandItem key={project.id} onSelect={() => {
                                setIsSearchOpen(false);
                                handleProjectClick();
                            }}>
                                <FileText className="mr-2 h-4 w-4" />
                                <span>{project.name}</span>
                            </CommandItem>
                        ))}
                    </CommandGroup>
                    <CommandSeparator />
                    <CommandGroup heading="前7天">
                        <CommandItem onSelect={() => {
                            setIsSearchOpen(false);
                            handleProjectClick();
                        }}>
                            <FileText className="mr-2 h-4 w-4" />
                            <span>Claude安装错误解决</span>
                        </CommandItem>
                        <CommandItem onSelect={() => {
                            setIsSearchOpen(false);
                            handleProjectClick();
                        }}>
                            <FileText className="mr-2 h-4 w-4" />
                            <span>盯着干还是定标准</span>
                        </CommandItem>
                        {projects.slice(2).map((project) => (
                            <CommandItem key={project.id} onSelect={() => {
                                setIsSearchOpen(false);
                                handleProjectClick();
                            }}>
                                <FileText className="mr-2 h-4 w-4" />
                                <span>{project.name}</span>
                            </CommandItem>
                        ))}
                    </CommandGroup>
                </CommandList>
            </CommandDialog>

            {/* New Project Dialog */}
            <Dialog open={isNewProjectDialogOpen} onOpenChange={setIsNewProjectDialogOpen}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>创建新项目</DialogTitle>
                        <DialogDescription>
                            请输入项目编号或项目关键词来创建新项目
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <label htmlFor="project-input" className="text-sm font-medium text-slate-700">
                                项目编号/关键词
                            </label>
                            <Input
                                id="project-input"
                                placeholder="例如：P-20241230-01 或 某商业中心结构安全性鉴定"
                                value={newProjectInput}
                                onChange={(e) => setNewProjectInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && newProjectInput.trim()) {
                                        handleCreateProject();
                                    }
                                }}
                                autoFocus
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button
                            variant="outline"
                            onClick={() => {
                                setIsNewProjectDialogOpen(false);
                                setNewProjectInput('');
                            }}
                        >
                            取消
                        </Button>
                        <Button
                            onClick={handleCreateProject}
                            disabled={!newProjectInput.trim()}
                        >
                            创建
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
}
