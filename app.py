import os  # <-- AGREGAR ESTO AL INICIO
import sys
import time
import hashlib
import logging
import re
from datetime import datetime, date, timedelta
from contextlib import contextmanager
from functools import wraps
from contextlib import contextmanager

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    send_file,
    g,
    session,
    flash
)
from werkzeug.utils import secure_filename
import unicodedata

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    Boolean,
    Text,
    Date,
    extract,
    func,
    case,
    Index,
    text,
    and_,
    or_
)
from sqlalchemy.orm import (
    sessionmaker,
    declarative_base,
    relationship
)
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# ======================================
# CONFIGURACIÓN
# ======================================
class Config:
    # Flask
    SECRET_KEY = 'dev-secret-key-change-in-production-12345'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Database
    DB_HOST = 'localhost'
    DB_PORT = '3306'
    DB_NAME = 'alta_colaboradores'
    DB_USER = 'root'
    DB_PASSWORD = 'Manu3l21'
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    LOGS_FOLDER = os.path.join(BASE_DIR, "logs")
    
    # Dashboard - ACTUALIZADO SEGÚN TU ESTRUCTURA
    AREA_COMERCIAL_ID = 2  # CAMBIADO: area_id = 2 es comercial (no 5)
    RECLUTADOR_COMERCIAL_IDS = [5]  # reclutador_id = 5 es comercial

# ======================================
# INICIALIZACIÓN FLASK
# ======================================
app = Flask(__name__)
app.config.from_object(Config)

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)

# ======================================
# LOGGING
# ======================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(app.config['LOGS_FOLDER'], 'app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ======================================
# BASE DE DATOS
# ======================================
DB_URL = f"mysql+pymysql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}?charset=utf8mb4"

engine = create_engine(
    DB_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    connect_args={'connect_timeout': 10, 'charset': 'utf8mb4'}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@contextmanager
def get_db():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        db.close()

Base = declarative_base()

# ======================================
# MODELOS
# ======================================
# Tablas many-to-many
colaborador_recurso = Table(
    "colaborador_recurso",
    Base.metadata,
    Column("colaborador_id", ForeignKey("colaboradores.id", ondelete="CASCADE")),
    Column("recurso_id", ForeignKey("recursos_ti.id", ondelete="CASCADE")),
    Index('idx_colaborador_recurso', 'colaborador_id', 'recurso_id')
)

colaborador_programa = Table(
    "colaborador_programa",
    Base.metadata,
    Column("colaborador_id", ForeignKey("colaboradores.id", ondelete="CASCADE")),
    Column("programa_id", ForeignKey("programas.id", ondelete="CASCADE")),
    Index('idx_colaborador_programa', 'colaborador_id', 'programa_id')
)

class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    nombre_normalizado = Column(String(100), unique=True, nullable=False)

    # 👇 NUEVOS CAMPOS
    nombre_coordinador = Column(String(150))
    correo_coordinador = Column(String(150))

    puestos = relationship("Puesto", back_populates="area")
    
    colaboradores_actuales = relationship(
        "Colaborador", 
        foreign_keys="[Colaborador.area_id]", 
        back_populates="area"
    )
    
    colaboradores_anteriores = relationship(
        "Colaborador", 
        foreign_keys="[Colaborador.area_anterior_id]", 
        back_populates="area_anterior"
    )


class Puesto(Base):
    __tablename__ = "puestos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    area = relationship("Area", back_populates="puestos")

class Reclutador(Base):
    __tablename__ = "reclutadores"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    colaboradores = relationship("Colaborador", back_populates="reclutador_rel")

class Banco(Base):
    __tablename__ = "bancos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)

class MetodoPago(Base):
    __tablename__ = "metodos_pago"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)

class Colaborador(Base):
    __tablename__ = "colaboradores"
    id = Column(Integer, primary_key=True)
    
    # DATOS PERSONALES
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    correo_coordinador = Column(String(150))
    edad = Column(Integer)
    estado_civil = Column(String(50))
    domicilio = Column(Text)
    telefono = Column(String(20))
    
    # DATOS OFICIALES
    rfc = Column(String(13), unique=True, nullable=False)
    curp = Column(String(18), unique=True, nullable=False)
    nss = Column(String(15), unique=True, nullable=False)
    fecha_alta = Column(Date, nullable=False)
    
    # LABORALES
    sueldo = Column(Integer)
    comentarios = Column(Text)
    baja = Column(Boolean, default=False)
    fecha_baja = Column(Date)
    motivo_baja = Column(String(200))
    
    # COMERCIAL
    rol_comercial = Column(String(100))
    comisionista = Column(Boolean)
    metodo_pago = Column(String(100))
    banco = Column(String(100))
    numero_cuenta = Column(String(18))
    numero_comisiones = Column(String(50))
    reclutador = Column(String(150))
    
    # CRÉDITOS
    tiene_infonavit = Column(Boolean, default=False)
    infonavit_credito = Column(String(50))
    tiene_fonacot = Column(Boolean, default=False)
    fonacot_credito = Column(String(50))
    
    # ÁREA Y PUESTO (ACTUALES)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    puesto_id = Column(Integer, ForeignKey("puestos.id"))
    
    # HISTORIAL DE CAMBIO DE ÁREA (NUEVOS CAMPOS)
    fecha_ultimo_cambio_area = Column(Date)
    motivo_ultimo_cambio_area = Column(String(200))
    area_anterior_id = Column(Integer, ForeignKey("areas.id"))
    
    # RELACIONES ORM (FKs)
    metodo_pago_id = Column(Integer, ForeignKey("metodos_pago.id"))
    banco_id = Column(Integer, ForeignKey("bancos.id"))
    reclutador_id = Column(Integer, ForeignKey("reclutadores.id"))
    
    # RELACIONES ORM - ESPECIFICAR foreign_keys EXPLÍCITAMENTE
    metodo_pago_rel = relationship("MetodoPago", foreign_keys=[metodo_pago_id])
    banco_rel = relationship("Banco", foreign_keys=[banco_id])
    reclutador_rel = relationship("Reclutador", back_populates="colaboradores", foreign_keys=[reclutador_id])
    
    # ÁREA ACTUAL (usando area_id)
    area = relationship("Area", foreign_keys=[area_id], back_populates="colaboradores_actuales")
    
    # ÁREA ANTERIOR (usando area_anterior_id)
    area_anterior = relationship("Area", foreign_keys=[area_anterior_id], back_populates="colaboradores_anteriores")
    
    # PUESTO ACTUAL
    puesto = relationship("Puesto")
    
    recursos = relationship(
        "RecursoTI",
        secondary=colaborador_recurso,
        back_populates="colaboradores"
    )
    
    programas = relationship(
        "Programa",
        secondary=colaborador_programa,
        back_populates="colaboradores"
    )
    
    documentos = relationship(
        "Documento",
        back_populates="colaborador"
    )

class RecursoTI(Base):
    __tablename__ = "recursos_ti"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    colaboradores = relationship(
        "Colaborador",
        secondary=colaborador_recurso,
        back_populates="recursos"
    )

class Programa(Base):
    __tablename__ = "programas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    colaboradores = relationship(
        "Colaborador",
        secondary=colaborador_programa,
        back_populates="programas"
    )

class Documento(Base):
    __tablename__ = "documentos"
    id = Column(Integer, primary_key=True)
    colaborador_id = Column(Integer, ForeignKey("colaboradores.id", ondelete="CASCADE"), nullable=False)
    nombre_archivo = Column(String(200), nullable=False)
    ruta_archivo = Column(String(300), nullable=False)
    tipo = Column(String(50))
    tamano = Column(Integer)
    fecha_subida = Column(Date, default=datetime.now)
    colaborador = relationship("Colaborador", back_populates="documentos")
# ======================================
# MODELOS DE USUARIO/AUTENTICACIÓN
# ======================================


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    correo = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    rol = Column(String(50), default="colaborador")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(Date, default=datetime.now)
    ultimo_acceso = Column(Date)
    
    area = relationship("Area")
def verificar_password(self, password):
    """Verifica si la contraseña es correcta - VERSIÓN CORREGIDA."""
    try:
        if not self.password_hash:
            return False
        
        # Si el hash está en formato Werkzeug ($scrypt$...)
        if self.password_hash.startswith('$scrypt$'):
            return check_password_hash(self.password_hash, password)
        
        # Si está en formato personalizado (scrypt:...)
        elif self.password_hash.startswith('scrypt:'):
            # Formato: scrypt:32768:8:1$salt$hash
            try:
                # Extraer las partes
                parts = self.password_hash.split('$')
                if len(parts) != 3:
                    return False
                
                param_part = parts[0]  # scrypt:32768:8:1
                salt = parts[1]
                hash_value = parts[2]
                
                # Extraer parámetros
                params = param_part.replace('scrypt:', '')  # 32768:8:1
                
                # Construir hash en formato Werkzeug
                # Reemplazar : por $
                werkzeug_hash = f"$scrypt${params.replace(':', '$')}${salt}${hash_value}"
                
                # Verificar la contraseña
                return check_password_hash(werkzeug_hash, password)
            except Exception as e:
                logger.error(f"Error procesando hash personalizado: {e}")
                return False
        
        # Para cualquier otro formato, usar check_password_hash directamente
        else:
            return check_password_hash(self.password_hash, password)
            
    except Exception as e:
        logger.error(f"Error en verificar_password: {e}")
        return False
    @staticmethod
    def hash_password(password):
        """Genera hash de la contraseña usando scrypt con formato Werkzeug."""
        from werkzeug.security import generate_password_hash
        # Generar hash con parámetros específicos
        return generate_password_hash(
            password, 
            method='scrypt', 
            salt_length=16,
            n=32768,
            r=8,
            p=1
        )
# ======================================
# FUNCIONES AUXILIARES PARA USUARIOS
# ======================================


def crear_usuarios_con_hash_correcto():
    """Crear o actualizar usuarios con hashes correctos."""
    with get_db() as db:
        # Lista de usuarios a crear/actualizar
        usuarios_data = [
            {
                'correo': 'admin@marnezdesarrollos.com',
                'password': 'Admin123!',
                'area_id': 1,  # Área admin
                'rol': 'admin'
            },
            {
                'correo': 'coordinador.ti@marnezdesarrollos.com',
                'password': 'TiPassword123!',
                'area_id': 3,  # Área TI
                'rol': 'coordinador'
            },
            {
                'correo': 'coordinador.rh@marnezdesarrollos.com',
                'password': 'RhPassword123!',
                'area_id': 4,  # Área RH
                'rol': 'coordinador'
            }
        ]
        
        for user_data in usuarios_data:
            # Verificar si ya existe
            usuario = db.query(Usuario)\
                .filter_by(correo=user_data['correo'])\
                .first()
            
            if usuario:
                # Verificar si el hash necesita actualización
                if usuario.password_hash and usuario.password_hash.startswith('scrypt:'):
                    # Usar la contraseña conocida
                    usuario.password_hash = Usuario.hash_password(user_data['password'])
                    print(f"✓ Usuario {user_data['correo']} actualizado con nuevo hash")
                else:
                    print(f"✓ Usuario {user_data['correo']} ya tiene hash válido")
                    
                # Actualizar otros campos
                usuario.area_id = user_data['area_id']
                usuario.rol = user_data['rol']
                usuario.activo = True
            else:
                # Crear nuevo usuario con hash correcto
                usuario = Usuario(
                    correo=user_data['correo'],
                    password_hash=Usuario.hash_password(user_data['password']),
                    area_id=user_data['area_id'],
                    rol=user_data['rol'],
                    activo=True,
                    fecha_creacion=date.today()
                )
                db.add(usuario)
                print(f"✓ Usuario {user_data['correo']} creado con hash correcto")
        
        db.commit()
        print("\n✅ Usuarios configurados correctamente")

# ======================================
# FUNCIONES DE AUTENTICACIÓN - CORREGIDAS
# ======================================
from werkzeug.security import check_password_hash, generate_password_hash  # <-- AGREGAR ESTO

def login_required(f):
    """Decorador para requerir inicio de sesión."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Debes iniciar sesión para acceder a esta página", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def area_required(area_ids):
    """Decorador para requerir área específica."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Primero verificar login
            if 'usuario_id' not in session:
                flash("Debes iniciar sesión para acceder a esta página", "warning")
                return redirect(url_for('login'))
            
            # Luego verificar área
            if session.get('usuario_area_id') not in area_ids:
                flash("No tienes permisos para acceder a esta página", "error")
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#crear usuarios 
def crear_usuarios_con_hash_correcto():
    """Crear o actualizar usuarios con hashes correctos."""
    with get_db() as db:
        # Lista de usuarios a crear/actualizar
        usuarios_data = [
            {
                'correo': 'admin@marnezdesarrollos.com',
                'password': 'Admin123!',
                'area_id': 1,  # Área admin
                'rol': 'admin'
            },
            {
                'correo': 'coordinador.ti@marnezdesarrollos.com',
                'password': 'TiPassword123!',
                'area_id': 3,  # Área TI
                'rol': 'coordinador'
            },
            {
                'correo': 'coordinador.rh@marnezdesarrollos.com',
                'password': 'RhPassword123!',
                'area_id': 4,  # Área RH
                'rol': 'coordinador'
            }
        ]
        
        for user_data in usuarios_data:
            # Verificar si ya existe
            usuario = db.query(Usuario)\
                .filter_by(correo=user_data['correo'])\
                .first()
            
            if usuario:
                # Verificar si el hash necesita actualización
                if usuario.password_hash and usuario.password_hash.startswith('scrypt:'):
                    # Usar la contraseña conocida
                    usuario.password_hash = Usuario.hash_password(user_data['password'])
                    print(f"✓ Usuario {user_data['correo']} actualizado con nuevo hash")
                else:
                    print(f"✓ Usuario {user_data['correo']} ya tiene hash válido")
                    
                # Actualizar otros campos
                usuario.area_id = user_data['area_id']
                usuario.rol = user_data['rol']
                usuario.activo = True
            else:
                # Crear nuevo usuario con hash correcto
                usuario = Usuario(
                    correo=user_data['correo'],
                    password_hash=Usuario.hash_password(user_data['password']),
                    area_id=user_data['area_id'],
                    rol=user_data['rol'],
                    activo=True,
                    fecha_creacion=date.today()
                )
                db.add(usuario)
                print(f"✓ Usuario {user_data['correo']} creado con hash correcto")
        
        db.commit()
        print("\n✅ Usuarios configurados correctamente")

# ======================================
# DECORADORES
# ======================================
def require_db(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        with get_db() as db:
            g.db = db
            return f(*args, **kwargs)
    return decorated_function

# ======================================
# MIDDLEWARE PARA VERIFICAR SESIÓN EN TODAS LAS RUTAS
# ======================================
@app.before_request
def before_request():
    """Verificar sesión antes de cada petición."""
    # Rutas públicas que no requieren autenticación
    public_routes = ['login', 'static', 'alta', 'dashboard', 'cambio_area_colaborador']
    
    if request.endpoint not in public_routes and 'usuario_id' not in session:
        # Si no está autenticado y no es una ruta pública
        if request.endpoint and 'colaboradores' in request.endpoint:
            return jsonify({"error": "Requiere autenticación"}), 401
    
    # Pasar información del usuario a todas las templates
    g.usuario = {
        'id': session.get('usuario_id'),
        'correo': session.get('usuario_correo'),
        'area_id': session.get('usuario_area_id'),
        'rol': session.get('usuario_rol'),
        'autenticado': 'usuario_id' in session
    }


# ======================================
# RUTAS DE AUTENTICACIÓN
# ======================================
@app.route("/login", methods=["GET", "POST"])
@require_db
def login():
    """Página de inicio de sesión - CORREGIDA."""
    if 'usuario_id' in session:
        flash("Ya tienes una sesión activa", "info")
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        correo = request.form.get('correo', '').strip().lower()
        password = request.form.get('password', '')
        
        logger.info(f"Intento de login para: {correo}")
        
        try:
            db = g.db
            
            # Buscar usuario por correo
            usuario = db.query(Usuario)\
                .filter(func.lower(Usuario.correo) == correo)\
                .first()
            
            if not usuario:
                logger.warning(f"Usuario no encontrado: {correo}")
                flash("Credenciales incorrectas", "danger")
                time.sleep(1)
                return render_template("login.html")
            
            if not usuario.activo:
                logger.warning(f"Usuario inactivo: {correo}")
                flash("Tu cuenta está desactivada. Contacta al administrador.", "warning")
                return render_template("login.html")
            
            # Verificar contraseña
            if not check_password_hash(usuario.password_hash, password):
                logger.warning(f"Contraseña incorrecta para: {correo}")
                flash("Credenciales incorrectas", "danger")
                time.sleep(1)
                return render_template("login.html")
            
            # Verificar que el área exista
            area = db.query(Area).filter_by(id=usuario.area_id).first()
            if not area:
                logger.error(f"Área ID {usuario.area_id} no encontrada para usuario {usuario.id}")
                flash("Error de configuración del usuario. Contacta al administrador.", "error")
                return render_template("login.html")
            
            # Actualizar último acceso
            usuario.ultimo_acceso = date.today()
            db.commit()
            
            # Crear sesión
            session['usuario_id'] = usuario.id
            session['usuario_correo'] = usuario.correo
            session['usuario_area_id'] = usuario.area_id
            session['usuario_rol'] = usuario.rol
            session.permanent = True
            
            logger.info(f"Login exitoso: {usuario.correo} (Área: {usuario.area_id}, Rol: {usuario.rol})")
            
            flash(f"¡Bienvenido, {usuario.correo}!", "success")
            return redirect(url_for('colaboradores'))
            
        except Exception as e:
            logger.error(f"Error en login: {e}", exc_info=True)
            flash("Error interno del servidor. Intenta nuevamente.", "error")
    
    return render_template("login.html")

# ======================================
# RUTA PARA CERRAR SESIÓN
# ======================================
@app.route("/logout")  # <-- ¡ESTO ES LO QUE TE FALTA!
def logout():
    """Cerrar sesión."""
    session.clear()
    flash("Sesión cerrada exitosamente", "success")
    return redirect(url_for('login'))
# ======================================
# RUTA PARA GESTIÓN DE USUARIOS (SOLO ADMIN)
# ======================================
@app.route("/admin/usuarios")
@login_required
@require_db
def admin_usuarios():
    """Página de administración de usuarios (solo admin)."""
    # Verificar si es admin
    if session.get('usuario_rol') != 'admin':
        flash("No tienes permisos para acceder a esta página", "error")
        return redirect(url_for('dashboard'))
    
    try:
        db = g.db
        
        # Obtener todos los usuarios
        usuarios = db.query(Usuario).join(Area).order_by(Usuario.id.desc()).all()
        
        # Obtener todas las áreas para el formulario
        areas = db.query(Area).order_by(Area.nombre).all()
        
        return render_template("admin_usuarios.html", 
                             usuarios=usuarios, 
                             areas=areas)
        
    except Exception as e:
        logger.error(f"Error en admin usuarios: {e}", exc_info=True)
        flash("Error al cargar la página", "error")
        return redirect(url_for('dashboard'))

# ======================================
# API PARA CREAR USUARIO
# ======================================
@app.route("/api/usuario/crear", methods=["POST"])
@login_required
@require_db
def api_crear_usuario():
    """API para crear un nuevo usuario - CORREGIDA."""
    try:
        # Verificar si es admin
        if session.get('usuario_rol') != 'admin':
            return jsonify({"error": "No autorizado"}), 403
        
        data = request.get_json()
        db = g.db
        
        # Validar campos
        required_fields = ['correo', 'password', 'area_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Campo requerido faltante: {field}"}), 400
        
        # Verificar que el área exista
        area = db.query(Area).filter_by(id=data['area_id']).first()
        if not area:
            return jsonify({"error": "Área no válida"}), 400
        
        # Verificar si el correo ya existe
        existe = db.query(Usuario).filter_by(correo=data['correo']).first()
        if existe:
            return jsonify({"error": "El correo ya está registrado"}), 400
        
        # ✅ CREAR USUARIO CON HASH CORRECTO
        usuario = Usuario(
            correo=data['correo'],
            password_hash=Usuario.hash_password(data['password']),  # <-- ¡CORREGIDO!
            area_id=data['area_id'],
            rol=data.get('rol', 'colaborador'),
            activo=True,
            fecha_creacion=date.today()
        )
        
        db.add(usuario)
        db.commit()
        
        # Log detallado del hash creado
        logger.info(f"Usuario creado: {usuario.correo} (Área: {area.nombre})")
        logger.info(f"Hash generado: {usuario.password_hash[:60]}...")
        logger.info(f"Formato hash: {'$scrypt$' if usuario.password_hash.startswith('$scrypt$') else 'scrypt:'}")
        
        return jsonify({
            "success": True,
            "message": "Usuario creado exitosamente",
            "usuario": {
                "id": usuario.id,
                "correo": usuario.correo,
                "area_id": usuario.area_id,
                "area_nombre": area.nombre,
                "rol": usuario.rol,
                "hash_format": "$scrypt$" if usuario.password_hash.startswith('$scrypt$') else "scrypt:"
            }
        })
        
    except Exception as e:
        logger.error(f"Error creando usuario: {e}", exc_info=True)
        db.rollback()
        return jsonify({"error": f"Error al crear usuario: {str(e)}"}), 500
        


# ======================================
# RUTAS DE VISTAS
# ======================================

@app.route("/dashboard")
@require_db
def dashboard():
    """Página principal del dashboard BI."""
    try:
        db = g.db
        
        # Obtener años disponibles desde fecha_alta
        min_year = db.query(func.min(extract("year", Colaborador.fecha_alta))).scalar()
        max_year = db.query(func.max(extract("year", Colaborador.fecha_alta))).scalar()
        
        # También considerar años desde fecha_baja
        min_year_baja = db.query(func.min(extract("year", Colaborador.fecha_baja))).scalar()
        max_year_baja = db.query(func.max(extract("year", Colaborador.fecha_baja))).scalar()
        
        # Encontrar el rango completo de años
        years_set = set()
        
        if min_year:
            years_set.add(int(min_year))
        if max_year:
            years_set.add(int(max_year))
        if min_year_baja:
            years_set.add(int(min_year_baja))
        if max_year_baja:
            years_set.add(int(max_year_baja))
        
        # Agregar año actual si no hay datos
        if not years_set:
            years_set.add(date.today().year)
        
        # Crear lista ordenada
        years = sorted(years_set, reverse=True)
        
        # Si hay pocos años, agregar algunos para tener rango
        if len(years) < 3:
            current_year = date.today().year
            years = [current_year - 2, current_year - 1, current_year]
        
        return render_template("dashboard_bi.html",
            current_year=date.today().year,
            available_years=years,
            current_date=date.today().strftime("%d/%m/%Y")
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}", exc_info=True)
        return render_template("dashboard_bi.html", 
            current_year=date.today().year,
            available_years=[date.today().year],
            current_date=date.today().strftime("%d/%m/%Y"),
            error=str(e)
        )

@app.route("/", methods=["GET", "POST"])
@require_db
def alta():
    """Página principal de alta de colaboradores."""
    try:
        db = g.db
        
        areas = db.query(Area).order_by(Area.nombre).all()
        recursos = db.query(RecursoTI).order_by(RecursoTI.nombre).all()
        programas = db.query(Programa).order_by(Programa.nombre).all()
        bancos = db.query(Banco).order_by(Banco.nombre).all()
        reclutadores = db.query(Reclutador).order_by(Reclutador.nombre).all()
        metodos_pago = db.query(MetodoPago).order_by(MetodoPago.nombre).all()
        
        puestos_por_area = {}
        for area in areas:
            puestos = db.query(Puesto).filter_by(area_id=area.id).order_by(Puesto.nombre).all()
            puestos_por_area[area.id] = [{"id": p.id, "nombre": p.nombre} for p in puestos]
        
        form_data = {
            'areas': areas,
            'recursos': recursos,
            'programas': programas,
            'bancos': bancos,
            'reclutadores': reclutadores,
            'metodos_pago': metodos_pago,
            'puestos_por_area': puestos_por_area,
            'today': date.today().isoformat(),
            'AREA_COMERCIAL_ID': app.config['AREA_COMERCIAL_ID'],
            'RECLUTADOR_COMERCIAL_IDS': app.config['RECLUTADOR_COMERCIAL_IDS']
        }
        
        if request.method == "POST":
            return handle_alta_post(db)
        
        return render_template("alta_colaborador.html", **form_data)
        
    except Exception as e:
        logger.error(f"Error in alta: {e}", exc_info=True)
        flash(f"Error al cargar el formulario: {str(e)}", "error")
        return render_template("alta_colaborador.html", today=date.today().isoformat())

def handle_alta_post(db):
    """Maneja el POST del formulario de alta CON VALIDACIÓN RFC y redirige al dashboard."""
    try:
        # NUEVA VALIDACIÓN: Verificar RFC antes de procesar
        rfc = request.form.get("rfc", "").upper().strip()
        
        if rfc:
            # Verificar si RFC ya existe
            existe_rfc = db.query(Colaborador).filter_by(rfc=rfc).first()
            if existe_rfc:
                flash(f"❌ El RFC <strong>{rfc}</strong> ya está registrado para el colaborador: {existe_rfc.nombre} {existe_rfc.apellido}", "error")
                return redirect(url_for('alta'))
        
        # Resto del código existente...
        required_fields = ['area', 'nombre', 'apellido', 'correo', 'rfc', 'curp', 'nss', 'fecha_alta']
        missing_fields = []
        
        for field in required_fields:
            if not request.form.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            flash(f"❌ Campos requeridos faltantes: {', '.join(missing_fields)}", "error")
            return redirect(url_for('alta'))
        
        # Validar datos únicos
        rfc = request.form.get("rfc", "").upper()
        curp = request.form.get("curp", "").upper()
        nss = request.form.get("nss", "")
        correo = request.form.get("correo", "")
        
        # Verificar duplicados
        duplicados = []
        
        if db.query(Colaborador).filter_by(rfc=rfc).first():
            duplicados.append(f"RFC: {rfc}")
        
        if db.query(Colaborador).filter_by(curp=curp).first():
            duplicados.append(f"CURP: {curp}")
        
        if db.query(Colaborador).filter_by(nss=nss).first():
            duplicados.append(f"NSS: {nss}")
        
        if db.query(Colaborador).filter_by(correo=correo).first():
            duplicados.append(f"Correo: {correo}")
        
        if duplicados:
            flash(f"❌ Datos duplicados encontrados: {', '.join(duplicados)}", "error")
            return redirect(url_for('alta'))
        
        # Crear colaborador - MODIFICADO para obtener solo el ID
        area_id = int(request.form.get("area"))
        colaborador_id = crear_colaborador(db, area_id)  # <-- Ahora retorna solo el ID
        
        # Obtener datos del colaborador para el mensaje flash
        colaborador = db.query(Colaborador).get(colaborador_id)
        
        flash(f"✅ Colaborador <strong>{colaborador.nombre} {colaborador.apellido}</strong> registrado exitosamente", "success")
        
        # REDIRIGIR AL DASHBOARD en lugar de volver al formulario
        return redirect(url_for('dashboard'))
        # Si quieres llevar el ID como parámetro (opcional):
        # return redirect(url_for('dashboard', nuevo_colaborador_id=colaborador_id))
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error en alta POST: {e}", exc_info=True)
        flash(f"❌ Error al registrar colaborador: {str(e)}", "error")
        return redirect(url_for('alta'))



def crear_colaborador(db, area_id):
    """Crea un nuevo colaborador y retorna su ID."""
    fecha_alta_str = request.form.get("fecha_alta")
    try:
        fecha_alta = datetime.strptime(fecha_alta_str, "%Y-%m-%d").date() if fecha_alta_str else date.today()
    except ValueError:
        fecha_alta = date.today()
    
    sueldo_str = request.form.get("sueldo", "0")
    try:
        sueldo = float(sueldo_str) if sueldo_str and sueldo_str.strip() else None
    except ValueError:
        sueldo = None
    
    edad_str = request.form.get("edad")
    try:
        edad = int(edad_str) if edad_str and edad_str.strip() else None
    except (ValueError, TypeError):
        edad = None
    
    # OBTENER EL CORREO DEL COORDINADOR DEL ÁREA SELECCIONADA
    area = db.query(Area).filter_by(id=area_id).first()
    correo_coordinador = area.correo_coordinador if area else None
    
    col = Colaborador(
        nombre=request.form.get("nombre", "").strip(),
        apellido=request.form.get("apellido", "").strip(),
        correo=request.form.get("correo", "").strip(),
        correo_coordinador=correo_coordinador,  # ✅ NUEVO: Asignar correo del coordinador
        edad=edad,
        estado_civil=request.form.get("estado_civil"),
        domicilio=request.form.get("domicilio"),
        telefono=request.form.get("telefono"),
        rfc=request.form.get("rfc", "").upper(),
        curp=request.form.get("curp", "").upper(),
        nss=request.form.get("nss", ""),
        fecha_alta=fecha_alta,
        sueldo=sueldo,
        comentarios=request.form.get("comentarios"),
        rol_comercial=request.form.get("rol_comercial") if area_id == app.config['AREA_COMERCIAL_ID'] else None,
        comisionista=request.form.get("comisionista") == "Sí" if area_id == app.config['AREA_COMERCIAL_ID'] else None,
        metodo_pago=request.form.get("metodo_pago_string"),
        banco=request.form.get("banco_string"),
        reclutador=request.form.get("reclutador_string"),
        metodo_pago_id=int(request.form.get("metodo_pago")) if request.form.get("metodo_pago") else None,
        banco_id=int(request.form.get("banco")) if request.form.get("banco") else None,
        reclutador_id=int(request.form.get("reclutador")) if request.form.get("reclutador") else None,
        numero_cuenta=request.form.get("numero_cuenta"),
        numero_comisiones=request.form.get("numero_comisiones"),
        tiene_infonavit=request.form.get("infonavit") == "Sí",
        infonavit_credito=request.form.get("infonavit_credito"),
        tiene_fonacot=request.form.get("fonacot") == "Sí",
        fonacot_credito=request.form.get("fonacot_credito"),
        area_id=area_id,
        puesto_id=int(request.form.get("puesto")) if request.form.get("puesto") else None,
        baja=False,
        fecha_baja=None,
        motivo_baja=None
    )
    
    db.add(col)
    db.flush()
    
    agregar_relaciones(db, col)
    
    # Guardar documentos
    try:
        guardar_documentos(db, col.id)
    except Exception as e:
        logger.warning(f"Error guardando documentos para colaborador {col.id}: {e}")
    
    db.commit()
    
    logger.info(f"✅ Colaborador creado: {col.nombre} {col.apellido} (ID: {col.id}) - Correo coordinador: {correo_coordinador}")
    return col.id

def agregar_relaciones(db, colaborador):
    """Agrega recursos y programas al colaborador."""
    equipo_ids = request.form.getlist("equipo[]")
    if equipo_ids:
        try:
            ids = [int(id) for id in equipo_ids if id and id.strip()]
            if ids:
                recursos = db.query(RecursoTI).filter(RecursoTI.id.in_(ids)).all()
                for recurso in recursos:
                    colaborador.recursos.append(recurso)
        except ValueError:
            pass
    
    programa_ids = request.form.getlist("programas[]")
    if programa_ids:
        try:
            ids = [int(id) for id in programa_ids if id and id.strip()]
            if ids:
                programas = db.query(Programa).filter(Programa.id.in_(ids)).all()
                for programa in programas:
                    colaborador.programas.append(programa)
        except ValueError:
            pass

def guardar_documentos(db, colaborador_id):
    """Guarda los documentos subidos."""
    carpeta = os.path.join(app.config['UPLOAD_FOLDER'], f"colaborador_{colaborador_id}")
    os.makedirs(carpeta, exist_ok=True)
    
    for f in request.files.getlist("documentos[]"):
        if f and f.filename:
            allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
            file_ext = os.path.splitext(f.filename)[1].lower()
            
            if file_ext not in allowed_extensions:
                continue
            
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(0)
            
            if file_size > 10 * 1024 * 1024:
                continue
            
            nombre = secure_filename(f.filename)
            ruta = os.path.join(carpeta, nombre)
            f.save(ruta)
            
            doc = Documento(
                colaborador_id=colaborador_id,
                nombre_archivo=nombre,
                ruta_archivo=ruta,
                tipo=file_ext[1:].upper(),
                tamano=file_size,
                fecha_subida=date.today()
            )
            db.add(doc)

# ======================================
# RUTA PARA PÁGINA DE CAMBIO DE ÁREA
# ======================================
@app.route("/cambio-area-colaborador", methods=["GET", "POST"])
@login_required  # Primero verificar login
@area_required([3, 4])  # Luego verificar área
@require_db
def cambio_area_colaborador():
    """Página para cambiar área de colaborador existente."""
    try:
        db = g.db
        
        # Obtener datos para el formulario
        areas = db.query(Area).order_by(Area.nombre).all()
        puestos = db.query(Puesto).order_by(Puesto.nombre).all()
        
        if request.method == "POST":
            return procesar_cambio_area(db)
        
        return render_template("cambio_area_colaborador.html",
            areas=areas,
            puestos=puestos,
            today=date.today().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error en página de cambio de área: {e}", exc_info=True)
        flash(f"Error al cargar la página: {str(e)}", "error")
        return redirect(url_for('dashboard'))

def procesar_cambio_area(db):
    """Procesa el formulario de cambio de área."""
    try:
        # Validar campos requeridos
        required_fields = ['colaborador_id', 'nueva_area_id', 'fecha_cambio', 'motivo']
        missing_fields = []
        
        for field in required_fields:
            if not request.form.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            flash(f"Campos requeridos faltantes: {', '.join(missing_fields)}", "error")
            return redirect(url_for('cambio_area_colaborador'))
        
        colaborador_id = int(request.form.get('colaborador_id'))
        nueva_area_id = int(request.form.get('nueva_area_id'))
        fecha_cambio = datetime.strptime(request.form.get('fecha_cambio'), "%Y-%m-%d").date()
        motivo = request.form.get('motivo')
        
        # Buscar colaborador
        colaborador = db.query(Colaborador).filter_by(id=colaborador_id).first()
        if not colaborador:
            flash("❌ Colaborador no encontrado", "error")
            return redirect(url_for('cambio_area_colaborador'))
        
        # Verificar nueva área
        nueva_area = db.query(Area).filter_by(id=nueva_area_id).first()
        if not nueva_area:
            flash("❌ Área no válida", "error")
            return redirect(url_for('cambio_area_colaborador'))
        
        # Registrar cambio
        area_anterior = colaborador.area.nombre if colaborador.area else "N/A"
        
        # Actualizar área
        colaborador.area_id = nueva_area_id
        
        # Actualizar puesto si se proporciona
        nuevo_puesto_id = request.form.get('nuevo_puesto_id')
        if nuevo_puesto_id:
            colaborador.puesto_id = int(nuevo_puesto_id)
        
        # Actualizar sueldo si se proporciona
        nuevo_sueldo = request.form.get('nuevo_sueldo')
        if nuevo_sueldo:
            try:
                colaborador.sueldo = float(nuevo_sueldo)
            except ValueError:
                pass
        
        # Registrar comentario sobre el cambio
        comentario = f"\n\n[CAMBIO ÁREA - {fecha_cambio.strftime('%Y-%m-%d')}]: "
        comentario += f"Cambio de '{area_anterior}' a '{nueva_area.nombre}'"
        comentario += f" - Motivo: {motivo}"
        
        colaborador.comentarios = (colaborador.comentarios or "") + comentario
        
        db.commit()
        
        flash(f"✅ Cambio de área procesado para <strong>{colaborador.nombre} {colaborador.apellido}</strong>", "success")
        return redirect(url_for('cambio_area_colaborador'))
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error procesando cambio de área: {e}", exc_info=True)
        flash(f"❌ Error al procesar cambio de área: {str(e)}", "error")
        return redirect(url_for('cambio_area_colaborador'))

#===================================================
#consultar areas
#=========================================
@app.route("/api/area-info/<int:area_id>", methods=["GET"])
@require_db
def api_area_info(area_id):
    """API para obtener información detallada de un área."""
    try:
        db = g.db
        
        area = db.query(Area).filter_by(id=area_id).first()
        
        if not area:
            return jsonify({"error": "Área no encontrada"}), 404
        
        return jsonify({
            "id": area.id,
            "nombre": area.nombre,
            "nombre_coordinador": area.nombre_coordinador,
            "correo_coordinador": area.correo_coordinador,
            "total_puestos": len(area.puestos) if area.puestos else 0
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo info del área {area_id}: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener información del área"}), 500
# ======================================
# API ENDPOINTS
# ======================================

@app.route("/puestos/<int:area_id>")
@require_db
def puestos_por_area(area_id: int):
    """API para obtener puestos por área."""
    try:
        db = g.db
        puestos = db.query(Puesto).filter_by(area_id=area_id).order_by(Puesto.nombre).all()
        return jsonify([{"id": p.id, "nombre": p.nombre} for p in puestos])
    except Exception as e:
        logger.error(f"Error getting puestos for area {area_id}: {e}")
        return jsonify([])

@app.route("/api/verificar-duplicados", methods=["POST"])
@require_db
def verificar_duplicados():
    """API para verificar duplicados en tiempo real."""
    try:
        data = request.get_json()
        db = g.db
        
        resultados = {
            'correo': False,
            'rfc': False,
            'curp': False,
            'nss': False
        }
        
        if 'correo' in data and data['correo']:
            existe = db.query(Colaborador).filter_by(correo=data['correo'].strip()).first()
            resultados['correo'] = existe is not None
        
        if 'rfc' in data and data['rfc']:
            existe = db.query(Colaborador).filter_by(rfc=data['rfc'].strip().upper()).first()
            resultados['rfc'] = existe is not None
        
        if 'curp' in data and data['curp']:
            existe = db.query(Colaborador).filter_by(curp=data['curp'].strip().upper()).first()
            resultados['curp'] = existe is not None
        
        if 'nss' in data and data['nss']:
            existe = db.query(Colaborador).filter_by(nss=data['nss'].strip()).first()
            resultados['nss'] = existe is not None
        
        return jsonify({
            'success': True,
            'resultados': resultados
        })
        
    except Exception as e:
        logger.error(f"Error verificando duplicados: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route("/api/areas", methods=["GET"])
@require_db
def api_areas():
    """API para obtener todas las áreas."""
    try:
        db = g.db
        areas = db.query(Area).order_by(Area.nombre).all()
        
        areas_data = []
        for area in areas:
            areas_data.append({
                "id": area.id,
                "nombre": area.nombre
            })
        
        return jsonify(areas_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo áreas: {e}")
        return jsonify([])

@app.route("/api/puestos-por-area/all", methods=["GET"])
@require_db
def api_todas_areas():
    """API para obtener todas las áreas (alias para compatibilidad)."""
    try:
        db = g.db
        areas = db.query(Area).order_by(Area.nombre).all()
        
        areas_data = []
        for area in areas:
            areas_data.append({
                "id": area.id,
                "nombre": area.nombre
            })
        
        return jsonify(areas_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo áreas: {e}")
        return jsonify([])
# ======================================
# API PARA VERIFICACIÓN RFC (NUEVA)
# ======================================
# En tu archivo app.py (solo la ruta de verificación RFC)

@app.route("/api/verificar-rfc", methods=["GET"])
@require_db
def api_verificar_rfc():
    """API para verificar si un RFC ya está registrado."""
    try:
        rfc = request.args.get('rfc', '').strip().upper()
        
        if not rfc or len(rfc) < 12:
            return jsonify({
                "error": "RFC inválido (debe tener al menos 12 caracteres)"
            }), 400
        
        db = g.db
        
        # Buscar colaborador por RFC
        colaborador = db.query(Colaborador).filter_by(rfc=rfc).first()
        
        if colaborador:
            # Obtener datos del área
            area_nombre = "N/A"
            if colaborador.area:
                area_nombre = colaborador.area.nombre
            
            # Obtener datos del puesto
            puesto_nombre = "N/A"
            if colaborador.puesto:
                puesto_nombre = colaborador.puesto.nombre
            
            return jsonify({
                "existe": True,
                "colaborador": {
                    "id": colaborador.id,
                    "nombre": f"{colaborador.nombre} {colaborador.apellido}",
                    "correo": colaborador.correo,
                    "rfc": colaborador.rfc,
                    "curp": colaborador.curp or "N/A",
                    "area": area_nombre,
                    "puesto": puesto_nombre,
                    "estado": "Activo" if not colaborador.baja else "Baja",
                    "fecha_alta": colaborador.fecha_alta.strftime("%Y-%m-%d") if colaborador.fecha_alta else "N/A",
                    "telefono": colaborador.telefono or "N/A",
                    "sueldo": float(colaborador.sueldo) if colaborador.sueldo else 0.00,
                    "baja": bool(colaborador.baja)
                }
            })
        else:
            return jsonify({
                "existe": False,
                "message": "RFC no encontrado en el sistema"
            })
            
    except Exception as e:
        logger.error(f"Error verificando RFC: {e}", exc_info=True)
        return jsonify({"error": "Error al verificar el RFC"}), 500

# ======================================
# Buscar colaborador por id 
# ======================================


@app.route("/api/reclutadores/comercial")
@require_db
def api_reclutadores_comercial():
    """API para obtener reclutadores del área comercial - REVISADO."""
    year = request.args.get("year", type=int, default=date.today().year)
    
    logger.info(f"API Reclutadores Comercial solicitada para año: {year}")
    
    try:
        db = g.db
        
        # Consulta para obtener reclutadores comerciales:
        # 1. Reclutadores con area_id = 2 (comercial)
        # 2. O reclutadores con id en RECLUTADOR_COMERCIAL_IDS
        sql = text("""
            SELECT 
                r.id,
                r.nombre,
                COUNT(c.id) as total
            FROM reclutadores r
            LEFT JOIN colaboradores c ON c.reclutador_id = r.id
                AND YEAR(c.fecha_alta) = :year
                AND c.baja = FALSE
                AND (
                    c.area_id = :area_id 
                    OR c.reclutador_id IN :reclutador_ids
                )
            WHERE r.id IN :reclutador_ids 
                OR EXISTS (
                    SELECT 1 FROM colaboradores c2 
                    WHERE c2.reclutador_id = r.id 
                    AND c2.area_id = :area_id
                    AND YEAR(c2.fecha_alta) = :year
                    AND c2.baja = FALSE
                )
            GROUP BY r.id, r.nombre
            HAVING COUNT(c.id) > 0
            ORDER BY total DESC
        """)
        
        resultados = db.execute(sql, {
            'year': year,
            'area_id': app.config['AREA_COMERCIAL_ID'],
            'reclutador_ids': tuple(app.config['RECLUTADOR_COMERCIAL_IDS'])
        }).fetchall()
        
        reclutadores = []
        for row in resultados:
            reclutadores.append({
                "id": row.id,
                "nombre": row.nombre,
                "total": row.total
            })
        
        logger.info(f"Reclutadores comerciales encontrados: {len(reclutadores)}")
        
        return jsonify(reclutadores)
        
    except Exception as e:
        logger.error(f"Error in reclutadores comercial API: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
     
# ======================================
# API PARA GENERAR CORREO (MEJORADA)
# ======================================
@app.route("/api/generar-correo", methods=["GET"])
@require_db
def api_generar_correo():
    """Genera correo institucional basado en nombre y apellido, verifica duplicados."""
    try:
        nombre = request.args.get('nombre', '').strip()
        apellido = request.args.get('apellido', '').strip()
        
        if not nombre or not apellido:
            return jsonify({"error": "Nombre y apellido requeridos"}), 400
        
        # Generar nombre de usuario
        def generar_usuario(nombre, apellido):
            # Normalizar texto
            def normalize(text):
                if not text:
                    return ""
                text = unicodedata.normalize('NFD', text)
                text = text.encode('ascii', 'ignore').decode('utf-8')
                return text.lower()
            
            nombre_norm = normalize(nombre.split()[0])  # Primer nombre
            apellido_norm = normalize(apellido.split()[0])  # Primer apellido
            
            # Generar combinaciones posibles
            combinaciones = [
                f"{nombre_norm}.{apellido_norm}",
                f"{nombre_norm[0]}{apellido_norm}",
                f"{nombre_norm}{apellido_norm[0]}",
                f"{nombre_norm}_{apellido_norm}",
            ]
            
            return combinaciones[0]  # Usar primera combinación por defecto
        
        usuario = generar_usuario(nombre, apellido)
        correo_propuesto = f"{usuario}@marnezdesarrollos.com"
        
        db = g.db
        
        # Verificar si el correo ya existe
        existe = db.query(Colaborador).filter_by(correo=correo_propuesto).first()
        
        if existe:
            # Si existe, buscar variantes disponibles
            contador = 1
            while True:
                correo_variante = f"{usuario}.{contador}@marnezdesarrollos.com"
                existe_variante = db.query(Colaborador).filter_by(correo=correo_variante).first()
                if not existe_variante:
                    correo_propuesto = correo_variante
                    break
                contador += 1
        
        return jsonify({
            "correo": correo_propuesto,
            "duplicado": existe is not None,
            "sugerencia_alternativa": existe is not None
        })
        
    except Exception as e:
        logger.error(f"Error generando correo: {e}", exc_info=True)
        return jsonify({"error": "Error al generar correo"}), 500

# ======================================
# API PARA BUSCAR COLABORADOR POR RFC (PARA CAMBIO ÁREA)
# ======================================
@app.route("/api/buscar-colaborador-rfc", methods=["GET"])
@require_db
def api_buscar_colaborador_rfc():
    """API para buscar colaborador por RFC para cambio de área."""
    try:
        rfc = request.args.get('rfc', '').strip().upper()
        
        if not rfc or len(rfc) < 12:
            return jsonify({
                "error": "RFC inválido (debe tener al menos 12 caracteres)"
            }), 400
        
        db = g.db
        
        # Buscar colaborador por RFC
        colaborador = db.query(Colaborador).filter_by(rfc=rfc).first()
        
        if not colaborador:
            return jsonify({
                "existe": False,
                "message": "Colaborador no encontrado"
            })
        
        # Obtener información completa
        area_actual = colaborador.area.nombre if colaborador.area else "N/A"
        puesto_actual = colaborador.puesto.nombre if colaborador.puesto else "N/A"
        estado = "Activo" if not colaborador.baja else "Baja"
        
        # Obtener historial de áreas si existe (asumiendo que tienes una tabla historial)
        historial = []
        # Si no tienes tabla de historial, puedes extraer de los comentarios
        if colaborador.comentarios and "[CAMBIO ÁREA" in colaborador.comentarios:
            lineas = colaborador.comentarios.split('\n')
            for linea in lineas:
                if "[CAMBIO ÁREA" in linea:
                    historial.append(linea.strip())
        
        return jsonify({
            "existe": True,
            "colaborador": {
                "id": colaborador.id,
                "nombre_completo": f"{colaborador.nombre} {colaborador.apellido}",
                "correo": colaborador.correo,
                "rfc": colaborador.rfc,
                "area_actual": area_actual,
                "area_actual_id": colaborador.area_id,
                "puesto_actual": puesto_actual,
                "puesto_actual_id": colaborador.puesto_id,
                "estado": estado,
                "fecha_alta": colaborador.fecha_alta.strftime("%Y-%m-%d") if colaborador.fecha_alta else "N/A",
                "telefono": colaborador.telefono or "N/A",
                "sueldo_actual": colaborador.sueldo,
                "historial": historial[:5]  # Últimos 5 cambios
            }
        })
        
    except Exception as e:
        logger.error(f"Error buscando colaborador por RFC: {e}", exc_info=True)
        return jsonify({"error": "Error al buscar colaborador"}), 500

# ======================================
# API PARA OBTENER PUESTOS POR ÁREA (ACTUALIZADA)
# ======================================
@app.route("/api/puestos-por-area/<int:area_id>")
@require_db
def api_puestos_por_area(area_id):
    """API para obtener puestos por área ID."""
    try:
        db = g.db
        puestos = db.query(Puesto).filter_by(area_id=area_id).order_by(Puesto.nombre).all()
        
        puestos_data = []
        for puesto in puestos:
            puestos_data.append({
                "id": puesto.id,
                "nombre": puesto.nombre,
                "area_id": puesto.area_id
            })
        
        return jsonify(puestos_data)
        
    except Exception as e:
        logger.error(f"Error obteniendo puestos para área {area_id}: {e}")
        return jsonify([])

# ======================================
# API PARA BÚSQUEDA DE COLABORADORES EXISTENTES
# ======================================
@app.route("/api/buscar-colaborador", methods=["GET"])
@require_db
def api_buscar_colaborador():
    """API para buscar colaborador por diferentes campos."""
    try:
        campo = request.args.get('campo')
        valor = request.args.get('valor')
        
        if not campo or not valor:
            return jsonify({"error": "Parámetros inválidos"}), 400
        
        db = g.db
        
        query = db.query(Colaborador)
        
        if campo == 'correo':
            query = query.filter(Colaborador.correo == valor)
        elif campo == 'rfc':
            query = query.filter(Colaborador.rfc == valor.upper())
        elif campo == 'curp':
            query = query.filter(Colaborador.curp == valor.upper())
        elif campo == 'nss':
            query = query.filter(Colaborador.nss == valor)
        else:
            return jsonify({"error": "Campo no válido"}), 400
        
        colaborador = query.first()
        
        if colaborador:
            return jsonify({
                "existe": True,
                "colaborador": {
                    "id": colaborador.id,
                    "nombre": colaborador.nombre,
                    "apellido": colaborador.apellido,
                    "correo": colaborador.correo,
                    "area": colaborador.area.nombre if colaborador.area else "N/A",
                    "fecha_alta": colaborador.fecha_alta.strftime("%Y-%m-%d") if colaborador.fecha_alta else "N/A",
                    "baja": colaborador.baja
                }
            })
        else:
            return jsonify({"existe": False})
            
    except Exception as e:
        logger.error(f"Error buscando colaborador: {e}", exc_info=True)
        return jsonify({"error": "Error al buscar colaborador"}), 500

# ======================================
# API PARA PROCESAR BAJA
# ======================================
@app.route("/api/procesar-baja", methods=["POST"])
@require_db
def api_procesar_baja():
    """API para procesar baja de colaborador."""
    try:
        data = request.get_json()
        
        required_fields = ['colaborador_id', 'motivo', 'fecha_baja']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo requerido faltante: {field}"}), 400
        
        db = g.db
        
        colaborador = db.query(Colaborador).filter_by(id=data['colaborador_id']).first()
        if not colaborador:
            return jsonify({"error": "Colaborador no encontrado"}), 404
        
        if colaborador.baja:
            return jsonify({"error": "El colaborador ya está dado de baja"}), 400
        
        # Procesar baja
        colaborador.baja = True
        colaborador.fecha_baja = datetime.strptime(data['fecha_baja'], "%Y-%m-%d").date()
        colaborador.motivo_baja = data['motivo']
        
        if data.get('comentarios'):
            colaborador.comentarios = (colaborador.comentarios or "") + f"\n\n[BAJA] {data['comentarios']}"
        
        db.commit()
        
        logger.info(f"Baja procesada para colaborador ID: {colaborador.id}")
        
        return jsonify({
            "success": True,
            "message": "Baja procesada exitosamente",
            "colaborador": {
                "id": colaborador.id,
                "nombre": f"{colaborador.nombre} {colaborador.apellido}"
            }
        })
        
    except Exception as e:
        logger.error(f"Error procesando baja: {e}", exc_info=True)
        db.rollback()
        return jsonify({"error": "Error al procesar la baja"}), 500

# ======================================
# API PARA PROCESAR CAMBIO DE ÁREA
# ======================================
@app.route("/api/procesar-cambio-area", methods=["POST"])
@require_db
def api_procesar_cambio_area():
    """API para procesar cambio de área - ACTUALIZADO con nuevo correo coordinador."""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['colaborador_id', 'nueva_area_id', 'fecha_cambio']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo requerido faltante: {field}"}), 400
        
        db = g.db
        
        # Buscar colaborador
        colaborador = db.query(Colaborador).filter_by(id=data['colaborador_id']).first()
        if not colaborador:
            return jsonify({"error": "Colaborador no encontrado"}), 404
        
        # Verificar nueva área
        nueva_area = db.query(Area).filter_by(id=data['nueva_area_id']).first()
        if not nueva_area:
            return jsonify({"error": "Área no válida"}), 400
        
        # ✅ OBTENER NUEVO CORREO DEL COORDINADOR DEL ÁREA
        nuevo_correo_coordinador = nueva_area.correo_coordinador
        nombre_coordinador = nueva_area.nombre_coordinador
        
        # Convertir fecha
        try:
            fecha_cambio = datetime.strptime(data['fecha_cambio'], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
        
        # Obtener información actual antes de cambiar
        area_actual = colaborador.area.nombre if colaborador.area else "N/A"
        area_actual_id = colaborador.area_id
        puesto_actual = colaborador.puesto.nombre if colaborador.puesto else "N/A"
        sueldo_actual = colaborador.sueldo
        
        # ✅ ACTUALIZAR CORREO DEL COORDINADOR
        colaborador.correo_coordinador = nuevo_correo_coordinador
        
        # ACTUALIZAR NUEVOS CAMPOS DE CAMBIO DE ÁREA
        colaborador.fecha_ultimo_cambio_area = fecha_cambio
        colaborador.motivo_ultimo_cambio_area = data.get('motivo_cambio', '')
        colaborador.area_anterior_id = area_actual_id  # Guardar área anterior
        
        # Cambiar área actual
        colaborador.area_id = data['nueva_area_id']
        
        # Cambiar puesto si se proporciona
        if data.get('nuevo_puesto_id'):
            colaborador.puesto_id = data['nuevo_puesto_id']
        
        # Cambiar sueldo si se proporciona
        nuevo_sueldo = data.get('nuevo_sueldo')
        if nuevo_sueldo is not None and nuevo_sueldo != '':
            try:
                colaborador.sueldo = float(nuevo_sueldo)
            except ValueError:
                pass  # Mantener sueldo actual si hay error
        
        # Registrar en comentarios (historial detallado)
        comentario_cambio = f"\n\n[CAMBIO ÁREA - {fecha_cambio.strftime('%Y-%m-%d')}]: "
        comentario_cambio += f"Área: '{area_actual}' → '{nueva_area.nombre}'"
        
        # Información del coordinador (nuevo campo)
        if nombre_coordinador:
            comentario_cambio += f" | Coordinador: '{nombre_coordinador}'"
        
        if nuevo_correo_coordinador:
            comentario_cambio += f" | Correo coordinador: '{nuevo_correo_coordinador}'"
        
        if data.get('nuevo_puesto_id'):
            nuevo_puesto = db.query(Puesto).filter_by(id=data['nuevo_puesto_id']).first()
            if nuevo_puesto:
                comentario_cambio += f" | Puesto: '{puesto_actual}' → '{nuevo_puesto.nombre}'"
        
        if nuevo_sueldo:
            comentario_cambio += f" | Sueldo: ${sueldo_actual or 0} → ${nuevo_sueldo}"
        
        if data.get('motivo_cambio'):
            comentario_cambio += f" | Motivo: {data['motivo_cambio']}"
        
        colaborador.comentarios = (colaborador.comentarios or "") + comentario_cambio
        
        db.commit()
        
        logger.info(f"Cambio de área procesado para colaborador ID: {colaborador.id}")
        logger.info(f"Nuevo coordinador: {nombre_coordinador} ({nuevo_correo_coordinador})")
        
        return jsonify({
            "success": True,
            "message": "Cambio de área procesado exitosamente",
            "colaborador": {
                "id": colaborador.id,
                "nombre": f"{colaborador.nombre} {colaborador.apellido}",
                "area_anterior": area_actual,
                "area_nueva": nueva_area.nombre,
                "fecha_cambio": fecha_cambio.strftime("%Y-%m-%d"),
                "coordinador_nuevo": nombre_coordinador,
                "correo_coordinador_nuevo": nuevo_correo_coordinador
            }
        })
        
    except Exception as e:
        logger.error(f"Error procesando cambio de área: {e}", exc_info=True)
        db.rollback()
        return jsonify({"error": f"Error al procesar el cambio de área: {str(e)}"}), 500
# ======================================
# API PARA BUSCAR COLABORADOR POR TEXTO
# ======================================
@app.route("/api/buscar-colaboradores", methods=["GET"])
@require_db
def api_buscar_colaboradores():
    """API para buscar colaboradores por nombre, correo o ID."""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({"resultados": []})
        
        db = g.db
        
        # Buscar por ID si es numérico
        if query.isdigit():
            colaboradores = db.query(Colaborador)\
                .filter(
                    or_(
                        Colaborador.id == int(query),
                        Colaborador.nombre.ilike(f"%{query}%"),
                        Colaborador.apellido.ilike(f"%{query}%"),
                        Colaborador.correo.ilike(f"%{query}%")
                    )
                )\
                .limit(10)\
                .all()
        else:
            # Buscar por texto
            colaboradores = db.query(Colaborador)\
                .filter(
                    or_(
                        Colaborador.nombre.ilike(f"%{query}%"),
                        Colaborador.apellido.ilike(f"%{query}%"),
                        Colaborador.correo.ilike(f"%{query}%")
                    )
                )\
                .limit(10)\
                .all()
        
        resultados = []
        for col in colaboradores:
            resultados.append({
                "id": col.id,
                "nombre_completo": f"{col.nombre} {col.apellido}",
                "correo": col.correo,
                "area": col.area.nombre if col.area else "N/A",
                "activo": not col.baja,
                "fecha_alta": col.fecha_alta.strftime("%Y-%m-%d") if col.fecha_alta else "N/A"
            })
        
        return jsonify({"resultados": resultados})
        
    except Exception as e:
        logger.error(f"Error buscando colaboradores: {e}", exc_info=True)
        return jsonify({"resultados": []})

# ======================================
# API - DASHBOARD DATOS
# ======================================

@app.route("/api/kpis")
@require_db
def api_kpis():
    """API para KPIs del dashboard."""
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int)
    
    logger.info(f"API KPIs solicitada para año: {year}, mes: {month}")
    
    try:
        db = g.db
        
        # Filtros base para TODAS las contrataciones (incluyendo bajas)
        filters_total = [
            extract("year", Colaborador.fecha_alta) == year
        ]
        
        # Filtros para contrataciones ACTIVAS (sin baja)
        filters_activos = [
            extract("year", Colaborador.fecha_alta) == year,
            Colaborador.baja == False
        ]
        
        # Filtro para COMERCIAL: area_id = 2
        filters_comercial = Colaborador.area_id == app.config['AREA_COMERCIAL_ID']
        
        # Filtro para GESTIÓN: NO comercial (area_id != 2)
        filters_gestion = Colaborador.area_id != app.config['AREA_COMERCIAL_ID']
        
        # Agregar filtro de mes si se especifica
        if month:
            filters_total.append(extract("month", Colaborador.fecha_alta) == month)
            filters_activos.append(extract("month", Colaborador.fecha_alta) == month)
        
        # TOTAL de contrataciones (INCLUYENDO BAJAS)
        total_contrataciones = db.query(func.count(Colaborador.id))\
            .filter(*filters_total)\
            .scalar() or 0
        
        # Contrataciones ACTIVAS (sin baja)
        total_activos = db.query(func.count(Colaborador.id))\
            .filter(*filters_activos)\
            .scalar() or 0
        
        # Contrataciones COMERCIALES (area_id = 2) - TOTAL (INCLUYENDO BAJAS)
        total_comercial = db.query(func.count(Colaborador.id))\
            .filter(
                *filters_total,
                filters_comercial
            )\
            .scalar() or 0
        
        # Contrataciones GESTIÓN (no comercial) - TOTAL (INCLUYENDO BAJAS)
        total_gestion = db.query(func.count(Colaborador.id))\
            .filter(
                *filters_total,
                filters_gestion
            )\
            .scalar() or 0
        
        # Bajas comerciales - MODIFICADO: Contar por año de alta
        filters_baja_comercial = [
            Colaborador.baja == True,
            extract("year", Colaborador.fecha_alta) == year,  # Cambiado: usar fecha_alta
            filters_comercial
        ]
        
        # Bajas gestión - MODIFICADO: Contar por año de alta
        filters_baja_gestion = [
            Colaborador.baja == True,
            extract("year", Colaborador.fecha_alta) == year,  # Cambiado: usar fecha_alta
            filters_gestion
        ]
        
        if month:
            # También filtrar por mes de alta para bajas
            filters_baja_comercial.append(extract("month", Colaborador.fecha_alta) == month)
            filters_baja_gestion.append(extract("month", Colaborador.fecha_alta) == month)
        
        # Bajas comerciales
        bajas_comercial = db.query(func.count(Colaborador.id))\
            .filter(*filters_baja_comercial)\
            .scalar() or 0
        
        # Bajas gestión
        bajas_gestion = db.query(func.count(Colaborador.id))\
            .filter(*filters_baja_gestion)\
            .scalar() or 0
        
        # Tasa de retención (basada en activos vs total)
        retencion = 0
        if total_contrataciones > 0:
            retencion = round(total_activos / total_contrataciones * 100, 1)
        
        logger.info(f"KPIs calculados: total={total_contrataciones}, activos={total_activos}, comercial={total_comercial}, gestion={total_gestion}")
        logger.info(f"Bajas: comercial={bajas_comercial}, gestion={bajas_gestion}")
        
        return jsonify({
            "total": total_contrataciones,          # Incluye bajas
            "activos": total_activos,               # Solo activos
            "comercial": total_comercial,           # Comercial TOTAL (incluye bajas)
            "gestion": total_gestion,               # Gestión TOTAL (incluye bajas)
            "bajas_comercial": bajas_comercial,
            "bajas_gestion": bajas_gestion,
            "retencion": retencion,
            "year": year,
            "month": month if month else "todos"
        })
        
    except Exception as e:
        logger.error(f"Error in KPIs API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener KPIs"}), 500


@app.route("/api/contrataciones")
@require_db
def api_contrataciones():
    """API para obtener contrataciones por mes."""
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int)
    
    logger.info(f"API Contrataciones solicitada para año: {year}, mes: {month}")
    
    try:
        db = g.db
        
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        resultados = []
        
        # Si se especifica un mes, solo devolver ese mes
        if month:
            mes_range = [month]
        else:
            mes_range = range(1, 13)
        
        # Definir filtros para comercial y gestión
        filtro_comercial = Colaborador.area_id == app.config['AREA_COMERCIAL_ID']
        filtro_gestion = Colaborador.area_id != app.config['AREA_COMERCIAL_ID']
        
        for mes_num in mes_range:
            # Filtros para TOTAL de contrataciones (INCLUYENDO BAJAS)
            filters_total = [
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes_num
            ]
            
            # Filtros para contrataciones ACTIVAS (sin baja)
            filters_activos = [
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes_num,
                Colaborador.baja == False
            ]
            
            # Contrataciones de GESTIÓN - TOTAL (incluye bajas)
            gestion_total = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_total,
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Contrataciones de COMERCIAL - TOTAL (incluye bajas)
            comercial_total = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_total,
                    filtro_comercial
                )\
                .scalar() or 0
            
            # Contrataciones de GESTIÓN - ACTIVAS (sin baja)
            gestion_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_activos,
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Contrataciones de COMERCIAL - ACTIVAS (sin baja)
            comercial_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_activos,
                    filtro_comercial
                )\
                .scalar() or 0
            
            # Total de contrataciones para este mes (TODAS, incluyendo bajas)
            total_mes_con_bajas = gestion_total + comercial_total
            
            # Total de contrataciones ACTIVAS para este mes
            total_mes_activos = gestion_activos + comercial_activos
            
            resultados.append({
                "mes": meses[mes_num - 1],
                "gestion": gestion_total,          # Total gestión (incluye bajas)
                "gestion_activos": gestion_activos, # Gestión activos
                "comercial": comercial_total,       # Total comercial (incluye bajas)
                "comercial_activos": comercial_activos, # Comercial activos
                "total_activos": total_mes_activos,
                "total_con_bajas": total_mes_con_bajas,
                "mes_num": mes_num
            })
        
        logger.info(f"Contrataciones para {year}: {len(resultados)} registros")
        
        # Si se filtró por un mes específico, devolver solo ese mes
        if month and len(resultados) > 0:
            return jsonify(resultados[0])
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error in contrataciones API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener contrataciones"}), 500




    """API para obtener contrataciones por mes."""
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int)
    
    logger.info(f"API Contrataciones solicitada para año: {year}, mes: {month}")
    
    try:
        db = g.db
        
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        resultados = []
        
        if month:
            mes_range = [month]
        else:
            mes_range = range(1, 13)
        
        filtro_comercial = or_(
            Colaborador.area_id == app.config['AREA_COMERCIAL_ID'],
            Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
        )
        
        filtro_gestion = and_(
            Colaborador.area_id != app.config['AREA_COMERCIAL_ID'],
            or_(
                Colaborador.reclutador_id.is_(None),
                ~Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
            )
        )
        
        for mes_num in mes_range:
            # Filtros para TOTAL de contrataciones (INCLUYENDO BAJAS) - REMOVIENDO EL FILTRO "baja == False"
            filters_total = [
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes_num
            ]
            
            # Filtros para contrataciones ACTIVAS (sin baja)
            filters_activos = [
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes_num,
                Colaborador.baja == False
            ]
            
            # Contrataciones de GESTIÓN - TOTAL (incluye bajas)
            gestion_total = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_total,  # SIN FILTRO DE BAJA
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Contrataciones de COMERCIAL - TOTAL (incluye bajas)
            comercial_total = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_total,  # SIN FILTRO DE BAJA
                    filtro_comercial
                )\
                .scalar() or 0
            
            # Contrataciones de GESTIÓN - ACTIVAS (sin baja)
            gestion_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_activos,
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Contrataciones de COMERCIAL - ACTIVAS (sin baja)
            comercial_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_activos,
                    filtro_comercial
                )\
                .scalar() or 0
            
            total_mes_con_bajas = gestion_total + comercial_total
            total_mes_activos = gestion_activos + comercial_activos
            
            resultados.append({
                "mes": meses[mes_num - 1],
                "gestion": gestion_total,          # Total gestión (INCLUYE BAJAS)
                "gestion_activos": gestion_activos, # Gestión solo activos
                "comercial": comercial_total,       # Total comercial (INCLUYE BAJAS)
                "comercial_activos": comercial_activos, # Comercial solo activos
                "total_activos": total_mes_activos,
                "total_con_bajas": total_mes_con_bajas,
                "mes_num": mes_num
            })
        
        logger.info(f"Contrataciones para {year}: {len(resultados)} registros")
        
        if month and len(resultados) > 0:
            return jsonify(resultados[0])
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error in contrataciones API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener contrataciones"}), 500


    """API para obtener contrataciones por mes."""
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int)
    
    logger.info(f"API Contrataciones solicitada para año: {year}, mes: {month}")
    
    try:
        db = g.db
        
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        resultados = []
        
        # Si se especifica un mes, solo devolver ese mes
        if month:
            mes_range = [month]
        else:
            mes_range = range(1, 13)
        
        # Definir filtros para comercial y gestión
        filtro_comercial = or_(
            Colaborador.area_id == app.config['AREA_COMERCIAL_ID'],
            Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
        )
        
        filtro_gestion = and_(
            Colaborador.area_id != app.config['AREA_COMERCIAL_ID'],
            or_(
                Colaborador.reclutador_id.is_(None),
                ~Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
            )
        )
        
        for mes_num in mes_range:
            # Filtros para TOTAL de contrataciones (INCLUYENDO BAJAS)
            filters_total = [
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes_num
            ]
            
            # Filtros para contrataciones ACTIVAS (sin baja)
            filters_activos = [
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes_num,
                Colaborador.baja == False
            ]
            
            # Contrataciones de GESTIÓN - TOTAL (incluye bajas)
            gestion_total = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_total,
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Contrataciones de COMERCIAL - TOTAL (incluye bajas)
            comercial_total = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_total,
                    filtro_comercial
                )\
                .scalar() or 0
            
            # Contrataciones de GESTIÓN - ACTIVAS (sin baja)
            gestion_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_activos,
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Contrataciones de COMERCIAL - ACTIVAS (sin baja)
            comercial_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_activos,
                    filtro_comercial
                )\
                .scalar() or 0
            
            # Total de contrataciones para este mes (TODAS, incluyendo bajas)
            total_mes_con_bajas = gestion_total + comercial_total
            
            # Total de contrataciones ACTIVAS para este mes
            total_mes_activos = gestion_activos + comercial_activos
            
            resultados.append({
                "mes": meses[mes_num - 1],
                "gestion": gestion_total,          # Total gestión (incluye bajas)
                "gestion_activos": gestion_activos, # Gestión activos
                "comercial": comercial_total,       # Total comercial (incluye bajas)
                "comercial_activos": comercial_activos, # Comercial activos
                "total_activos": total_mes_activos,
                "total_con_bajas": total_mes_con_bajas,
                "mes_num": mes_num
            })
        
        logger.info(f"Contrataciones para {year}: {len(resultados)} registros")
        
        # Si se filtró por un mes específico, devolver solo ese mes
        if month and len(resultados) > 0:
            return jsonify(resultados[0])
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error in contrataciones API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener contrataciones"}), 500

@app.route("/api/bajas")
@require_db
def api_bajas():
    """API para obtener bajas por mes."""
    year = request.args.get("year", type=int, default=date.today().year)
    month = request.args.get("month", type=int)
    
    logger.info(f"API Bajas solicitada para año: {year}, mes: {month}")
    
    try:
        db = g.db
        
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        resultados = []
        
        # Filtros para comercial y gestión
        filtro_comercial = or_(
            Colaborador.area_id == app.config['AREA_COMERCIAL_ID'],
            Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
        )
        
        filtro_gestion = and_(
            Colaborador.area_id != app.config['AREA_COMERCIAL_ID'],
            or_(
                Colaborador.reclutador_id.is_(None),
                ~Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
            )
        )
        
        # Si se especifica un mes, solo devolver ese mes
        if month:
            mes_range = [month]
        else:
            mes_range = range(1, 13)
        
        for mes_num in mes_range:
            # Filtros base para bajas del mes
            filters_mes = [
                Colaborador.baja == True,
                Colaborador.fecha_baja.isnot(None),
                extract("year", Colaborador.fecha_baja) == year,
                extract("month", Colaborador.fecha_baja) == mes_num
            ]
            
            # Bajas de GESTIÓN (no comercial)
            gestion = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_mes,
                    filtro_gestion
                )\
                .scalar() or 0
            
            # Bajas de COMERCIAL (comercial)
            comercial = db.query(func.count(Colaborador.id))\
                .filter(
                    *filters_mes,
                    filtro_comercial
                )\
                .scalar() or 0
            
            resultados.append({
                "mes": meses[mes_num - 1],
                "gestion": gestion,
                "comercial": comercial,
                "total": gestion + comercial,
                "mes_num": mes_num
            })
        
        logger.info(f"Bajas para {year}: {len(resultados)} registros")
        
        # Si se filtró por un mes específico, devolver solo ese mes
        if month and len(resultados) > 0:
            return jsonify(resultados[0])
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error in bajas API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener bajas"}), 500

@app.route("/api/contrataciones/comparativa")
@require_db
def api_contrataciones_comparativa():
    """API para comparativa entre años."""
    years = request.args.getlist("years[]", type=int)
    
    if not years:
        current_year = date.today().year
        years = [current_year - 2, current_year - 1, current_year]
    
    logger.info(f"API Comparativa solicitada para años: {years}")
    
    try:
        db = g.db
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        filtro_comercial = or_(
            Colaborador.area_id == app.config['AREA_COMERCIAL_ID'],
            Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
        )
        
        filtro_gestion = and_(
            Colaborador.area_id != app.config['AREA_COMERCIAL_ID'],
            or_(
                Colaborador.reclutador_id.is_(None),
                ~Colaborador.reclutador_id.in_(app.config['RECLUTADOR_COMERCIAL_IDS'])
            )
        )
        
        comparativa = {}
        
        for year in years:
            datos_year = []
            
            for mes_num in range(1, 13):
                # Total de contrataciones (INCLUYENDO BAJAS) - REMOVIENDO "baja == False"
                total = db.query(func.count(Colaborador.id))\
                    .filter(
                        extract("year", Colaborador.fecha_alta) == year,
                        extract("month", Colaborador.fecha_alta) == mes_num
                        # REMOVED: Colaborador.baja == False
                    )\
                    .scalar() or 0
                
                # Contrataciones comerciales - TOTAL (INCLUYENDO BAJAS)
                comercial = db.query(func.count(Colaborador.id))\
                    .filter(
                        extract("year", Colaborador.fecha_alta) == year,
                        extract("month", Colaborador.fecha_alta) == mes_num,
                        # REMOVED: Colaborador.baja == False,
                        filtro_comercial
                    )\
                    .scalar() or 0
                
                # Contrataciones gestión - TOTAL (INCLUYENDO BAJAS)
                gestion = db.query(func.count(Colaborador.id))\
                    .filter(
                        extract("year", Colaborador.fecha_alta) == year,
                        extract("month", Colaborador.fecha_alta) == mes_num,
                        # REMOVED: Colaborador.baja == False,
                        filtro_gestion
                    )\
                    .scalar() or 0
                
                datos_year.append({
                    "mes": meses[mes_num - 1],
                    "total": total,        # TOTAL incluyendo bajas
                    "comercial": comercial, # Comercial incluyendo bajas
                    "gestion": gestion,    # Gestión incluyendo bajas
                    "mes_num": mes_num
                })
            
            comparativa[str(year)] = datos_year
        
        return jsonify(comparativa)
        
    except Exception as e:
        logger.error(f"Error in comparativa API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener comparativa"}), 500
@app.route("/api/contrataciones/reclutador")
@require_db
def api_contrataciones_reclutador():
    """API para contrataciones por reclutador."""
    year = request.args.get("year", type=int, default=date.today().year)
    
    logger.info(f"API Reclutadores solicitada para año: {year}")
    
    try:
        db = g.db
        
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        # Obtener todos los reclutadores que tienen colaboradores en el año (INCLUYENDO BAJAS)
        reclutadores = db.query(Reclutador)\
            .join(Colaborador, Reclutador.id == Colaborador.reclutador_id)\
            .filter(
                extract("year", Colaborador.fecha_alta) == year
            )\
            .distinct()\
            .order_by(Reclutador.nombre)\
            .all()
        
        resultados = []
        
        for reclutador in reclutadores:
            contratos_por_mes = []
            contratos_activos_por_mes = []
            total_anual = 0
            total_anual_activos = 0
            
            for mes_num in range(1, 13):
                # Contar TOTAL de contrataciones por reclutador y mes (INCLUYENDO BAJAS)
                total = db.query(func.count(Colaborador.id))\
                    .filter(
                        extract("year", Colaborador.fecha_alta) == year,
                        extract("month", Colaborador.fecha_alta) == mes_num,
                        Colaborador.reclutador_id == reclutador.id
                    )\
                    .scalar() or 0
                
                # Contar contrataciones ACTIVAS por reclutador y mes (sin baja)
                total_activos = db.query(func.count(Colaborador.id))\
                    .filter(
                        extract("year", Colaborador.fecha_alta) == year,
                        extract("month", Colaborador.fecha_alta) == mes_num,
                        Colaborador.baja == False,  # Solo activos
                        Colaborador.reclutador_id == reclutador.id
                    )\
                    .scalar() or 0
                
                total_anual += total
                total_anual_activos += total_activos
                
                contratos_por_mes.append({
                    "mes": meses[mes_num - 1],
                    "total": total,
                    "total_activos": total_activos,
                    "mes_num": mes_num
                })
            
            if total_anual > 0:
                resultados.append({
                    "reclutador": reclutador.nombre,
                    "reclutador_id": reclutador.id,
                    "contratos": contratos_por_mes,
                    "total_anual": total_anual,
                    "total_anual_activos": total_anual_activos
                })
        
        # También agregar contrataciones sin reclutador asignado (INCLUYENDO BAJAS)
        contratos_sin_reclutador = []
        total_sin_reclutador = 0
        total_sin_reclutador_activos = 0
        
        for mes_num in range(1, 13):
            total = db.query(func.count(Colaborador.id))\
                .filter(
                    extract("year", Colaborador.fecha_alta) == year,
                    extract("month", Colaborador.fecha_alta) == mes_num,
                    Colaborador.reclutador_id.is_(None)
                )\
                .scalar() or 0
            
            total_activos = db.query(func.count(Colaborador.id))\
                .filter(
                    extract("year", Colaborador.fecha_alta) == year,
                    extract("month", Colaborador.fecha_alta) == mes_num,
                    Colaborador.baja == False,  # Solo activos
                    Colaborador.reclutador_id.is_(None)
                )\
                .scalar() or 0
            
            total_sin_reclutador += total
            total_sin_reclutador_activos += total_activos
            
            contratos_sin_reclutador.append({
                "mes": meses[mes_num - 1],
                "total": total,
                "total_activos": total_activos,
                "mes_num": mes_num
            })
        
        if total_sin_reclutador > 0:
            resultados.append({
                "reclutador": "Sin reclutador asignado",
                "reclutador_id": 0,
                "contratos": contratos_sin_reclutador,
                "total_anual": total_sin_reclutador,
                "total_anual_activos": total_sin_reclutador_activos
            })
        
        # Ordenar por total anual descendente
        resultados.sort(key=lambda x: x["total_anual"], reverse=True)
        
        logger.info(f"Reclutadores encontrados: {len(resultados)}")
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error in reclutador API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener datos de reclutadores"}), 500

@app.route("/api/contrataciones/detalle-reclutador/<int:reclutador_id>")
@require_db
def api_contrataciones_detalle_reclutador(reclutador_id):
    """API para obtener detalle de contrataciones por reclutador específico."""
    year = request.args.get("year", type=int, default=date.today().year)
    
    logger.info(f"API Detalle Reclutador {reclutador_id} solicitada para año: {year}")
    
    try:
        db = g.db
        
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        # Verificar si es "Sin reclutador asignado"
        if reclutador_id == 0:
            reclutador_nombre = "Sin reclutador asignado"
            reclutador_id_filter = None
        else:
            reclutador = db.query(Reclutador).filter_by(id=reclutador_id).first()
            if not reclutador:
                return jsonify({"error": "Reclutador no encontrado"}), 404
            reclutador_nombre = reclutador.nombre
            reclutador_id_filter = reclutador_id
        
        contratos_por_mes = []
        total_anual = 0
        
        for mes_num in range(1, 13):
            # Contar contrataciones por reclutador y mes (solo activos)
            query = db.query(func.count(Colaborador.id))\
                .filter(
                    extract("year", Colaborador.fecha_alta) == year,
                    extract("month", Colaborador.fecha_alta) == mes_num,
                    Colaborador.baja == False
                )
            
            if reclutador_id == 0:
                query = query.filter(Colaborador.reclutador_id.is_(None))
            else:
                query = query.filter(Colaborador.reclutador_id == reclutador_id)
            
            total = query.scalar() or 0
            total_anual += total
            
            contratos_por_mes.append({
                "mes": meses[mes_num - 1],
                "total": total,
                "mes_num": mes_num
            })
        
        return jsonify({
            "reclutador": {
                "id": reclutador_id,
                "nombre": reclutador_nombre
            },
            "contratos": contratos_por_mes,
            "total_anual": total_anual,
            "year": year
        })
        
    except Exception as e:
        logger.error(f"Error in detalle reclutador API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener detalle del reclutador"}), 500

@app.route("/api/contrataciones/mes-detalle/<int:mes>")
@require_db
def api_contrataciones_mes_detalle(mes):
    """API para obtener detalle de contrataciones por mes específico."""
    year = request.args.get("year", type=int, default=date.today().year)
    
    logger.info(f"API Mes Detalle solicitada para mes: {mes}, año: {year}")
    
    try:
        db = g.db
        
        # Obtener reclutadores con contrataciones en este mes (ACTIVOS)
        sql = text("""
            SELECT 
                COALESCE(r.nombre, 'Sin reclutador asignado') as reclutador_nombre,
                COALESCE(r.id, 0) as reclutador_id,
                COUNT(c.id) as total
            FROM colaboradores c
            LEFT JOIN reclutadores r ON c.reclutador_id = r.id
            WHERE YEAR(c.fecha_alta) = :year
                AND MONTH(c.fecha_alta) = :mes
                AND c.baja = FALSE
            GROUP BY COALESCE(r.id, 0), COALESCE(r.nombre, 'Sin reclutador asignado')
            HAVING COUNT(c.id) > 0
            ORDER BY total DESC
        """)
        
        resultados = db.execute(sql, {'year': year, 'mes': mes}).fetchall()
        
        # Total del mes (ACTIVOS)
        total_mes = db.query(func.count(Colaborador.id))\
            .filter(
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes,
                Colaborador.baja == False
            )\
            .scalar() or 0
        
        # Total comercial (área_id = 2) - ACTIVOS
        total_comercial = db.query(func.count(Colaborador.id))\
            .filter(
                extract("year", Colaborador.fecha_alta) == year,
                extract("month", Colaborador.fecha_alta) == mes,
                Colaborador.baja == False,
                Colaborador.area_id == app.config['AREA_COMERCIAL_ID']
            )\
            .scalar() or 0
        
        # Total por área comercial (para detalle)
        detalles_comercial = []
        if total_comercial > 0:
            sql_comercial = text("""
                SELECT 
                    COALESCE(r.nombre, 'Sin reclutador asignado') as reclutador_nombre,
                    COALESCE(r.id, 0) as reclutador_id,
                    COUNT(c.id) as total
                FROM colaboradores c
                LEFT JOIN reclutadores r ON c.reclutador_id = r.id
                WHERE YEAR(c.fecha_alta) = :year
                    AND MONTH(c.fecha_alta) = :mes
                    AND c.baja = FALSE
                    AND c.area_id = :area_id
                GROUP BY COALESCE(r.id, 0), COALESCE(r.nombre, 'Sin reclutador asignado')
                HAVING COUNT(c.id) > 0
                ORDER BY total DESC
            """)
            
            resultados_comercial = db.execute(sql_comercial, {
                'year': year, 
                'mes': mes,
                'area_id': app.config['AREA_COMERCIAL_ID']
            }).fetchall()
            
            for row in resultados_comercial:
                detalles_comercial.append({
                    "reclutador": row.reclutador_nombre,
                    "reclutador_id": row.reclutador_id if row.reclutador_id != 0 else None,
                    "total": row.total
                })
        
        detalles = []
        for row in resultados:
            detalles.append({
                "reclutador": row.reclutador_nombre,
                "reclutador_id": row.reclutador_id if row.reclutador_id != 0 else None,
                "total": row.total
            })
        
        return jsonify({
            "mes": mes,
            "year": year,
            "total_mes": total_mes,
            "total_comercial": total_comercial,
            "detalles": detalles,
            "detalles_comercial": detalles_comercial
        })
        
    except Exception as e:
        logger.error(f"Error in mes detalle API: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener detalle del mes"}), 500

@app.route("/api/buscar-reclutador")
@require_db
def api_buscar_reclutador():
    """API para buscar ID de reclutador por nombre."""
    nombre = request.args.get("nombre", "").strip()
    
    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400
    
    try:
        db = g.db
        
        reclutador = db.query(Reclutador).filter_by(nombre=nombre).first()
        if reclutador:
            return jsonify({
                "id": reclutador.id,
                "nombre": reclutador.nombre
            })
        else:
            # Intentar búsqueda sin acentos
            def remove_accents(text):
                if not text:
                    return text
                text = unicodedata.normalize('NFD', text)
                text = text.encode('ascii', 'ignore').decode('utf-8')
                return text.lower()
            
            nombre_sin_acentos = remove_accents(nombre)
            
            all_reclutadores = db.query(Reclutador).all()
            matches = []
            
            for r in all_reclutadores:
                r_nombre_sin_acentos = remove_accents(r.nombre)
                if nombre_sin_acentos in r_nombre_sin_acentos.lower():
                    matches.append({
                        "id": r.id,
                        "nombre": r.nombre
                    })
            
            if matches:
                return jsonify(matches)
            
            return jsonify({"error": "Reclutador no encontrado"}), 404
            
    except Exception as e:
        logger.error(f"Error buscando reclutador: {e}", exc_info=True)
        return jsonify({"error": "Error al buscar reclutador"}), 500


def reparar_hash_password(hash_actual, password):
    """Intenta reparar un hash de contraseña dañado."""
    if not hash_actual:
        return Usuario.hash_password(password, method='scrypt')
    
    # Si el hash está vacío o parece dañado
    if hash_actual == '' or len(hash_actual) < 10:
        return Usuario.hash_password(password, method='scrypt')
    
    return hash_actual

# ======================================
# INICIALIZACIÓN
# ======================================
def initialize_app():
    """Inicializa la aplicación."""
    logger.info("Starting application initialization...")
    
    Base.metadata.create_all(engine)
    logger.info("Database tables verified/created")
    
    create_initial_data()
    
    logger.info("Application initialized successfully")

def create_initial_data():
    """Crea datos iniciales si las tablas están vacías."""
    with get_db() as db:
        if db.query(Area).count() == 0:
            logger.info("Creating initial data...")
            
            areas = [
                Area(nombre="Gestión", nombre_normalizado="gestion"),
                Area(nombre="Comercial", nombre_normalizado="comercial")
            ]
            db.add_all(areas)
            db.flush()
            
            puestos = [
                Puesto(nombre="Analista", area_id=1),
                Puesto(nombre="Coordinador", area_id=1),
                Puesto(nombre="Gerente", area_id=1),
                Puesto(nombre="Vendedor", area_id=2),
                Puesto(nombre="Coordinador Comercial", area_id=2),
                Puesto(nombre="Gerente Comercial", area_id=2)
            ]
            db.add_all(puestos)
            
            metodos = [
                MetodoPago(nombre="Transferencia"),
                MetodoPago(nombre="Cheque"),
                MetodoPago(nombre="Efectivo")
            ]
            db.add_all(metodos)
            
            bancos = [
                Banco(nombre="BBVA"),
                Banco(nombre="Banorte"),
                Banco(nombre="Santander"),
                Banco(nombre="HSBC")
            ]
            db.add_all(bancos)
            
            reclutadores = [
                Reclutador(nombre="Francesca Argáez"),
                Reclutador(nombre="Jazmín Moo"),
                Reclutador(nombre="Ana Mata"),
                Reclutador(nombre="Rousseli Trejo"),
                Reclutador(nombre="Comercial"),  # ID:5 - Este es especial para área comercial
                Reclutador(nombre="Julio"),
                Reclutador(nombre="Nilson"),
                Reclutador(nombre="Erick")
            ]
            db.add_all(reclutadores)
            
            db.commit()
            logger.info("Initial data created")

# ======================================
# RUTA PARA BAJA COLABORADOR
# ======================================
@app.route("/baja-colaborador", methods=["GET"])
@login_required  # Primero verificar login
@area_required([3, 4])  # Luego verificar área
@require_db
def baja_colaborador():
    """Página para dar de baja colaboradores."""
    return render_template("baja_colaborador.html")

# ======================================
# RUTA ALTERNATIVA PARA POST DE ALTA
# ======================================
@app.route("/alta-colaborador", methods=["POST"])
@require_db
def alta_colaborador_post():
    """Ruta para POST del formulario de alta que redirige al dashboard."""
    try:
        db = g.db
        
        # NUEVA VALIDACIÓN: Verificar RFC antes de procesar
        rfc = request.form.get("rfc", "").upper().strip()
        
        if rfc:
            # Verificar si RFC ya existe
            existe_rfc = db.query(Colaborador).filter_by(rfc=rfc).first()
            if existe_rfc:
                flash(f"❌ El RFC <strong>{rfc}</strong> ya está registrado para el colaborador: {existe_rfc.nombre} {existe_rfc.apellido}", "error")
                return redirect(url_for('alta'))
        
        # Validar campos requeridos
        required_fields = ['area', 'nombre', 'apellido', 'correo', 'rfc', 'curp', 'nss', 'fecha_alta']
        missing_fields = []
        
        for field in required_fields:
            if not request.form.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            flash(f"❌ Campos requeridos faltantes: {', '.join(missing_fields)}", "error")
            return redirect(url_for('alta'))
        
        # Validar datos únicos
        rfc = request.form.get("rfc", "").upper()
        curp = request.form.get("curp", "").upper()
        nss = request.form.get("nss", "")
        correo = request.form.get("correo", "")
        
        # Verificar duplicados
        duplicados = []
        
        if db.query(Colaborador).filter_by(rfc=rfc).first():
            duplicados.append(f"RFC: {rfc}")
        
        if db.query(Colaborador).filter_by(curp=curp).first():
            duplicados.append(f"CURP: {curp}")
        
        if db.query(Colaborador).filter_by(nss=nss).first():
            duplicados.append(f"NSS: {nss}")
        
        if db.query(Colaborador).filter_by(correo=correo).first():
            duplicados.append(f"Correo: {correo}")
        
        if duplicados:
            flash(f"❌ Datos duplicados encontrados: {', '.join(duplicados)}", "error")
            return redirect(url_for('alta'))
        
        # Crear colaborador - MODIFICADO para obtener solo el ID
        area_id = int(request.form.get("area"))
        colaborador_id = crear_colaborador(db, area_id)  # <-- Ahora retorna solo el ID
        
        # Obtener datos del colaborador para el mensaje flash
        colaborador = db.query(Colaborador).get(colaborador_id)
        
        # Mensaje de éxito con el nombre del colaborador
        flash(f"✅ Colaborador <strong>{colaborador.nombre} {colaborador.apellido}</strong> registrado exitosamente", "success")
        
        # REDIRIGIR AL DASHBOARD en lugar de volver al formulario
        return redirect(url_for('dashboard'))
        # Si quieres llevar el ID como parámetro (opcional):
        # return redirect(url_for('dashboard', nuevo_colaborador_id=colaborador_id))
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error en alta POST: {e}", exc_info=True)
        flash(f"❌ Error al registrar colaborador: {str(e)}", "error")
        return redirect(url_for('alta'))

# ======================================
# API PARA OBTENER TODOS LOS COLABORADORES (FIXED)
# ======================================
@app.route("/api/colaboradores/todos")
@login_required
@area_required([3, 4])
@require_db
def api_colaboradores_todos():
    """API para obtener todos los colaboradores - CORREGIDO CON TODOS LOS CAMPOS."""
    try:
        db = g.db
        
        # Obtener todos los colaboradores con información de área y puesto - CORREGIDO
        colaboradores = db.query(
            Colaborador.id,
            Colaborador.nombre,
            Colaborador.apellido,
            Colaborador.correo,
            Colaborador.rfc,
            Colaborador.curp,
            Colaborador.nss,
            Colaborador.fecha_alta,
            Colaborador.telefono,
            Colaborador.domicilio,  # ✅ AGREGADO
            Colaborador.sueldo,
            Colaborador.comentarios,  # ✅ AGREGADO
            Colaborador.baja,
            Colaborador.area_id,
            Colaborador.puesto_id,
            Colaborador.correo_coordinador,
            Colaborador.edad,  # ✅ AGREGADO
            Colaborador.estado_civil,  # ✅ AGREGADO
            Area.nombre.label('area_nombre'),
            Area.nombre_coordinador,
            Puesto.nombre.label('puesto_nombre')
        ).join(
            Area, Colaborador.area_id == Area.id
        ).outerjoin(
            Puesto, Colaborador.puesto_id == Puesto.id
        ).order_by(
            Colaborador.id.desc()
        ).all()
        
        resultados = []
        for col in colaboradores:
            resultados.append({
                'id': col.id,
                'nombre': col.nombre or '',
                'apellido': col.apellido or '',
                'correo': col.correo or '',
                'rfc': col.rfc or '',
                'curp': col.curp or '',
                'nss': col.nss or '',  # ✅ AHORA SÍ VIENE
                'fecha_alta': col.fecha_alta.isoformat() if col.fecha_alta else None,
                'telefono': col.telefono or '',
                'domicilio': col.domicilio or '',  # ✅ AHORA SÍ VIENE
                'sueldo': float(col.sueldo) if col.sueldo else None,
                'comentarios': col.comentarios or '',  # ✅ AHORA SÍ VIENE
                'baja': bool(col.baja),
                'area_id': col.area_id,
                'area_nombre': col.area_nombre or 'N/A',
                'puesto_nombre': col.puesto_nombre or 'N/A',
                'nombre_coordinador': col.nombre_coordinador or 'N/A',
                'correo_coordinador': col.correo_coordinador or 'N/A',
                'edad': col.edad or None,  # ✅ AHORA SÍ VIENE
                'estado_civil': col.estado_civil or 'N/A'  # ✅ AHORA SÍ VIENE
            })
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error obteniendo colaboradores: {e}", exc_info=True)
        return jsonify([])
# ======================================
# RUTA PARA LA VISTA DE COLABORADORES
# ======================================
@app.route("/colaboradores")
@login_required
@area_required([3, 4])  # Solo áreas con ID 3 y 4 pueden acceder
def colaboradores():
    """Página de lista de colaboradores - ahora protegida."""
    return render_template("colaboradores.html")

# ======================================
# API PARA DETALLES DE COLABORADOR (COMPLETA)
# ======================================

@app.route("/api/colaborador/detalle/<int:colaborador_id>")
@require_db
def api_colaborador_detalle(colaborador_id):
    """API para obtener detalles completos de un colaborador - VERSIÓN CORREGIDA."""
    try:
        db = g.db
        
        # Consulta que obtiene TODOS los campos necesarios - CORREGIDO SIN ISOOUTER
        colaborador = db.query(
            Colaborador,
            Area.nombre.label('area_nombre'),
            Area.nombre_coordinador,
            Area.correo_coordinador,
            Puesto.nombre.label('puesto_nombre')
        ).join(
            Area, Colaborador.area_id == Area.id
        ).outerjoin(
            Puesto, Colaborador.puesto_id == Puesto.id  # SIN ISOOUTER
        ).filter(
            Colaborador.id == colaborador_id
        ).first()
        
        if not colaborador:
            return jsonify({"success": False, "error": "Colaborador no encontrado"}), 404
        
        col = colaborador[0]  # El objeto Colaborador
        
        # Preparar respuesta con TODOS los campos
        response_data = {
            'success': True,
            'colaborador': {
                # DATOS PERSONALES
                'id': col.id,
                'nombre': col.nombre or '',
                'apellido': col.apellido or '',
                'correo': col.correo or '',
                'edad': col.edad,
                'estado_civil': col.estado_civil or '',
                'telefono': col.telefono or '',
                'domicilio': col.domicilio or '',
                
                # DATOS OFICIALES
                'rfc': col.rfc or '',
                'curp': col.curp or '',
                'nss': col.nss or '',  # ✅ NSS incluido
                'fecha_alta': col.fecha_alta.isoformat() if col.fecha_alta else None,
                
                # DATOS LABORALES
                'area_id': col.area_id,
                'area_nombre': colaborador.area_nombre or '',
                'puesto_id': col.puesto_id,
                'puesto_nombre': colaborador.puesto_nombre or '',
                'sueldo': float(col.sueldo) if col.sueldo else None,
                'comentarios': col.comentarios or '',  # ✅ Comentarios incluidos
                'baja': bool(col.baja),
                'fecha_baja': col.fecha_baja.isoformat() if col.fecha_baja else None,
                'motivo_baja': col.motivo_baja or '',
                
                # DATOS DE COORDINADOR
                'nombre_coordinador': colaborador.nombre_coordinador or '',
                'correo_coordinador': colaborador.correo_coordinador or '',
                
                # DATOS COMERCIALES
                'rol_comercial': col.rol_comercial or '',
                'comisionista': bool(col.comisionista) if col.comisionista is not None else None,
                'metodo_pago': col.metodo_pago or '',
                'banco': col.banco or '',
                'reclutador': col.reclutador or '',
                'numero_cuenta': col.numero_cuenta or '',
                'numero_comisiones': col.numero_comisiones or '',
                
                # DATOS DE CRÉDITOS
                'tiene_infonavit': bool(col.tiene_infonavit),
                'infonavit_credito': col.infonavit_credito or '',
                'tiene_fonacot': bool(col.tiene_fonacot),
                'fonacot_credito': col.fonacot_credito or '',
                
                # DATOS DE RELACIONES (IDs)
                'metodo_pago_id': col.metodo_pago_id,
                'banco_id': col.banco_id,
                'reclutador_id': col.reclutador_id,
                
                # DATOS DE CAMBIO DE ÁREA (si existen)
                'fecha_ultimo_cambio_area': col.fecha_ultimo_cambio_area.isoformat() if col.fecha_ultimo_cambio_area else None,
                'motivo_ultimo_cambio_area': col.motivo_ultimo_cambio_area or '',
                'area_anterior_id': col.area_anterior_id
            }
        }
        
        # Log para depuración
        logger.info(f"✅ Detalles cargados para colaborador ID: {colaborador_id}")
        logger.info(f"📋 Campos cargados: NSS={'SÍ' if col.nss else 'NO'}, "
                   f"Domicilio={'SÍ' if col.domicilio else 'NO'}, "
                   f"Comentarios={'SÍ' if col.comentarios else 'NO'}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalle de colaborador {colaborador_id}: {e}", exc_info=True)
        return jsonify({
            "success": False, 
            "error": f"Error al obtener detalles del colaborador: {str(e)}"
        }), 500


# ======================================
# API PARA BUSCAR COLABORADOR POR ID (SIMPLIFICADA)
# ======================================
# MANTÉN SOLO UNA VERSIÓN - ELIMINA LA DUPLICADA
@app.route("/api/colaborador/<int:colaborador_id>", methods=["GET"])
@require_db
def api_colaborador_por_id(colaborador_id):
    """API para obtener colaborador por ID - VERSIÓN ÚNICA."""
    try:
        db = g.db
        
        colaborador = db.query(Colaborador).filter_by(id=colaborador_id).first()
        
        if not colaborador:
            return jsonify({"error": "Colaborador no encontrado"}), 404
        
        # Obtener información básica
        area_nombre = "N/A"
        if colaborador.area:
            area_nombre = colaborador.area.nombre
        
        puesto_nombre = "N/A"
        if colaborador.puesto:
            puesto_nombre = colaborador.puesto.nombre
        
        # Obtener área anterior (nuevo campo)
        area_anterior_nombre = "N/A"
        if colaborador.area_anterior_id:
            area_anterior = db.query(Area).filter_by(id=colaborador.area_anterior_id).first()
            if area_anterior:
                area_anterior_nombre = area_anterior.nombre
        
        return jsonify({
            "id": colaborador.id,
            "nombre": f"{colaborador.nombre} {colaborador.apellido}",
            "correo": colaborador.correo,
            "rfc": colaborador.rfc,
            "curp": colaborador.curp or "N/A",
            "area": area_nombre,
            "area_id": colaborador.area_id,
            "puesto": puesto_nombre,
            "puesto_id": colaborador.puesto_id,
            "estado": "Activo" if not colaborador.baja else "Baja",
            "fecha_alta": colaborador.fecha_alta.strftime("%Y-%m-%d") if colaborador.fecha_alta else "N/A",
            "telefono": colaborador.telefono or "N/A",
            "sueldo": float(colaborador.sueldo) if colaborador.sueldo else 0.00,
            "baja": bool(colaborador.baja),
            
            # NUEVOS CAMPOS DE CAMBIO DE ÁREA
            "fecha_ultimo_cambio_area": colaborador.fecha_ultimo_cambio_area.strftime("%Y-%m-%d") 
                                       if colaborador.fecha_ultimo_cambio_area else "N/A",
            "motivo_ultimo_cambio_area": colaborador.motivo_ultimo_cambio_area or "N/A",
            "area_anterior": area_anterior_nombre,
            "area_anterior_id": colaborador.area_anterior_id or "N/A",
            
            # Para compatibilidad
            "ultimo_cambio": colaborador.fecha_ultimo_cambio_area.strftime("%Y-%m-%d") 
                           if colaborador.fecha_ultimo_cambio_area else "N/A"
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo colaborador por ID: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener colaborador"}), 500


@app.route("/api/test/colaboradores")
@require_db
def api_test_colaboradores():
    """API de prueba para verificar datos."""
    try:
        db = g.db
        
        # Contar colaboradores
        total = db.query(func.count(Colaborador.id)).scalar() or 0
        
        # Obtener primeros 5 colaboradores
        colaboradores = db.query(Colaborador).limit(5).all()
        
        resultados = []
        for col in colaboradores:
            resultados.append({
                'id': col.id,
                'nombre': col.nombre or '',
                'apellido': col.apellido or '',
                'correo': col.correo or '',
                'rfc': col.rfc or '',
                'area_id': col.area_id,
                'baja': bool(col.baja)
            })
        
        return jsonify({
            'success': True,
            'total_colaboradores': total,
            'muestra': resultados,
            'message': f'Total en BD: {total} colaboradores'
        })
        
    except Exception as e:
        logger.error(f"Error en API de prueba: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ======================================
# API PARA ACTUALIZAR COLABORADOR - CORREGIDA
# ======================================
@app.route("/api/colaborador/actualizar", methods=["POST"])
@require_db
def api_actualizar_colaborador():
    """API para actualizar datos de colaborador - CORREGIDO con límites de longitud."""
    try:
        data = request.get_json()
        db = g.db
        
        if not data or 'id' not in data:
            return jsonify({"error": "Datos inválidos"}), 400
        
        colaborador = db.query(Colaborador).filter_by(id=data['id']).first()
        if not colaborador:
            return jsonify({"error": "Colaborador no encontrado"}), 404
        
        # Actualizar campos básicos con validación de longitud
        if 'nombre' in data:
            colaborador.nombre = data['nombre'][:100]  # Limitar a 100 caracteres
        if 'apellido' in data:
            colaborador.apellido = data['apellido'][:100]
        if 'correo' in data:
            colaborador.correo = data['correo'][:150]
        if 'telefono' in data:
            colaborador.telefono = data['telefono'][:20] if data['telefono'] else None
        if 'rfc' in data:
            colaborador.rfc = data['rfc'][:13].upper() if data['rfc'] else None
        if 'curp' in data:
            colaborador.curp = data['curp'][:18].upper() if data['curp'] else None
        if 'nss' in data:
            # LIMITAR NSS A 15 CARACTERES (SOLUCIÓN AL ERROR)
            colaborador.nss = data['nss'][:15] if data['nss'] else None
        if 'domicilio' in data:
            colaborador.domicilio = data['domicilio'][:500] if data['domicilio'] else None
        if 'sueldo' in data:
            try:
                colaborador.sueldo = float(data['sueldo']) if data['sueldo'] else None
            except ValueError:
                pass
        if 'comentarios' in data:
            colaborador.comentarios = data['comentarios'][:1000] if data['comentarios'] else None
        if 'edad' in data:
            try:
                colaborador.edad = int(data['edad']) if data['edad'] else None
            except ValueError:
                pass
        if 'area_id' in data and data['area_id']:
            colaborador.area_id = int(data['area_id'])
            # Obtener coordinador del área
            area = db.query(Area).filter_by(id=data['area_id']).first()
            if area:
                colaborador.correo_coordinador = area.correo_coordinador
        if 'puesto_id' in data and data['puesto_id']:
            colaborador.puesto_id = int(data['puesto_id'])
        if 'baja' in data:
            colaborador.baja = bool(data['baja'])
            if data['baja'] and not colaborador.fecha_baja:
                colaborador.fecha_baja = date.today()
            elif not data['baja']:
                colaborador.fecha_baja = None
        
        db.commit()
        
        logger.info(f"Colaborador actualizado: {colaborador.id} - {colaborador.nombre} {colaborador.apellido}")
        
        return jsonify({
            "success": True,
            "message": "Colaborador actualizado correctamente",
            "colaborador": {
                "id": colaborador.id,
                "nombre": f"{colaborador.nombre} {colaborador.apellido}"
            }
        })
        
    except Exception as e:
        logger.error(f"Error actualizando colaborador: {e}", exc_info=True)
        db.rollback()
        return jsonify({"error": f"Error al actualizar colaborador: {str(e)}"}), 500

# ======================================
# API PARA OBTENER DOCUMENTOS
# ======================================
@app.route("/api/documentos/<int:colaborador_id>")
@require_db
def api_documentos(colaborador_id):
    """API para obtener documentos de un colaborador."""
    try:
        db = g.db
        
        documentos = db.query(Documento).filter_by(colaborador_id=colaborador_id).order_by(Documento.id.desc()).all()
        
        resultados = []
        for doc in documentos:
            resultados.append({
                "id": doc.id,
                "nombre_archivo": doc.nombre_archivo,
                "ruta_archivo": doc.ruta_archivo,
                "tipo": doc.tipo,
                "tamano": doc.tamano,
                "fecha_subida": doc.fecha_subida.strftime("%Y-%m-%d") if doc.fecha_subida else "N/A"
            })
        
        return jsonify(resultados)
        
    except Exception as e:
        logger.error(f"Error obteniendo documentos: {e}", exc_info=True)
        return jsonify([])

# ======================================
# API PARA DESCARGAR DOCUMENTO
# ======================================
@app.route("/api/documento/descargar")
@require_db
def api_descargar_documento():
    """API para descargar un documento."""
    try:
        ruta = request.args.get('ruta')
        nombre = request.args.get('nombre')
        
        if not ruta or not os.path.exists(ruta):
            return jsonify({"error": "Documento no encontrado"}), 404
        
        return send_file(
            ruta,
            as_attachment=True,
            download_name=nombre,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error descargando documento: {e}", exc_info=True)
        return jsonify({"error": "Error al descargar el documento"}), 500

# ======================================
# API PARA PREVIEW DE DOCUMENTOS
# ======================================
@app.route("/api/documento/preview")
@require_db
def api_documento_preview():
    """API para previsualizar documentos (imágenes y PDFs) - VERSIÓN MEJORADA."""
    try:
        ruta = request.args.get('ruta')
        
        if not ruta or not os.path.exists(ruta):
            return jsonify({"error": "Documento no encontrado"}), 404
        
        # Verificar seguridad - asegurar que está dentro de uploads
        uploads_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
        file_path = os.path.abspath(ruta)
        
        if not file_path.startswith(uploads_path):
            return jsonify({"error": "Acceso no permitido"}), 403
        
        # Determinar tipo de archivo
        file_ext = os.path.splitext(ruta)[1].lower()
        
        # Tipos MIME
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.pdf': 'application/pdf'  # ✅ AGREGADO PARA PDFs
        }
        
        if file_ext not in mime_types:
            return jsonify({"error": "Tipo de archivo no soportado para previsualización"}), 400
        
        # Obtener tipo MIME
        mime_type = mime_types[file_ext]
        
        # Para imágenes: enviar como imagen
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return send_file(
                ruta,
                mimetype=mime_type
            )
        
        # Para PDFs: enviar como PDF (PDF.js lo manejará en el frontend)
        elif file_ext == '.pdf':
            return send_file(
                ruta,
                mimetype=mime_type,
                as_attachment=False,  # Importante: no como adjunto
                download_name=os.path.basename(ruta)
            )
            
    except Exception as e:
        logger.error(f"Error en preview de documento: {e}", exc_info=True)
        return jsonify({"error": "Error al previsualizar el documento"}), 500


# ======================================
# API PARA COORDINADOR POR ÁREA
# ======================================
@app.route("/api/coordinador-por-area/<int:area_id>")
@require_db
def api_coordinador_por_area(area_id):
    """API para obtener coordinador por área."""
    try:
        db = g.db
        
        area = db.query(Area).filter_by(id=area_id).first()
        
        if not area:
            return jsonify({"error": "Área no encontrada"}), 404
        
        return jsonify({
            "nombre_coordinador": area.nombre_coordinador or "N/A",
            "correo_coordinador": area.correo_coordinador or "N/A"
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo coordinador: {e}", exc_info=True)
        return jsonify({"error": "Error al obtener información del coordinador"}), 500

# Ejecutar reparación de hashes al iniciar
def verificar_y_reparar_hashes():
    """Verificar y reparar hashes al iniciar la aplicación."""
    with get_db() as db:
        usuarios = db.query(Usuario).all()
        actualizados = 0
        
        for usuario in usuarios:
            # Si el hash está vacío o parece dañado
            if not usuario.password_hash or usuario.password_hash == '':
                # Asignar contraseña por defecto basada en el rol
                password_default = 'admin123' if usuario.rol == 'admin' else 'coordinador123'
                usuario.password_hash = Usuario.hash_password(user_data['password'])
                actualizados += 1
                logger.warning(f"Hash reparado para usuario: {usuario.correo}")
        
        if actualizados > 0:
            db.commit()
            logger.info(f"Se repararon {actualizados} hashes de contraseña")

def migrar_hashes_existentes():
    """Migra los hashes existentes a formato scrypt."""
    with get_db() as db:
        usuarios = db.query(Usuario).all()
        passwords_por_rol = {
            'admin': 'Admin123!',
            'coordinador': 'TiPassword123!'
        }
        
        actualizados = 0
        for usuario in usuarios:
            # Determinar qué contraseña usar según el correo
            if 'admin' in usuario.correo:
                password = 'Admin123!'
            elif 'coordinador.ti' in usuario.correo:
                password = 'TiPassword123!'
            elif 'coordinador.rh' in usuario.correo:
                password = 'Coordinador123!'  # Ajusta según necesites
            else:
                password = 'Default123!'
            
            # Generar nuevo hash con scrypt
            nuevo_hash = Usuario.hash_password(password)
            usuario.password_hash = nuevo_hash
            actualizados += 1
            
            logger.info(f"Actualizado hash para {usuario.correo}")
        
        if actualizados > 0:
            db.commit()
            logger.info(f"✓ Migrados {actualizados} hashes a scrypt")


if __name__ == "__main__":
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    initialize_app()
    

    # Luego asegurar que todos los usuarios estén creados correctamente
    crear_usuarios_con_hash_correcto()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )