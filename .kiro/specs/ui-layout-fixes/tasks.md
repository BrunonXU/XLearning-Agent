# 实施计划

- [ ] 1. 编写缺陷条件探索测试
  - **Property 1: Fault Condition** - 5 个 UI 布局缺陷验证
  - **重要**: 在实施修复之前编写此属性测试
  - **目标**: 生成反例证明缺陷存在
  - **范围化 PBT 方法**: 针对 5 个具体缺陷场景编写确定性测试
  - 测试 1: 断言 `get_css()` 中 `--sidebar-width` 值为 `294px`（当前为 `420px`，将失败）
  - 测试 2: 断言 `.stepper-fixed-wrap` 的 `top` 不为 `0`，且 `.stepper-btn-row` 包含 `visibility: hidden`（当前缺失，将失败）
  - 测试 3: 断言 `render_plan_panel()` 函数体中不包含 `st.columns` 调用（当前包含，将失败）
  - 测试 4: 断言 `render_workspace_view()` 执行路径中调用了 `render_brain_tab()`（当前未调用，将失败）
  - 测试 5: 断言 `_COLUMN_RESIZE_JS` 中包含排除 `.stepper-btn-row` 的逻辑（当前缺失，将失败）
  - 在未修复代码上运行测试
  - **预期结果**: 测试失败（确认缺陷存在）
  - 记录发现的反例以理解根因
  - 测试编写、运行并记录失败后标记任务完成
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. 编写保留性属性测试（修复前）
  - **Property 2: Preservation** - 现有功能行为保留
  - **重要**: 遵循观察优先方法论
  - 观察: 在未修复代码上运行非缺陷输入，记录实际输出
  - 测试 1: `get_css()` 返回的 CSS 包含侧边栏完整样式规则（`background-color`、`border-right`、`overflow-y`、`scrollbar-width`）
  - 测试 2: `_render_clickable_stepper()` 正确渲染 Stepper 标签并支持 Tab 切换（Plan/Study/Quiz/Trace）
  - 测试 3: `render_plan_panel()` 中下载大纲和重新生成按钮的功能逻辑不变
  - 测试 4: 各 Tab 面板（Plan/Study/Quiz/Trace）内容渲染函数可正常调用
  - 测试 5: `_COLUMN_RESIZE_JS` 保留默认 30%~75% 拖拽范围限制和 60%/40% 初始比例逻辑
  - 在未修复代码上运行测试
  - **预期结果**: 测试通过（确认基线行为）
  - 测试编写、运行并通过后标记任务完成
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. 修复 5 个 UI 布局缺陷

  - [x] 3.1 修复侧边栏宽度（styles.py）
    - 将 `--sidebar-width: 420px` 改为 `--sidebar-width: 294px`
    - 所有引用 `var(--sidebar-width)` 的规则（width、min-width、max-width、flex、margin-left）自动生效
    - _Bug_Condition: css_variable('--sidebar-width') == '420px'_
    - _Expected_Behavior: css_variable('--sidebar-width') == '294px'_
    - _Preservation: 侧边栏内容（Logo、按钮、设置、历史列表、状态栏）正常显示不截断_
    - _Requirements: 2.1, 3.1, 3.6_

  - [x] 3.2 修复重复 Stepper 显示（styles.py）
    - 将 `.stepper-fixed-wrap` 的 `top: 0` 改为 `top: 48px`，使 Stepper 显示在 header 下方
    - 增强 `.stepper-btn-row` 隐藏策略：添加 `visibility: hidden !important; max-height: 0 !important;`
    - 保留 `pointer-events: auto` 使按钮仍可被 JS 点击
    - _Bug_Condition: stepper_fixed_wrap.top == '0' AND stepper_btn_row 隐藏不完全_
    - _Expected_Behavior: 仅一个正确定位的 Stepper，按钮行完全不可见_
    - _Preservation: Stepper 标签点击切换 Tab 功能正常，状态正确显示_
    - _Requirements: 2.2, 3.2_

  - [x] 3.3 修复嵌套列异常（renderer.py）
    - 在 `render_plan_panel()` 中将 `col_dl, col_gen = st.columns(2)` 替换为两个独立的 `st.button` 垂直排列
    - 移除 `with col_dl:` 和 `with col_gen:` 上下文管理器
    - 保持下载按钮和重新生成按钮的功能逻辑不变
    - _Bug_Condition: render_plan_panel() 在 c_panel 列内调用 st.columns(2)_
    - _Expected_Behavior: 不嵌套 st.columns()，无 StreamlitAPIException_
    - _Preservation: 下载大纲和重新生成计划按钮点击行为不变_
    - _Requirements: 2.3, 3.3_

  - [x] 3.4 添加 Brain/记忆与知识区域（layout.py）
    - 在 `render_workspace_view()` 的 `c_panel` 列中，在 `</div>` 关闭标签之前调用 `render_brain_tab()`
    - 添加 `from src.ui.renderer import render_brain_tab` 导入
    - Brain 区域应在所有 Tab 内容下方始终显示
    - _Bug_Condition: render_workspace_view() 从未调用 render_brain_tab()_
    - _Expected_Behavior: 右侧面板包含"🧠 记忆与知识"区域_
    - _Preservation: 各 Tab 面板内容渲染不受影响_
    - _Requirements: 2.4, 3.4_

  - [x] 3.5 修复列宽拖拽 JS 选择器（layout.py）
    - 修改 `_COLUMN_RESIZE_JS` 中的选择器逻辑，排除 `.stepper-btn-row` 内部的水平块
    - 在遍历 `stHorizontalBlock` 时添加 `b.closest('.stepper-btn-row') === null` 检查
    - 确保精确匹配聊天/面板的双列容器
    - _Bug_Condition: JS 选择器可能匹配到 stepper-btn-row 而非聊天/面板列_
    - _Expected_Behavior: 拖拽操作正确调整列宽，范围 30%~75%_
    - _Preservation: 默认 60%/40% 列宽比例不变，sticky 定位和边框样式不受影响_
    - _Requirements: 2.5, 3.5_

  - [ ] 3.6 验证缺陷条件探索测试现在通过
    - **Property 1: Expected Behavior** - 5 个 UI 布局缺陷已修复
    - **重要**: 重新运行任务 1 中的同一测试，不要编写新测试
    - 任务 1 的测试编码了期望行为
    - 当测试通过时，确认期望行为已满足
    - **预期结果**: 测试通过（确认缺陷已修复）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.7 验证保留性测试仍然通过
    - **Property 2: Preservation** - 现有功能行为保留
    - **重要**: 重新运行任务 2 中的同一测试，不要编写新测试
    - **预期结果**: 测试通过（确认无回归）
    - 确认修复后所有保留性测试仍然通过

- [ ] 4. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请咨询用户。
