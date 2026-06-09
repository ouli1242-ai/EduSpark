"""
ML 知识库种子数据生成器
使用 DeepSeek LLM 生成《机器学习》核心知识点内容
写入 MySQL knowledge_graph 表 + ChromaDB 向量数据库
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.services.llm import deepseek_llm
from app.core.database import SessionLocal, init_chroma, get_chroma_collection


# 19 个知识点（与 PathAgent 知识图谱对齐）
ML_KNOWLEDGE_POINTS = [
    {
        "name": "机器学习概述",
        "chapter": 1,
        "difficulty": 1,
        "prerequisites": [],
        "related": [2, 3, 4],
    },
    {
        "name": "监督学习",
        "chapter": 2,
        "difficulty": 1,
        "prerequisites": [1],
        "related": [3, 5, 6],
    },
    {
        "name": "无监督学习",
        "chapter": 2,
        "difficulty": 2,
        "prerequisites": [1, 2],
        "related": [2, 7],
    },
    {
        "name": "模型评估与选择",
        "chapter": 1,
        "difficulty": 2,
        "prerequisites": [1],
        "related": [2, 3, 5],
    },
    {
        "name": "线性回归",
        "chapter": 3,
        "difficulty": 2,
        "prerequisites": [2],
        "related": [6, 8],
    },
    {
        "name": "逻辑回归",
        "chapter": 3,
        "difficulty": 2,
        "prerequisites": [2, 5],
        "related": [5, 9],
    },
    {
        "name": "聚类算法",
        "chapter": 4,
        "difficulty": 2,
        "prerequisites": [3],
        "related": [3, 8],
    },
    {
        "name": "决策树",
        "chapter": 3,
        "difficulty": 2,
        "prerequisites": [2, 5],
        "related": [9, 11],
    },
    {
        "name": "支持向量机(SVM)",
        "chapter": 3,
        "difficulty": 3,
        "prerequisites": [5, 6],
        "related": [6, 10],
    },
    {
        "name": "神经网络基础",
        "chapter": 5,
        "difficulty": 3,
        "prerequisites": [2, 5],
        "related": [12, 13, 17],
    },
    {
        "name": "集成学习",
        "chapter": 3,
        "difficulty": 3,
        "prerequisites": [8, 6],
        "related": [8, 9],
    },
    {
        "name": "卷积神经网络(CNN)",
        "chapter": 5,
        "difficulty": 4,
        "prerequisites": [10],
        "related": [10, 13, 18],
    },
    {
        "name": "循环神经网络(RNN)",
        "chapter": 5,
        "difficulty": 4,
        "prerequisites": [10],
        "related": [10, 12, 17],
    },
    {
        "name": "降维与特征选择",
        "chapter": 4,
        "difficulty": 3,
        "prerequisites": [3],
        "related": [3, 7, 16],
    },
    {
        "name": "贝叶斯分类器",
        "chapter": 3,
        "difficulty": 3,
        "prerequisites": [2],
        "related": [6, 14],
    },
    {
        "name": "梯度下降与优化",
        "chapter": 2,
        "difficulty": 2,
        "prerequisites": [1, 5],
        "related": [5, 10, 13],
    },
    {
        "name": "自然语言处理基础",
        "chapter": 6,
        "difficulty": 4,
        "prerequisites": [10, 13],
        "related": [13, 18],
    },
    {
        "name": "强化学习",
        "chapter": 6,
        "difficulty": 4,
        "prerequisites": [1, 2],
        "related": [10, 12],
    },
    {
        "name": "深度学习框架与实践",
        "chapter": 5,
        "difficulty": 2,
        "prerequisites": [10],
        "related": [10, 12, 13],
    },
]


async def generate_knowledge_content(name: str) -> str:
    """用 LLM 生成某个知识点的详细内容"""
    prompt = f"""请为《机器学习》课程知识点"{name}"生成一份教学文档。要求：

1. **概念定义**（2-3句话精确描述）
2. **核心原理**（3-5句话，包含关键公式/概念）
3. **典型应用场景**（2-3个实际例子）
4. **与其他知识点的关系**（列出相关概念并简述关系）
5. **常见误区**（2-3个学生常犯的错误理解）

用中文回答，控制在300-500字，内容要准确、教学性强。"""
    try:
        content = await deepseek_llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        return content.strip()
    except Exception as e:
        print(f"  [WARN] 生成 {name} 内容失败: {e}")
        return ""


def seed_knowledge_graph():
    """将 19 个知识点写入 MySQL knowledge_graph 表"""
    from app.models.knowledge_graph import KnowledgeGraphNode

    db = SessionLocal()
    try:
        # 清空已有数据
        existing = db.query(KnowledgeGraphNode).filter(KnowledgeGraphNode.course == "机器学习").all()
        for node in existing:
            db.delete(node)
        db.commit()

        nodes = {}
        for i, kp in enumerate(ML_KNOWLEDGE_POINTS, 1):
            node = KnowledgeGraphNode(
                course="机器学习",
                name=kp["name"],
                chapter=kp["chapter"],
                difficulty=kp["difficulty"],
                prerequisites=kp["prerequisites"],
                related=kp["related"],
                description=f"机器学习核心知识点：{kp['name']}",
            )
            db.add(node)
            db.flush()
            nodes[i] = node

        db.commit()
        print(f"[OK] 知识图谱: {len(nodes)} 个知识点已写入 MySQL")
        return nodes
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 知识图谱写入失败: {e}")
        return {}
    finally:
        db.close()


async def seed_chromadb():
    """为每个知识点生成详细内容并存入 ChromaDB"""
    print("[INFO] 开始生成知识内容并向量化...")

    # 初始化 ChromaDB
    init_chroma()
    collection = get_chroma_collection()

    # 清空已有数据
    try:
        existing = collection.get()
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    doc_id = 0
    for kp in ML_KNOWLEDGE_POINTS:
        name = kp["name"]
        print(f"  生成: {name}...")
        content = await generate_knowledge_content(name)

        if not content:
            continue

        # 分块存入 ChromaDB
        chunks = split_text(content, chunk_size=300, overlap=50)
        for ci, chunk in enumerate(chunks):
            doc_id += 1
            collection.add(
                ids=[f"kp_{doc_id}"],
                documents=[chunk],
                metadatas=[{
                    "knowledge_point": name,
                    "chapter": kp["chapter"],
                    "difficulty": kp["difficulty"],
                    "chunk_index": ci,
                    "source": "llm_generated",
                }],
            )

    print(f"[OK] ChromaDB: {doc_id} 个文本块已存入 (覆盖 {len(ML_KNOWLEDGE_POINTS)} 个知识点)")


def split_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """简单文本分块"""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


async def main():
    print("=" * 50)
    print("  EduSpark 知识库种子数据生成")
    print("=" * 50)

    # 1. 写入 MySQL 知识图谱
    seed_knowledge_graph()

    # 2. 生成内容并向量化
    await seed_chromadb()

    print("\n[DONE] 知识库种子数据生成完成！")


if __name__ == "__main__":
    asyncio.run(main())
