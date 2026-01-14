#!/usr/bin/env python3
"""
Script para corregir las contraseñas en la base de datos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, Usuario, get_db, generate_password_hash
from werkzeug.security import generate_password_hash

def fix_passwords():
    """Corrige las contraseñas en la base de datos."""
    with app.app_context():
        with get_db() as db:
            # Usuarios que necesitan corrección
            usuarios_data = [
                {
                    'correo': 'admin@marnezdesarrollos.com',
                    'nueva_password': 'Admin123!',
                    'area_id': 1,
                    'rol': 'admin'
                },
                {
                    'correo': 'coordinador.ti@marnezdesarrollos.com',
                    'nueva_password': 'TiPassword123!',
                    'area_id': 3,
                    'rol': 'coordinador'
                }
            ]
            
            for user_data in usuarios_data:
                usuario = db.query(Usuario).filter_by(correo=user_data['correo']).first()
                
                if usuario:
                    print(f"\nCorrigiendo usuario: {usuario.correo}")
                    print(f"Hash actual: {usuario.password_hash[:50]}...")
                    
                    # Generar nuevo hash con scrypt
                    nuevo_hash = generate_password_hash(user_data['nueva_password'], method='scrypt')
                    usuario.password_hash = nuevo_hash
                    
                    print(f"Nuevo hash: {nuevo_hash[:50]}...")
                    print(f"Contraseña establecida: {user_data['nueva_password']}")
                else:
                    print(f"\nUsuario no encontrado: {user_data['correo']}")
                    # Crear usuario si no existe
                    usuario = Usuario(
                        correo=user_data['correo'],
                        password_hash=generate_password_hash(user_data['nueva_password'], method='scrypt'),
                        area_id=user_data['area_id'],
                        rol=user_data['rol'],
                        activo=True
                    )
                    db.add(usuario)
                    print(f"Usuario creado: {user_data['correo']}")
            
            db.commit()
            print("\n✅ Contraseñas corregidas exitosamente!")

if __name__ == "__main__":
    fix_passwords()