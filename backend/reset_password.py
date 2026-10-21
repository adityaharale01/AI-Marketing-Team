
from app.database import SessionLocal
from app.models.user import User
from app.auth.hashing import hash_password

EMAIL = "aditya.test@gmail.com"

db = SessionLocal()

try:
    user = db.query(User).filter(User.email == EMAIL).first()

    if not user:
        print(f"User not found: {EMAIL}")
    else:
        new_password = input("Enter the new password: ")

        if len(new_password) < 8:
            print("Password must contain at least 8 characters.")
        else:
            user.password = hash_password(new_password)
            db.commit()
            print(f"Password reset successfully for {EMAIL}")

finally:
    db.close()
