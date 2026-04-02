from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import os

# 定义本地 Embeddings 函数
def get_embeddings():
    """
    使用 HuggingFace 本地 Embeddings 模型
    - 模型: paraphrase-multilingual-MiniLM-L12-v2 (约 20MB)
    - 支持中文和英文
    - 完全免费，本地运行
    - 通过国内镜像源下载（需在 .env 中配置 HF_ENDPOINT）
    """
    return HuggingFaceEmbeddings(
        model_name="paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}  # 归一化向量，提升检索效果
    )

def get_qdrant_client():
    """获取Qdrant客户端"""
    return QdrantClient(path="./local_qdrant")

def upload_and_index_pdf(file_path: str, collection_name: str, doc_id: str = None):
    """
    上传并索引PDF到向量库
    doc_id: 文档唯一ID，用于后续删除
    """
    import re
    from langchain_core.documents import Document

    # 1. 加载 PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 2. 智能切分 - 按政策条目切分，保持完整性
    all_chunks = []
    ITEM_PATTERN = re.compile(r'^（[一二三四五六七八九十]+）|^（[0-9]+）|^[0-9]+\.\s*|^（[0-9]+）\s*')

    for doc in documents:
        text = doc.page_content

        # 先按换行符分段落
        paragraphs = text.split('\n')

        current_chunk = ""
        for para in paragraphs:
            if not para.strip():
                continue

            # 检查是否是新的政策条目开始
            is_new_item = bool(ITEM_PATTERN.match(para.strip()))

            if is_new_item and current_chunk:
                # 保存当前chunk
                if current_chunk.strip():
                    all_chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                # 累加到当前chunk
                if current_chunk:
                    current_chunk += "\n" + para
                else:
                    current_chunk = para

        # 保存最后一个chunk
        if current_chunk.strip():
            all_chunks.append(current_chunk.strip())

    # 3. 合并太短的chunks（<100字的）与前一个合并
    merged_chunks = []
    for chunk in all_chunks:
        if not merged_chunks:
            merged_chunks.append(chunk)
        elif len(chunk) < 100:
            # 合并到前一个
            merged_chunks[-1] += "\n" + chunk
        else:
            merged_chunks.append(chunk)

    # 转为Document对象
    texts = [Document(page_content=chunk, metadata=doc.metadata) for chunk in merged_chunks]

    # 3. 为每个chunk添加doc_id元数据
    if doc_id is None:
        doc_id = str(uuid.uuid4())[:8]
    for i, doc in enumerate(texts):
        doc.metadata["doc_id"] = doc_id
        doc.metadata["chunk_index"] = i

    # 4. 存储到向量库 - 使用底层API避免兼容性问题
    embeddings = get_embeddings()
    client = get_qdrant_client()

    # 确保 collection 存在
    try:
        client.get_collection(collection_name)
    except Exception:
        # 创建 collection（384维向量，对应 paraphrase-multilingual-MiniLM-L12-v2）
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    # 获取向量维度
    vector_size = 384

    # 为每个文本生成向量并存储
    points = []
    for i, doc in enumerate(texts):
        vector = embeddings.embed_query(doc.page_content)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
        )
        points.append(point)

    # 批量上传
    client.upsert(
        collection_name=collection_name,
        points=points
    )

    return {"status": "success", "doc_id": doc_id, "chunks": len(texts)}

def search_knowledge(query: str, collection_name: str):
    """搜索知识库并返回合并的文本结果（用于增强Prompt）
    通用策略：向量检索 + 关键词兜底检索
    - 向量检索召回候选chunks
    - 如果top结果不包含查询关键词，则补充关键词检索
    """
    import re

    embeddings = get_embeddings()
    client = get_qdrant_client()

    try:
        client.get_collection(collection_name)
    except Exception:
        return ""

    try:
        query_vector = embeddings.embed_query(query)

        # 第一路召回：向量检索
        search_results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=50
        )

        # 构建候选集
        candidate_map = {}
        for result in search_results.points:
            payload = result.payload
            content = payload.get("page_content", "")
            key = (payload.get("metadata", {}).get("doc_id", ""), payload.get("metadata", {}).get("chunk_index", 0))

            candidate_map[key] = {
                "content": content,
                "doc_id": payload.get("metadata", {}).get("doc_id", ""),
                "chunk_index": payload.get("metadata", {}).get("chunk_index", 0),
                "score": result.score
            }

        candidate_chunks = list(candidate_map.values())
        candidate_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 检查top结果是否包含查询关键词
        query_keywords = [w for w in query if len(w) >= 2]
        top_has_keyword = any(
            any(kw in c["content"] for kw in query_keywords)
            for c in candidate_chunks[:5]
        )

        # 如果top结果不包含关键词，补充关键词召回
        if not top_has_keyword and query_keywords:
            # scroll所有chunks做关键词匹配
            all_results = client.scroll(collection_name=collection_name, limit=200)
            for point in all_results[0]:
                payload = point.payload
                content = payload.get("page_content", "")
                key = (payload.get("metadata", {}).get("doc_id", ""), payload.get("metadata", {}).get("chunk_index", 0))
                if key not in candidate_map:
                    # 检查是否包含关键词
                    for kw in query_keywords:
                        if kw in content:
                            candidate_map[key] = {
                                "content": content,
                                "doc_id": payload.get("metadata", {}).get("doc_id", ""),
                                "chunk_index": payload.get("metadata", {}).get("chunk_index", 0),
                                "score": 0.3  # 关键词匹配得分
                            }
                            break

            candidate_chunks = list(candidate_map.values())
            candidate_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 通用策略：如果检索到的chunk是列表项（以序号开头），往前找header合并
        final_contents = []
        used_keys = set()

        for c in candidate_chunks:
            key = (c["doc_id"], c["chunk_index"])
            if key in used_keys:
                continue

            parts = []
            base_index = c["chunk_index"]

            # 检查是否是列表项chunk（以"1." "（1）" "8." 等序号开头）
            is_list_item = re.search(r'^（?\d+[．.）)]', c["content"].strip()[:10])

            if is_list_item:
                # 往前找header chunk（chunk_index更小的，包含政策关键词的）
                for offset in range(-1, -5, -1):
                    header_key = (c["doc_id"], base_index + offset)
                    if header_key not in used_keys and header_key in candidate_map:
                        header = candidate_map[header_key]
                        # header应该包含更多关键词且在列表之前
                        if header["chunk_index"] < base_index:
                            parts.append(header["content"])
                            used_keys.add(header_key)
                            break

            parts.append(c["content"])
            used_keys.add(key)
            final_contents.append("\n".join(parts))

            if len(final_contents) >= 5:
                break

        return "\n".join(final_contents)
    except Exception as e:
        print(f"RAG search error: {e}")
        return ""

def search_knowledge_preview(query: str, collection_name: str, top_k: int = 5):
    """
    搜索知识库并返回详细结果（用于预览）
    通用策略：向量检索 + 列表项智能合并
    """
    import re

    embeddings = get_embeddings()
    client = get_qdrant_client()

    try:
        client.get_collection(collection_name)
    except Exception:
        return {"status": "success", "chunks": [], "total": 0}

    try:
        query_vector = embeddings.embed_query(query)

        # 召回更多候选
        search_results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=50
        )

        candidate_map = {}
        for result in search_results.points:
            payload = result.payload
            content = payload.get("page_content", "")
            key = (payload.get("metadata", {}).get("doc_id", ""), payload.get("metadata", {}).get("chunk_index", 0))

            candidate_map[key] = {
                "content": content,
                "source": payload.get("metadata", {}).get("source", "未知"),
                "doc_id": payload.get("metadata", {}).get("doc_id", ""),
                "chunk_index": payload.get("metadata", {}).get("chunk_index", 0),
                "score": result.score
            }

        candidate_chunks = list(candidate_map.values())
        candidate_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 通用策略：如果检索到的chunk是列表项（以序号开头），往前找header合并
        final_chunks = []
        used_keys = set()

        for c in candidate_chunks:
            key = (c["doc_id"], c["chunk_index"])
            if key in used_keys:
                continue

            parts = []
            base_index = c["chunk_index"]

            # 检查是否是列表项chunk（以"1." "（1）" "8." 等序号开头）
            is_list_item = re.search(r'^（?\d+[．.）)]', c["content"].strip()[:10])

            if is_list_item:
                # 往前找header chunk
                for offset in range(-1, -5, -1):
                    header_key = (c["doc_id"], base_index + offset)
                    if header_key not in used_keys and header_key in candidate_map:
                        header = candidate_map[header_key]
                        if header["chunk_index"] < base_index:
                            parts.append(header["content"])
                            used_keys.add(header_key)
                            break

            parts.append(c["content"])
            used_keys.add(key)

            final_chunks.append({
                "content": "\n".join(parts),
                "source": c["source"],
                "doc_id": c["doc_id"],
                "chunk_index": c["chunk_index"]
            })

            if len(final_chunks) >= top_k:
                break

        return {"status": "success", "chunks": final_chunks, "total": len(final_chunks)}
    except Exception as e:
        return {"status": "success", "chunks": [], "total": 0}

def get_collection_stats(collection_name: str):
    """获取collection统计信息"""
    client = get_qdrant_client()
    try:
        info = client.get_collection(collection_name)
        # 获取 collection 的 info
        count_result = client.count(collection_name=collection_name)
        return {
            "status": "success",
            "vectors_count": count_result.count,
            "points_count": count_result.count
        }
    except Exception:
        return {"status": "success", "vectors_count": 0, "points_count": 0}

def get_file_chunks(collection_name: str, doc_id: str):
    """获取指定文档的所有 chunks"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = get_qdrant_client()
    try:
        # 查询该 doc_id 的所有 points
        results = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="metadata.doc_id", match=MatchValue(value=doc_id))
                ]
            ),
            limit=1000
        )
        chunks = []
        for point in results[0]:
            if point.payload and "page_content" in point.payload:
                chunks.append({
                    "chunk_index": point.payload.get("metadata", {}).get("chunk_index", 0),
                    "content": point.payload["page_content"],
                    "source": point.payload.get("source", "未知")
                })
        # 按 chunk_index 排序
        chunks.sort(key=lambda x: x["chunk_index"])
        return {"status": "success", "chunks": chunks, "total": len(chunks)}
    except Exception as e:
        return {"status": "error", "message": str(e), "chunks": [], "total": 0}

def delete_from_vectorstore(collection_name: str, doc_id: str):
    """根据doc_id从向量库删除"""
    from qdrant_client.models import Filter, FieldCondition, MatchValue, Payload

    client = get_qdrant_client()
    try:
        # 先找到所有匹配的point IDs
        results = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="metadata.doc_id", match=MatchValue(value=doc_id))
                ]
            ),
            limit=1000
        )

        if not results[0]:
            return {"status": "success", "deleted": 0}

        # 获取所有point id
        point_ids = [point.id for point in results[0]]

        # 删除这些points
        client.delete(
            collection_name=collection_name,
            points_selector=point_ids
        )

        return {"status": "success", "deleted": len(point_ids)}
    except Exception as e:
        return {"status": "error", "message": str(e)}