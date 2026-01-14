import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash, check_password_hash

# Hash de ejemplo de tu base de datos
hash_actual = "scrypt:32768:8:1$zZ46VNCLejq76FH7$3d049919dbccc27ee0e981a081fb17a13131781fffe85dea107494cf45ab7fca53285b0375b391016d8941f3371191c76573057e339c325886838c74af2d78c5"
password = "Admin123!"

# Convertir formato
if hash_actual.startswith('scrypt:'):
    partes = hash_actual.split('$')
    if len(partes) == 3:
        params_part = partes[0]  # scrypt:32768:8:1
        salt = partes[1]
        hash_value = partes[2]
        
        # Extraer parámetros
        params = params_part.replace('scrypt:', '')
        params_parts = params.split(':')
        params_str = '$'.join(params_parts)
        
        # Reconstruir
        nuevo_formato = f"$scrypt${params_str}${salt}${hash_value}"
        
        print("Hash original (primeros 60 chars):")
        print(hash_actual[:60])
        print("\nHash convertido (primeros 60 chars):")
        print(nuevo_formato[:60])
        print("\nProbando verificación...")
        
        # Verificar
        resultado = check_password_hash(nuevo_formato, password)
        print(f"Resultado: {'✅ CORRECTO' if resultado else '❌ INCORRECTO'}")
        
        # También probar con formato incorrecto
        print("\nProbando sin conversión:")
        resultado2 = check_password_hash(hash_actual, password)
        print(f"Resultado sin conversión: {'✅ CORRECTO' if resultado2 else '❌ INCORRECTO'}")