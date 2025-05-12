from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Table, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

# Enum定義


class ForeshadowingStatus(str, enum.Enum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    INVALIDATED = "invalidated"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 多対多: PlotEvents <-> Characters
plot_event_character_association = Table('plot_event_character_association', Base.metadata,
                                         Column('plot_event_id', Integer, ForeignKey(
                                             'plot_events.id', ondelete="CASCADE"), primary_key=True),
                                         Column('character_id', Integer, ForeignKey(
                                             'characters.id', ondelete="CASCADE"), primary_key=True)
                                         )
# 多対多: PlotEvents <-> Locations
plot_event_location_association = Table('plot_event_location_association', Base.metadata,
                                        Column('plot_event_id', Integer, ForeignKey(
                                            'plot_events.id', ondelete="CASCADE"), primary_key=True),
                                        Column('location_id', Integer, ForeignKey(
                                            'locations.id', ondelete="CASCADE"), primary_key=True)
                                        )
# 多対多: PlotEvents <-> Items
plot_event_item_association = Table('plot_event_item_association', Base.metadata,
                                    Column('plot_event_id', Integer, ForeignKey(
                                        'plot_events.id', ondelete="CASCADE"), primary_key=True),
                                    Column('item_id', Integer, ForeignKey(
                                        'items.id', ondelete="CASCADE"), primary_key=True)
                                    )


class Novel(Base):
    __tablename__ = "novels"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String)
    url = Column(String, unique=True, nullable=False, index=True)
    platform = Column(String, index=True)
    tags = Column(Text)
    synopsis = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        default=func.now(), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True))
    overall_sentiment_llm = Column(String)
    main_theme_llm = Column(Text)
    episodes = relationship("Episode", back_populates="novel",
                            cascade="all, delete-orphan", order_by="Episode.episode_number")
    characters = relationship(
        "Character", back_populates="novel", cascade="all, delete-orphan")
    locations = relationship(
        "Location", back_populates="novel", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="novel",
                         cascade="all, delete-orphan")
    world_settings = relationship(
        "WorldSetting", back_populates="novel", cascade="all, delete-orphan")
    foreshadowings = relationship(
        "Foreshadowing", back_populates="novel", cascade="all, delete-orphan")
    plot_events = relationship(
        "PlotEvent", back_populates="novel", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_title = Column(String)
    episode_url = Column(String, unique=True, index=True)
    episode_number = Column(Integer, index=True)
    content_raw = Column(Text)
    content_cleaned = Column(Text)
    char_count = Column(Integer, index=True)
    publication_date = Column(DateTime(timezone=True), index=True)
    last_fetched_at = Column(DateTime(timezone=True), default=func.now())
    summary_short = Column(Text)
    summary_long = Column(Text)
    key_events_extraction_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_ep_key_events"), default=ProcessingStatus.PENDING, index=True)
    summary_generation_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_ep_summary"), default=ProcessingStatus.PENDING, index=True)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_ep_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="episodes")
    plot_events = relationship(
        "PlotEvent", back_populates="episode", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    reading = Column(String)
    aliases = Column(Text)
    description_by_author = Column(Text)
    description_by_llm = Column(Text)
    role_in_story_llm = Column(String)
    first_appearance_episode_id = Column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"))
    status = Column(String, index=True)
    importance_score_llm = Column(Float)
    llm_analysis_notes = Column(Text)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_char_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="characters")
    first_appearance_episode = relationship("Episode")


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description_by_author = Column(Text)
    description_by_llm = Column(Text)
    first_appearance_episode_id = Column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"))
    importance_score_llm = Column(Float)
    llm_analysis_notes = Column(Text)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_loc_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="locations")
    first_appearance_episode = relationship("Episode")


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description_by_author = Column(Text)
    description_by_llm = Column(Text)
    item_type = Column(String, index=True)
    owner_character_id = Column(Integer, ForeignKey(
        "characters.id", ondelete="SET NULL"))
    first_appearance_episode_id = Column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"))
    importance_score_llm = Column(Float)
    llm_analysis_notes = Column(Text)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_item_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="items")
    owner_character = relationship("Character")
    first_appearance_episode = relationship("Episode")


class PlotEvent(Base):
    __tablename__ = "plot_events"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_id = Column(Integer, ForeignKey(
        "episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    event_type = Column(String, index=True)
    timestamp_in_episode_llm = Column(String)
    absolute_timestamp_llm = Column(DateTime(timezone=True), index=True)
    significance_score_llm = Column(Float)
    sentiment_llm = Column(String)
    llm_analysis_notes = Column(Text)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_event_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="plot_events")
    episode = relationship("Episode", back_populates="plot_events")
    characters_involved = relationship(
        "Character", secondary=plot_event_character_association, backref="involved_events")
    locations_involved = relationship(
        "Location", secondary=plot_event_location_association, backref="events_at_location")
    items_involved = relationship(
        "Item", secondary=plot_event_item_association, backref="events_involving_item")


class WorldSetting(Base):
    __tablename__ = "world_settings"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    setting_key = Column(String, nullable=False, index=True)
    setting_value = Column(Text)
    description_by_llm = Column(Text)
    source_episode_id = Column(Integer, ForeignKey(
        "episodes.id", ondelete="SET NULL"))
    category = Column(String, index=True)
    is_explicitly_stated = Column(Boolean, default=True)
    llm_implications = Column(Text)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_setting_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="world_settings")
    source_episode = relationship("Episode")


class Foreshadowing(Base):
    __tablename__ = "foreshadowings"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey(
        "novels.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_episode_id = Column(Integer, ForeignKey(
        "episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    description_by_llm = Column(Text, nullable=False)
    context_snippet = Column(Text)
    status = Column(SQLAlchemyEnum(ForeshadowingStatus, name="foreshadowing_status_enum"),
                    default=ForeshadowingStatus.UNRESOLVED, nullable=False, index=True)
    resolved_episode_id = Column(Integer, ForeignKey(
        "episodes.id", ondelete="SET NULL"))
    resolution_description_llm = Column(Text)
    llm_confidence_score = Column(Float)
    llm_predicted_resolution_episode_number = Column(Integer)
    llm_analysis_notes = Column(Text)
    llm_analysis_status = Column(SQLAlchemyEnum(
        ProcessingStatus, name="proc_status_fs_analysis"), default=ProcessingStatus.PENDING, index=True)
    novel = relationship("Novel", back_populates="foreshadowings")
    raised_episode = relationship("Episode", foreign_keys=[raised_episode_id])
    resolved_episode = relationship(
        "Episode", foreign_keys=[resolved_episode_id])
