from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on startup."""
    Base.metadata.create_all(bind=engine)


# ---- ChromaDB (向量数据库) ----
_chroma_client = None
_chroma_collection = None


def init_chroma():
    """Initialize ChromaDB persistent client and get/create the knowledge collection."""
    global _chroma_client, _chroma_collection
    import chromadb
    import os
    persist_dir = os.path.abspath(settings.CHROMA_PERSIST_DIR)
    os.makedirs(persist_dir, exist_ok=True)
    _chroma_client = chromadb.PersistentClient(path=persist_dir)
    _chroma_collection = _chroma_client.get_or_create_collection(
        name="ml_knowledge",
        metadata={"description": "Machine Learning knowledge base for EduSpark RAG"}
    )
    print(f"[OK] ChromaDB initialized: {persist_dir} | collection=ml_knowledge")
    return _chroma_collection


def get_chroma_collection():
    """Get the ChromaDB collection. Call after init_chroma()."""
    return _chroma_collection
