"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
import os

class User(Base):
    """
    User model for authentication and user management
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with tax records
    tax_records = relationship("TaxRecord", back_populates="user")

# --- Employee and EmployeeTax models ---
class Employee(Base):
    """
    Employee model for employee registration
    """
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    tax_number = Column(String(50), unique=True, nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    skills = Column(String(255), nullable=True)  # Comma-separated string
    salary = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with employee taxes
    taxes = relationship("EmployeeTax", back_populates="employee")

class EmployeeTax(Base):
    """
    EmployeeTax model for storing calculated tax for employees
    """
    __tablename__ = "employee_taxes"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    calculated_tax = Column(Float, nullable=False)
    tax_rate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="taxes")

class TaxRecord(Base):
    """
    Tax record model to store salary and tax calculations
    """
    __tablename__ = "tax_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gross_salary = Column(Float, nullable=False)
    tax_paid = Column(Float, nullable=False)
    net_salary = Column(Float, nullable=False)
    tax_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationship with user
    user = relationship("User", back_populates="tax_records")

## Database initialization commands (for reference, not used in code)
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost:5432/taxcalculator")
# INIT_DB_COMMANDS = [
#     "CREATE DATABASE taxcalculator;",
#     "CREATE USER myuser WITH PASSWORD 'mypassword';",
#     "GRANT ALL PRIVILEGES ON DATABASE taxcalculator TO myuser;"
# ]






