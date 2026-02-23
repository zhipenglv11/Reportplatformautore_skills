import React from 'react';
import { FileText, Share2, Download, Copy, X } from 'lucide-react';

interface ReportPreviewProps {
  isGenerating?: boolean;
  chapters?: Array<{
    chapter_id: string;
    title: string;
    chapter_content: {
      blocks: Array<any>;
    };
  }>;
  onClose?: () => void;
}

const CN_NUM = '一二三四五六七八九十';

function getPreviewChapterTitle(title: string): string {
  const raw = String(title || '').trim();
  if (!raw) return '未命名章节';

  const separatedNumberTitle = raw.match(/^(?:第?\s*\d+(?:\.\d+)*\s*(?:章|节)?|[一二三四五六七八九十]+)[、.．。:：\-—\s]+(.+)$/);
  if (separatedNumberTitle?.[1]?.trim()) {
    return separatedNumberTitle[1].trim();
  }

  const directNumberPrefix = raw.match(/^\d+(?:\.\d+)+(?!\d)(.+)$/);
  if (directNumberPrefix?.[1]?.trim()) {
    return directNumberPrefix[1].trim();
  }

  return raw;
}

function getLineClass(line: string): string {
  if (!line) return 'text-gap';

  const isCnSection = new RegExp(`^（[${CN_NUM}]+）`).test(line) || new RegExp(`^\\([${CN_NUM}]+\\)`).test(line);
  if (isCnSection) return 'report-section-title';

  // 编号段落不做首行缩进，确保“编号+正文”与续行左侧对齐
  if (/^\d+[.、]/.test(line)) return 'report-text no-indent';
  if (/^\d+[)）]/.test(line)) return 'report-text no-indent';
  if (/^[（(]\d+[）)]/.test(line)) return 'report-text no-indent';

  return 'report-text indent-2';
}

export function ReportPreview({ isGenerating = false, chapters = [], onClose }: ReportPreviewProps) {
  return (
    <div className="h-full flex flex-col bg-slate-50 min-h-0 w-full relative">
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
        .report-title {
          font-family: "SimHei", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
          font-size: 24px;
          font-weight: 700;
          text-align: left;
          line-height: 1.45;
          margin-bottom: 4px;
          color: #0f172a;
        }
        .report-section-title {
          font-family: "SimHei", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
          font-size: 19px;
          font-weight: 700;
          text-indent: 2em;
          line-height: 1.65;
          margin-bottom: 4px;
          color: #0f172a;
        }
        .report-text {
          font-family: "FangSong", "STFangsong", "FangSong_GB2312", "SimSun", "Songti SC", "Noto Serif SC", serif;
          font-size: 16px;
          line-height: 1.85;
          letter-spacing: 0.01em;
          color: #0f172a;
        }
        .report-subtitle {
          font-family: "SimHei", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
          font-size: 17px;
          font-weight: 700;
          line-height: 1.6;
          color: #334155;
        }
        .report-item-row {
          margin-top: 6px;
          line-height: 1.85;
        }
        .report-item-label {
          font-family: "SimHei", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
          font-size: 16px;
          font-weight: 700;
          color: #0f172a;
        }
        .report-item-value {
          font-family: "FangSong", "STFangsong", "FangSong_GB2312", "SimSun", "Songti SC", "Noto Serif SC", serif;
          font-size: 16px;
          line-height: 1.85;
          color: #0f172a;
        }
        .report-table {
          width: 100%;
          table-layout: fixed;
          border-collapse: collapse;
          border: 1px solid #cbd5e1;
        }
        .report-table th {
          font-family: "SimHei", "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif;
          font-size: 15px;
          font-weight: 700;
          color: #334155;
          border: 1px solid #cbd5e1;
          padding: 7px 10px;
          line-height: 1.6;
          text-align: left;
          background: #f8fafc;
        }
        .report-table td {
          font-family: "FangSong", "STFangsong", "FangSong_GB2312", "SimSun", "Songti SC", "Noto Serif SC", serif;
          font-size: 15px;
          color: #0f172a;
          border: 1px solid #cbd5e1;
          padding: 7px 10px;
          line-height: 1.75;
          vertical-align: top;
        }
        .indent-2 {
          text-indent: 2em;
        }
        .indent-4 {
          text-indent: 4em;
        }
        .hang-indent-2 {
          padding-left: 2em;
          text-indent: -2em;
        }
        .no-indent {
          text-indent: 0;
          padding-left: 0;
        }
        .text-gap {
          height: 10px;
        }
      `}</style>

      <div className="flex-none flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white z-10">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-slate-100 rounded-md">
            <FileText className="w-4 h-4 text-slate-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              {isGenerating ? 'AI 正在生成报告...' : '报告预览'}
            </h3>
            <p className="text-xs text-slate-500">
              {isGenerating ? '请稍候' : '展示标题、段落与表格'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!isGenerating && (
            <>
              <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="复制">
                <Copy className="w-4 h-4" />
              </button>
              <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="下载">
                <Download className="w-4 h-4" />
              </button>
              <button className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors" title="分享">
                <Share2 className="w-4 h-4" />
              </button>
            </>
          )}
          {onClose && (
            <>
              <div className="h-4 w-px bg-slate-200 mx-1" />
              <button
                onClick={onClose}
                className="p-1.5 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors"
                title="关闭预览"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-white min-h-0 custom-scrollbar">
        <div className="w-full max-w-5xl mx-auto bg-white min-h-full px-10 py-10">
          {isGenerating ? (
            <div className="space-y-4">
              <div className="h-5 bg-slate-100 rounded w-1/3 animate-pulse" />
              <div className="h-24 bg-slate-100 rounded animate-pulse" />
              <div className="h-24 bg-slate-100 rounded animate-pulse" />
            </div>
          ) : chapters.length > 0 ? (
            <div className="space-y-8">
              {chapters.map((chapter) => (
                <section key={chapter.chapter_id} className="space-y-3">
                  <h2 className="report-title">{getPreviewChapterTitle(chapter.title)}</h2>

                  <div className="space-y-4">
                    {(chapter.chapter_content?.blocks || []).map((block: any, index: number) => {
                      if (block.type === 'note') {
                        return (
                          <div
                            key={`${chapter.chapter_id}-note-${index}`}
                            className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700"
                          >
                            {block.text || '暂无提示'}
                          </div>
                        );
                      }

                      if (block.type === 'table') {
                        const columns = block.columns || [];
                        const headerRows = Array.isArray(block.header_rows) ? block.header_rows : [];
                        const bodyRows = Array.isArray(block.body_rows) ? block.body_rows : [];
                        const rows = block.rows || [];
                        const firstColKey = columns[0]?.key;
                        const shouldAutoMergeBearingHeader =
                          headerRows.length === 0 &&
                          Array.isArray(columns) &&
                          columns.length >= 6 &&
                          String(columns[0]?.label || '').includes('鉴定对象') &&
                          String(columns[1]?.label || '').includes('构件类别') &&
                          String(columns[2]?.label || '').includes('墙体类型') &&
                          String(columns[3]?.label || '').includes('鉴定范围') &&
                          String(columns[4]?.label || '').includes('承载能力') &&
                          String(columns[5]?.label || '').includes('结论');
                        const effectiveHeaderRows = shouldAutoMergeBearingHeader
                          ? [[
                              { label: '鉴定对象（构件）', colSpan: 4 },
                              { label: columns[4]?.label || '承载能力 φR/γ0S' },
                              { label: columns[5]?.label || '结论' },
                            ]]
                          : headerRows;

                        // 首列空值自动并入上一个非空单元格，用于“同一层主要/一般构件”场景。
                        const firstColRowspan = Array.isArray(rows) ? new Array(rows.length).fill(1) : [];
                        const firstColHidden = Array.isArray(rows) ? new Array(rows.length).fill(false) : [];
                        if (firstColKey && Array.isArray(rows)) {
                          let anchor = -1;
                          rows.forEach((row: any, idx: number) => {
                            const v = String(row?.[firstColKey] ?? '').trim();
                            if (v) {
                              anchor = idx;
                              return;
                            }
                            if (anchor >= 0) {
                              firstColRowspan[anchor] += 1;
                              firstColHidden[idx] = true;
                            }
                          });
                        }

                        return (
                          <div key={`${chapter.chapter_id}-table-${index}`} className="space-y-2">
                            <div className="report-subtitle text-center">{block.title || '表格'}</div>
                            <div className="overflow-x-auto">
                              <table className="report-table">
                                <thead>
                                  {effectiveHeaderRows.length > 0 ? (
                                    effectiveHeaderRows.map((headerRow: any[], headerRowIndex: number) => (
                                      <tr key={`header-row-${headerRowIndex}`}>
                                        {headerRow.map((cell: any, cellIndex: number) => (
                                          <th
                                            key={`header-cell-${headerRowIndex}-${cellIndex}`}
                                            colSpan={cell?.colSpan || 1}
                                            rowSpan={cell?.rowSpan || 1}
                                          >
                                            {cell?.label ?? ''}
                                          </th>
                                        ))}
                                      </tr>
                                    ))
                                  ) : (
                                    <tr>
                                      {columns.map((col: any) => (
                                        <th key={col.key}>{col.label}</th>
                                      ))}
                                    </tr>
                                  )}
                                </thead>
                                <tbody>
                                  {bodyRows.length > 0 ? (
                                    bodyRows.map((row: any[], rowIndex: number) => (
                                      <tr key={rowIndex}>
                                        {Array.isArray(row) && row.length > 0 ? (
                                          row.map((cell: any, cellIndex: number) => (
                                            <td
                                              key={`body-cell-${rowIndex}-${cellIndex}`}
                                              colSpan={cell?.colSpan || 1}
                                              rowSpan={cell?.rowSpan || 1}
                                            >
                                              {cell?.text ?? ''}
                                            </td>
                                          ))
                                        ) : (
                                          <td colSpan={columns.length || 1} className="text-center text-slate-400">
                                            暂无数据
                                          </td>
                                        )}
                                      </tr>
                                    ))
                                  ) : rows.length > 0 ? (
                                    rows.map((row: any, rowIndex: number) => {
                                      const values = columns.map((col: any) => String(row?.[col.key] ?? '').trim());
                                      const isSingleCellNoteRow =
                                        values.length > 1 && values[0] && values.slice(1).every((v: string) => !v);
                                      const isTwoCellNoteRow =
                                        values.length > 2 &&
                                        /^注[:：]?$/.test(values[0]) &&
                                        !!values[1] &&
                                        values.slice(2).every((v: string) => !v);
                                      const isNoteRow = isSingleCellNoteRow || isTwoCellNoteRow;
                                      if (isNoteRow) {
                                        const mergedText = isTwoCellNoteRow ? `${values[0]} ${values[1]}` : values[0];
                                        return (
                                          <tr key={rowIndex}>
                                            <td colSpan={columns.length || 1}>{mergedText}</td>
                                          </tr>
                                        );
                                      }
                                      return (
                                        <tr key={rowIndex}>
                                          {columns.map((col: any, colIndex: number) => {
                                            if (colIndex === 0 && firstColHidden[rowIndex]) {
                                              return null;
                                            }
                                            return (
                                              <td
                                                key={col.key}
                                                rowSpan={colIndex === 0 ? firstColRowspan[rowIndex] : undefined}
                                              >
                                                {row[col.key] ?? ''}
                                              </td>
                                            );
                                          })}
                                        </tr>
                                      );
                                    })
                                  ) : (
                                    <tr>
                                      <td colSpan={columns.length || 1} className="text-center text-slate-400">
                                        暂无数据
                                      </td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        );
                      }

                      if (block.type === 'kv_list') {
                        const items = Array.isArray(block.items) ? block.items : [];
                        return (
                          <div key={`${chapter.chapter_id}-kv-${index}`} className="space-y-2">
                            {items.map((item: any, itemIndex: number) => {
                              const label = String(item?.label || '').trim();
                              const value = String(item?.value || '').trim();
                              if (!label && !value) return null;

                              return (
                                <div key={`${chapter.chapter_id}-kv-${index}-${itemIndex}`} className="report-item-row">
                                  <span className="report-item-label">{label}：</span>
                                  <span className="report-item-value">{value || '—'}</span>
                                </div>
                              );
                            })}
                          </div>
                        );
                      }

                      if (block.type === 'text') {
                        const lines = String(block.text || '')
                          .split('\n')
                          .map((line) => line.trim());

                        return (
                          <div key={`${chapter.chapter_id}-text-${index}`} className="space-y-1">
                            {lines.length === 0 ? (
                              <p className="report-text indent-2">暂无文本</p>
                            ) : (
                              lines.map((line, lineIndex) => (
                                <p
                                  key={`${chapter.chapter_id}-text-${index}-${lineIndex}`}
                                  className={getLineClass(line)}
                                >
                                  {line}
                                </p>
                              ))
                            )}
                          </div>
                        );
                      }

                      return null;
                    })}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-400 py-16">
              <div className="text-sm font-medium">暂无预览数据</div>
              <div className="text-xs mt-1">请先生成报告章节</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
