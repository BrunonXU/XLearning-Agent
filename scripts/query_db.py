"""查询 SQLite 数据库中的生成内容"""
import sqlite3
import json
import glob

# 找到数据库文件
db_files = glob.glob("data/*.db") + glob.glob("*.db")
print(f"找到的数据库文件: {db_files}")

for db_path in db_files:
    print(f"\n=== {db_path} ===")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 列出所有表
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"表: {tables}")
    
    # 查找生成内容表
    for t in tables:
        if "generated" in t.lower() or "content" in t.lower():
            rows = conn.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 3").fetchall()
            for r in rows:
                d = dict(r)
                # 截断 content 字段
                if "content" in d and d["content"] and len(str(d["content"])) > 300:
                    d["content"] = str(d["content"])[:300] + "..."
                print(json.dumps(d, ensure_ascii=False, indent=2))
    
    conn.close()
