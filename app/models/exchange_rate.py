from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.core.constants import DEFAULT_CURRENCY


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True)

    currency = Column(String(3), nullable=False)

    rate_to_cny = Column(Numeric(10, 6), nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    is_default = Column(Integer, nullable=False, default=0)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('currency', 'user_id', name='uq_currency_user'),
        Index('idx_exchange_rates_currency', 'currency'),
        Index('idx_exchange_rates_user_id', 'user_id'),
    )
