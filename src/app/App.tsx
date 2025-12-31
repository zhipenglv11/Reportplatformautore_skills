import { useState, useEffect, useCallback, useRef } from 'react';
import { Node, Edge } from 'reactflow';
import Dashboard from './components/dashboard';
import { ProjectSidebar, Project } from './components/project-sidebar';
import { ProjectHeader } from './components/project-header';
import { ProjectOverviewPage } from './components/project-overview-page';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';
import DataCollectionEditor from './components/data-collection-editor';
import ReportEditor from './components/report-editor';
import ReportManagement from './components/report-management';
import ReviewPanel from './components/review-panel';

// 获取项目存储的 key
const getStorageKey = (projectId: string, type: string) => `project_${projectId}_${type}`;

// 从 localStorage 加载数据
const loadFromStorage = <T,>(key: string, defaultValue: T): T => {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.error('Failed to load from storage:', e);
  }
  return defaultValue;
};

// 保存数据到 localStorage
const saveToStorage = (key: string, data: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error('Failed to save to storage:', e);
  }
};

// 初始项目
const defaultProject: Project = {
  id: '1',
  name: '某商业中心结构安全性鉴定项目',
  code: 'P-20241230-01',
  date: '2024-12-30',
  status: '进行中',
  engineer: '王工',
};

export default function App() {
  const [activeTab, setActiveTab] = useState('collection');
  const [currentView, setCurrentView] = useState<'dashboard' | 'workspace' | 'overview'>('workspace');
  const [currentProject, setCurrentProject] = useState<Project>(() => 
    loadFromStorage('currentProject', defaultProject)
  );
  const [isAnimating, setIsAnimating] = useState(false);
  const [animatingProjectName, setAnimatingProjectName] = useState('');
  
  // 使用 useRef 来防止初始加载时的重复保存
  const isInitialMount = useRef(true);
  
  // 从 localStorage 加载节点数据
  const [collectionNodes, setCollectionNodes] = useState<Node[]>(() => 
    loadFromStorage(getStorageKey(defaultProject.id, 'collectionNodes'), [])
  );
  const [collectionEdges, setCollectionEdges] = useState<Edge[]>(() => 
    loadFromStorage(getStorageKey(defaultProject.id, 'collectionEdges'), [])
  );
  const [reportNodes, setReportNodes] = useState<Node[]>(() => 
    loadFromStorage(getStorageKey(defaultProject.id, 'reportNodes'), [])
  );
  const [reportEdges, setReportEdges] = useState<Edge[]>(() => 
    loadFromStorage(getStorageKey(defaultProject.id, 'reportEdges'), [])
  );
  
  // 自动保存当前项目到 localStorage
  useEffect(() => {
    saveToStorage('currentProject', currentProject);
  }, [currentProject]);
  
  // 自动保存节点数据到 localStorage（带防抖）
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    const timer = setTimeout(() => {
      saveToStorage(getStorageKey(currentProject.id, 'collectionNodes'), collectionNodes);
    }, 500);
    return () => clearTimeout(timer);
  }, [collectionNodes, currentProject.id]);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      saveToStorage(getStorageKey(currentProject.id, 'collectionEdges'), collectionEdges);
    }, 500);
    return () => clearTimeout(timer);
  }, [collectionEdges, currentProject.id]);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      saveToStorage(getStorageKey(currentProject.id, 'reportNodes'), reportNodes);
    }, 500);
    return () => clearTimeout(timer);
  }, [reportNodes, currentProject.id]);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      saveToStorage(getStorageKey(currentProject.id, 'reportEdges'), reportEdges);
    }, 500);
    return () => clearTimeout(timer);
  }, [reportEdges, currentProject.id]);

  const handleProjectCreated = (projectName: string) => {
    setAnimatingProjectName(projectName);
    setIsAnimating(true);
    
    // 新建项目时清空画布节点数据
    setCollectionNodes([]);
    setCollectionEdges([]);
    setReportNodes([]);
    setReportEdges([]);
    
    // 动画完成后更新项目名称
    setTimeout(() => {
      setIsAnimating(false);
      setAnimatingProjectName('');
    }, 600);
  };

  // 加载项目数据
  const loadProjectData = useCallback((projectId: string) => {
    const savedCollectionNodes = loadFromStorage<Node[]>(getStorageKey(projectId, 'collectionNodes'), []);
    const savedCollectionEdges = loadFromStorage<Edge[]>(getStorageKey(projectId, 'collectionEdges'), []);
    const savedReportNodes = loadFromStorage<Node[]>(getStorageKey(projectId, 'reportNodes'), []);
    const savedReportEdges = loadFromStorage<Edge[]>(getStorageKey(projectId, 'reportEdges'), []);
    
    setCollectionNodes(savedCollectionNodes);
    setCollectionEdges(savedCollectionEdges);
    setReportNodes(savedReportNodes);
    setReportEdges(savedReportEdges);
  }, []);

  const handleProjectSelect = (project: Project) => {
    // 先保存当前项目的数据
    saveToStorage(getStorageKey(currentProject.id, 'collectionNodes'), collectionNodes);
    saveToStorage(getStorageKey(currentProject.id, 'collectionEdges'), collectionEdges);
    saveToStorage(getStorageKey(currentProject.id, 'reportNodes'), reportNodes);
    saveToStorage(getStorageKey(currentProject.id, 'reportEdges'), reportEdges);
    
    // 切换到新项目
    setCurrentProject(project);
    
    // 加载新项目的数据（新项目会加载空数组）
    loadProjectData(project.id);
  };

  return (
    <div className="h-screen w-full bg-slate-50 flex overflow-hidden font-sans text-slate-900">
      {/* 1. Global Project Sidebar (Left - Green Area) */}
      <ProjectSidebar 
        onNavigate={(view) => setCurrentView(view)} 
        currentView={currentView}
        onProjectCreated={handleProjectCreated}
        onProjectSelect={handleProjectSelect}
        currentProjectId={currentProject.id}
      />

      {/* 2. Main Content Area (Right) */}
      <div className="flex-1 flex flex-col min-w-0 bg-slate-50">

        {currentView === 'overview' ? (
          <ProjectOverviewPage onBack={() => setCurrentView('workspace')} />
        ) : currentView === 'dashboard' ? (
          <Dashboard />
        ) : (
          <>
            {/* 2a. Project Header (Right Top - Blue Area) */}
            <ProjectHeader 
              projectName={currentProject.name} 
              projectCode={currentProject.code}
              projectDate={currentProject.date}
              projectStatus={currentProject.status}
              engineer={currentProject.engineer}
              isAnimating={isAnimating} 
              animatingProjectName={animatingProjectName} 
            />

            {/* 2b. Workspace Content (Right Bottom - Red Area) */}
            <div className="flex-1 overflow-hidden relative flex flex-col">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">

                {/* Workspace Sub-Navigation (Tabs) */}
                <div className="px-6 border-b border-slate-200 bg-white/50 backdrop-blur-sm shrink-0 flex justify-center">
                  <TabsList className="flex gap-6 bg-transparent p-0 h-10 w-fit">
                    <TabsTrigger
                      value="collection"
                      className="relative h-full px-1 bg-transparent text-slate-500 data-[state=active]:text-slate-900 data-[state=active]:shadow-none font-medium text-sm transition-colors hover:text-slate-700 group"
                    >
                      <span className="relative z-10">信息采集</span>
                      {/* Active Line Indicator */}
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-900 scale-x-0 group-data-[state=active]:scale-x-100 transition-transform duration-200 ease-out origin-center" />
                    </TabsTrigger>

                    <TabsTrigger
                      value="report"
                      className="relative h-full px-1 bg-transparent text-slate-500 data-[state=active]:text-slate-900 data-[state=active]:shadow-none font-medium text-sm transition-colors hover:text-slate-700 group"
                    >
                      <span className="relative z-10">报告生成</span>
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-900 scale-x-0 group-data-[state=active]:scale-x-100 transition-transform duration-200 ease-out origin-center" />
                    </TabsTrigger>

                    <TabsTrigger
                      value="management"
                      className="relative h-full px-1 bg-transparent text-slate-500 data-[state=active]:text-slate-900 data-[state=active]:shadow-none font-medium text-sm transition-colors hover:text-slate-700 group"
                    >
                      <span className="relative z-10">生成记录</span>
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-900 scale-x-0 group-data-[state=active]:scale-x-100 transition-transform duration-200 ease-out origin-center" />
                    </TabsTrigger>

                    {/* 分隔线 - 在线审核为管理员功能 */}
                    <div className="h-4 w-px bg-slate-300 self-center" />

                    <TabsTrigger
                      value="review"
                      className="relative h-full px-1 bg-transparent text-slate-500 data-[state=active]:text-slate-900 data-[state=active]:shadow-none font-medium text-sm transition-colors hover:text-slate-700 group"
                    >
                      <span className="relative z-10">在线审核</span>
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-900 scale-x-0 group-data-[state=active]:scale-x-100 transition-transform duration-200 ease-out origin-center" />
                    </TabsTrigger>
                  </TabsList>
                </div>

                {/* Tab Contents - The actual workspaces */}
                <TabsContent value="collection" className="flex-1 m-0 p-0 min-h-0 overflow-hidden flex flex-col data-[state=inactive]:hidden">
                  <DataCollectionEditor
                    key={`collection-${currentProject.id}`}
                    initialNodes={collectionNodes}
                    initialEdges={collectionEdges}
                    onNodesChange={setCollectionNodes}
                    onEdgesChange={setCollectionEdges}
                  />
                </TabsContent>

                <TabsContent value="report" className="flex-1 m-0 p-0 min-h-0 overflow-hidden flex flex-col data-[state=inactive]:hidden">
                  <ReportEditor
                    key={`report-${currentProject.id}`}
                    initialNodes={reportNodes}
                    initialEdges={reportEdges}
                    onNodesChange={setReportNodes}
                    onEdgesChange={setReportEdges}
                  />
                </TabsContent>

                <TabsContent value="management" className="flex-1 m-0 p-0 min-h-0 overflow-hidden flex flex-col data-[state=inactive]:hidden">
                  <ReportManagement projectId={currentProject.id} />
                </TabsContent>

                <TabsContent value="review" className="flex-1 m-0 p-0 min-h-0 overflow-hidden flex flex-col data-[state=inactive]:hidden">
                  <ReviewPanel />
                </TabsContent>
              </Tabs>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
