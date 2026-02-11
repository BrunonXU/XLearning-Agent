"""
启动前自检：不启动 Streamlit 服务器，只验证配置与导入是否正常。
运行: python check_startup.py
若全部通过，再运行: venv\\Scripts\\python.exe -m streamlit run app.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> int:
    errors = []

    # 1) config.toml
    config_path = os.path.join(ROOT, ".streamlit", "config.toml")
    if not os.path.exists(config_path):
        errors.append(f"缺少配置文件: {config_path}")
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = f.read()
            if raw.startswith("\ufeff"):
                errors.append("config.toml 含 BOM，请保存为 UTF-8（无 BOM）")
            import toml

            toml.loads(raw)
            print("[OK] .streamlit/config.toml 语法正确")
        except Exception as e:
            errors.append(f"config.toml 解析失败: {e}")

    # 2) app import
    try:
        from src.ui.app import main as _main  # noqa: F401

        print("[OK] src.ui.app 导入成功")
    except Exception as e:
        errors.append(f"导入 src.ui.app 失败: {e}")

    # 3) quick compatibility checks
    try:
        from src.ui import layout
        import inspect

        source = inspect.getsource(layout.render_home_view)
        if "st.form_submit_button" in source:
            print("[OK] 首页表单包含提交按钮")
        else:
            errors.append("render_home_view 中未找到 form_submit_button")

        if "label_visibility" in source:
            errors.append("render_home_view 使用了 label_visibility（旧版 Streamlit 可能不兼容）")
        else:
            print("[OK] 未使用 label_visibility")
    except Exception as e:
        errors.append(f"layout 自检失败: {e}")

    if errors:
        print("\n--- 发现问题 ---")
        for item in errors:
            print(f"- {item}")
        return 1

    print("\n全部自检通过，可执行启动命令：")
    print("venv\\Scripts\\python.exe -m streamlit run app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
