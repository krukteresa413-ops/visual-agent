from pathlib import Path
from app.db.session import SessionLocal
from app.models.auth import User
from app.services.auth_service import hash_password, verify_password

EMAIL = "admin@moyag.local"
PASSWORD = r"********"
CREDENTIAL_PATH = Path("/root/moyag-admin-credentials.txt")

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == EMAIL).first()
    if not user:
        raise SystemExit("admin user not found")
    user.password_hash = hash_password(PASSWORD)
    db.commit()
    db.refresh(user)
    if not verify_password(PASSWORD, user.password_hash):
        raise SystemExit("password verification failed after update")
    CREDENTIAL_PATH.write_text(f"email={EMAIL}\npassword={PASSWORD}\n", encoding="utf-8")
    CREDENTIAL_PATH.chmod(0o600)
    print("updated", EMAIL, user.role)
finally:
    db.close()
