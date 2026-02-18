import sys
import os

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from database import SessionLocal
from models.usuario import Usuario
from security_tokens import get_password_hash

client = TestClient(app)

def create_user_if_not_exists(db: Session, email: str, role: str) -> Usuario:
    user = db.query(Usuario).filter(Usuario.correo == email).first()
    if not user:
        print(f"Creating user {email} with role {role}")
        # ID generation logic - keeping it simple and fitting within 9 chars
        base_id = email.split("@")[0][:9]
        
        user = Usuario(
            id=base_id, 
            nombre="Test",
            apellido="User",
            correo=email,
            telefono="1234567890", # Needs 10 digits
            password=get_password_hash("password123"),
            rol=role,
            verificado=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def run_verification():
    db = SessionLocal()
    try:
        # Create users
        admin_email = "admintest@exam.com"
        user_email = "usertest@exam.com"
        
        # Ensure we don't have ID collisions if running multiple times or with existing data
        # Using specific IDs or check by email is better.
        
        create_user_if_not_exists(db, admin_email, "admin")
        create_user_if_not_exists(db, user_email, "user")
        
        # Test 1: User access denied
        print("\n--- Testing User Access (Should fail) ---")
        login_response = client.post("/auth/login", json={"correo": user_email, "password": "password123"})
        if login_response.status_code != 200:
            print(f"Failed to login as user: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/auditoria/", headers=headers)
        print(f"User access /auditoria status: {response.status_code}")
        if response.status_code == 403:
             print("SUCCESS: User access denied as expected.")
        else:
             print(f"FAILURE: User access NOT denied. Status: {response.status_code}")

        # Test 2: Admin access granted
        print("\n--- Testing Admin Access (Should succeed) ---")
        login_response = client.post("/auth/login", json={"correo": admin_email, "password": "password123"})
        if login_response.status_code != 200:
            print(f"Failed to login as admin: {login_response.text}")
            return

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/auditoria/", headers=headers)
        print(f"Admin access /auditoria status: {response.status_code}")
        if response.status_code == 200:
             print("SUCCESS: Admin access granted.")
             data = response.json()
             print(f"Retrieved {len(data)} audit logs.")
             
             if len(data) > 0:
                 audit_id = data[0]["id"]
                 print(f"Testing detail view for ID {audit_id}...")
                 detail_response = client.get(f"/auditoria/{audit_id}", headers=headers)
                 if detail_response.status_code == 200:
                     print("SUCCESS: Admin detail access granted.")
                 else:
                     print(f"FAILURE: Admin detail access failed. Status: {detail_response.status_code}")
        else:
             print(f"FAILURE: Admin access failed. Status: {response.status_code}")
             print(response.text)

    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
