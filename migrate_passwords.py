#!/usr/bin/env python3
"""
Script para migrar contraseñas a formato scrypt
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '3306',
    'name': 'alta_colaboradores',
    'user': 'root',
    'password': 'Manu3l21'
}

def main():
    # Crear conexión
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['name']}?charset=utf8mb4"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Obtener todos los usuarios
        result = conn.execute(text("SELECT id, correo, password_hash FROM usuarios"))
        usuarios = result.fetchall()
        
        print(f"Encontrados {len(usuarios)} usuarios")
        
        for usuario in usuarios:
            user_id, correo, old_hash = usuario
            
            print(f"\nUsuario ID {user_id}: {correo}")
            print(f"Hash actual: {old_hash[:50]}...")
            
            # Verificar si el hash necesita migración
            if not old_hash or old_hash.startswith('$scrypt$'):
                print("✓ Hash ya está en formato scrypt")
                continue
            
            # Preguntar nueva contraseña
            nueva_password = input(f"Ingresa nueva contraseña para {correo} (dejar vacío para saltar): ").strip()
            
            if not nueva_password:
                print("Saltando usuario...")
                continue
            
            # Generar nuevo hash con scrypt
            nuevo_hash = generate_password_hash(nueva_password, method='scrypt')
            
            # Actualizar en la base de datos
            conn.execute(
                text("UPDATE usuarios SET password_hash = :hash WHERE id = :id"),
                {"hash": nuevo_hash, "id": user_id}
            )
            conn.commit()
            
            print(f"✓ Contraseña actualizada para {correo}")
        
        print("\n" + "="*50)
        print("Migración completada")

if __name__ == "__main__":
    main()