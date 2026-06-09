# Task 2：课程知识库构建（3天）

> 课程知识图谱构建、ChromaDB 向量化、RAG 校验

---

## 2.1 课程知识图谱构建

- [x] 确定目标课程：《机器学习》
- [x] 定义 19 个机器学习知识点（涵盖 6 章、4 级难度）
- [x] 设计前置依赖关系（prerequisites）和相关概念（related）
- [x] 写入 MySQL `knowledge_graph` 表

## 2.2 ChromaDB 向量数据库搭建

- [x] 安装 ChromaDB：`pip install chromadb`
- [x] 创建 `ml_knowledge` Collection
- [x] 调用 DeepSeek LLM 为每个知识点生成教学文档（300-500字）
- [x] 文本分块（chunk_size=300, overlap=50）
- [x] 向量化并存入 ChromaDB

## 2.3 RAG 校验模块

- [x] 实现 `RAGValidator` 类（`app/services/rag_validator.py`）
- [x] 实现原子声明提取→知识库检索→置信度计算
- [x] 集成到 TutorAgent（生成答案后自动校验）

## 2.4 文件上传与自动向量化

- [x] 文档解析服务（`app/services/document_parser.py`）
  - [x] 支持 PDF（pymupdf + pdfplumber 双引擎）
  - [x] 支持 PPT（python-pptx）
  - [x] 支持 DOCX（python-docx）
  - [x] 支持 TXT/MD
- [x] 上传文档自动分块 + 向量化 + 存入 ChromaDB
- [x] API 接口：上传/列表/详情/删除

## 2.5 RAG 检索验证

- [ ] 设计测试查询（20个典型问题）
- [ ] 测试检索效果：
  - [ ] 相关性评分
  - [ ] 响应时间
  - [ ] 召回率
- [ ] 优化分块策略（如效果不佳）

---

## 输出物

- [x] 知识图谱数据（knowledge_graph 表，19个知识点）
- [x] ChromaDB 向量数据库（ml_knowledge collection）
- [x] 文件上传与自动解析服务
- [x] RAG 校验模块代码
- [ ] RAG 检索测试报告（**未完成** — 需人工验证检索效果）

---

> **实际状态**：部分完成。知识库种子数据已入库，RAGValidator 代码已写，但实际检索效果未充分验证和调优。
