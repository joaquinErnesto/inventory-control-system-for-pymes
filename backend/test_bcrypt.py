from passlib.context import CryptContext
import bcrypt

print("bcrypt version:", bcrypt.__version__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

password = "Admin1234"

print("Hashing...")

hashed = pwd_context.hash(password)

print(hashed)

print(pwd_context.verify(password, hashed))