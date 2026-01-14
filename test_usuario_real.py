import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash

print("🔄 ACTUALIZANDO HASHES DE CONTRASEÑA - VERSIÓN CORREGIDA")
print("=" * 70)

# Conectar a la base de datos
engine = create_engine('mysql+pymysql://root:Manu3l21@localhost:3306/alta_colaboradores?charset=utf8mb4')
conn = engine.connect()

# Usuarios y sus contraseñas
usuarios = [
    ('admin@marnezdesarrollos.com', 'Admin123!'),
    ('coordinador.ti@marnezdesarrollos.com', 'TiPassword123!'),
    ('coordinador.rh@marnezdesarrollos.com', 'RhPassword123!')
]

for correo, password in usuarios:
    print(f"\n📝 Procesando: {correo}")
    
    # Verificar si el usuario existe
    check_sql = text("SELECT id, password_hash FROM usuarios WHERE correo = :correo")
    result = conn.execute(check_sql, {'correo': correo})
    usuario = result.fetchone()
    
    if usuario:
        usuario_id, hash_actual = usuario
        print(f"   Usuario ID: {usuario_id}")
        print(f"   Hash actual (40 chars): {hash_actual[:40] if hash_actual else 'VACÍO'}...")
        
        # ✅ CORRECCIÓN: Generar hash con parámetros EXPLÍCITOS para formato correcto
        try:
            # Usar los mismos parámetros que Werkzeug usa internamente
            nuevo_hash = generate_password_hash(
                password, 
                method='scrypt',
                salt_length=16,
                n=32768,
                r=8,
                p=1
            )
            
            print(f"   ✅ Hash generado con scrypt correctamente")
            print(f"   Formato: {'$scrypt$' if nuevo_hash.startswith('$scrypt$') else 'otro'}")
        except Exception as e:
            print(f"   ⚠️ Error con scrypt: {e}, usando pbkdf2 como respaldo")
            # Usar pbkdf2 como respaldo
            nuevo_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        print(f"   Nuevo hash (primeros 60 chars): {nuevo_hash[:60]}...")
        
        # Verificar que el hash funcione inmediatamente
        try:
            if check_password_hash(nuevo_hash, password):
                print(f"   ✅ Hash verificado exitosamente")
            else:
                print(f"   ❌ ERROR: El hash NO funciona con la contraseña")
        except Exception as e:
            print(f"   ⚠️ Error verificando hash: {e}")
        
        # Actualizar en BD
        update_sql = text("UPDATE usuarios SET password_hash = :hash WHERE id = :id")
        conn.execute(update_sql, {'hash': nuevo_hash, 'id': usuario_id})
        print(f"   ✅ Hash actualizado en BD")
        
    else:
        print(f"   ⚠️ Usuario no encontrado, saltando...")

# Confirmar cambios
conn.commit()
conn.close()

print("\n" + "=" * 70)
print("✅ HASHES ACTUALIZADOS EXITOSAMENTE")
print("\n🔑 Ahora puedes iniciar sesión con:")
print("   • admin@marnezdesarrollos.com / Admin123!")
print("   • coordinador.ti@marnezdesarrollos.com / TiPassword123!")
print("   • coordinador.rh@marnezdesarrollos.com / RhPassword123!")