import sqlite3
conn = sqlite3.connect("data/app.db")
conn.row_factory = sqlite3.Row
r = conn.execute(
    "SELECT content FROM generated_contents WHERE id=?",
    ("45a872e7-990d-4704-a7cf-a3e8e2a95e36",)
).fetchone()
if r:
    print(dict(r)["content"])
else:
    print("NOT FOUND")
conn.close()
