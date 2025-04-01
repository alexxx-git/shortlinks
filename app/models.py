from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    # Связь с активными короткими ссылками
    links = relationship("ShortLink", back_populates="user")
    # Связь с архивными короткими ссылками
    archived_links = relationship("ShortLinkArchive", back_populates="user")

# Таблица коротких ссылок
class ShortLink(Base):
    __tablename__ = "short_links"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    short_code = Column(String, unique=True, nullable=False, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime)
    expires_at = Column(DateTime, nullable=True)
    last_access_at = Column(DateTime, nullable=True)
    auto_expires_at = Column(DateTime, nullable=True)
     
    # Связь с визитами (основная таблица)
    visits = relationship("Visit", back_populates="short_link", 
                         foreign_keys="[Visit.short_code]",
                         primaryjoin="ShortLink.short_code == Visit.short_code")
    user = relationship("User", back_populates="links")  # Связь с таблицей пользователей

# Таблица архивных коротких ссылок
class ShortLinkArchive(Base):
    __tablename__ = "short_links_archive"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    short_code = Column(String, nullable=False, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime)
    expires_at = Column(DateTime, nullable=True)
    last_access_at = Column(DateTime, nullable=True)
    auto_expires_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)  # Время удаления
    archival_reason = Column(String, nullable=True)  # Причина архивации (удалена, истёк срок и т.д.)
    user = relationship("User", back_populates="archived_links")
# Связь с архивными визитами
    visits_archive = relationship("VisitArchive", back_populates="archived_link",
                                foreign_keys="[VisitArchive.short_code]",
                                primaryjoin="ShortLinkArchive.short_code == VisitArchive.short_code")


   
# Таблица визитов
class Visit(Base):
    __tablename__ = "visits"
    
    id = Column(Integer, primary_key=True)
    owner=Column(Integer, nullable=True) # userid
    timestamp = Column(DateTime, default=datetime,  index=True) #time
    short_code = Column(String, ForeignKey("short_links.short_code"), nullable=False, index=True)
    original_url = Column(String, nullable=False) 
    domain_1st = Column(String, nullable=True)  # Домен 1-го уровня
    domain_2nd = Column(String, nullable=True)  # Домен 2-го уровня
    ip_address = Column(String, nullable=False)
    device_type = Column(String, nullable=False)  # Тип устройства (mobile, desktop)
    country = Column(String, nullable=True) #
    referer = Column(String, nullable=True) #
    short_link = relationship("ShortLink", back_populates="visits", primaryjoin="ShortLink.short_code == Visit.short_code")

class VisitArchive(Base):
    __tablename__ = "visit_archives"

    id = Column(Integer, primary_key=True)
    owner=Column(Integer, nullable=True) 
    timestamp = Column(DateTime, default=datetime,  index=True)
    short_code = Column(String, nullable=False, index=True)
    original_url = Column(String, nullable=False)
    domain_1st = Column(String, nullable=True)  # Домен 1-го уровня
    domain_2nd = Column(String, nullable=True)  # Домен 2-го уровня
    ip_address = Column(String, nullable=False)
    device_type = Column(String, nullable=False)  # Тип устройства (mobile, desktop)
    country = Column(String, nullable=True)
    referer = Column(String, nullable=True)
    archived_at = Column(DateTime, nullable=True)  # Время удаления
    archival_reason = Column(String, nullable=True)  # Причина архивации (удалена, истёк срок и т.д.)

    # Связь с основной ссылкой
    archived_link = relationship("ShortLinkArchive", back_populates="visits_archive",
                                foreign_keys=[short_code],
                                primaryjoin="ShortLinkArchive.short_code == VisitArchive.short_code")
        
        # Добавьте эти строки в вашу модель, чтобы связать архивные ссылки с пользователями
