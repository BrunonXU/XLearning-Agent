"""检查 ChromaDB 中存储的文档切片内容"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
import dashscope

api_key = os.getenv("DASHSCOPE_API_KEY")
if api_key:
    dashscope.api_key = api_key

persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")

# 列出所有 collection
import chromadb
client = chromadb.PersistentClient(path=persist_dir)
collections = client.list_collections()

print(f"=== ChromaDB 持久化目录: {persist_dir} ===")
print(f"=== 共 {len(collections)} 个 collection ===\n")

for col in collections:
    print(f"--- Collection: {col.name} (count={col.count()}) ---")
    
    # 获取所有文档
    result = col.get(include=["documents", "metadatas"])
    
    ids = result["ids"]
    docs = result["documents"]
    metas = result["metadatas"]
    
    # 按 material_id 分组
    grouped = {}
    for i in range(len(ids)):
        mid = metas[i].get("material_id", "unknown") if metas[i] else "unknown"
        grouped.setdefault(mid, []).append((ids[i], docs[i], metas[i]))
    
    for mid, chunks in grouped.items():
        source = chunks[0][2].get("source", "?") if chunks[0][2] else "?"
        print(f"\n  📄 material_id={mid}")
        print(f"     source={source}")
        print(f"     chunks={len(chunks)}")
        
        for j, (cid, doc, meta) in enumerate(chunks[:3]):  # 只显示前3个chunk
            preview = doc[:200].replace("\n", "\\n") if doc else "(empty)"
            has_image = "data:image" in doc if doc else False
            print(f"\n     [chunk {j}] id={cid[:20]}...")
            print(f"     meta={meta}")
            print(f"     has_image_base64={has_image}")
            print(f"     len={len(doc) if doc else 0}")
            print(f"     preview: {preview}...")
        
        if len(chunks) > 3:
            print(f"\n     ... 还有 {len(chunks)-3} 个 chunks 未显示")
    
    print()
