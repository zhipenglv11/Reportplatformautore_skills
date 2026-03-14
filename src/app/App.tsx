import { useState, useEffect, useCallback, useRef } from 'react';
import { Node, Edge } from 'reactflow';
import Dashboard from './components/dashboard';
import { ProjectSidebar, Project } from './components/project-sidebar';
import { ProjectHeader } from './components/project-header';
import { ProjectOverviewPage } from './components/project-overview-page';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';
import { Button } from './components/ui/button';
import { History, Clock, FileText, CheckCircle2, XCircle } from 'lucide-react';
import DataCollectionEditor from './components/data-collection-editor';
import ReportEditor from './components/report-editor';

const getStorageKey = (projectId: string, type: string) => `project_${projectId}_${type}`;

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

const saveToStorage = (key: string, data: any) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.error('Failed to save to storage:', e);
  }
};

const defaultProject: Project = {
  id: '1',
  name: '某商业中心结构安全性鉴定项目',
  code: 'P-20241230-01',
  date: '2024-12-30',
  status: '进行中',
  engineer: '王工',
  reportType: '民标安全性',
};

export default function App() {
  const [activeTab, setActiveTab] = useState('collection');
  const [currentView, setCurrentView] = useState<'dashboard' | 'workspace' | 'overview'>('workspace');
  const [currentProject, setCurrentProject] = useState<Project>(() => loadFromStorage('currentProject', defaultProject));
  const [isAnimating, setIsAnimating] = useState(false);
  const [animatingProjectName, setAnimatingProjectName] = useState('');
  
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (historyRef.current && !historyRef.current.contains(event.target as Node)) {
        setIsHistoryOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isInitialMount = useRef(true);

  const [collectionNodes, setCollectionNodes] = useState<Node[]>(() =>
    loadFromStorage(getStorageKey(defaultProject.id, 'collectionNodes'), []),
  );
  const [collectionEdges, setCollectionEdges] = useState<Edge[]>(() =>
    loadFromStorage(getStorageKey(defaultProject.id, 'collectionEdges'), []),
  );
  const [reportNodes, setReportNodes] = useState<Node[]>(() =>
    loadFromStorage(getStorageKey(defaultProject.id, 'reportNodes'), []),
  );
  const [reportEdges, setReportEdges] = useState<Edge[]>(() =>
    loadFromStorage(getStorageKey(defaultProject.id, 'reportEdges'), []),
  );

  useEffect(() => {
    saveToStorage('currentProject', currentProject);
  }, [currentProject]);

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

  const handleProjectCreated = (projectName: string, newProject?: Project) => {
    setAnimatingProjectName(projectName);
    setIsAnimating(true);

    if (newProject) {
      setCurrentProject(newProject);
    }

    setCollectionNodes([]);
    setCollectionEdges([]);
    setReportNodes([]);
    setReportEdges([]);

    setTimeout(() => {
      setIsAnimating(false);
      setAnimatingProjectName('');
    }, 600);
  };

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
    saveToStorage(getStorageKey(currentProject.id, 'collectionNodes'), collectionNodes);
    saveToStorage(getStorageKey(currentProject.id, 'collectionEdges'), collectionEdges);
    saveToStorage(getStorageKey(currentProject.id, 'reportNodes'), reportNodes);
    saveToStorage(getStorageKey(currentProject.id, 'reportEdges'), reportEdges);

    setCurrentProject(project);
    loadProjectData(project.id);
  };

  return (
    <div className="h-screen w-full bg-slate-50 flex overflow-hidden font-sans text-slate-900">
      <ProjectSidebar
        onNavigate={(view) => setCurrentView(view)}
        currentView={currentView}
        onProjectCreated={handleProjectCreated}
        onProjectSelect={handleProjectSelect}
        currentProjectId={currentProject.id}
      />

      <div className="flex-1 flex flex-col min-w-0 bg-slate-50">
        {currentView === 'overview' ? (
          <ProjectOverviewPage onBack={() => setCurrentView('workspace')} />
        ) : currentView === 'dashboard' ? (
          <Dashboard />
        ) : (
          <>
            <ProjectHeader
              projectName={currentProject.name}
              projectCode={currentProject.code}
              projectDate={currentProject.date}
              projectStatus={currentProject.status}
              engineer={currentProject.engineer}
              reportType={currentProject.reportType}
              isAnimating={isAnimating}
              animatingProjectName={animatingProjectName}
            />

            <div className="flex-1 overflow-hidden relative flex flex-col">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                <div className="px-6 border-b border-slate-200 bg-white/50 backdrop-blur-sm shrink-0 relative flex justify-center items-center h-10">
                  <TabsList className="flex gap-6 bg-transparent p-0 h-full w-fit">
                    <TabsTrigger
                      value="collection"
                      className="relative h-full px-1 bg-transparent text-slate-500 data-[state=active]:text-slate-900 data-[state=active]:shadow-none font-medium text-sm transition-colors hover:text-slate-700 group"
                    >
                      <span className="relative z-10">信息采集</span>
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-900 scale-x-0 group-data-[state=active]:scale-x-100 transition-transform duration-200 ease-out origin-center" />
                    </TabsTrigger>

                    <TabsTrigger
                      value="report"
                      className="relative h-full px-1 bg-transparent text-slate-500 data-[state=active]:text-slate-900 data-[state=active]:shadow-none font-medium text-sm transition-colors hover:text-slate-700 group"
                    >
                      <span className="relative z-10">报告生成</span>
                      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-900 scale-x-0 group-data-[state=active]:scale-x-100 transition-transform duration-200 ease-out origin-center" />
                    </TabsTrigger>
                  </TabsList>
                  
                  {/* 右侧的历史记录按钮与悬浮面板 */}
                  <div className="absolute right-4 top-0 bottom-0 flex items-center" ref={historyRef}>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                      className={`h-7 text-slate-500 hover:text-slate-800 hover:bg-slate-200/50 gap-1.5 focus-visible:ring-0 transition-colors ${isHistoryOpen ? 'bg-slate-200/50 text-slate-800' : ''}`}
                    >
                      <History className="w-3.5 h-3.5" />
                      <span className="text-xs">历史记录</span>
                    </Button>

                    {isHistoryOpen && (
                      <div className="absolute top-[calc(100%+8px)] right-0 w-[300px] bg-white border border-slate-200 shadow-lg rounded-xl z-50 overflow-hidden animate-in fade-in zoom-in slide-in-from-top-2 duration-200">
                          <div className="bg-slate-50 border-b border-slate-100 px-4 py-2.5 flex items-center justify-between">
                            <h4 className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                              <Clock className="w-3.5 h-3.5 text-slate-500" />
                              最近生成记录
                            </h4>
                            <span className="text-[10px] text-slate-400 font-mono">Top 10</span>
                          </div>
                          <div className="max-h-[280px] overflow-y-auto w-full flex flex-col p-1.5 gap-0.5 custom-scrollbar">
                            {/* 示例：成功项目 */}
                            <button className="flex flex-col text-left p-2.5 rounded-lg hover:bg-slate-50 transition-colors gap-2 group cursor-pointer border border-transparent hover:border-slate-200">
                              <div className="flex items-center justify-between w-full">
                                <span className="text-xs font-medium text-slate-700 group-hover:text-slate-900 flex items-center gap-1.5">
                                  <FileText className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 transition-colors" />
                                  最终鉴定报告_v2
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">10分钟前</span>
                              </div>
                              <div className="flex items-center justify-between w-full pl-5">
                                <span className="text-[10px] text-slate-500">包含 12 个分析章节</span>
                                <span className="text-[10px] text-emerald-600 flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 rounded font-medium border border-emerald-100">
                                  <CheckCircle2 className="w-3 h-3" /> 生成成功
                                </span>
                              </div>
                            </button>
                            
                            {/* 示例：草稿项目 */}
                            <button className="flex flex-col text-left p-2.5 rounded-lg hover:bg-slate-50 transition-colors gap-2 group cursor-pointer border border-transparent hover:border-slate-200">
                              <div className="flex items-center justify-between w-full">
                                <span className="text-xs font-medium text-slate-700 group-hover:text-slate-900 flex items-center gap-1.5">
                                  <FileText className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 transition-colors" />
                                  初评报告_v1
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">2小时前</span>
                              </div>
                              <div className="flex items-center justify-between w-full pl-5">
                                <span className="text-[10px] text-slate-500">包含 8 个分析章节</span>
                                <span className="text-[10px] text-emerald-600 flex items-center gap-1 bg-emerald-50 px-1.5 py-0.5 rounded font-medium border border-emerald-100">
                                  <CheckCircle2 className="w-3 h-3" /> 生成成功
                                </span>
                              </div>
                            </button>
                          </div>
                      </div>
                    )}
                  </div>
                </div>

                <TabsContent value="collection" className="flex-1 m-0 p-0 min-h-0 overflow-hidden flex flex-col data-[state=inactive]:hidden">
                  <DataCollectionEditor
                    key={`collection-${currentProject.id}`}
                    projectId={currentProject.id}
                    initialNodes={collectionNodes}
                    initialEdges={collectionEdges}
                    onNodesChange={setCollectionNodes}
                    onEdgesChange={setCollectionEdges}
                  />
                </TabsContent>

                <TabsContent value="report" className="flex-1 m-0 p-0 min-h-0 overflow-hidden flex flex-col data-[state=inactive]:hidden">
                  <ReportEditor
                    key={`report-${currentProject.id}`}
                    projectId={currentProject.id}
                    reportType={currentProject.reportType}
                    collectionNodes={collectionNodes}
                    initialNodes={reportNodes}
                    initialEdges={reportEdges}
                    onNodesChange={setReportNodes}
                    onEdgesChange={setReportEdges}
                  />
                </TabsContent>
              </Tabs>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
