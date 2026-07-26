import uuid
from typing import Optional, List
from datetime import date, datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
    Table,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


research_authors = Table(
    "research_authors",
    Base.metadata,
    Column("research_id", String(36), ForeignKey("researches.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", String(36), ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(128), nullable=True),
)

research_institutions = Table(
    "research_institutions",
    Base.metadata,
    Column("research_id", String(36), ForeignKey("researches.id", ondelete="CASCADE"), primary_key=True),
    Column("institution_id", String(36), ForeignKey("institutions.id", ondelete="CASCADE"), primary_key=True),
)


class Research(Base):
    __tablename__ = "researches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    field_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("fields.id", ondelete="SET NULL"),
                                                    nullable=True)

    unit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cluster: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contribution_category: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    start_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    finish_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_researches_year", "year"),
    )

    field: Mapped[Optional["Field"]] = relationship(back_populates="researches")
    institutions: Mapped[List["Institution"]] = relationship(secondary=research_institutions, back_populates="researches")
    authors: Mapped[List["Author"]] = relationship(secondary=research_authors, back_populates="researches")
    validation_flag: Mapped[Optional["ResearchValidationFlag"]] = relationship(back_populates="research", uselist=False)


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    researches: Mapped[List["Research"]] = relationship(secondary=research_institutions, back_populates="institutions")


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)

    researches: Mapped[List["Research"]] = relationship(back_populates="field")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    nidn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    researches: Mapped[List["Research"]] = relationship(secondary=research_authors, back_populates="authors")


class ResearchValidationFlag(Base):
    __tablename__ = "research_validation_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    research_id: Mapped[str] = mapped_column(String(36), ForeignKey("researches.id", ondelete="CASCADE"),
                                             nullable=False, unique=True)

    is_entropy: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    alt_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    alt_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_efficiency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    efficiency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_validation_entropy", "is_entropy"),
    )

    research: Mapped["Research"] = relationship(back_populates="validation_flag")


class CategorizationConfig(Base):
    __tablename__ = "categorization_config"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class EfficiencyKeywordGroup(Base):
    __tablename__ = "efficiency_keyword_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)

    keywords: Mapped[List["EfficiencyKeyword"]] = relationship(back_populates="group", order_by="EfficiencyKeyword.id")


class EfficiencyKeyword(Base):
    __tablename__ = "efficiency_keywords"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(String(36), ForeignKey("efficiency_keyword_groups.id", ondelete="CASCADE"),
                                          nullable=False)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="EN")

    __table_args__ = (
        Index("idx_efficiency_keywords_group", "group_id"),
    )

    group: Mapped["EfficiencyKeywordGroup"] = relationship(back_populates="keywords")


class EfficiencyCueWord(Base):
    __tablename__ = "efficiency_cue_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    word: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
