from sqlalchemy import Column, Integer, Text, DateTime, Boolean, String
from backend.config import Base


# --- Database Model ---
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_username = Column(Text)
    sender = Column(Text)
    message = Column(Text)
    timestamp_iso_dt = Column(String)  # Add the timestamp_iso column
    story_reply = Column(Text)
    liked = Column(Boolean)
    timestamp_liked = Column(DateTime)
    attachment = Column(Text)
    attachment_link = Column(Text)
    reference_account = Column(Text)
    audio = Column(Boolean)
    photo = Column(Boolean)
    video = Column(Boolean)
