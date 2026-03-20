import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.mesa_regalos.core.database import Base


class GiftStatus(str, enum.Enum):
    """Estado de un regalo dentro de una mesa."""

    DISPONIBLE = "disponible"
    COMPRADO = "comprado"


class User(Base):
    """Usuario registrado en la plataforma."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(50), default="email")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    paypal_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relación: un usuario tiene muchas mesas de regalos
    gift_tables: Mapped[list["GiftTable"]] = relationship(
        "GiftTable", back_populates="user", cascade="all, delete-orphan"
    )


class GiftTable(Base):
    """Mesa de regalos (wishlist) creada por un usuario."""

    __tablename__ = "gift_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    slug_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    user: Mapped["User"] = relationship("User", back_populates="gift_tables")
    gifts: Mapped[list["Gift"]] = relationship(
        "Gift", back_populates="gift_table", cascade="all, delete-orphan"
    )


class Gift(Base):
    """Producto/regalo individual dentro de una mesa de regalos."""

    __tablename__ = "gifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gift_table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("gift_tables.id"), nullable=False
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    affiliate_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[GiftStatus] = mapped_column(
        Enum(GiftStatus, values_callable=lambda x: [e.value for e in x]),
        default=GiftStatus.DISPONIBLE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relación: un regalo pertenece a una mesa
    gift_table: Mapped["GiftTable"] = relationship("GiftTable", back_populates="gifts")
