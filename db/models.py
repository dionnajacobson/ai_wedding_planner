from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BudgetCategory(StrEnum):
    """Budget line item categories."""

    ATTIRE = "attire"
    CATERING = "catering"
    DECOR = "decor"
    FLOWERS = "flowers"
    MUSIC = "music"
    OTHER = "other"
    PHOTOGRAPHY = "photography"
    STATIONERY = "stationery"
    TRANSPORTATION = "transportation"
    VENUE = "venue"
    VIDEOGRAPHY = "videography"


class MessageRole(StrEnum):
    """Role of a message in a wedding planning conversation."""

    ASSISTANT = "assistant"
    USER = "user"


class VendorCategory(StrEnum):
    """Vendor types tracked for a wedding."""

    ATTIRE = "attire"
    CATERING = "catering"
    DECOR = "decor"
    FLOWERS = "flowers"
    MUSIC = "music"
    OTHER = "other"
    PHOTOGRAPHY = "photography"
    STATIONERY = "stationery"
    TRANSPORTATION = "transportation"
    VENUE = "venue"
    VIDEOGRAPHY = "videography"


class VendorStatus(StrEnum):
    """Progress state for a vendor shortlist entry."""

    BOOKED = "booked"
    CONTACTED = "contacted"
    DECLINED = "declined"
    RESEARCHING = "researching"
    TO_CONTACT = "to_contact"


class Base(DeclarativeBase):
    """Base class for all models."""


class Client(Base):
    """Couple member using the wedding assistant."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sessions: Mapped[list[WeddingSession]] = relationship(back_populates="client")
    wedding: Mapped[Wedding | None] = relationship(
        back_populates="client",
        uselist=False,
    )


class Wedding(Base):
    """Wedding details for a couple."""

    __tablename__ = "weddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    guest_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    style: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)),
        nullable=False,
        server_default="{}",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    wedding_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    budget_items: Mapped[list[BudgetItem]] = relationship(
        back_populates="wedding",
        cascade="all, delete-orphan",
        order_by="BudgetItem.created_at",
    )
    client: Mapped[Client] = relationship(back_populates="wedding")
    sessions: Mapped[list[WeddingSession]] = relationship(back_populates="wedding")
    vendors: Mapped[list[WeddingVendor]] = relationship(
        back_populates="wedding",
        cascade="all, delete-orphan",
        order_by="WeddingVendor.created_at",
    )


class BudgetItem(Base):
    """A planned or actual expense line on the wedding budget."""

    __tablename__ = "budget_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actual_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[BudgetCategory] = mapped_column(
        SAEnum(BudgetCategory, native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    estimated_amount: Mapped[float] = mapped_column(Float, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    wedding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("weddings.id"), nullable=False
    )

    wedding: Mapped[Wedding] = relationship(back_populates="budget_items")


class WeddingVendor(Base):
    """A vendor the couple is researching or has booked."""

    __tablename__ = "wedding_vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[VendorCategory] = mapped_column(
        SAEnum(VendorCategory, native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photos: Mapped[list[str]] = mapped_column(
        ARRAY(String(1000)),
        nullable=False,
        server_default="{}",
    )
    status: Mapped[VendorStatus] = mapped_column(
        SAEnum(VendorStatus, native_enum=False),
        nullable=False,
        default=VendorStatus.RESEARCHING,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    wedding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("weddings.id"), nullable=False
    )

    wedding: Mapped[Wedding] = relationship(back_populates="vendors")


class WeddingSession(Base):
    """Chat session for a wedding planning conversation."""

    __tablename__ = "wedding_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    wedding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("weddings.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    client: Mapped[Client] = relationship(back_populates="sessions")
    messages: Mapped[list[Message]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    wedding: Mapped[Wedding] = relationship(back_populates="sessions")


class Message(Base):
    """Chat message within a wedding session."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, native_enum=False), nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wedding_sessions.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[WeddingSession] = relationship(back_populates="messages")
