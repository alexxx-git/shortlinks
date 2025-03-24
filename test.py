import bcrypt
print(bcrypt.__version__)  # Должно быть 4.0.1
import passlib.hash
print(passlib.hash.bcrypt.hash("test"))

