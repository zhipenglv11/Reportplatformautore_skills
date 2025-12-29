import { memo } from 'react';
import { FlaskConical, Cylinder, BrickWall, Cable, Ruler, TestTube } from 'lucide-react';

const getIcon = (type: string) => {
  switch (type) {
    case 'mortar-strength':
      return <FlaskConical className="w-5 h-5" />;
    case 'concrete-strength':
      return <Cylinder className="w-5 h-5" />;
    case 'rebar-diameter':
      return <Cable className="w-5 h-5" />;
    case 'brick-strength':
      return <BrickWall className="w-5 h-5" />;
    case 'inclination':
      return <Ruler className="w-5 h-5" />;
    case 'material-test':
      return <TestTube className="w-5 h-5" />;
    default:
      return <TestTube className="w-5 h-5" />;
  }
};

const getColor = (type: string) => {
  switch (type) {
    case 'mortar-strength':
      return 'from-blue-500 to-blue-600';
    case 'concrete-strength':
      return 'from-indigo-500 to-indigo-600';
    case 'rebar-diameter':
      return 'from-violet-500 to-violet-600';
    case 'brick-strength':
      return 'from-rose-500 to-rose-600';
    case 'inclination':
      return 'from-amber-500 to-amber-600';
    case 'material-test':
      return 'from-emerald-500 to-emerald-600';
    default:
      return 'from-blue-500 to-blue-600';
  }
};

const getBorderColor = (type: string) => {
  switch (type) {
    case 'mortar-strength':
      return 'border-blue-200 hover:border-blue-300';
    case 'concrete-strength':
      return 'border-indigo-200 hover:border-indigo-300';
    case 'rebar-diameter':
      return 'border-violet-200 hover:border-violet-300';
    case 'brick-strength':
      return 'border-rose-200 hover:border-rose-300';
    case 'inclination':
      return 'border-amber-200 hover:border-amber-300';
    case 'material-test':
      return 'border-emerald-200 hover:border-emerald-300';
    default:
      return 'border-blue-200 hover:border-blue-300';
  }
};

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'mortar-strength': '砂浆强度',
    'concrete-strength': '混凝土强度',
    'rebar-diameter': '钢筋直径',
    'brick-strength': '砖强度',
    'inclination': '倾斜测量',
    'material-test': '材料检测',
  };
  return labels[type] || '数据输入';
};

function CollectionNode({ data }: any) {
  return (
    <div className={`bg-white rounded-lg shadow-lg border-2 ${getBorderColor(data.type)} min-w-[260px] overflow-hidden hover:shadow-xl transition-all cursor-pointer`}>
      <div className={`bg-gradient-to-r ${getColor(data.type)} p-3 text-white flex items-center gap-2`}>
        {getIcon(data.type)}
        <span className="font-medium">{data.label}</span>
      </div>
      
      <div className="p-4 text-sm text-slate-600">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-slate-500">类型:</span>
          <span className="text-xs font-medium">{getTypeLabel(data.type)}</span>
        </div>
        
        {data.fields && data.fields.length > 0 && (
          <div className="mb-2">
            <div className="text-xs text-slate-500 mb-2">
              {data.fields.length} 个字段已配置
            </div>
            <div className="space-y-1">
              {data.fields.slice(0, 3).map((field: any, index: number) => (
                <div key={index} className="text-xs text-slate-600 flex items-center gap-1">
                  <div className="w-1 h-1 rounded-full bg-slate-400"></div>
                  {field.label}
                </div>
              ))}
              {data.fields.length > 3 && (
                <div className="text-xs text-slate-400">
                  + {data.fields.length - 3} 更多字段
                </div>
              )}
            </div>
          </div>
        )}

        <div className="text-xs text-slate-400 text-center mt-3 pt-2 border-t border-slate-100">
          点击节点查看详情
        </div>
      </div>
    </div>
  );
}

export default memo(CollectionNode);