from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

print("Backend:", pwd_context.handler().get_backend())

password = "Admin1234"

hashed = pwd_context.hash(password)

print(hashed)

print(
    pwd_context.verify(
        password,
        hashed
    )
)