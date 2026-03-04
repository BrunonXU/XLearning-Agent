# 需求文档：SQLite 统一持久化

## 简介

将学习规划平台的数据存储架构从分散的"后端内存字典 + 前端 localStorage"迁移到统一的 SQLite 持久化方案。SQLite 数据库文件位于 `data/app.db`，作为唯一数据源（Single Source of Truth）。前端 zustand store 去掉 `persist` 中间件，改为普通 store + 后端 API 调用。后端内存字典（`_store`、`_plans`、`_notes`）全部替换为 SQLite 读写。磁盘文件（uploads、chroma、cookies）保持不变。

## 术语表

- **Database_Layer**: 后端 SQLite 数据访问层，封装所有数据库读写操作，位于 `backend/database.py`
- **API_Server**: FastAPI 后端应用，提供 REST API 供前端调用
- **Frontend_Store**: 前端 zustand 状态管理 store，不再使用 persist 中间件，改为从 API 获取数据
- **Plan**: 学习规划，包含标题、描述、来源数量、学习天数等元数据
- **Message**: 聊天消息，属于某个 Plan，包含角色、内容、引用来源
- **Material**: 学习材料元数据，属于某个 Plan，包含类型、名称、URL、解析状态
- **Progress**: 学习进度，属于某个 Plan，包含每日任务及完成状态
- **Note**: 用户笔记，属于某个 Plan，包含标题和 Markdown 内容
- **Generated_Content**: AI 生成的学习内容，属于某个 Plan，包含类型、标题和 Markdown 内容
- **Search_History**: 搜索历史记录，属于某个 Plan，包含查询词、平台列表和搜索结果

## 需求

### 需求 1：SQLite 数据库初始化

**用户故事：** 作为开发者，我希望后端启动时自动创建并初始化 SQLite 数据库，以便应用无需手动配置即可使用持久化存储。

#### 验收标准

1. WHEN API_Server 启动时，THE Database_Layer SHALL 在 `data/app.db` 路径创建 SQLite 数据库文件（如果文件不存在）
2. WHEN 数据库文件创建后，THE Database_Layer SHALL 执行建表语句创建以下表：`plans`、`messages`、`materials`、`progress`、`notes`、`generated_contents`、`search_history`
3. THE Database_Layer SHALL 启用 WAL 模式（`PRAGMA journal_mode=WAL`）以提高读写并发性能
4. THE Database_Layer SHALL 启用外键约束（`PRAGMA foreign_keys=ON`）
5. WHEN 数据库文件已存在且表结构完整时，THE Database_Layer SHALL 跳过建表操作，保留已有数据
6. IF 数据库文件创建失败（如磁盘空间不足或权限不足），THEN THE Database_Layer SHALL 记录错误日志并抛出异常，阻止 API_Server 启动

### 需求 2：Plans 表持久化

**用户故事：** 作为用户，我希望创建的学习规划在后端重启后仍然存在，以便我不会丢失已创建的规划。

#### 验收标准

1. THE Database_Layer SHALL 提供 `plans` 表，包含字段：`id`（TEXT 主键）、`title`（TEXT 非空）、`description`（TEXT）、`source_count`（INTEGER 默认 0）、`last_accessed_at`（TEXT）、`cover_color`（TEXT）、`total_days`（INTEGER 默认 0）、`completed_days`（INTEGER 默认 0）、`created_at`（TEXT 非空）
2. WHEN 用户通过 `POST /api/plans` 创建规划时，THE API_Server SHALL 将规划数据写入 `plans` 表
3. WHEN 用户通过 `GET /api/plans` 请求规划列表时，THE API_Server SHALL 从 `plans` 表读取所有规划并返回
4. WHEN 用户通过 `PUT /api/plans/{plan_id}` 更新规划时，THE API_Server SHALL 更新 `plans` 表中对应记录
5. WHEN 用户通过 `DELETE /api/plans/{plan_id}` 删除规划时，THE API_Server SHALL 删除 `plans` 表中对应记录，并级联删除该规划关联的所有 Message、Material、Progress、Note、Generated_Content 和 Search_History 数据
6. IF 删除的 plan_id 在 `plans` 表中不存在，THEN THE API_Server SHALL 返回 HTTP 404 状态码

### 需求 3：Messages 表持久化

**用户故事：** 作为用户，我希望聊天记录在刷新页面或重启后端后仍然保留，以便我可以回顾之前的对话。

#### 验收标准

1. THE Database_Layer SHALL 提供 `messages` 表，包含字段：`id`（TEXT 主键）、`plan_id`（TEXT 非空，外键关联 `plans.id`）、`role`（TEXT 非空，值为 'user'、'assistant' 或 'system'）、`content`（TEXT 非空）、`sources`（TEXT，JSON 格式存储引用来源数组）、`created_at`（TEXT 非空）
2. WHEN 用户发送聊天消息时，THE API_Server SHALL 将用户消息写入 `messages` 表
3. WHEN AI 回复完成时，THE API_Server SHALL 将助手消息（含引用来源）写入 `messages` 表
4. WHEN 前端通过 `GET /api/plans/{plan_id}/messages` 请求消息列表时，THE API_Server SHALL 从 `messages` 表读取该规划的所有消息，按 `created_at` 升序返回
5. WHEN 前端请求消息列表时，THE API_Server SHALL 将 `sources` 字段从 JSON 字符串反序列化为对象数组后返回

### 需求 4：Materials 表持久化

**用户故事：** 作为用户，我希望上传的学习材料元数据在后端重启后仍然保留，以便我不需要重新上传文件。

#### 验收标准

1. THE Database_Layer SHALL 提供 `materials` 表，包含字段：`id`（TEXT 主键）、`plan_id`（TEXT 非空，外键关联 `plans.id`）、`type`（TEXT 非空）、`name`（TEXT 非空）、`url`（TEXT）、`status`（TEXT 非空，默认 'parsing'）、`added_at`（TEXT 非空）、`extra_data`（TEXT，JSON 格式存储搜索来源的附加信息，如 contentSummary、imageUrls、topComments、engagementMetrics 等）
2. WHEN 用户上传文件或提交 URL 时，THE API_Server SHALL 将材料元数据写入 `materials` 表
3. WHEN 材料解析状态变化时（parsing → chunking → ready 或 error），THE API_Server SHALL 更新 `materials` 表中对应记录的 `status` 字段
4. WHEN 前端通过 `GET /api/plans/{plan_id}/materials` 请求材料列表时，THE API_Server SHALL 从 `materials` 表读取该规划的所有材料并返回
5. WHEN 用户删除材料时，THE API_Server SHALL 从 `materials` 表中删除对应记录
6. WHEN 用户删除材料时，THE API_Server SHALL 同步更新 `plans` 表中对应规划的 `source_count` 字段


### 需求 5：Progress 表持久化

**用户故事：** 作为用户，我希望学习进度（每日任务完成状态）在刷新页面后仍然保留，以便我可以持续跟踪学习进展。

#### 验收标准

1. THE Database_Layer SHALL 提供 `progress` 表，包含字段：`id`（INTEGER 自增主键）、`plan_id`（TEXT 非空，外键关联 `plans.id`）、`day_number`（INTEGER 非空）、`title`（TEXT 非空）、`completed`（INTEGER 默认 0，布尔值）、`tasks`（TEXT，JSON 格式存储任务数组）
2. THE Database_Layer SHALL 对 `progress` 表的 `(plan_id, day_number)` 组合建立唯一约束
3. WHEN AI 生成学习计划后，THE API_Server SHALL 通过 `POST /api/plans/{plan_id}/progress` 将每日进度数据批量写入 `progress` 表
4. WHEN 前端通过 `GET /api/plans/{plan_id}/progress` 请求进度数据时，THE API_Server SHALL 从 `progress` 表读取该规划的所有天数进度，按 `day_number` 升序返回
5. WHEN 用户标记某天完成时，THE API_Server SHALL 更新 `progress` 表中对应记录的 `completed` 字段，并同步更新 `plans` 表的 `completed_days` 字段
6. WHEN 用户切换某个任务的完成状态时，THE API_Server SHALL 更新 `progress` 表中对应记录的 `tasks` JSON 字段

### 需求 6：Notes 表持久化

**用户故事：** 作为用户，我希望我的学习笔记在后端重启后仍然保留，以便我不会丢失手写的笔记内容。

#### 验收标准

1. THE Database_Layer SHALL 提供 `notes` 表，包含字段：`id`（TEXT 主键）、`plan_id`（TEXT 非空，外键关联 `plans.id`）、`title`（TEXT 非空）、`content`（TEXT 非空）、`created_at`（TEXT 非空）、`updated_at`（TEXT 非空）
2. WHEN 用户通过 `POST /api/notes` 创建笔记时，THE API_Server SHALL 将笔记数据写入 `notes` 表
3. WHEN 用户通过 `PUT /api/notes/{note_id}` 更新笔记时，THE API_Server SHALL 更新 `notes` 表中对应记录，并更新 `updated_at` 时间戳
4. WHEN 用户通过 `DELETE /api/notes/{note_id}` 删除笔记时，THE API_Server SHALL 从 `notes` 表中删除对应记录
5. WHEN 前端通过 `GET /api/plans/{plan_id}/notes` 请求笔记列表时，THE API_Server SHALL 从 `notes` 表读取该规划的所有笔记，按 `updated_at` 降序返回

### 需求 7：Generated_Contents 表持久化

**用户故事：** 作为用户，我希望 AI 生成的学习内容（学习计划、闪卡、测验等）在刷新页面后仍然保留，以便我可以反复查阅。

#### 验收标准

1. THE Database_Layer SHALL 提供 `generated_contents` 表，包含字段：`id`（TEXT 主键）、`plan_id`（TEXT 非空，外键关联 `plans.id`）、`type`（TEXT 非空）、`title`（TEXT 非空）、`content`（TEXT 非空）、`created_at`（TEXT 非空）
2. WHEN AI 生成内容后，THE API_Server SHALL 将生成的内容写入 `generated_contents` 表
3. WHEN 前端通过 `GET /api/plans/{plan_id}/generated-contents` 请求生成内容列表时，THE API_Server SHALL 从 `generated_contents` 表读取该规划的所有生成内容，按 `created_at` 降序返回

### 需求 8：Search_History 表持久化

**用户故事：** 作为用户，我希望搜索历史在刷新页面后仍然保留，以便我可以回顾之前的搜索结果。

#### 验收标准

1. THE Database_Layer SHALL 提供 `search_history` 表，包含字段：`id`（TEXT 主键）、`plan_id`（TEXT 非空，外键关联 `plans.id`）、`query`（TEXT 非空）、`platforms`（TEXT，JSON 格式存储平台数组）、`results`（TEXT，JSON 格式存储搜索结果数组，包含每条结果的详情信息如 contentSummary、imageUrls、topComments、engagementMetrics 等）、`result_count`（INTEGER 默认 0）、`searched_at`（TEXT 非空）
2. WHEN 搜索完成后，THE API_Server SHALL 将搜索历史写入 `search_history` 表
3. WHEN 前端通过 `GET /api/plans/{plan_id}/search-history` 请求搜索历史时，THE API_Server SHALL 从 `search_history` 表读取该规划的搜索历史，按 `searched_at` 降序返回，最多返回 20 条
4. WHEN 前端请求搜索历史时，THE API_Server SHALL 将 `platforms` 和 `results` 字段从 JSON 字符串反序列化为对象后返回
5. WHEN 用户清除搜索历史时，THE API_Server SHALL 通过 `DELETE /api/plans/{plan_id}/search-history` 删除该规划的所有搜索历史记录

### 需求 9：前端 Store 迁移

**用户故事：** 作为用户，我希望页面数据始终从后端加载，以便在不同浏览器或清除缓存后仍能看到完整数据。

#### 验收标准

1. THE Frontend_Store SHALL 移除所有 zustand `persist` 中间件，改为普通 zustand store
2. THE Frontend_Store SHALL 移除所有 `_cache`、`_activePlanId`、`_hasHydrated` 等 localStorage 缓存相关字段和逻辑
3. WHEN 用户进入工作区页面时，THE Frontend_Store SHALL 通过 API 调用从后端加载该规划的 messages、materials、progress、notes、generated_contents 数据
4. WHEN 用户执行写操作（创建、更新、删除）时，THE Frontend_Store SHALL 先调用后端 API 完成持久化，成功后再更新本地状态
5. IF 后端 API 调用失败，THEN THE Frontend_Store SHALL 保持本地状态不变，并向用户展示错误提示
6. WHEN 用户进入工作区页面时，THE Frontend_Store SHALL 展示加载状态（骨架屏），直到后端数据加载完成

### 需求 10：后端内存存储替换

**用户故事：** 作为开发者，我希望后端所有数据读写都通过 SQLite 完成，以便后端重启后数据不会丢失。

#### 验收标准

1. THE API_Server SHALL 移除 `backend/store.py` 中的内存字典 `_store`，所有数据读写改为调用 Database_Layer
2. THE API_Server SHALL 移除 `backend/routers/plans.py` 中的内存字典 `_plans`，所有规划 CRUD 改为调用 Database_Layer
3. THE API_Server SHALL 移除 `backend/routers/notes.py` 中的内存字典 `_notes`，所有笔记 CRUD 改为调用 Database_Layer
4. THE API_Server SHALL 删除 `backend/routers/session.py` 文件，该端点已被各独立 API 替代，不再需要
5. THE API_Server SHALL 从 `backend/main.py` 中移除 session router 的注册
6. THE API_Server SHALL 更新 `backend/routers/upload.py`，在文件上传和 URL 提交时将材料元数据写入 SQLite
7. WHEN API_Server 重启后，THE API_Server SHALL 能从 SQLite 恢复所有之前保存的数据

### 需求 11：遗留数据清理

**用户故事：** 作为开发者，我希望清理掉老版本遗留的数据文件和代码，以便项目结构干净整洁。

#### 验收标准

1. THE API_Server SHALL 删除 `backend/routers/session.py` 文件及其在 `backend/main.py` 中的路由注册
2. THE API_Server SHALL 删除 `backend/store.py` 文件（内存字典存储已被 SQLite 替代）
3. THE API_Server SHALL 删除 `data/sessions/` 目录及其中所有 JSON 文件（老版本会话数据，当前代码未使用）
4. THE API_Server SHALL 删除 `data/index.json` 文件（老版本 plan 索引，当前代码未使用）
5. THE Frontend_Store SHALL 在迁移完成后清理浏览器 localStorage 中的旧 key（`plan-store`、`chat-store`、`source-store`、`studio-store`、`search-history`），避免残留数据占用空间

### 需求 12：数据完整性与一致性

**用户故事：** 作为用户，我希望删除规划时所有关联数据都被清理干净，以便不会残留无用数据。

#### 验收标准

1. THE Database_Layer SHALL 对所有子表（messages、materials、progress、notes、generated_contents、search_history）的 `plan_id` 外键设置 `ON DELETE CASCADE`
2. WHEN 用户删除一个 Plan 时，THE Database_Layer SHALL 自动级联删除该 Plan 关联的所有子表数据
3. THE Database_Layer SHALL 对所有写操作使用事务（transaction），确保操作的原子性
4. IF 事务执行过程中发生错误，THEN THE Database_Layer SHALL 回滚事务并返回错误信息
