#!/usr/bin/env python3
"""
Script para forzar el formato $scrypt$ en los hashes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
import secrets
import base64
import hashlib

def convert_scrypt_format(old_hash):
    """Convierte scrypt:... a $scrypt$..."""
    if not old_hash or not old_hash.startswith('scrypt:'):
        return old_hash
    
    # Formato: scrypt:N:r:p$salt$hash
    # Ejemplo: scrypt:32768:8:1$salt$hash
    
    try:
        # Dividir en partes
        parts = old_hash.split('$')
        if len(parts) != 3:
            return old_hash
        
        # Extraer componentes
        params_part = parts[0]  # scrypt:32768:8:1
        salt = parts[1]
        hash_value = parts[2]
        
        # Extraer parámetros
        params = params_part.replace('scrypt:', '')
        
        # Convertir a formato nuevo: $scrypt$N$r$p$salt$hash
        new_hash = f"$scrypt${params.replace(':', '$')}${salt}${hash_value}"
        
        return new_hash
    except:
        return old_hash

def force_new_format():
    """Fuerza el formato nuevo en la base de datos."""
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'Manu3l21',
        'database': 'alta_colaboradores',
        'charset': 'utf8mb4'
    }
    
    try:
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            print("=" * 80)
            print("FORZANDO FORMATO $scrypt$ EN HASHES")
            print("=" * 80)
            
            # Obtener todos los usuarios
            cursor.execute("SELECT id, correo, password_hash FROM usuarios")
            usuarios = cursor.fetchall()
            
            updated_count = 0
            
            for user_id, email, old_hash in usuarios:
                print(f"\nUsuario: {email}")
                print(f"Hash actual: {old_hash[:50]}...")
                
                # Verificar formato actual
                if old_hash and old_hash.startswith('scrypt:'):
                    # Convertir a formato nuevo
                    new_hash = convert_scrypt_format(old_hash)
                    
                    if new_hash != old_hash:
                        print(f"Hash convertido: {new_hash[:50]}...")
                        
                        # Actualizar en la base de datos
                        sql = "UPDATE usuarios SET password_hash = %s WHERE id = %s"
                        cursor.execute(sql, (new_hash, user_id))
                        updated_count += 1
                        print("✅ Convertido y actualizado")
                    else:
                        print("⚠️  No se pudo convertir")
                elif old_hash and old_hash.startswith('$scrypt$'):
                    print("✅ Ya tiene formato correcto")
                else:
                    print("⚠️  Formato desconocido")
            
            connection.commit()
            
            print("\n" + "="*80)
            print(f"✅ {updated_count} hashes convertidos a formato $scrypt$")
            print("="*80)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    force_new_format()