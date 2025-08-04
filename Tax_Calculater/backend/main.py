# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List
import traceback

from . import crud, models, schemas, auth
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Tax Calculator API",
    description="A production-grade tax calculator with user authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# 🌐 ROOT ENDPOINT
# =============================
@app.get("/")
async def root():
    return {"message": "Tax Calculator API", "version": "1.0.0"}

# =============================
# 🔐 AUTHENTICATION ENDPOINTS
# =============================

@app.post("/auth/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    return crud.create_user(db=db, user=user)

@app.post("/auth/login", response_model=schemas.Token)
async def login_user(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

# =============================
# ✅ TAX CALCULATION ENDPOINT
# =============================

@app.post("/tax/calculate", response_model=schemas.TaxBreakdown)
async def calculate_tax_endpoint(data: schemas.TaxRecordCreate):
    try:
        gross_salary = data.gross_salary
        if gross_salary <= 0:
            raise HTTPException(status_code=400, detail="Gross salary must be positive")

        result = crud.calculate_tax(gross_salary)

        return {
            "gross_salary": gross_salary,
            "tax_paid": result["tax_paid"],
            "net_salary": result["net_salary"],
            "tax_rate": result["tax_rate"],
            "tax_brackets": result["tax_brackets"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate tax: {str(e)}")

# =============================
# 📄 TAX RECORDS ENDPOINTS
# =============================

@app.post("/tax/records", response_model=schemas.TaxRecordResponse)
async def create_tax_record(
    tax_record: schemas.TaxRecordCreate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    print("Received request to create tax record")  # <-- Add this line
    try:
        return crud.create_tax_record(db, tax_record, current_user.id)
    except Exception as e:
        print("Error saving tax record:", e)
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save tax record")

@app.get("/tax/records", response_model=List[schemas.TaxRecordResponse])
async def get_tax_records(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    return crud.get_tax_records(db, user_id=current_user.id, skip=skip, limit=limit)

@app.get("/tax/records/{record_id}", response_model=schemas.TaxRecordResponse)
async def get_tax_record(
    record_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    db_record = crud.get_tax_record(db, record_id=record_id, user_id=current_user.id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Tax record not found")
    return db_record

@app.put("/tax/records/{record_id}", response_model=schemas.TaxRecordResponse)
async def update_tax_record(
    record_id: int,
    tax_record: schemas.TaxRecordUpdate,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    db_record = crud.update_tax_record(
        db, record_id=record_id, user_id=current_user.id, tax_record=tax_record
    )
    if db_record is None:
        raise HTTPException(status_code=404, detail="Tax record not found")
    return db_record

@app.delete("/tax/records/{record_id}")
async def delete_tax_record(
    record_id: int,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    db_record = crud.delete_tax_record(db, record_id=record_id, user_id=current_user.id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Tax record not found")
    return {"message": "Tax record deleted successfully"}

# =============================
# 🩺 HEALTH CHECK ENDPOINT
# =============================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Tax Calculator API is running"}

# =============================
# � EMPLOYEE ENDPOINTS
# =============================

from fastapi import Body

@app.post("/employees/register", response_model=schemas.EmployeeResponse)
async def register_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db)
):
    # Check for duplicate tax number
    db_employee = crud.get_employee_by_tax_number(db, tax_number=employee.tax_number)
    if db_employee:
        raise HTTPException(status_code=400, detail="Employee with this tax number already exists")
    # Create employee
    db_employee = crud.create_employee(db, employee)
    # Calculate and store tax for employee
    crud.create_employee_tax(db, db_employee.employee_id, db_employee.salary)
    return db_employee





# --- All employees with tax info ---
@app.get("/employees/records")
async def all_employees_with_tax(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    results = []
    for emp in employees:
        latest_tax = (
            db.query(models.EmployeeTax)
            .filter(models.EmployeeTax.employee_id == emp.employee_id)
            .order_by(models.EmployeeTax.created_at.desc())
            .first()
        )
        results.append({
            "employee": schemas.EmployeeResponse.from_orm(emp),
            "tax": schemas.EmployeeTaxResponse.from_orm(latest_tax) if latest_tax else None
        })
    return results

# --- Employee dashboard endpoint (employee + tax info) ---
@app.get("/employees/{employee_id}/dashboard")
async def employee_dashboard(employee_id: int, db: Session = Depends(get_db)):
    result = crud.get_employee_with_tax(db, employee_id)
    if not result:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee, tax = result
    return {"employee": schemas.EmployeeResponse.from_orm(employee), "tax": schemas.EmployeeTaxResponse.from_orm(tax) if tax else None}

# --- Get single employee (no tax info) ---
@app.get("/employees/{employee_id}", response_model=schemas.EmployeeResponse)
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    result = crud.get_employee_with_tax(db, employee_id)
    if not result:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee, _ = result
    return employee

# --- List all employees (no tax info) ---
@app.get("/employees", response_model=List[schemas.EmployeeResponse])
async def list_employees(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    return employees

# =============================
# �🚀 LOCAL DEV ENTRY POINT
# =============================

# Only include this block for FastAPI backend, not Streamlit frontend
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Remove Streamlit code from FastAPI backend
