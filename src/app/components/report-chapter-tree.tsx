import { Node, Edge } from 'reactflow';
import { Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

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
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
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
    const hasChildren = children.length > 0;
    const isOpen = !collapsed[node.id];

    return (
      <div key={node.id} className="space-y-0.5">
        <div
          data-nodeid={node.id}
          className={`group grid items-center py-1.5 pr-1 rounded-md cursor-pointer transition-colors ${
            isSelected ? 'bg-slate-200 text-slate-900' : 'hover:bg-slate-100 text-slate-700'
          }`}
          style={{
            paddingLeft: `${12 + level * 24}px`,
            gridTemplateColumns: '16px 1fr auto',
          }}
          onClick={() => onSelectNode(node.id)}
        >
          {/* 展开/折叠三角 — 列1：固定16px */}
          {hasChildren ? (
            <button
              className="w-4 h-4 flex items-center justify-center rounded hover:bg-slate-300 text-slate-500 hover:text-slate-700 transition-colors"
              onClick={e => {
                e.stopPropagation();
                setCollapsed(prev => ({ ...prev, [node.id]: !prev[node.id] }));
              }}
            >
              {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </button>
          ) : (
            <span className="w-4 h-4" />
          )}

          {/* 文字区 — 列2：1fr，超长文字截断省略 */}
          <div className="overflow-hidden pl-1">
            <div className="text-xs font-medium truncate text-slate-700 text-left" title={`${node.data.chapterNumber ? node.data.chapterNumber + ' ' : ''}${node.data.label || '未命名章节'}`}>
              {node.data.chapterNumber && <span className="text-slate-400 mr-1.5 font-mono text-[10px]">{node.data.chapterNumber}</span>}
              {node.data.label || '未命名章节'}
            </div>
          </div>

          {/* 操作按钮 — 列3：auto，永远不被压缩，位置固定 */}
          <div className="flex items-center gap-0.5 ml-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddSubChapter(node.id);
              }}
              className="p-1 rounded text-slate-300 hover:bg-slate-300 hover:text-slate-900 transition-colors"
              title="添加子章节"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteNode(node.id);
              }}
              className="p-1 rounded text-slate-300 hover:bg-red-100 hover:text-red-600 transition-colors"
              title="删除"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        {hasChildren && isOpen && (
          <div className="mt-0.5 space-y-0.5">
            {children.map((child) => renderNode(child, level + 1))}
          </div>
        )}
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
