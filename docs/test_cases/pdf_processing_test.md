# PDF 处理链路验证规范

**测试文件**: `tests/verify_pdf_rag.py`
**测试目的**: 验证“文件上传 -> 文本提取 -> RAG 入库 -> 智能问答”的全链路联通性。

## 1. 测试环境准备
- **输入数据**: 自动生成一个包含特定“暗号”的测试 PDF 文件（`temp_test_doc.pdf`）。
- **暗号内容**: "XLearning Agent 的核心是 Orchestrator。"（如果 LLM 能回答这句话，说明它读到了 PDF）。

## 2. 测试步骤详解

### Step 1: 模拟文件上传
- **输入**: 调用 `orchestrator.process_file(bytes, filename)`。
- **预期输出**:
  - `success`: True
  - `chunks`: > 0
  - `message`: 包含“已处理”字样。

### Step 2: 验证 RAG 检索 (Retrieval)
- **输入**: 调用 `orchestrator.run("XLearning Agent 的核心是什么？")`。
- **预期输出**:
  - 回复中必须包含 "Orchestrator" 关键词。
  - 这证明 Agent 不是在瞎编，而是真的检索到了我们刚刚上传的 PDF 内容。

## 3. 结果判定
- ✅ **PASS**: 成功提取文本且回答命中关键词。
- ❌ **FAIL**: 上传失败，或回答未能检索到 PDF 内容。
