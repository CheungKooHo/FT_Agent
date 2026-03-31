from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
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

def upload_and_index_pdf(file_path: str, collection_name: str):
    # 1. 加载 PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 2. 切片
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)

    # 3. 存储到向量库
    embeddings = get_embeddings()

    vectorstore = Qdrant.from_documents(
        texts,
        embeddings,
        path="./local_qdrant",
        collection_name=collection_name,
    )
    return "知识库构建成功"

def search_knowledge(query: str, collection_name: str):
    embeddings = get_embeddings()

    # 连接本地库并搜索
    vectorstore = Qdrant.from_existing_index(
        embeddings=embeddings,
        path="./local_qdrant",
        collection_name=collection_name
    )
    docs = vectorstore.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in docs])