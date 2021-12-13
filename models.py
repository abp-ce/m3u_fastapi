from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, String, DateTime, Integer, Identity, CheckConstraint
from sqlalchemy.orm import relationship

Base = declarative_base()

class Telebot_User(Base):
  __tablename__ = "telebot_users"
  chat_id = Column(Integer, primary_key=True)
  first_name = Column(String(30), nullable=False)
  shift =Column(Integer)

class M3U_User(Base):
  __tablename__ = "m3u_users"
  id = Column(Integer, Identity(always= True), primary_key=True)
  name = Column(String(30), unique=True, nullable=False)
  email = Column(String(50), unique=True, nullable=False)
  password = Column(String(80))
  creation_date = Column(DateTime, nullable=False)
  disabled = Column(String(1), CheckConstraint("disabled in ['Y','N'])"))

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
