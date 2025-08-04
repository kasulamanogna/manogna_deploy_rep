from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
from .auth import get_password_hash
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

def get_employee_by_tax_number(db: Session, tax_number: str):
    """Get employee by tax number"""
    return db.query(models.Employee).filter(models.Employee.tax_number == tax_number).first()

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    """Create new employee and return the instance"""
    db_employee = models.Employee(
        full_name=employee.full_name,
        tax_number=employee.tax_number,
        years_of_experience=employee.years_of_experience,
        skills=employee.skills,
        salary=employee.salary
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def create_employee_tax(db: Session, employee_id: int, salary: float):
    """Calculate tax for employee and save to employee_taxes table"""
    tax_result = calculate_tax(salary)
    db_tax = models.EmployeeTax(
        employee_id=employee_id,
        calculated_tax=tax_result["tax_paid"],
        tax_rate=tax_result["tax_rate"]
    )
    db.add(db_tax)
    db.commit()
    db.refresh(db_tax)
    return db_tax

def get_employee_with_tax(db: Session, employee_id: int):
    """Get employee and their latest tax info"""
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not employee:
        return None
    latest_tax = (
        db.query(models.EmployeeTax)
        .filter(models.EmployeeTax.employee_id == employee_id)
        .order_by(models.EmployeeTax.created_at.desc())
        .first()
    )
    return employee, latest_tax
"""
CRUD operations for database models
"""

def get_user(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Create new user"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def calculate_tax(gross_salary: float) -> dict:
    """
    Calculate tax based on progressive tax brackets
    Tax Brackets (Example - Indian Tax Slabs for FY 2023-24):
    - 0 to 2,50,000: 0%
    - 2,50,001 to 5,00,000: 5%
    - 5,00,001 to 10,00,000: 20%
    - Above 10,00,000: 30%
    """
    tax_brackets = [
        {"min": 0, "max": 250000, "rate": 0.0},
        {"min": 250001, "max": 500000, "rate": 0.05},
        {"min": 500001, "max": 1000000, "rate": 0.20},
        {"min": 1000001, "max": float('inf'), "rate": 0.30}
    ]
    
    total_tax = 0.0

    for bracket in tax_brackets:
        lower = bracket["min"]
        upper = bracket["max"]
        rate = bracket["rate"]

        if gross_salary > lower:
            taxable_amount = min(gross_salary, upper) - lower
            tax = taxable_amount * rate
            total_tax += tax

    net_salary = gross_salary - total_tax
    tax_rate = (total_tax / gross_salary * 100) if gross_salary > 0 else 0

    return {
        "tax_paid": round(total_tax, 2),
        "net_salary": round(net_salary, 2),
        "tax_rate": round(tax_rate, 2),
        "tax_brackets": tax_brackets
    }


def create_tax_record(db: Session, tax_record: schemas.TaxRecordCreate, user_id: int):
    tax_calc = calculate_tax(tax_record.gross_salary)
    now = datetime.utcnow()
    db_record = models.TaxRecord(
        user_id=user_id,
        gross_salary=tax_record.gross_salary,
        tax_paid=tax_calc["tax_paid"],
        net_salary=tax_calc["net_salary"],
        tax_year=tax_record.tax_year,
        created_at=now,
        updated_at=now,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_tax_records(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all tax records for a user"""
    return db.query(models.TaxRecord).filter(
        models.TaxRecord.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_tax_record(db: Session, record_id: int, user_id: int):
    """Get specific tax record for a user"""
    return db.query(models.TaxRecord).filter(
        and_(models.TaxRecord.id == record_id, models.TaxRecord.user_id == user_id)
    ).first()

def update_tax_record(db: Session, record_id: int, user_id: int, tax_record: schemas.TaxRecordUpdate):
    """Update existing tax record"""
    db_record = get_tax_record(db, record_id, user_id)
    if not db_record:
        return None
    
    update_data = tax_record.dict(exclude_unset=True)
    
    # Recalculate tax if gross_salary is updated
    if "gross_salary" in update_data:
        tax_calc = calculate_tax(update_data["gross_salary"])
        update_data.update({
            "tax_paid": tax_calc["tax_paid"],
            "net_salary": tax_calc["net_salary"]
        })
    
    for field, value in update_data.items():
        setattr(db_record, field, value)
    
    db.commit()
    db.refresh(db_record)
    return db_record

def delete_tax_record(db: Session, record_id: int, user_id: int):
    """Delete tax record"""
    db_record = get_tax_record(db, record_id, user_id)
    if not db_record:
        return None
    
    db.delete(db_record)
    db.commit()
    return db_record