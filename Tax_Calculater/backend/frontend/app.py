"""
Streamlit frontend application
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
# Ensure the API base URL is set correctly
def all_employees_page():
    """Show all employee records and their tax info in a table/grid."""
    st.header("👥 All Employee Records")
    if st.button("Refresh Employee List") or 'employee_table_loaded' not in st.session_state:
        try:
            response = requests.get(f"{API_BASE_URL}/employees/records")
            if response.status_code == 200:
                data = response.json()
                st.session_state.employee_table_loaded = True
                if data:
                    # Flatten for DataFrame
                    rows = []
                    for rec in data:
                        emp = rec.get("employee", {})
                        tax = rec.get("tax", {})
                        rows.append({
                            "Employee ID": emp.get("employee_id"),
                            "Full Name": emp.get("full_name"),
                            "Tax Number": emp.get("tax_number"),
                            "Experience": emp.get("years_of_experience"),
                            "Skills": emp.get("skills"),
                            "Salary": emp.get("salary"),
                            "Tax": tax.get("calculated_tax"),
                            "Tax Rate": tax.get("tax_rate"),
                            "Created At": emp.get("created_at")
                        })
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No employee records found.")
            else:
                st.error(f"Failed to fetch employee records: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
def employee_dashboard_page():
    """Employee dashboard: show profile and tax info by employee ID"""
    st.header("📋 Employee Dashboard")
    employee_id = st.number_input("Enter Employee ID", min_value=1, step=1)
    if st.button("View Dashboard"):
        try:
            response = requests.get(f"{API_BASE_URL}/employees/{int(employee_id)}/dashboard")
            if response.status_code == 200:
                data = response.json()
                emp = data.get("employee")
                tax = data.get("tax")
                st.subheader("Employee Profile")
                st.write(f"**Full Name:** {emp['full_name']}")
                st.write(f"**Tax Number:** {emp['tax_number']}")
                st.write(f"**Years of Experience:** {emp['years_of_experience']}")
                st.write(f"**Skills:** {emp['skills']}")
                st.write(f"**Salary:** ₹{emp['salary']:,.2f}")
                st.write(f"**Created At:** {emp['created_at'][:19].replace('T', ' ')}")
                st.markdown("---")
                if tax:
                    st.subheader("Tax Information")
                    st.write(f"**Calculated Tax:** ₹{tax['calculated_tax']:,.2f}")
                    st.write(f"**Tax Rate:** {tax['tax_rate']}%")
                    st.write(f"**Tax Calculated At:** {tax['created_at'][:19].replace('T', ' ')}")
                else:
                    st.info("No tax data available for this employee.")
            else:
                st.error(f"Not found or error: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
def employee_registration_page():
    """Employee registration form and auto-tax calculation"""
    st.header("👤 Employee Registration")
    with st.form("employee_registration_form"):
        full_name = st.text_input("Full Name")
        tax_number = st.text_input("Tax Number")
        years_of_experience = st.number_input("Years of Experience", min_value=0, step=1)
        skills = st.text_input("Skills (comma-separated)")
        salary = st.number_input("Salary (₹)", min_value=0.0, step=1000.0, format="%.2f")
        submit = st.form_submit_button("Register Employee")

        if submit:
            if not (full_name and tax_number and salary > 0):
                st.error("Please fill all required fields and enter a valid salary.")
            else:
                payload = {
                    "full_name": full_name,
                    "tax_number": tax_number,
                    "years_of_experience": int(years_of_experience),
                    "skills": skills,
                    "salary": salary
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/employees/register", json=payload)
                    if response.status_code == 200:
                        st.success("Employee registered and tax calculated!")
                        data = response.json()
                        st.json(data)
                    else:
                        st.error(f"Registration failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Configuration
API_BASE_URL = "http://localhost:8000"
os.chdir("C:\\Users\\HP\\Desktop\\Tax Calculater")

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

def make_authenticated_request(endpoint, method="GET", data=None):
    """Make authenticated API request"""
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None

def login_user(username, password):
    """Login user and store token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        st.session_state.token = token_data["access_token"]
        
        # Get user info
        user_response = make_authenticated_request("/auth/me")
        if user_response and user_response.status_code == 200:
            st.session_state.user_info = user_response.json()
            return True
    return False

def register_user(username, email, password):
    """Register new user"""
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": username, "email": email, "password": password}
    )
    return response.status_code == 200

def logout_user():
    """Logout user"""
    st.session_state.token = None
    st.session_state.user_info = None

def display_tax_breakdown(gross_salary, tax_data):
    """Display tax breakdown with visualizations"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Tax Summary")
        st.metric("Gross Salary", f"₹{gross_salary:,.2f}")
        st.metric("Tax Paid", f"₹{tax_data['tax_paid']:,.2f}")
        st.metric("Net Salary", f"₹{tax_data['net_salary']:,.2f}")
        st.metric("Tax Rate", f"{tax_data['tax_rate']:.2f}%")
    
    with col2:
        st.subheader("📊 Salary Breakdown")
        # Pie chart
        fig = px.pie(
            values=[tax_data['tax_paid'], tax_data['net_salary']],
            names=['Tax Paid', 'Net Salary'],
            title="Salary Distribution",
            color_discrete_map={'Tax Paid': '#ff6b6b', 'Net Salary': '#4ecdc4'}
        )
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Tax Calculator",
        page_icon="🧮",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🧮 Tax Calculator")
    st.markdown("---")

    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")

        if st.session_state.token:
            st.success(f"Welcome, {st.session_state.user_info['username']}!")
            page = st.selectbox(
                "Choose a page:",
                ["Calculate Tax", "My Tax Records", "Profile", "Employee Registration", "Employee Dashboard", "All Employees"]
            )
            if st.button("Logout"):
                logout_user()
                st.rerun()
        else:
            page = st.selectbox(
                "Choose a page:",
                ["Login", "Register", "Quick Calculator", "Employee Registration", "Employee Dashboard", "All Employees"]
            )

    # Main content based on selected page
    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
    elif page == "Quick Calculator":
        quick_calculator_page()
    elif page == "Employee Registration":
        employee_registration_page()
    elif page == "Employee Dashboard":
        employee_dashboard_page()
    elif page == "All Employees":
        all_employees_page()
    elif st.session_state.token:
        if page == "Calculate Tax":
            calculate_tax_page()
        elif page == "My Tax Records":
            tax_records_page()
        elif page == "Profile":
            profile_page()

def login_page():
    """Login page"""
    st.header("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                if login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter username and password")

def register_page():
    """Registration page"""
    st.header("📝 Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if username and email and password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    if register_user(username, email, password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Registration failed. Username or email might already exist.")
            else:
                st.error("Please fill in all fields")

def quick_calculator_page():
    """Quick tax calculator without authentication"""
    st.header("⚡ Quick Tax Calculator")
    st.info("💡 Register to save your calculations and track your tax records!")

    gross_salary = st.number_input(
        "Enter your gross annual salary (₹):",
        min_value=0.0,
        step=1000.0,
        format="%.2f"
    )

    if st.button("Calculate Tax"):
        if gross_salary > 0:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/tax/calculate",
                    json={"gross_salary": gross_salary, "tax_year": datetime.now().year}
                )
                if response.status_code == 200:
                    tax_data = response.json()
                    display_tax_breakdown(gross_salary, tax_data)
                else:
                    st.error(f"Failed to calculate tax. Status code: {response.status_code}")
                    st.text(response.text)
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {str(e)}")
        else:
            st.error("Please enter a valid salary amount")



def calculate_tax_page():
    """Calculate and save tax page"""
    st.header("🧮 Calculate & Save Tax")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("tax_calculation_form"):
            gross_salary = st.number_input(
                "Gross Annual Salary (₹):",
                min_value=0.0,
                step=1000.0,
                format="%.2f"
            )
            
            tax_year = st.selectbox(
                "Tax Year:",
                options=list(range(2020, datetime.now().year + 2)),
                index=len(list(range(2020, datetime.now().year + 2))) - 2
            )
            
            col_calc, col_save = st.columns(2)
            
            with col_calc:
                calculate_button = st.form_submit_button("Calculate Tax")
            
            with col_save:
                save_button = st.form_submit_button("Calculate & Save")
            
            if calculate_button or save_button:
                if gross_salary > 0:
                    # Calculate tax using authenticated request and correct JSON body
                    response = make_authenticated_request(
                        "/tax/calculate",
                        method="POST",
                        data={"gross_salary": gross_salary, "tax_year": tax_year}
                    )
                    if response and response.status_code == 200:
                        tax_data = response.json()
                        display_tax_breakdown(gross_salary, tax_data)
                        # Save if requested
                        if save_button:
                            save_response = make_authenticated_request(
                                "/tax/records",
                                method="POST",
                                data={"gross_salary": gross_salary, "tax_year": tax_year}
                            )
                            if save_response and save_response.status_code == 200:
                                st.success("Tax record saved successfully!")
                                
                                st.rerun()  # Refresh to show new record
                            else:
                                if save_response is not None:
                                    try:
                                        error_detail = save_response.json().get("detail", save_response.text)
                                    except Exception:
                                        error_detail = save_response.text
                                    st.error(f"Failed to save tax record: {error_detail}")
                                else:
                                    st.error("Failed to save tax record (no response)")
                    else:
                        st.error("Failed to calculate tax")
                        if response is not None:
                            st.text(response.text)
                else:
                    st.error("Please enter a valid salary amount")

def tax_records_page():
    """Tax records management page"""
    st.header("📊 My Tax Records")
    
    # Get tax records
    response = make_authenticated_request("/tax/records")
    if response and response.status_code == 200:
        records = response.json()
        
        if records:
            # Display records in a table
            df = pd.DataFrame(records)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(records))
            with col2:
                total_gross = sum(r['gross_salary'] for r in records)
                st.metric("Total Gross Salary", f"₹{total_gross:,.2f}")
            with col3:
                total_tax = sum(r['tax_paid'] for r in records)
                st.metric("Total Tax Paid", f"₹{total_tax:,.2f}")
            with col4:
                avg_tax_rate = (total_tax / total_gross * 100) if total_gross > 0 else 0
                st.metric("Average Tax Rate", f"{avg_tax_rate:.2f}%")
            
            st.subheader("Records Table")
            st.dataframe(
                df[['id', 'gross_salary', 'tax_paid', 'net_salary', 'tax_year', 'created_at']],
                use_container_width=True
            )
            
            # Chart showing tax records over time
            if len(records) > 1:
                st.subheader("Tax Trends")
                fig = px.line(
                    df, 
                    x='tax_year', 
                    y=['gross_salary', 'tax_paid', 'net_salary'],
                    title="Salary and Tax Trends Over Years"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Edit/Delete functionality
            st.subheader("Manage Records")
            selected_record_id = st.selectbox(
                "Select record to edit/delete:",
                options=[r['id'] for r in records],
                format_func=lambda x: f"Record {x} - ₹{next(r['gross_salary'] for r in records if r['id'] == x):,.2f}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit Selected Record"):
                    st.session_state.edit_record_id = selected_record_id
            
            with col2:
                if st.button("Delete Selected Record", type="secondary"):
                    delete_response = make_authenticated_request(
                        f"/tax/records/{selected_record_id}",
                        method="DELETE"
                    )
                    if delete_response and delete_response.status_code == 200:
                        st.success("Record deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete record")
            
            # Edit form
            if hasattr(st.session_state, 'edit_record_id'):
                record_to_edit = next(r for r in records if r['id'] == st.session_state.edit_record_id)
                st.subheader(f"Edit Record {st.session_state.edit_record_id}")
                
                with st.form("edit_record_form"):
                    new_gross_salary = st.number_input(
                        "Gross Salary:",
                        value=float(record_to_edit['gross_salary']),
                        min_value=0.0,
                        step=1000.0
                    )
                    new_tax_year = st.selectbox(
                        "Tax Year:",
                        options=list(range(2020, datetime.now().year + 2)),
                        index=list(range(2020, datetime.now().year + 2)).index(record_to_edit['tax_year'])
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Update Record"):
                            update_response = make_authenticated_request(
                                f"/tax/records/{st.session_state.edit_record_id}",
                                method="PUT",
                                data={"gross_salary": new_gross_salary, "tax_year": new_tax_year}
                            )
                            if update_response and update_response.status_code == 200:
                                st.success("Record updated successfully!")
                                del st.session_state.edit_record_id
                                st.rerun()
                            else:
                                st.error("Failed to update record")
                    
                    with col2:
                        if st.form_submit_button("Cancel"):
                            del st.session_state.edit_record_id
                            st.rerun()
        else:
            st.info("No tax records found. Create your first calculation!")
    else:
        st.error("Failed to fetch tax records")

def profile_page():
    """User profile page"""
    st.header("👤 Profile")
    
    if st.session_state.user_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("User Information")
            st.write(f"**Username:** {st.session_state.user_info['username']}")
            st.write(f"**Email:** {st.session_state.user_info['email']}")
            st.write(f"**Member Since:** {st.session_state.user_info['created_at'][:10]}")
            st.write(f"**Status:** {'Active' if st.session_state.user_info['is_active'] else 'Inactive'}")
        
        with col2:
            st.subheader("Account Statistics")
            # Get tax records count
            response = make_authenticated_request("/tax/records")
            if response and response.status_code == 200:
                records = response.json()
                st.metric("Total Tax Records", len(records))
                if records:
                    total_tax_paid = sum(r['tax_paid'] for r in records)
                    st.metric("Total Tax Calculated", f"₹{total_tax_paid:,.2f}")

if __name__ == "__main__":
    main()