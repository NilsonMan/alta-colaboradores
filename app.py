import os  # <-- AGREGAR ESTO AL INICIO
import sys
import time
import hashlib
import logging
import re
from datetime import datetime, date, timedelta
from contextlib import contextmanager
from functools import wraps

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
    puestos = relationship("Puesto", back_populates="area")
    
    # Relaciones con colaboradores
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
    
    col = Colaborador(
        nombre=request.form.get("nombre", "").strip(),
        apellido=request.form.get("apellido", "").strip(),
        correo=request.form.get("correo", "").strip(),
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
    db.flush()  # Obtiene el ID sin hacer commit
    
    agregar_relaciones(db, col)
    
    # Guardar documentos
    try:
        guardar_documentos(db, col.id)
    except Exception as e:
        logger.warning(f"Error guardando documentos para colaborador {col.id}: {e}")
    
    db.commit()  # Ahora sí hacemos commit de TODO
    
    logger.info(f"✅ Colaborador creado: {col.nombre} {col.apellido} (ID: {col.id})")
    return col.id  # <-- Retorna el ID del colaborador creado


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
@app.route("/api/colaborador/<int:colaborador_id>", methods=["GET"])
@require_db
def api_colaborador_por_id(colaborador_id):
    """API para obtener colaborador por ID - ACTUALIZADO con campos de cambio."""
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
    """API para procesar cambio de área - ACTUALIZADO con nuevos campos."""
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
        
        return jsonify({
            "success": True,
            "message": "Cambio de área procesado exitosamente",
            "colaborador": {
                "id": colaborador.id,
                "nombre": f"{colaborador.nombre} {colaborador.apellido}",
                "area_anterior": area_actual,
                "area_nueva": nueva_area.nombre,
                "fecha_cambio": fecha_cambio.strftime("%Y-%m-%d")
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
# MAIN
# ======================================
if __name__ == "__main__":
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    initialize_app()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )