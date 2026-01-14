#!/usr/bin/env python3
"""
Script para verificar creación de nuevos usuarios - VERSIÓN CORREGIDA
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash, check_password_hash

def test_hash_methods():
    """Prueba diferentes métodos para generar hashes."""
    print("=" * 80)
    print("PRUEBA DE MÉTODOS DE HASH")
    print("=" * 80)
    
    password = "TestPassword123!"
    
    print(f"\nContraseña de prueba: {password}")
    
    # Método 1: Directamente con generate_password_hash
    hash1 = generate_password_hash(password, method='scrypt')
    print(f"\n1. generate_password_hash(password, method='scrypt'):")
    print(f"   Hash: {hash1[:60]}...")
    print(f"   Formato: {'$scrypt$' if hash1.startswith('$scrypt$') else 'scrypt:'}")
    print(f"   Longitud: {len(hash1)} caracteres")
    
    # Verificar si funciona con check_password_hash
    try:
        resultado1 = check_password_hash(hash1, password)
        print(f"   Verificación: {'✅ CORRECTA' if resultado1 else '❌ FALLIDA'}")
    except Exception as e:
        print(f"   Error verificación: {e}")
    
    # Método 2: Intentar crear un método hash_password si no existe
    print(f"\n2. Creando método hash_password si no existe:")
    
    try:
        # Intentar importar Usuario
        from app import Usuario
        
        # Verificar si Usuario tiene el método hash_password
        if hasattr(Usuario, 'hash_password'):
            print("   ✅ Usuario.hash_password() existe")
            
            # Probar el método
            hash2 = Usuario.hash_password(password)
            print(f"   Hash generado: {hash2[:60]}...")
            print(f"   Formato: {'$scrypt$' if hash2.startswith('$scrypt$') else 'scrypt:'}")
            
            # Verificar
            resultado2 = check_password_hash(hash2, password)
            print(f"   Verificación: {'✅ CORRECTA' if resultado2 else '❌ FALLIDA'}")
        else:
            print("   ❌ Usuario.hash_password() NO existe")
            print("   Creando método temporal...")
            
            # Crear método temporal
            def hash_password_temp(password):
                return generate_password_hash(password, method='scrypt')
            
            Usuario.hash_password = staticmethod(hash_password_temp)
            hash2 = Usuario.hash_password(password)
            print(f"   Hash temporal: {hash2[:60]}...")
            
    except ImportError as e:
        print(f"   Error importando: {e}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print(f"\n" + "="*80)
    print("RECOMENDACIÓN:")
    print("1. Asegúrate que Usuario tenga el método @staticmethod hash_password()")
    print("2. En api_crear_usuario, usar: Usuario.hash_password(password)")
    print("="*80)

if __name__ == "__main__":
    test_hash_methods()