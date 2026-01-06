import { memo } from 'react';
import { FlaskConical, Cylinder, BrickWall, Cable, Ruler, TestTube, ClipboardCheck } from 'lucide-react';

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
    case 'site-inspection':
      return <ClipboardCheck className="w-5 h-5" />;
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
    case 'site-inspection':
      return 'from-teal-500 to-teal-600';
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
    case 'site-inspection':
      return 'border-teal-200 hover:border-teal-300';
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
    'site-inspection': '现场情况检查',
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
      
      <div className="p-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">类型:</span>
          <span className="text-xs font-medium text-slate-700">{getTypeLabel(data.type)}</span>
        </div>
      </div>
    </div>
  );
}

export default memo(CollectionNode);