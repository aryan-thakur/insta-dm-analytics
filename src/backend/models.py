from sqlalchemy import Column, Integer, Text, DateTime, Boolean, String, BigInteger
from backend.config import Base


# --- Database Model ---
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_username = Column(Text)
    sender = Column(Text)
    message = Column(Text)
    timestamp_iso_dt = Column(DateTime(timezone=False))  # Add the timestamp_iso column
    story_reply = Column(Text)
    liked = Column(Boolean)
    timestamp_liked = Column(DateTime)
    attachment = Column(Text)
    attachment_link = Column(Text)
    reference_account = Column(Text)
    audio = Column(Boolean)
    photo = Column(Boolean)
    video = Column(Boolean)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(BigInteger)
    username = Column(String, primary_key=True, index=True)
    name = Column(String)
    created_at = Column(DateTime(timezone=False))
