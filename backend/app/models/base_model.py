from app.database.base import Base
from app.database.mixins import UUIDMixin, TimestampMixin


class BaseModel(UUIDMixin, TimestampMixin, Base):
    """Base class for all database models"""
    __abstract__=True
