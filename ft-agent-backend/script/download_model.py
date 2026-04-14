"""
预下载 HuggingFace 模型脚本
运行此脚本将下载 embedding 模型到本地缓存，避免运行时下载问题
"""
import os

# 设置镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

print("开始下载 HuggingFace 模型...")
print("使用镜像源: https://hf-mirror.com")
print("-" * 50)

try:
    from sentence_transformers import SentenceTransformer

    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    print(f"下载模型: {model_name}")
    print("模型大小约 20MB，请稍候...")

    model = SentenceTransformer(model_name)

    print("-" * 50)
    print("[OK] 模型下载成功！")
    print(f"模型已缓存到: ~/.cache/huggingface/hub/")
    print("\n测试模型...")

    # 测试一下模型
    test_embedding = model.encode("测试文本")
    print(f"[OK] 模型测试成功！向量维度: {len(test_embedding)}")
    print("\n现在可以启动服务了：python main.py")

except Exception as e:
    print(f"\n✗ 下载失败: {str(e)}")
    print("\n可能的解决方案:")
    print("1. 检查网络连接")
    print("2. 尝试使用代理")
    print("3. 或者使用其他 embedding 方案")
