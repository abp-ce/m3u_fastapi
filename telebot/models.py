from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, String, DateTime, Integer, Identity
from sqlalchemy.orm import relationship

Base = declarative_base()

class Channel(Base):
  __tablename__ = "channel"
  ch_id = Column(String(10), primary_key=True)
  disp_name = Column(String(80), unique=True, nullable=False)
  disp_name_l = Column(String(80), unique=True, nullable=False)
  icon = Column(String(80))
  programmes = relationship("Programme", back_populates="channel_rel")

class Programme(Base):
  __tablename__ = "programme"
  id = Column(Integer, Identity(always= True), primary_key=True)
  channel = Column(String(10), ForeignKey('channel.ch_id'))
  pstart = Column(DateTime, nullable=False)
  pstop = Column(DateTime, nullable=False)
  title = Column(String(400))
  pdesc = Column(String(1500))
  cat = Column(String(50))
  channel_rel = relationship("Channel", back_populates="programmes")
