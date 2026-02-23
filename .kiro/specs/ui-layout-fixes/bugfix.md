# Bugfix Requirements Document

## Introduction

XLearning Agent 的 Streamlit UI 存在 5 个 UI/UX 缺陷，影响布局、导航、功能完整性和交互体验。这些缺陷涉及侧边栏宽度过大、Stepper 导航重复显示、Streamlit 列嵌套异常、右侧面板缺少"记忆与知识"内容、以及列宽拖拽调整功能失效。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN 用户打开应用时 THEN 侧边栏宽度为 420px（CSS 变量 `--sidebar-width: 420px`），占据过多屏幕空间，导致主内容区域偏窄

1.2 WHEN 用户进入工作区视图时 THEN 系统渲染了两个 Stepper：一个是 `stepper-fixed-wrap` 中的 HTML Stepper（使用 `position: fixed; top: 0` 定位，被 Streamlit 顶部 header 遮挡了一半），另一个是 `.stepper-btn-row` 中的 Streamlit 按钮行（CSS 隐藏不完全，在某些情况下可见），导致用户看到重复的导航条

1.3 WHEN 工作区视图渲染右侧面板中的 Plan 面板时 THEN `render_plan_panel()` 在 `c_panel` 列内部调用 `st.columns(2)` 创建下载/重新生成按钮的子列，触发 `StreamlitAPIException: Columns may not be nested inside other columns` 异常（调用链：`app.py:12 → src/ui/app.py:39 → layout.py:142 → layout.py:269 → renderer.py:382`）

1.4 WHEN 用户进入工作区视图时 THEN 右侧面板仅显示当前 Tab 对应的内容（Plan/Study/Quiz/Trace），缺少 `docs/ui_mockups.md` 中设计的"🧠 记忆与知识"区域（包含上传的上下文文件和生成的产物），`render_brain_tab()` 函数虽然存在于 `renderer.py` 中但从未被调用

1.5 WHEN 用户尝试拖拽聊天区与右侧面板之间的灰色分隔线来调整列宽时 THEN 拖拽功能不生效，原因包括：(a) `_COLUMN_RESIZE_JS` 中的 JavaScript 选择器 `[data-testid="stHorizontalBlock"]` 匹配到的是第一个有 2 个子元素的水平块（可能是 Stepper 按钮行而非聊天/面板列），(b) 侧边栏 `::after` 伪元素设置了 `pointer-events: auto` 可能干扰拖拽事件，(c) `components.html()` 注入的 JS 执行时机不可靠

### Expected Behavior (Correct)

2.1 WHEN 用户打开应用时 THEN 系统 SHALL 将侧边栏宽度设置为约 294px（原 420px 缩减 30%），CSS 变量 `--sidebar-width` 及所有引用该变量的样式（width、min-width、max-width、flex）均使用新值

2.2 WHEN 用户进入工作区视图时 THEN 系统 SHALL 仅显示一个 Stepper 导航条，该导航条应正确定位在 Streamlit header 下方（而非 `top: 0` 被遮挡），且隐藏的 Streamlit 按钮行在所有情况下均不可见

2.3 WHEN 工作区视图渲染右侧面板中的 Plan 面板时 THEN 系统 SHALL 不在已有列内部嵌套 `st.columns()`，下载和重新生成按钮应使用非嵌套的布局方式（如并排按钮、单独按钮行、或 `st.container`）来避免 `StreamlitAPIException`

2.4 WHEN 用户进入工作区视图时 THEN 系统 SHALL 在右侧面板中显示"🧠 记忆与知识"区域（调用 `render_brain_tab()`），展示上传的上下文文件信息和生成的产物，该区域应与当前 Tab 对应的内容（Plan/Study/Quiz）一起显示

2.5 WHEN 用户拖拽聊天区与右侧面板之间的灰色分隔线时 THEN 系统 SHALL 正确响应拖拽操作，允许用户在 30%~75% 范围内调整左右列宽比例，JavaScript 选择器应精确匹配聊天/面板的双列容器而非其他水平块

### Unchanged Behavior (Regression Prevention)

3.1 WHEN 侧边栏宽度调整后 THEN 系统 SHALL CONTINUE TO 正确显示侧边栏中的所有内容（Logo、新对话按钮、设置、历史对话列表、底部状态栏），不出现截断或溢出

3.2 WHEN Stepper 修复后 THEN 系统 SHALL CONTINUE TO 支持点击 Stepper 标签切换 Tab（Plan/Study/Quiz/Trace），且 Stepper 状态（active/done）根据学习进度正确显示

3.3 WHEN Plan 面板列嵌套修复后 THEN 系统 SHALL CONTINUE TO 提供下载大纲和重新生成计划的功能，按钮点击行为不变

3.4 WHEN 右侧面板增加"记忆与知识"区域后 THEN 系统 SHALL CONTINUE TO 正确渲染各 Tab 对应的面板内容（Plan 面板的学习大纲、Study 面板的学习助手、Quiz 面板的测验题目）

3.5 WHEN 列宽拖拽修复后 THEN 系统 SHALL CONTINUE TO 在不拖拽时保持默认的 60%/40% 列宽比例，且右侧面板的 sticky 定位和左侧列的边框分隔线样式不受影响

3.6 WHEN 侧边栏宽度调整后 THEN 系统 SHALL CONTINUE TO 禁用侧边栏原生拖拽调整功能（`::after` 伪元素遮挡），保持侧边栏固定宽度的设计意图
