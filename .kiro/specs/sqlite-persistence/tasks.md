# 实施计划：SQLite 统一持久化

## 概述

将学习规划平台的数据存储从"后端内存字典 + 前端 localStorage"迁移到统一的 SQLite 持久化方案。按照以下顺序实施：后端数据库层 → 后端路由迁移 → 前端 Store 迁移 → 遗留清理 → 测试。

## 任务

- [x] 1. 创建 `backend/database.py` 数据访问层
  - [x] 1.1 实现连接管理和数据库初始化
    - 创建 `backend/database.py` 文件
    - 实现 `get_connection()` 函数（模块级 `_connection` 懒初始化）
    - 实现 `init_db()` 函数：创建 7 张表（plans、messages、materials、progress、notes、generated_contents、search_history）、启用 WAL 模式和外键约束
    - 使用 `CREATE TABLE IF NOT EXISTS` 保证幂等性
    - 实现 `_to_camel()` 和 `_to_snake()` 辅助函数用于字段命名转换
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 1.2 实现 Plans 表 CRUD 函数
    - 实现 `create_plan()`、`get_all_plans()`、`get_plan()`、`update_plan()`、`delete_plan()`
    - 所有写操作使用 `with conn:` 上下文管理器确保事务原子性
    - 返回值使用 `_to_camel()` 转换为 camelCase
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.3 实现 Messages 表 CRUD 函数
    - 实现 `insert_message()`、`get_messages(plan_id)`
    - `sources` 字段使用 `json.dumps`/`json.loads` 序列化
    - `get_messages` 按 `created_at` 升序返回
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 1.4 实现 Materials 表 CRUD 函数
    - 实现 `insert_material()`、`get_materials()`、`update_material_status()`、`update_material_extra_data()`、`delete_material()`
    - `extra_data` 字段使用 JSON 序列化
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 1.5 实现 Progress 表 CRUD 函数
    - 实现 `upsert_progress()`、`get_progress()`、`update_progress_completed()`、`update_progress_tasks()`
    - `tasks` 字段使用 JSON 序列化
    - `upsert_progress` 使用 `INSERT OR REPLACE` 处理 `(plan_id, day_number)` 唯一约束
    - `get_progress` 按 `day_number` 升序返回
    - `update_progress_completed` 同步更新 plans 表的 `completed_days`
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 1.6 实现 Notes 表 CRUD 函数
    - 实现 `create_note()`、`get_notes()`、`update_note()`、`delete_note()`
    - `update_note` 自动更新 `updated_at` 时间戳
    - `get_notes` 按 `updated_at` 降序返回
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 1.7 实现 Generated Contents 表 CRUD 函数
    - 实现 `insert_generated_content()`、`get_generated_contents()`
    - `get_generated_contents` 按 `created_at` 降序返回
    - _需求: 7.1, 7.2, 7.3_

  - [x] 1.8 实现 Search History 表 CRUD 函数
    - 实现 `insert_search_history()`、`get_search_history(limit=20)`、`delete_search_history()`
    - `platforms` 和 `results` 字段使用 JSON 序列化
    - `get_search_history` 按 `searched_at` 降序返回，最多 20 条
    - _需求: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2. 检查点 - 数据库层验证
  - 确保所有 database.py 函数可正常调用，如有问题请向用户确认。

- [x] 3. 迁移后端路由：plans.py
  - [x] 3.1 迁移 `backend/routers/plans.py`
    - 移除内存字典 `_plans`
    - `POST /api/plans` 改为调用 `database.create_plan()`
    - `GET /api/plans` 改为调用 `database.get_all_plans()`
    - `PUT /api/plans/{plan_id}` 改为调用 `database.update_plan()`
    - `DELETE /api/plans/{plan_id}` 改为调用 `database.delete_plan()`（级联删除），不存在时返回 404
    - _需求: 2.2, 2.3, 2.4, 2.5, 2.6, 10.2_

  - [x] 3.2 在 plans.py 中添加新的子资源端点
    - `GET /api/plans/{plan_id}/messages` → 调用 `database.get_messages()`
    - `GET /api/plans/{plan_id}/materials` → 调用 `database.get_materials()`
    - `POST /api/plans/{plan_id}/progress` → 调用 `database.upsert_progress()`
    - `GET /api/plans/{plan_id}/progress` → 调用 `database.get_progress()`
    - `PUT /api/plans/{plan_id}/progress/{day_number}` → 调用 `database.update_progress_completed()`
    - `PUT /api/plans/{plan_id}/progress/{day_number}/tasks` → 调用 `database.update_progress_tasks()`
    - `GET /api/plans/{plan_id}/notes` → 调用 `database.get_notes()`
    - `GET /api/plans/{plan_id}/generated-contents` → 调用 `database.get_generated_contents()`
    - `POST /api/plans/{plan_id}/generated-contents` → 调用 `database.insert_generated_content()`
    - `GET /api/plans/{plan_id}/search-history` → 调用 `database.get_search_history()`
    - `POST /api/plans/{plan_id}/search-history` → 调用 `database.insert_search_history()`
    - `DELETE /api/plans/{plan_id}/search-history` → 调用 `database.delete_search_history()`
    - _需求: 3.4, 4.4, 5.3, 5.4, 5.5, 5.6, 6.5, 7.3, 8.2, 8.3, 8.5_

- [x] 4. 迁移后端路由：notes.py、chat.py、upload.py
  - [x] 4.1 迁移 `backend/routers/notes.py`
    - 移除内存字典 `_notes`
    - `POST /api/notes` 改为调用 `database.create_note()`
    - `PUT /api/notes/{note_id}` 改为调用 `database.update_note()`
    - `DELETE /api/notes/{note_id}` 改为调用 `database.delete_note()`
    - _需求: 6.2, 6.3, 6.4, 10.3_

  - [x] 4.2 迁移 `backend/routers/chat.py`
    - 移除对 `store.py` 的依赖
    - 用户消息在 SSE 流开始前通过 `database.insert_message()` 写入
    - 助手消息在 SSE done 事件后通过 `database.insert_message()` 写入（含 sources）
    - _需求: 3.2, 3.3, 10.1_

  - [x] 4.3 迁移 `backend/routers/upload.py`
    - 移除对 `store.py` 的依赖
    - 文件上传和 URL 提交时通过 `database.insert_material()` 写入材料元数据
    - 解析状态变化时通过 `database.update_material_status()` 更新
    - 删除材料时通过 `database.delete_material()` 删除，并更新 plan 的 `source_count`
    - _需求: 4.2, 4.3, 4.5, 4.6, 10.6_

- [x] 5. 迁移后端路由：search.py、studio.py、resource.py
  - [x] 5.1 迁移 `backend/routers/search.py`
    - 搜索历史由前端在收到 done 事件后通过 `POST /api/plans/{plan_id}/search-history` 保存（后端不自动保存）
    - 移除对 `store.py` 的依赖（如有）
    - _需求: 8.2, 10.1_

  - [x] 5.2 迁移 `backend/routers/studio.py`
    - 内容生成完成后通过 `database.insert_generated_content()` 保存到 `generated_contents` 表
    - 移除对 `store.py` 的依赖（如有）
    - _需求: 7.2, 10.1_

  - [x] 5.3 迁移 `backend/routers/resource.py`
    - 资源刷新完成后通过 `database.update_material_extra_data()` 更新 `materials.extra_data`
    - _需求: 4.3, 10.1_

- [x] 6. 更新 `backend/main.py` 启动逻辑
  - 在 FastAPI startup 事件中调用 `database.init_db()`
  - 移除 session router 的注册（`session.py` 路由）
  - 确保数据库初始化失败时阻止服务启动并记录错误日志
  - _需求: 1.1, 1.6, 10.4, 10.5_

- [x] 7. 检查点 - 后端迁移验证
  - 确保所有后端路由正常工作，所有测试通过，如有问题请向用户确认。

- [x] 8. 迁移前端 Store
  - [x] 8.1 迁移 `frontend/src/store/planStore.ts`
    - 移除 `persist` 中间件
    - 移除 `_cache`、`_activePlanId`、`_hasHydrated` 等 localStorage 相关字段
    - 新增 `loading`、`error` 状态字段
    - 新增 `loadPlans()` 异步方法（`GET /api/plans`）
    - 写操作（addPlan、deletePlan、updatePlan）改为先调用 API 再更新本地状态
    - API 失败时保持本地状态不变，设置 error
    - _需求: 9.1, 9.2, 9.4, 9.5_

  - [x] 8.2 迁移 `frontend/src/store/chatStore.ts`
    - 移除 `persist` 中间件
    - 移除 localStorage 缓存相关字段
    - 新增 `loading` 状态字段
    - 新增 `loadMessages(planId)` 异步方法（`GET /api/plans/{planId}/messages`）
    - 消息持久化由后端 chat SSE 端点完成，前端不需要额外 POST 调用
    - _需求: 9.1, 9.2, 9.3_

  - [x] 8.3 迁移 `frontend/src/store/sourceStore.ts`
    - 移除 `persist` 中间件
    - 新增 `loading` 状态字段
    - 新增 `loadMaterials(planId)` 异步方法（`GET /api/plans/{planId}/materials`）
    - 删除材料改为先调用 `DELETE /api/material/{id}` 再更新本地状态
    - _需求: 9.1, 9.3, 9.4_

  - [x] 8.4 迁移 `frontend/src/store/studioStore.ts`
    - 移除 `persist` 中间件
    - 新增 `loading` 状态字段
    - 新增 `loadStudioData(planId)` 异步方法，使用 `Promise.all` 并行加载 progress、generated-contents、notes
    - 写操作（toggleDay、toggleTask、saveNote 等）改为先调用 API 再更新本地状态
    - _需求: 9.1, 9.3, 9.4_

  - [x] 8.5 迁移 `frontend/src/store/searchStore.ts`
    - 移除 `persist` 中间件
    - 新增 `loadHistory(planId)` 异步方法（`GET /api/plans/{planId}/search-history`）
    - `addEntry` 改为先 `POST /api/plans/{planId}/search-history` 再更新本地状态
    - `clearHistory` 改为先 `DELETE /api/plans/{planId}/search-history` 再清空本地
    - 加载时重建 `resultDetailMap`
    - _需求: 9.1, 9.3, 9.4_

  - [x] 8.6 更新 `frontend/src/pages/WorkspacePage.tsx`
    - 简化为 `Promise.all` 并行调用各 store 的 loadData 方法
    - 移除 `setActivePlan` 切换逻辑和 localStorage 恢复兜底
    - 加载期间展示加载状态（骨架屏）
    - _需求: 9.3, 9.6_

  - [x] 8.7 更新 `frontend/src/pages/HomePage.tsx`
    - 页面加载时调用 `planStore.loadPlans()` 从 API 获取规划列表
    - _需求: 9.3_

- [x] 9. 检查点 - 前端迁移验证
  - 确保前端所有 store 正常工作，页面加载和写操作流程正确，如有问题请向用户确认。

- [x] 10. 遗留数据清理
  - [x] 10.1 删除后端遗留文件
    - 删除 `backend/store.py`
    - 删除 `backend/routers/session.py`
    - 确认 `backend/main.py` 中已移除 session router 注册
    - _需求: 11.1, 11.2_

  - [x] 10.2 删除遗留数据文件
    - 删除 `data/sessions/` 目录及其中所有 JSON 文件
    - 删除 `data/index.json` 文件
    - _需求: 11.3, 11.4_

  - [x] 10.3 前端 localStorage 清理
    - 在应用初始化时（如 `main.tsx` 或 `App.tsx`）添加一次性清理逻辑
    - 清理 localStorage 中的旧 key：`plan-store`、`chat-store`、`source-store`、`studio-store`、`search-history`
    - _需求: 11.5_

- [x] 11. 检查点 - 清理验证
  - 确保删除的文件不再被引用，应用正常启动，如有问题请向用户确认。

- [ ]* 12. 后端属性测试
  - [ ]* 12.1 编写 Property 1 属性测试：Plan CRUD 往返一致性
    - **Property 1: Plan CRUD 往返一致性**
    - 使用 hypothesis 生成随机 title + description，验证创建→读取→更新→读取的数据一致性
    - 测试文件：`backend/tests/test_database_properties.py`
    - **验证: 需求 2.2, 2.3, 2.4**

  - [ ]* 12.2 编写 Property 2 属性测试：级联删除完整性
    - **Property 2: 级联删除完整性**
    - 创建 plan 及各子表数据，删除 plan 后验证所有 6 张子表中该 plan_id 的记录数为 0
    - **验证: 需求 2.5, 12.1, 12.2**

  - [ ]* 12.3 编写 Property 3 属性测试：Message 往返一致性
    - **Property 3: Message 往返一致性（含 JSON sources）**
    - 使用 hypothesis 生成随机 role + content + sources 数组，验证插入→读取的数据一致性和 JSON 反序列化正确性
    - **验证: 需求 3.2, 3.3, 3.5**

  - [ ]* 12.4 编写 Property 4 属性测试：列表查询排序不变量
    - **Property 4: 列表查询排序不变量**
    - 生成随机时间戳的多条记录，验证各表返回列表的排序正确性
    - **验证: 需求 3.4, 5.4, 6.5, 7.3, 8.3**

  - [ ]* 12.5 编写 Property 5 属性测试：Material 往返一致性
    - **Property 5: Material 往返一致性（含 extra_data JSON）**
    - 使用 hypothesis 生成随机 material + extra_data，验证插入→读取→更新 status 的数据一致性
    - **验证: 需求 4.2, 4.3, 4.4**

  - [ ]* 12.6 编写 Property 6 属性测试：Material 删除同步 source_count
    - **Property 6: Material 删除同步 source_count**
    - 创建 N 条 materials，删除一条后验证 source_count = N-1
    - **验证: 需求 4.5, 4.6**

  - [ ]* 12.7 编写 Property 7 属性测试：Progress 往返一致性
    - **Property 7: Progress 往返一致性（含 JSON tasks 和唯一约束）**
    - 使用 hypothesis 生成随机 progress 数据，验证批量写入→读取→更新 tasks 的一致性，以及 upsert 幂等性
    - **验证: 需求 5.2, 5.3, 5.6**

  - [ ]* 12.8 编写 Property 8 属性测试：Day 完成状态同步 completed_days
    - **Property 8: Day 完成状态同步 completed_days**
    - 随机标记 progress 完成状态，验证 plans.completed_days 等于 completed=1 的记录数
    - **验证: 需求 5.5**

  - [ ]* 12.9 编写 Property 9 属性测试：Note CRUD 往返一致性
    - **Property 9: Note CRUD 往返一致性（含 updated_at 更新）**
    - 使用 hypothesis 生成随机 title + content，验证创建→读取→更新→删除的完整生命周期
    - **验证: 需求 6.2, 6.3, 6.4**

  - [ ]* 12.10 编写 Property 10 属性测试：Search History 往返一致性
    - **Property 10: Search History 往返一致性（含 JSON 和条数限制）**
    - 使用 hypothesis 生成随机搜索历史，验证 JSON 反序列化、20 条限制和删除功能
    - **验证: 需求 8.2, 8.3, 8.4, 8.5**

  - [ ]* 12.11 编写 Property 11 属性测试：数据库初始化幂等性
    - **Property 11: 数据库初始化幂等性**
    - 插入数据后重复调用 init_db()，验证已有数据不变
    - **验证: 需求 1.5**

  - [ ]* 12.12 编写 Property 12 属性测试：事务原子性
    - **Property 12: 事务原子性**
    - 构造约束违反场景，验证数据库状态与操作前一致
    - **验证: 需求 12.3, 12.4**

- [x] 13. 最终检查点 - 全部验证
  - 确保所有测试通过，应用可正常启动和使用，如有问题请向用户确认。

## 备注

- 标记 `*` 的任务为可选，可跳过以加速 MVP 交付
- 每个任务引用了具体的需求编号，确保可追溯性
- 检查点任务用于阶段性验证，确保增量正确性
- 属性测试验证设计文档中定义的 12 个正确性属性
- 不重构 `src/` 目录下的 agents、providers、rag、specialists 等已有代码，只做增量修改
