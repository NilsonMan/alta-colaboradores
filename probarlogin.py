#!/usr/bin/env python3
"""
Script para probar login después de corregir hashes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, Usuario, get_db
from werkzeug.security import check_password_hash

def test_login_after_fix():
    """Prueba el login después de corregir los hashes."""
    with app.app_context():
        with get_db() as db:
            print("=" * 80)
            print("PRUEBA DE LOGIN DESPUÉS DE CORRECCIÓN")
            print("=" * 80)
            
            usuarios = [
                ('admin@marnezdesarrollos.com', 'Admin123!'),
                ('coordinador.ti@marnezdesarrollos.com', 'TiPassword123!')
            ]
            
            for email, password in usuarios:
                usuario = db.query(Usuario).filter_by(correo=email).first()
                
                if not usuario:
                    print(f"\n✗ Usuario no encontrado: {email}")
                    continue
                
                print(f"\nProbando: {email}")
                print(f"Hash almacenado: {usuario.password_hash[:60]}...")
                
                # Verificar formato
                if usuario.password_hash.startswith('$scrypt$'):
                    print("✅ Formato CORRECTO")
                    
                    # Probar contraseña
                    try:
                        if check_password_hash(usuario.password_hash, password):
                            print(f"✅ Contraseña '{password}' es CORRECTA")
                        else:
                            print(f"✗ Contraseña '{password}' es INCORRECTA")
                    except Exception as e:
                        print(f"✗ Error verificando contraseña: {e}")
                else:
                    print(f"✗ Formato INCORRECTO: {usuario.password_hash[:30]}...")
                    print(f"  Debe empezar con '$scrypt$'")

if __name__ == "__main__":
    test_login_after_fix()