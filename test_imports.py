try:
    from flask_wtf.csrf import CSRFProtect, generate_csrf
    print("✅ Flask-WTF importado correctamente")
except Exception as e:
    print(f"❌ Error importando Flask-WTF: {e}")

try:
    from flask_limiter import Limiter
    print("✅ Flask-Limiter importado correctamente")
except Exception as e:
    print(f"❌ Error importando Flask-Limiter: {e}")

try:
    from flask_caching import Cache
    print("✅ Flask-Caching importado correctamente")
except Exception as e:
    print(f"❌ Error importando Flask-Caching: {e}")

try:
    from sqlalchemy import create_engine
    print("✅ SQLAlchemy importado correctamente")
except Exception as e:
    print(f"❌ Error importando SQLAlchemy: {e}")