import os
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker, Session, load_only, joinedload
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Type, TypeVar, Tuple, Generator
from datetime import datetime

from core.db_schemas import (
    Base, Novel, Episode, Character, Location, Item, PlotEvent, WorldSetting, Foreshadowing,
    ProcessingStatus, ForeshadowingStatus
)
from core.config import config as app_config
from core.logger_setup import setup_logger

logger = setup_logger()
T = TypeVar('T', bound=Base)  # 型ヒント用（mypy対策でコメントアウト）
T = TypeVar('T')


class ContextDB:
    """
    アプリケーションのコンテキストデータベースを操作するためのクラス。
    SQLiteデータベースへの接続、セッション管理、CRUD操作を提供します。
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or app_config.DATABASE_URL
        self._ensure_db_directory_exists()
        self.engine = create_engine(self.db_url, echo=False)
        try:
            Base.metadata.create_all(self.engine)
            logger.info(
                f"Database tables checked/created successfully at {self.db_url}")
        except Exception as e:
            logger.error(
                f"Error creating database tables at {self.db_url}: {e}", exc_info=True)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

    def _ensure_db_directory_exists(self):
        if self.db_url.startswith("sqlite:///"):
            db_file_path = self.db_url[len("sqlite:///"):]
            if not os.path.isabs(db_file_path):
                db_file_path = os.path.join(os.getcwd(), db_file_path)
            db_dir = os.path.dirname(db_file_path)
            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                    logger.info(f"Created database directory: {db_dir}")
                except OSError as e:
                    logger.error(
                        f"Failed to create database directory {db_dir}: {e}")

    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}", exc_info=True)
            db.rollback()
            raise
        finally:
            db.close()

    def _get_or_create(self, db: Session, model: Type[T], defaults: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Tuple[T, bool]:
        instance = db.query(model).filter_by(
            **kwargs).with_for_update().first()
        created = False
        updated = False
        if instance:
            if defaults:
                for key, value in defaults.items():
                    if hasattr(instance, key) and getattr(instance, key) != value:
                        setattr(instance, key, value)
                        updated = True
        else:
            params = {**kwargs, **(defaults or {})}
            instance = model(**params)
            db.add(instance)
            db.flush()
            created = True
        return instance, created or updated

    # --- Novel Operations ---
    def get_or_create_novel(self, url: str, defaults: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Novel], bool]:
        try:
            with self.get_db() as db:
                novel, modified = self._get_or_create(
                    db, Novel, defaults=defaults, url=url)
                action = "created" if modified and not db.query(Novel).filter(
                    Novel.id == novel.id).first() else ("updated" if modified else "found")
                logger.info(
                    f"Novel {action}: URL={url}, ID={novel.id if novel else 'N/A'}")
                return novel, modified
        except Exception as e:
            logger.error(
                f"Error in get_or_create_novel for URL {url}: {e}", exc_info=True)
            return None, False

    def get_novel_by_id(self, novel_id: int) -> Optional[Novel]:
        try:
            with self.get_db() as db:
                return db.query(Novel).filter(Novel.id == novel_id).first()
        except Exception as e:
            logger.error(
                f"Error getting novel by ID {novel_id}: {e}", exc_info=True)
            return None

    def update_novel_metadata(self, novel_id: int, metadata: Dict[str, Any]) -> Optional[Novel]:
        try:
            with self.get_db() as db:
                novel = db.query(Novel).filter(Novel.id == novel_id).first()
                if novel:
                    updated = False
                    for key, value in metadata.items():
                        if hasattr(novel, key) and getattr(novel, key) != value:
                            setattr(novel, key, value)
                            updated = True
                    if updated:
                        novel.last_scraped_at = datetime.utcnow().replace(tzinfo=None)
                        db.flush()
                        logger.info(
                            f"Novel metadata updated for ID: {novel_id}")
                    return novel
                logger.warning(
                    f"Novel not found for metadata update: ID={novel_id}")
                return None
        except Exception as e:
            logger.error(
                f"Error updating novel metadata for ID {novel_id}: {e}", exc_info=True)
            return None

    # --- Episode Operations ---
    def get_or_create_episode(self, novel_id: int, episode_url: str, defaults: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Episode], bool]:
        if not self.get_novel_by_id(novel_id):
            logger.error(
                f"Cannot get/create episode, Novel ID {novel_id} not found.")
            return None, False
        try:
            with self.get_db() as db:
                episode, modified = self._get_or_create(
                    db, Episode, defaults=defaults, novel_id=novel_id, episode_url=episode_url)
                action = "created" if modified and not db.query(Episode).filter(
                    Episode.id == episode.id).first() else ("updated" if modified else "found")
                logger.info(
                    f"Episode {action}: URL={episode_url}, NovelID={novel_id}, ID={episode.id if episode else 'N/A'}")
                return episode, modified
        except Exception as e:
            logger.error(
                f"Error in get_or_create_episode for URL {episode_url} (Novel ID {novel_id}): {e}", exc_info=True)
            return None, False

    def get_episode_by_id(self, episode_id: int) -> Optional[Episode]:
        try:
            with self.get_db() as db:
                return db.query(Episode).filter(Episode.id == episode_id).first()
        except Exception as e:
            logger.error(
                f"Error getting episode by ID {episode_id}: {e}", exc_info=True)
            return None

    def get_episodes_for_novel(self, novel_id: int, start_num: Optional[int] = None, end_num: Optional[int] = None, only_fields: Optional[List[str]] = None) -> List[Episode]:
        try:
            with self.get_db() as db:
                query = db.query(Episode).filter(Episode.novel_id == novel_id)
                if start_num is not None:
                    query = query.filter(Episode.episode_number >= start_num)
                if end_num is not None:
                    query = query.filter(Episode.episode_number <= end_num)
                if only_fields:
                    query = query.options(load_only(*only_fields))
                return query.order_by(asc(Episode.episode_number)).all()
        except Exception as e:
            logger.error(
                f"Error getting episodes for novel ID {novel_id}: {e}", exc_info=True)
            return []

    def update_episode_content(self, episode_id: int, content_cleaned: str, char_count: int) -> Optional[Episode]:
        try:
            with self.get_db() as db:
                episode = db.query(Episode).filter(
                    Episode.id == episode_id).first()
                if episode:
                    episode.content_cleaned = content_cleaned
                    episode.char_count = char_count
                    db.flush()
                    logger.info(
                        f"Cleaned content and char count updated for Episode ID: {episode_id}")
                    return episode
                return None
        except Exception as e:
            logger.error(
                f"Error updating episode content for ID {episode_id}: {e}", exc_info=True)
            return None

    def update_episode_llm_results(self, episode_id: int, updates: Dict[str, Any]) -> Optional[Episode]:
        allowed_keys = {"summary_short", "summary_long", "key_events_extraction_status",
                        "summary_generation_status", "llm_analysis_status"}
        update_data = {k: v for k, v in updates.items() if k in allowed_keys}
        if not update_data:
            logger.warning(
                "No valid keys provided for updating episode LLM results.")
            return None
        try:
            with self.get_db() as db:
                episode = db.query(Episode).filter(
                    Episode.id == episode_id).first()
                if episode:
                    for key, value in update_data.items():
                        setattr(episode, key, value)
                    db.flush()
                    logger.info(
                        f"LLM results updated for Episode ID: {episode_id}")
                    return episode
                return None
        except Exception as e:
            logger.error(
                f"Error updating episode LLM results for ID {episode_id}: {e}", exc_info=True)
            return None

    # --- Character Operations (基本的なもの) ---
    def get_or_create_character(self, novel_id: int, name: str, defaults: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Character], bool]:
        if not self.get_novel_by_id(novel_id):
            return None, False
        try:
            with self.get_db() as db:
                character, modified = self._get_or_create(
                    db, Character, defaults=defaults, novel_id=novel_id, name=name)
                action = "created" if modified and not db.query(Character).filter(
                    Character.id == character.id).first() else ("updated" if modified else "found")
                logger.info(
                    f"Character {action}: Name='{name}', NovelID={novel_id}, ID={character.id if character else 'N/A'}")
                return character, modified
        except Exception as e:
            logger.error(
                f"Error in get_or_create_character for Name '{name}' (Novel ID {novel_id}): {e}", exc_info=True)
            return None, False

    def get_characters_for_novel(self, novel_id: int) -> List[Character]:
        try:
            with self.get_db() as db:
                return db.query(Character).filter(Character.novel_id == novel_id).order_by(Character.name).all()
        except Exception as e:
            logger.error(
                f"Error getting characters for novel ID {novel_id}: {e}", exc_info=True)
            return []

    # --- Location, Item, PlotEvent, WorldSetting, Foreshadowing のメソッド ---
    # 上記のNovel, Episode, Characterと同様に、必要に応じてget_or_createや
    # updateメソッドを実装してください。
    # 例:
    # def add_plot_event(self, episode_id: int, event_data: Dict[str, Any]) -> Optional[PlotEvent]: ...
    # def update_foreshadowing_status(self, foreshadowing_id: int, status: ForeshadowingStatus, resolved_episode_id: Optional[int] = None, resolution_description: Optional[str] = None) -> Optional[Foreshadowing]: ...

    # --- 削除系メソッド (必要であれば) ---
    # def delete_novel(self, novel_id: int) -> bool: ...
    # def delete_episode(self, episode_id: int) -> bool: ...
