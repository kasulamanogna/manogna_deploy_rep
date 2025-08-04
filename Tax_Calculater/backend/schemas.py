"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
import traceback


# Add missing TaxBreakdown schema for /tax/calculate endpoint
class TaxBreakdown(BaseModel):
    gross_salary: float
    tax_paid: float
    net_salary: float
    tax_rate: float
    tax_brackets: List[dict]

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# Tax Record schemas
class TaxRecordBase(BaseModel):
    gross_salary: float
    tax_year: int
    
    @validator('gross_salary')
    def validate_salary(cls, v):
        if v <= 0:
            raise ValueError('Gross salary must be positive')
        return v
    
    @validator('tax_year')
    def validate_tax_year(cls, v):
        current_year = datetime.now().year
        if v < 2020 or v > current_year + 1:
            raise ValueError(f'Tax year must be between 2020 and {current_year + 1}')
        return v

class TaxRecordCreate(BaseModel):
    gross_salary: float
    tax_year: int

class TaxRecordUpdate(BaseModel):
    gross_salary: Optional[float] = None
    tax_year: Optional[int] = None

class TaxRecordResponse(TaxRecordBase):
    id: int
    user_id: int
    tax_paid: float
    net_salary: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# --- Employee schemas ---
class EmployeeBase(BaseModel):
    full_name: str
    tax_number: str
    years_of_experience: int
    skills: str
    salary: float

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    employee_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class EmployeeTaxBase(BaseModel):
    employee_id: int
    calculated_tax: float
    tax_rate: float
    created_at: datetime

class EmployeeTaxResponse(EmployeeTaxBase):
    id: int
    class Config:
        from_attributes = True
    