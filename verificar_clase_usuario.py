#!/usr/bin/env python3
"""
Verificar que la clase Usuario tenga todos los métodos necesarios
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_clase_usuario():
    """Verifica que la clase Usuario esté correcta."""
    print("=" * 80)
    print("VERIFICACIÓN CLASE USUARIO")
    print("=" * 80)
    
    try:
        # Importar
        from app import Usuario
        from werkzeug.security import check_password_hash
        
        print("✅ Clase Usuario importada correctamente")
        
        # Verificar métodos
        print("\n🔍 Verificando métodos:")
        
        # 1. hash_password (debe ser estático)
        if hasattr(Usuario, 'hash_password'):
            print("   ✅ hash_password existe")
            
            # Probar que sea estático
            try:
                hash_result = Usuario.hash_password("Test123!")
                print(f"   ✅ Es método estático")
                print(f"   Hash generado: {hash_result[:50]}...")
                print(f"   Formato: {'$scrypt$' if hash_result.startswith('$scrypt$') else 'scrypt:'}")
                
                # Verificar que funcione con check_password_hash
                if check_password_hash(hash_result, "Test123!"):
                    print("   ✅ Hash verificable")
                else:
                    print("   ❌ Hash no verificable")
                    
            except TypeError as e:
                print(f"   ❌ No es estático: {e}")
        else:
            print("   ❌ hash_password NO existe")
        
        # 2. verificar_password
        print("\n2. verificar_password:")
        
        # Crear usuario de prueba
        usuario_prueba = Usuario(
            correo="prueba@test.com",
            password_hash=Usuario.hash_password("MiContraseña123"),
            area_id=1,
            rol="test"
        )
        
        # Probar verificación
        correcto = usuario_prueba.verificar_password("MiContraseña123")
        incorrecto = usuario_prueba.verificar_password("WrongPassword")
        
        print(f"   ✅ Instancia creada")
        print(f"   Contraseña correcta: {'✅ SÍ' if correcto else '❌ NO'}")
        print(f"   Contraseña incorrecta: {'✅ Rechazada' if not incorrecto else '❌ Aceptada (ERROR)'}")
        
        # 3. Probar conversión de formato
        print("\n3. Probando conversión de formato:")
        
        # Hash en formato antiguo
        hash_viejo = 'scrypt:32768:8:1$testsalt$testhash1234567890'
        
        # Crear usuario con hash viejo
        usuario_viejo = Usuario(
            correo="viejo@test.com",
            password_hash=hash_viejo,
            area_id=1,
            rol="test"
        )
        
        print(f"   Hash viejo asignado: {hash_viejo[:40]}...")
        print(f"   Método verificar_password existe: {hasattr(usuario_viejo, 'verificar_password')}")
        
    except ImportError as e:
        print(f"❌ Error importando: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("PASOS FINALES:")
    print("1. Asegurar identación correcta de @staticmethod")
    print("2. Actualizar api_crear_usuario para usar Usuario.hash_password()")
    print("3. Actualizar crear_usuarios_con_hash_correcto")
    print("="*80)

if __name__ == "__main__":
    verificar_clase_usuario()