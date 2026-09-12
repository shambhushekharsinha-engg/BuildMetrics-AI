import os
import json
from datetime import datetime, timedelta
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, SingletonThreadPool

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    failed_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)

class SavedProject(Base):
    __tablename__ = 'saved_projects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    project_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    plot_length = Column(Float)
    plot_width = Column(Float)
    num_floors = Column(Integer)
    prompt_data = Column(Text)

class DatabaseRepository:
    def __init__(self, db_url=None):
        # 12-factor config fallback to SQLite
        self.db_url = db_url or os.environ.get("DATABASE_URL", "sqlite:///buildmetrics.db")
        
        # Branch correctly for SQLite's thread checking if used
        if self.db_url.startswith("sqlite"):
            self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False}, poolclass=SingletonThreadPool)
        else:
            self.engine = create_engine(self.db_url, poolclass=QueuePool, pool_size=5, max_overflow=10)
        
        self.SessionFactory = scoped_session(sessionmaker(bind=self.engine))

    def create_user(self, username, password):
        session = self.SessionFactory()
        try:
            if session.query(User).filter_by(username=username).first():
                return False
            import bcrypt
            pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            new_user = User(username=username, password_hash=pw_hash)
            session.add(new_user)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def verify_user(self, username, password):
        session = self.SessionFactory()
        try:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return None, "Invalid credentials"
            
            # Check lockout
            if user.lockout_until and datetime.now() < user.lockout_until:
                return None, f"Account locked until {user.lockout_until.strftime('%H:%M:%S')}"
            elif user.lockout_until:
                user.failed_attempts = 0
                user.lockout_until = None
                session.commit()

            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                user.failed_attempts = 0
                user.lockout_until = None
                session.commit()
                return user.id, "Success"
            else:
                user.failed_attempts += 1
                if user.failed_attempts >= 5:
                    user.lockout_until = datetime.now() + timedelta(minutes=15)
                    session.commit()
                    return None, "Account locked due to 5 failed attempts (15 min lockout)."
                session.commit()
                return None, f"Invalid credentials. {5 - user.failed_attempts} attempts remaining."
        finally:
            session.close()

    def save_project(self, user_id, project_name, plot_length, plot_width, num_floors, prompt_data):
        session = self.SessionFactory()
        try:
            proj = SavedProject(
                user_id=user_id,
                project_name=project_name,
                plot_length=plot_length,
                plot_width=plot_width,
                num_floors=num_floors,
                prompt_data=json.dumps(prompt_data)
            )
            session.add(proj)
            session.commit()
        except Exception as e:
            session.rollback()
            print("Error saving project:", e)
        finally:
            session.close()

    def load_user_projects(self, user_id):
        session = self.SessionFactory()
        try:
            projects = session.query(SavedProject).filter_by(user_id=user_id).order_by(SavedProject.timestamp.desc()).all()
            return [
                {
                    "id": p.id,
                    "name": p.project_name,
                    "time": p.timestamp.isoformat() if p.timestamp else None,
                    "l": p.plot_length,
                    "w": p.plot_width,
                    "floors": p.num_floors,
                    "data": json.loads(p.prompt_data) if p.prompt_data else {}
                } for p in projects
            ]
        finally:
            session.close()

# Global repository instance
repo = DatabaseRepository()

def init_db():
    """Runs Alembic migrations programmatically to ensure schema is up to date."""
    import sys
    from alembic.config import Config
    from alembic import command
    
    # If the database doesn't exist, this will run migrations.
    # In a real deployed PG environment, we'd run this outside the app, but this keeps Streamlit usage seamless.
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Migration error (ignoring if running in tests): {e}")

