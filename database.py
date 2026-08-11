from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)

    orders = relationship("Order", back_populates="user")


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    registration_date = Column(String)  # дата регистрации
    number_type = Column(String)  # "DE" или "MIX"
    nickname = Column(String, nullable=True)
    has_game = Column(Boolean, default=False)
    is_top = Column(Boolean, default=False)
    cookies_filename = Column(String)  # имя файла в папке cookies/
    price = Column(Float)
    is_sold = Column(Boolean, default=False)
    sold_to = Column(BigInteger, ForeignKey('users.telegram_id'), nullable=True)
    sold_at = Column(DateTime, nullable=True)

    orders = relationship("Order", back_populates="account")


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_id = Column(String, unique=True, index=True)  # например, "37362038"
    user_id = Column(BigInteger, ForeignKey('users.telegram_id'))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # "Оплачен", "Ожидает оплаты", "Отменен"
    amount = Column(Float)
    payment_method = Column(String)  # "CryptoBot" или "xRocket"
    payment_id = Column(String, nullable=True)  # ID платежа от платежной системы

    user = relationship("User", back_populates="orders")
    account = relationship("Account", back_populates="orders")


# Создаем таблицы
def init_db():
    Base.metadata.create_all(engine)


# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()