# UI 布局修复 Bugfix Design

## Overview

XLearning Agent 的 Streamlit UI 存在 5 个布局/交互缺陷，需要在 `styles.py`、`layout.py`、`renderer.py` 三个文件中进行针对性修复。修复策略遵循最小变更原则：仅修改触发缺陷的代码路径，保留所有正常工作的功能不变。

核心修复思路：
1. CSS 变量 `--sidebar-width` 从 420px 改为 ~294px
2. 消除重复 Stepper（修正 HTML Stepper 定位 + 确保按钮行完全隐藏）
3. 将 `render_plan_panel()` 中嵌套的 `st.columns(2)` 替换为非嵌套布局
4. 在工作区视图中调用 `render_brain_tab()` 显示"记忆与知识"区域
5. 修复列宽拖拽 JS 选择器，精确匹配聊天/面板双列容器

## Glossary

- **Bug_Condition (C)**: 触发各缺陷的条件集合（侧边栏渲染、Stepper 渲染、Plan 面板渲染、工作区视图渲染、拖拽交互）
- **Property (P)**: 修复后各场景的期望行为（正确宽度、单一 Stepper、无异常、Brain 区域可见、拖拽生效）
- **Preservation**: 修复不应影响的现有行为（侧边栏内容显示、Stepper 切换、按钮功能、Tab 面板内容、默认列宽比例）
- **`get_css()`**: `src/ui/styles.py` 中返回全局 CSS 字符串的函数
- **`render_workspace_view()`**: `src/ui/layout.py` 中渲染工作区双列布局的函数
- **`_render_clickable_stepper()`**: `src/ui/layout.py` 中渲染 HTML Stepper + 隐藏按钮行的函数
- **`render_plan_panel()`**: `src/ui/renderer.py` 中渲染 Plan 面板（含嵌套列 bug）的函数
- **`render_brain_tab()`**: `src/ui/renderer.py` 中已实现但从未被调用的 Brain 区域渲染函数
- **`_COLUMN_RESIZE_JS`**: `src/ui/layout.py` 中注入的列宽拖拽 JavaScript 代码

## Bug Details

### Fault Condition

5 个缺陷在以下条件下触发：

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UIRenderContext
  OUTPUT: boolean

  // Bug 1: 侧边栏宽度
  condition1 := input.page IN ['home', 'workspace']
                AND css_variable('--sidebar-width') == '420px'

  // Bug 2: 重复 Stepper
  condition2 := input.page == 'workspace'
                AND input.session IS NOT NULL
                AND stepper_fixed_wrap.style.top == '0'
                AND stepper_btn_row.isVisibleInSomeCases == TRUE

  // Bug 3: 嵌套列异常
  condition3 := input.page == 'workspace'
                AND input.activeTab == 'Plan'
                AND plan_has_phases == TRUE
                AND render_plan_panel() calls st.columns(2) inside c_panel column

  // Bug 4: 缺少 Brain 区域
  condition4 := input.page == 'workspace'
                AND input.session IS NOT NULL
                AND render_brain_tab() is never called in render_workspace_view()

  // Bug 5: 拖拽失效
  condition5 := input.page == 'workspace'
                AND user.isDragging == TRUE
                AND JS_selector matches wrong stHorizontalBlock element

  RETURN condition1 OR condition2 OR condition3 OR condition4 OR condition5
END FUNCTION
```

### Examples

- **Bug 1**: 用户打开应用 → 侧边栏占 420px，主内容区被压缩。期望：侧边栏约 294px（缩减 30%）
- **Bug 2**: 用户进入工作区 → 看到两个导航条：一个 HTML Stepper 被 header 遮挡一半（`top: 0`），一个按钮行在某些情况下可见。期望：仅一个正确定位的 Stepper
- **Bug 3**: 工作区 Plan Tab 有学习大纲时 → `render_plan_panel()` 在 `c_panel` 列内调用 `st.columns(2)` → 抛出 `StreamlitAPIException: Columns may not be nested inside other columns`。期望：按钮正常渲染无异常
- **Bug 4**: 用户进入工作区 → 右侧面板仅显示当前 Tab 内容，缺少 `docs/ui_mockups.md` 设计的"🧠 记忆与知识"区域。期望：Brain 区域与 Tab 内容一起显示
- **Bug 5**: 用户拖拽聊天区与面板之间的分隔线 → 无响应。JS 选择器 `querySelectorAll('[data-testid="stHorizontalBlock"]')` 遍历找第一个有 2 个子元素的块，可能匹配到 Stepper 按钮行而非聊天/面板列。期望：拖拽正确调整列宽

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- 侧边栏中所有内容（Logo、新对话按钮、设置、历史对话列表、底部状态栏）正确显示，不截断不溢出（3.1）
- Stepper 标签点击切换 Tab（Plan/Study/Quiz/Trace）功能正常，状态（active/done）根据学习进度正确显示（3.2）
- Plan 面板的下载大纲和重新生成计划按钮点击行为不变（3.3）
- 各 Tab 对应的面板内容（Plan 学习大纲、Study 学习助手、Quiz 测验题目）正确渲染（3.4）
- 不拖拽时保持默认 60%/40% 列宽比例，右侧面板 sticky 定位和左侧列边框分隔线样式不受影响（3.5）
- 侧边栏原生拖拽调整功能保持禁用（`::after` 伪元素遮挡），固定宽度设计意图不变（3.6）

**Scope:**
所有不涉及上述 5 个缺陷触发条件的输入和交互应完全不受影响，包括：
- 首页的表单提交、快捷按钮
- 聊天消息的渲染和输入
- Quiz 答题和评分流程
- Trace 面板的事件展示
- 完成庆祝页的渲染

## Hypothesized Root Cause

基于代码分析，各缺陷的根因如下：

1. **侧边栏宽度过大**: `styles.py` 第 20 行 CSS 变量 `--sidebar-width: 420px` 值过大。所有引用该变量的选择器（`width`、`min-width`、`max-width`、`flex`、`margin-left`）均受影响。

2. **重复 Stepper 显示**:
   - `_render_clickable_stepper()` 中 HTML Stepper 使用 `position: fixed; top: 0`（styles.py `.stepper-fixed-wrap`），被 Streamlit 自带的顶部 header 遮挡
   - `.stepper-btn-row` 的 CSS 隐藏策略（`height: 0; overflow: hidden; opacity: 0`）在某些 Streamlit 版本/浏览器下不完全生效，按钮行仍可见
   - 两者同时存在导致用户看到重复导航

3. **嵌套列异常**: `renderer.py` 的 `render_plan_panel()` 约第 382 行，在已有 `c_panel` 列上下文中调用 `col_dl, col_gen = st.columns(2)` 创建下载/重新生成按钮的子列。Streamlit 不允许列嵌套，抛出 `StreamlitAPIException`。

4. **缺少 Brain 区域**: `renderer.py` 中 `render_brain_tab()` 函数已完整实现，但 `layout.py` 的 `render_workspace_view()` 从未调用它。`docs/ui_mockups.md` 设计要求在右侧面板中始终显示"🧠 记忆与知识"区域。

5. **列宽拖拽失效**:
   - `_COLUMN_RESIZE_JS` 中 `querySelectorAll('[data-testid="stHorizontalBlock"]')` 遍历所有水平块，取第一个 `children.length === 2` 的元素。Stepper 按钮行（`.stepper-btn-row` 内的 `st.columns`）也是有 2+ 子元素的水平块，可能被错误匹配
   - 侧边栏 `::after` 伪元素的 `pointer-events: auto` 可能干扰拖拽事件
   - `components.html()` 注入的 JS 执行时机不可靠，可能在 DOM 未就绪时执行

## Correctness Properties

Property 1: Fault Condition - 5 个 UI 缺陷均被修复

_For any_ 渲染上下文 input，当 isBugCondition(input) 为 true 时，修复后的代码 SHALL：
- (Bug 1) 侧边栏宽度为 ~294px
- (Bug 2) 仅显示一个正确定位的 Stepper
- (Bug 3) Plan 面板渲染不抛出异常
- (Bug 4) 右侧面板包含"🧠 记忆与知识"区域
- (Bug 5) 拖拽操作正确调整列宽

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - 现有功能不受影响

_For any_ 渲染上下文 input，当 isBugCondition(input) 为 false 时，修复后的代码 SHALL 产生与修复前完全相同的行为，保留侧边栏内容显示、Stepper 切换、按钮功能、Tab 面板内容、默认列宽比例等所有现有功能。

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

假设根因分析正确：

**File**: `src/ui/styles.py`

**Function**: `get_css()`

**Specific Changes**:
1. **侧边栏宽度缩减**: 将 `--sidebar-width: 420px` 改为 `--sidebar-width: 294px`（缩减 30%）。所有引用 `var(--sidebar-width)` 的规则自动生效，无需逐一修改。

2. **Stepper 定位修正**: 将 `.stepper-fixed-wrap` 的 `top: 0` 改为 `top: 48px`（或 Streamlit header 的实际高度），使 HTML Stepper 显示在 header 下方而非被遮挡。

3. **按钮行彻底隐藏**: 增强 `.stepper-btn-row` 的隐藏策略，添加 `visibility: hidden !important; max-height: 0 !important;` 确保在所有情况下不可见，同时保留 `pointer-events: auto` 使按钮仍可被 JS 点击。

---

**File**: `src/ui/renderer.py`

**Function**: `render_plan_panel()`

**Specific Changes**:
4. **消除嵌套列**: 将 `col_dl, col_gen = st.columns(2)` 替换为两个并排的按钮（不使用 `st.columns`）。可选方案：
   - 方案 A: 使用两个独立的 `st.button` 垂直排列
   - 方案 B: 使用 `st.container()` 包裹按钮（container 不受嵌套限制）
   - 推荐方案 A，最简单且避免所有嵌套问题

---

**File**: `src/ui/layout.py`

**Function**: `render_workspace_view()`

**Specific Changes**:
5. **调用 render_brain_tab()**: 在 `c_panel` 列中，在当前 Tab 内容渲染之后（`</div>` 之前），调用 `render_brain_tab()` 显示"🧠 记忆与知识"区域。根据 `docs/ui_mockups.md` 设计，Brain 区域应始终显示在右侧面板底部。

---

**File**: `src/ui/layout.py`

**Variable**: `_COLUMN_RESIZE_JS`

**Specific Changes**:
6. **精确匹配聊天/面板列**: 修改 JS 选择器逻辑，不再简单取第一个有 2 个子元素的 `stHorizontalBlock`，而是：
   - 方案 A: 从后向前遍历（`Array.from(blocks).reverse()`），因为聊天/面板列通常是最后一个双列容器
   - 方案 B: 在 `render_workspace_view()` 中给双列容器添加一个自定义 `data-` 属性或 CSS class，JS 通过该标识精确匹配
   - 方案 C: 排除 `.stepper-btn-row` 内部的水平块（检查 `b.closest('.stepper-btn-row')` 是否为 null）
   - 推荐方案 C，最精确且不依赖 DOM 顺序

## Testing Strategy

### Validation Approach

测试策略分两阶段：先在未修复代码上复现缺陷（确认根因），再验证修复后缺陷消除且现有行为不变。

### Exploratory Fault Condition Checking

**Goal**: 在实施修复前，复现 5 个缺陷，确认或否定根因分析。如果否定，需重新假设。

**Test Plan**: 编写单元测试模拟各缺陷的触发条件，在未修复代码上运行观察失败。

**Test Cases**:
1. **侧边栏宽度测试**: 断言 `get_css()` 返回的 CSS 中 `--sidebar-width` 值为 294px（未修复代码上将失败，返回 420px）
2. **Stepper 定位测试**: 断言 `.stepper-fixed-wrap` 的 `top` 值不为 `0`（未修复代码上将失败）
3. **嵌套列测试**: 在模拟的列上下文中调用 `render_plan_panel()`，断言不抛出 `StreamlitAPIException`（未修复代码上将失败）
4. **Brain 区域调用测试**: 断言 `render_workspace_view()` 的执行路径中包含 `render_brain_tab()` 调用（未修复代码上将失败）
5. **JS 选择器测试**: 断言 `_COLUMN_RESIZE_JS` 中的选择器逻辑排除了 `.stepper-btn-row` 内的水平块（未修复代码上将失败）

**Expected Counterexamples**:
- Bug 1: CSS 中 `--sidebar-width: 420px` 而非 294px
- Bug 2: `.stepper-fixed-wrap` 使用 `top: 0` 且 `.stepper-btn-row` 隐藏不完全
- Bug 3: `render_plan_panel()` 在列上下文中调用 `st.columns(2)` 导致异常
- Bug 4: `render_workspace_view()` 不调用 `render_brain_tab()`
- Bug 5: JS 遍历逻辑可能匹配到错误的水平块

### Fix Checking

**Goal**: 验证所有触发缺陷的输入在修复后产生期望行为。

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := renderUI_fixed(input)
  ASSERT expectedBehavior(result)
  // Bug 1: sidebar width == 294px
  // Bug 2: single stepper, correctly positioned
  // Bug 3: no StreamlitAPIException
  // Bug 4: brain section rendered
  // Bug 5: drag resize works on correct element
END FOR
```

### Preservation Checking

**Goal**: 验证所有不触发缺陷的输入在修复后行为不变。

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT renderUI_original(input) == renderUI_fixed(input)
END FOR
```

**Testing Approach**: 推荐使用 Property-Based Testing 进行 Preservation Checking，因为：
- 可自动生成大量测试用例覆盖输入域
- 能捕获手动单元测试可能遗漏的边界情况
- 对"行为不变"提供强保证

**Test Plan**: 先在未修复代码上观察正常输入的行为，再编写 PBT 测试验证修复后行为一致。

**Test Cases**:
1. **侧边栏内容保留**: 验证修复后侧边栏中 Logo、按钮、设置、历史列表、状态栏均正常显示
2. **Stepper 切换保留**: 验证点击 Stepper 标签仍能正确切换 Tab，状态正确更新
3. **按钮功能保留**: 验证 Plan 面板的下载和重新生成按钮点击行为不变
4. **Tab 内容保留**: 验证 Plan/Study/Quiz/Trace 各面板内容渲染不变
5. **默认列宽保留**: 验证不拖拽时 60%/40% 比例不变
6. **侧边栏固定宽度保留**: 验证侧边栏原生拖拽仍被禁用

### Unit Tests

- 测试 `get_css()` 返回的 CSS 中 `--sidebar-width` 值正确
- 测试 `get_css()` 返回的 CSS 中 `.stepper-fixed-wrap` 的 `top` 值正确
- 测试 `get_css()` 返回的 CSS 中 `.stepper-btn-row` 包含完整隐藏规则
- 测试 `render_plan_panel()` 在列上下文中不调用 `st.columns()`（通过 mock 或 AST 检查）
- 测试 `render_workspace_view()` 调用 `render_brain_tab()`（通过 mock 验证）
- 测试 `_COLUMN_RESIZE_JS` 包含排除 `.stepper-btn-row` 的逻辑

### Property-Based Tests

- 生成随机 session 状态和 active_tab 组合，验证 `calculate_stage_logic()` 返回值不受修复影响
- 生成随机消息列表，验证 `_extract_plan_from_messages()` 行为不变
- 生成随机 CSS 属性查询，验证非修改属性的值不变

### Integration Tests

- 端到端测试：打开应用 → 验证侧边栏宽度 → 进入工作区 → 验证单一 Stepper → 切换到 Plan Tab → 验证无异常 → 验证 Brain 区域可见
- 拖拽测试：模拟 mousedown/mousemove/mouseup 事件序列，验证列宽正确调整
- 回归测试：完整走一遍 Plan → Study → Quiz 流程，验证所有功能正常
