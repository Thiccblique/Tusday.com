"""
models.py - Database Models

SQLAlchemy models for the Tusday.com app.
Defines User, Board, Column, and Task table structures.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from passlib.hash import bcrypt

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship to boards
    boards = relationship("Board", back_populates="owner", cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Hash and store the password"""
        self.password_hash = bcrypt.hash(password)
    
    def check_password(self, password):
        """Verify a password against the hash"""
        return bcrypt.verify(password, self.password_hash)
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Board(Base):
    """Board model for organizing tasks"""
    
    __tablename__ = 'boards'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    owner = relationship("User", back_populates="boards")
    columns = relationship("BoardColumn", back_populates="board", cascade="all, delete-orphan", order_by="BoardColumn.position")
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan", order_by="Task.position")
    
    def __repr__(self):
        return f"<Board(name='{self.name}', user_id={self.user_id})>"


class BoardColumn(Base):
    """Column definition for a board"""
    
    __tablename__ = 'board_columns'
    
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey('boards.id'), nullable=False)
    name = Column(String(100), nullable=False)
    column_type = Column(String(20), nullable=False)  # 'text', 'status', 'date'
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship
    board = relationship("Board", back_populates="columns")
    
    def __repr__(self):
        return f"<BoardColumn(name='{self.name}', type='{self.column_type}')>"


class Task(Base):
    """Task/row in a board"""
    
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    board_id = Column(Integer, ForeignKey('boards.id'), nullable=False)
    name = Column(String(200), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    board = relationship("Board", back_populates="tasks")
    cells = relationship("TaskCell", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(name='{self.name}', board_id={self.board_id})>"


class TaskCell(Base):
    """Cell value for a task in a specific column"""
    
    __tablename__ = 'task_cells'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    column_id = Column(Integer, ForeignKey('board_columns.id'), nullable=False)
    value = Column(Text)  # Stores text, status, or date as string
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship
    task = relationship("Task", back_populates="cells")
    
    def __repr__(self):
        return f"<TaskCell(task_id={self.task_id}, column_id={self.column_id}, value='{self.value}')>"
