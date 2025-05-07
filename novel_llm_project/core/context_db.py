import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db_schemas import Base, User, Novel
from core.config import config
from core.logger_setup import setup_logger

logger = setup_logger()

class ContextDB:
    def __init__(self, db_url=None):
        self.db_url = db_url or "sqlite:///data/novel_context.db"
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized with URL: {self.db_url}")

    def add_user(self, username, email):
        session = self.Session()
        try:
            new_user = User(username=username, email=email)
            session.add(new_user)
            session.commit()
            logger.info(f"User added: {username}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add user: {e}")
        finally:
            session.close()

    def add_novel(self, title, author, user_id):
        session = self.Session()
        try:
            new_novel = Novel(title=title, author=author, user_id=user_id)
            session.add(new_novel)
            session.commit()
            logger.info(f"Novel added: {title}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add novel: {e}")
        finally:
            session.close()

    def get_user(self, user_id):
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
        finally:
            session.close()

    def get_novel(self, novel_id):
        session = self.Session()
        try:
            novel = session.query(Novel).filter_by(id=novel_id).first()
            return novel
        except Exception as e:
            logger.error(f"Failed to get novel: {e}")
            return None
        finally:
            session.close()
