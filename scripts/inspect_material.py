"""查看指定 material 在 SQLite 中的数据"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend import database
database.init_db()

plan_id = "10d065ee-85a3-4f62-a1ab-db25913064a5"
target_id = "1e5c711a-9bac-45e0-81ed-32a870b25344"

materials = database.get_materials(plan_id)
print(f"=== Plan {plan_id} 共 {len(materials)} 个材料 ===\n")

for m in materials:
    marker = " <<<< TARGET" if m["id"] == target_id else ""
    print(f"  id={m['id'][:12]}... type={m.get('type','?'):15s} name={m.get('name','?')[:40]}{marker}")

print("\n--- 目标材料详情 ---")
target = next((m for m in materials if m["id"] == target_id), None)
if target:
    print(f"  id: {target['id']}")
    print(f"  type: {target.get('type')}")
    print(f"  name: {target.get('name')}")
    print(f"  url: {target.get('url')}")
    print(f"  status: {target.get('status')}")
    extra = target.get("extraData") or {}
    print(f"  extraData keys: {list(extra.keys())}")
    for k, v in extra.items():
        if isinstance(v, str):
            print(f"    {k}: {v[:150]}...")
        elif isinstance(v, list):
            print(f"    {k}: [{len(v)} items] {str(v)[:150]}...")
        else:
            print(f"    {k}: {v}")
else:
    print("  NOT FOUND!")
    # 也查 extra_data
    extra = database.get_material_extra_data(target_id)
    print(f"  get_material_extra_data: {json.dumps(extra, ensure_ascii=False)[:500] if extra else 'None'}")
