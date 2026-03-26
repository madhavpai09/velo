"""
Script to initialize Alembic migrations for the project
Run this once: python scripts/init_migrations.py
"""
import os
import sys
from pathlib import Path

def init_alembic():
    """Initialize Alembic for database migrations"""
    project_root = Path(__file__).parent.parent
    alembic_dir = project_root / "serverapp" / "alembic"
    
    if alembic_dir.exists():
        print("❌ Alembic already initialized at", alembic_dir)
        return
    
    os.chdir(project_root / "serverapp")
    
    # Run alembic init
    os.system("alembic init alembic")
    
    # Update alembic.ini
    alembic_ini = project_root / "serverapp" / "alembic.ini"
    
    if alembic_ini.exists():
        content = alembic_ini.read_text()
        # Update sqlalchemy.url to use environment variable
        content = content.replace(
            "sqlalchemy.url = driver://user:password@localhost/dbname",
            "sqlalchemy.url = "
        )
        alembic_ini.write_text(content)
        print("✅ Updated alembic.ini")
    
    # Update env.py to use config
    env_py = alembic_dir / "env.py"
    if env_py.exists():
        content = env_py.read_text()
        # Add imports for config
        content = """import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

load_dotenv()

""" + content
        env_py.write_text(content)
        print("✅ Updated env.py")
    
    print("✅ Alembic initialized successfully")
    print("📝 Next steps:")
    print("   1. Define your models in serverapp/database/models.py")
    print("   2. Run: alembic revision --autogenerate -m 'Initial migration'")
    print("   3. Run: alembic upgrade head")


if __name__ == "__main__":
    init_alembic()
