import { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';

interface NodeEditorProps {
  node: any;
  onClose: () => void;
  onUpdate: (node: any) => void;
}

export default function NodeEditor({ node, onClose, onUpdate }: NodeEditorProps) {
  const [label, setLabel] = useState(node.data.label);
  const [fields, setFields] = useState(node.data.fields || []);

  const addField = () => {
    setFields([...fields, { name: '', type: 'text', required: false }]);
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_: any, i: number) => i !== index));
  };

  const updateField = (index: number, key: string, value: any) => {
    const newFields = [...fields];
    newFields[index] = { ...newFields[index], [key]: value };
    setFields(newFields);
  };

  const handleSave = () => {
    onUpdate({
      ...node,
      data: {
        ...node.data,
        label,
        fields,
      },
    });
    onClose();
  };

  return (
    <div className="w-96 bg-white border-l border-slate-200 shadow-xl overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between z-10">
        <h3 className="text-slate-800">节点配置</h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-100 rounded transition-colors"
        >
          <X className="w-5 h-5 text-slate-500" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Node Name */}
        <div>
          <label className="block text-sm text-slate-600 mb-2">节点名称</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Fields */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm text-slate-600">字段配置</label>
            <button
              onClick={addField}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
            >
              <Plus className="w-4 h-4" />
              添加字段
            </button>
          </div>

          <div className="space-y-3">
            {fields.map((field: any, index: number) => (
              <div key={index} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-start justify-between mb-2">
                  <input
                    type="text"
                    placeholder="字段名称"
                    value={field.name}
                    onChange={(e) => updateField(index, 'name', e.target.value)}
                    className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => removeField(index)}
                    className="ml-2 p-1 text-red-500 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex gap-2">
                  <select
                    value={field.type}
                    onChange={(e) => updateField(index, 'type', e.target.value)}
                    className="flex-1 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="text">文本</option>
                    <option value="number">数字</option>
                    <option value="date">日期</option>
                    <option value="file">文件</option>
                  </select>
                  <label className="flex items-center gap-1 text-sm text-slate-600">
                    <input
                      type="checkbox"
                      checked={field.required}
                      onChange={(e) => updateField(index, 'required', e.target.checked)}
                      className="rounded"
                    />
                    必填
                  </label>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="sticky bottom-0 bg-white border-t border-slate-200 p-4 flex gap-2">
        <button
          onClick={handleSave}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          保存
        </button>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
        >
          取消
        </button>
      </div>
    </div>
  );
}
