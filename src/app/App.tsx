import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/tabs';
import DataCollectionEditor from './components/data-collection-editor';
import ReportEditor from './components/report-editor';
import ReviewPanel from './components/review-panel';
import { Node, Edge } from 'reactflow';

// 初始节点数据
const initialCollectionNodes: Node[] = [
  {
    id: '1',
    type: 'collection',
    position: { x: 250, y: 100 },
    data: { 
      label: '混凝土强度', 
      type: 'concrete-strength', 
      fields: [
        { name: 'specimen_number', label: '试块编号', type: 'text', required: true },
        { name: 'compressive_strength', label: '抗压强度(MPa)', type: 'number', required: true },
        { name: 'curing_days', label: '养护天数', type: 'number', required: true },
        { name: 'test_date', label: '测试日期', type: 'date', required: true },
      ]
    },
  },
];

const initialReportNodes: Node[] = [];

// 从localStorage加载数据
const loadFromStorage = (key: string, defaultValue: any) => {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
  } catch {
    return defaultValue;
  }
};

export default function App() {
  const [activeTab, setActiveTab] = useState('collection');
  
  // 为每个模块维护独立的节点和边状态
  const [collectionNodes, setCollectionNodes] = useState<Node[]>(() => 
    loadFromStorage('collectionNodes', initialCollectionNodes)
  );
  const [collectionEdges, setCollectionEdges] = useState<Edge[]>(() => 
    loadFromStorage('collectionEdges', [])
  );
  
  const [reportNodes, setReportNodes] = useState<Node[]>(() => 
    loadFromStorage('reportNodes', initialReportNodes)
  );
  const [reportEdges, setReportEdges] = useState<Edge[]>(() => 
    loadFromStorage('reportEdges', [])
  );

  // 持久化存储到localStorage
  useEffect(() => {
    localStorage.setItem('collectionNodes', JSON.stringify(collectionNodes));
  }, [collectionNodes]);

  useEffect(() => {
    localStorage.setItem('collectionEdges', JSON.stringify(collectionEdges));
  }, [collectionEdges]);

  useEffect(() => {
    localStorage.setItem('reportNodes', JSON.stringify(reportNodes));
  }, [reportNodes]);

  useEffect(() => {
    localStorage.setItem('reportEdges', JSON.stringify(reportEdges));
  }, [reportEdges]);

  return (
    <div className="h-screen w-full bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="px-6 py-4">
          <h1 className="text-slate-800">建筑工程智能报告平台</h1>
          <p className="text-slate-500 text-sm mt-1">建筑工程检测报告自动化生成系统</p>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="bg-white border-b border-slate-200 px-6">
            <TabsList className="bg-transparent border-none h-auto p-0 gap-8">
              <TabsTrigger 
                value="collection"
                className="relative px-4 py-3 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none bg-transparent text-slate-600 data-[state=active]:text-blue-600 transition-all"
              >
                信息采集
              </TabsTrigger>
              <TabsTrigger 
                value="report"
                className="relative px-4 py-3 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none bg-transparent text-slate-600 data-[state=active]:text-blue-600 transition-all"
              >
                报告
              </TabsTrigger>
              <TabsTrigger 
                value="review"
                className="relative px-4 py-3 rounded-none border-b-2 border-transparent data-[state=active]:border-blue-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none bg-transparent text-slate-600 data-[state=active]:text-blue-600 transition-all"
              >
                审核
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="collection" className="flex-1 m-0 p-0">
            <DataCollectionEditor 
              initialNodes={collectionNodes}
              initialEdges={collectionEdges}
              onNodesChange={setCollectionNodes}
              onEdgesChange={setCollectionEdges}
            />
          </TabsContent>

          <TabsContent value="report" className="flex-1 m-0 p-0">
            <ReportEditor 
              initialNodes={reportNodes}
              initialEdges={reportEdges}
              onNodesChange={setReportNodes}
              onEdgesChange={setReportEdges}
            />
          </TabsContent>

          <TabsContent value="review" className="flex-1 m-0 p-0">
            <ReviewPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}