"""
聊天气泡 Markdown 渲染回归测试（对应 TODO UI-FIX-2）
验证 _markdown_to_html 对代码块、列表、引用的处理。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.renderer import _markdown_to_html


def test_code_block():
    """代码块应渲染为 <pre><code>"""
    text = """Hello
```python
def foo():
    return 1
```
Done"""
    out = _markdown_to_html(text)
    assert '<pre class="chat-code-block">' in out
    assert "<code>" in out and "</code>" in out
    assert "def foo():" in out
    assert "return 1" in out


def test_blockquote():
    """引用应渲染为 blockquote"""
    text = "> 这是一段引用文字"
    out = _markdown_to_html(text)
    assert 'class="chat-blockquote"' in out
    assert "引用" in out


def test_list_and_bold():
    """无序列表和粗体"""
    text = """**粗体标题**
- 列表项 1
- 列表项 2"""
    out = _markdown_to_html(text)
    assert "<strong>" in out
    assert "<ul>" in out
    assert "<li>" in out


def test_code_block_escaping():
    """代码块内容应转义，防止 HTML/JS 注入"""
    b = chr(96) * 3
    text = f"{b}\n<script>alert(1)</script>\n{b}"
    out = _markdown_to_html(text)
    # 代码块内应使用 html.escape，故 < 变成 &lt;
    assert "&lt;script&gt;" in out or "<script>" not in out


def test_heading_and_hr():
    """标题和分隔线"""
    text = """### 三级标题
---
正文"""
    out = _markdown_to_html(text)
    assert "<h3>" in out
    assert "<hr" in out


if __name__ == "__main__":
    test_code_block()
    test_blockquote()
    test_list_and_bold()
    test_no_html_leak()
    test_heading_and_hr()
    print("✅ 全部 Markdown 渲染回归测试通过")
