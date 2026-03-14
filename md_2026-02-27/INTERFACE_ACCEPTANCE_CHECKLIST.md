# AutoRe 接口验收清单（模板）

## 1. 文档目的
本清单用于验证 API 与 Skill 输出是否符合已冻结的接口级 Schema，确保：
1. 联调一致。
2. 回归可追踪。
3. 版本发布可验收。

## 2. 验收范围
1. `POST /api/report/generate`
2. `POST /api/skill/{skill_name}/run`
3. `POST /api/skill/confirm`
4. `POST /api/ingest/commit`
5. 错误返回结构（`detail`）
6. Skill 输出契约（Ingest/Parse/Mapping/Validation/Declarative/Generation）

## 3. 前置条件
| 项 | 说明 |
|---|---|
| 后端服务 | `uvicorn main:app --reload --port 8000` |
| 测试数据库 | 测试环境独立库，含最小模板与规则数据 |
| 测试样本 | 混凝土/砂浆/砖/委托信息/计算书各1份 |
| 校验基线 | `backend/schemas/interface/*.json`, `backend/schemas/skills/*.json` |

## 4. 冒烟测试
| 用例ID | 接口 | 场景 | 输入摘要 | 期望HTTP | 期望断言 |
|---|---|---|---|---|---|
| SMK-001 | `/api/skill/{skill_name}/run` | 单文件技能执行成功 | 合法PDF + `persist_result=false` | 200 | `success=true` 且 `records` 为数组 |
| SMK-002 | `/api/skill/confirm` | 确认并落库成功 | 合法 `records` | 200 | `success=true` 且返回 `run_id` |
| SMK-003 | `/api/report/generate` | 单章节生成成功 | 合法 `dataset_key` | 200 | `chapters[0].chapter_content.blocks` 非空 |
| SMK-004 | `/api/ingest/commit` | 选模板提交成功 | 合法 `selections` | 200 | `results[*].status` 存在 |

## 5. 失败路径测试
| 用例ID | 接口 | 场景 | 输入摘要 | 期望HTTP | 期望断言 |
|---|---|---|---|---|---|
| ERR-001 | `/api/skill/{skill_name}/run` | 文件类型不支持 | 上传 `.exe` | 4xx | `detail` 存在 |
| ERR-002 | `/api/skill/confirm` | records为空 | `records=[]` | 400 | `detail` 明确说明空记录 |
| ERR-003 | `/api/report/generate` | dataset_key无效 | 不支持键值 | 4xx/5xx | 返回标准错误结构 |
| ERR-004 | `/api/ingest/commit` | 模板不存在 | 错误 `template_id` | 200/4xx | `results[*].status=failed` 或标准错误 |

## 6. 契约一致性检查
| 检查项 | 方法 | 通过标准 |
|---|---|---|
| 请求结构一致性 | 用 schema 校验请求体 | 必填字段不缺失，类型正确 |
| 响应结构一致性 | 用 schema 校验响应体 | 关键字段齐全，类型正确 |
| 错误结构一致性 | 人造错误请求 | 返回 `detail` |
| Skill输出一致性 | 打点或单测调用skill | 输出满足 `backend/schemas/skills/*.json` |

## 7. 回归记录表（执行时填写）
| 日期 | 环境 | 用例ID | 结果(PASS/FAIL) | 缺陷ID | 备注 |
|---|---|---|---|---|---|
| YYYY-MM-DD | dev/staging/prod |  |  |  |  |

## 8. 发布门禁建议
1. 冒烟用例 100% 通过。
2. 失败路径核心用例 100% 通过。
3. 无 P0/P1 未解决缺陷。
4. 契约变更必须同步更新 Schema 与 PRD 附录。
