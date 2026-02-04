"""
RAG Engine - 检索增强生成引擎

核心功能：
1. 文档切分（RecursiveCharacterTextSplitter）
2. 向量化存储（ChromaDB + Embedding）
3. 相似度检索（Top-K）
4. 上下文组装

技术选型理由：
- ChromaDB：轻量级、支持本地持久化、LangChain 原生支持
- RecursiveCharacterTextSplitter：智能切分，保持语义完整性
- chunk_size=1000, overlap=200：经验值，平衡上下文和召回

面试话术：
> "RAG 解决了 LLM 知识时效性和个性化的问题。用户上传的资料会被
>  切分、向量化、存入 ChromaDB。提问时先检索相关内容，再让 LLM
>  基于这些内容回答，既利用了 LLM 的推理能力，又保证了准确性。"
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from src.providers import ProviderFactory, EmbeddingProvider


class Document(BaseModel):
    """文档模型"""
    content: str
    metadata: Dict[str, Any] = {}


class RetrievalResult(BaseModel):
    """检索结果模型"""
    content: str
    metadata: Dict[str, Any]
    score: float  # 相似度分数


class RAGEngine:
    """
    RAG 引擎
    
    负责文档的存储和检索
    """
    
    def __init__(
        self,
        collection_name: str = "knowledge_base",
        persist_directory: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        初始化 RAG 引擎
        
        Args:
            collection_name: ChromaDB collection 名称
            persist_directory: 持久化目录，默认从环境变量读取
            embedding_provider: Embedding Provider，默认使用工厂创建
            chunk_size: 切分块大小
            chunk_overlap: 切分重叠大小
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIR", 
            "./data/chroma"
        )
        
        # 确保目录存在
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化 Embedding Provider
        self._embedding_provider = embedding_provider or ProviderFactory.create_embedding()
        
        # 初始化文本切分器
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )
        
        # 初始化 ChromaDB（使用 LangChain 包装）
        self._vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self._create_langchain_embedding(),
            persist_directory=self.persist_directory,
        )
    
    def _create_langchain_embedding(self):
        """创建 LangChain 兼容的 Embedding 函数"""
        # LangChain Chroma 需要一个有 embed_documents 和 embed_query 方法的对象
        from langchain_community.embeddings import DashScopeEmbeddings
        return DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
    
    def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> List[str]:
        """
        添加文档到知识库
        
        Args:
            content: 文档内容
            metadata: 元数据（来源、类型等）
            doc_id: 文档 ID（可选）
            
        Returns:
            切分后的 chunk IDs
        """
        metadata = metadata or {}
        
        # 切分文档
        chunks = self._splitter.split_text(content)
        
        # 为每个 chunk 添加元数据
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            metadatas.append(chunk_meta)
        
        # 添加到向量库
        ids = self._vectorstore.add_texts(
            texts=chunks,
            metadatas=metadatas,
        )
        
        return ids
    
    def add_documents(
        self,
        documents: List[Document],
    ) -> List[str]:
        """
        批量添加文档
        
        Args:
            documents: 文档列表
            
        Returns:
            所有 chunk IDs
        """
        all_ids = []
        for doc in documents:
            ids = self.add_document(doc.content, doc.metadata)
            all_ids.extend(ids)
        return all_ids
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter: 元数据过滤条件
            
        Returns:
            检索结果列表
        """
        # 使用 similarity_search_with_score
        results = self._vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
        )
        
        # 转换为 RetrievalResult
        retrieval_results = []
        for doc, score in results:
            retrieval_results.append(RetrievalResult(
                content=doc.page_content,
                metadata=doc.metadata,
                score=float(score),
            ))
        
        return retrieval_results
    
    def build_context(
        self,
        query: str,
        k: int = 5,
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        构建 RAG 上下文
        
        Args:
            query: 查询文本
            k: 检索结果数量
            separator: 结果分隔符
            
        Returns:
            组装好的上下文字符串
        """
        results = self.retrieve(query, k=k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.metadata.get("source", "未知来源")
            context_parts.append(f"[来源 {i}: {source}]\n{result.content}")
        
        return separator.join(context_parts)
    
    def delete_collection(self):
        """删除整个 collection"""
        self._vectorstore.delete_collection()
    
    def count(self) -> int:
        """返回文档数量"""
        return self._vectorstore._collection.count()
