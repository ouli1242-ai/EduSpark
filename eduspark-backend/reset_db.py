"""数据库重置脚本：清空 eduspark 数据库 → 重建表 → 创建测试用户"""
import sys
import os

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

# 1. 连接到 MySQL（不指定数据库），删除并重建 eduspark
ROOT_URL = "mysql+pymysql://root:root@localhost:3306"
engine = create_engine(ROOT_URL, isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    conn.execute(text("DROP DATABASE IF EXISTS eduspark"))
    conn.execute(text("CREATE DATABASE eduspark CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    print("[OK] 数据库 eduspark 已重建")

engine.dispose()

# 2. 导入所有模型（确保 metadata 注册），再创建表
from app.models.user import User  # noqa: F401
from app.models.profile import StudentProfile  # noqa: F401
from app.models.learning_record import LearningRecord  # noqa: F401
from app.models.learning_path import LearningPath  # noqa: F401
from app.models.resource import Resource  # noqa: F401
from app.models.chat_history import ChatHistory  # noqa: F401
from app.models.evaluation import EvaluationReport  # noqa: F401

from app.core.database import init_db
from app.core.config import get_settings

settings = get_settings()
print(f"[INFO] 数据库 URL: {settings.DATABASE_URL}")

# 创建所有表
init_db()
print("[OK] 所有数据表已创建")

# 3. 创建测试用户
from app.utils.auth import hash_password
from app.core.database import SessionLocal

db = SessionLocal()
try:
    existing = db.query(User).filter(User.username == "test").first()
    if existing:
        print("[INFO] 用户 test 已存在，跳过")
    else:
        user = User(username="test", password_hash=hash_password("123456"))
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[OK] 测试用户创建成功：id={user.id}, username=test, password=123456")
except Exception as e:
    db.rollback()
    print(f"[ERROR] 创建用户失败：{e}")
    sys.exit(1)
finally:
    db.close()

print("\n✅ 数据库重置完成！")
