import { Node, Edge } from 'reactflow';
import { FileText, Plus, Trash2 } from 'lucide-react';

interface ReportChapterTreeProps {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  onAddSubChapter: (parentId: string) => void;
  onDeleteNode: (nodeId: string) => void;
}

export function ReportChapterTree({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode,
  onAddSubChapter,
  onDeleteNode,
}: ReportChapterTreeProps) {
  const parseChapterNumber = (value: string): number[] => {
    if (!value || value.trim() === '') return [Number.MAX_SAFE_INTEGER];
    return value
      .split('.')
      .map((part) => Number.parseInt(part, 10))
      .map((num) => (Number.isFinite(num) ? num : Number.MAX_SAFE_INTEGER));
  };

  const compareByChapterNumber = (a: Node, b: Node): number => {
    const aNum = String(a.data?.chapterNumber || '');
    const bNum = String(b.data?.chapterNumber || '');
    const aKey = parseChapterNumber(aNum);
    const bKey = parseChapterNumber(bNum);
    const maxLen = Math.max(aKey.length, bKey.length);

    for (let i = 0; i < maxLen; i += 1) {
      const av = aKey[i] ?? 0;
      const bv = bKey[i] ?? 0;
      if (av !== bv) return av - bv;
    }

    return String(a.data?.label || '').localeCompare(String(b.data?.label || ''), 'zh-CN');
  };

  const nodeMap = new Map((nodes || []).map((node) => [node.id, node]));
  const childrenMap = new Map<string, Node[]>();
  const hasParent = new Set<string>();

  (edges || []).forEach((edge) => {
    const parent = nodeMap.get(edge.source);
    const child = nodeMap.get(edge.target);
    if (!parent || !child) return;

    const children = childrenMap.get(parent.id) || [];
    children.push(child);
    childrenMap.set(parent.id, children);
    hasParent.add(child.id);
  });

  const rootNodes = (nodes || []).filter((node) => !hasParent.has(node.id)).sort(compareByChapterNumber);

  const renderNode = (node: Node, level: number): JSX.Element => {
    const isSelected = node.id === selectedNodeId;
    const children = (childrenMap.get(node.id) || []).sort(compareByChapterNumber);

    return (
      <div key={node.id} className="space-y-1">
        <div
          className={`group flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
            isSelected ? 'bg-slate-200 text-slate-900' : 'hover:bg-slate-100 text-slate-700'
          }`}
          style={{ paddingLeft: `${8 + level * 16}px` }}
          onClick={() => onSelectNode(node.id)}
        >
          <FileText className="w-4 h-4 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium truncate">
              {node.data.chapterNumber && <span className="text-slate-500 mr-1">{node.data.chapterNumber}</span>}
              {node.data.label || '未命名章节'}
            </div>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddSubChapter(node.id);
              }}
              className="p-1 hover:bg-slate-200 rounded"
              title="添加子章节"
            >
              <Plus className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteNode(node.id);
              }}
              className="p-1 hover:bg-red-100 rounded text-red-600"
              title="删除"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </div>
        {children.map((child) => renderNode(child, level + 1))}
      </div>
    );
  };

  return (
    <div className="space-y-1">
      {rootNodes.map((node) => renderNode(node, 0))}
      {nodes.length === 0 && <div className="text-center py-8 text-slate-400 text-xs">暂无章节，点击上方按钮添加</div>}
    </div>
  );
}
