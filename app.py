from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for, send_file
)
from sqlalchemy import (
    create_engine, Column, Integer, String,
    ForeignKey, Table, Boolean, Text, Date
)
from sqlalchemy.orm import (
    sessionmaker, declarative_base, relationship
)
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import unicodedata

# ======================================
# FLASK
# ======================================
app = Flask(__name__)

# ======================================
# RUTAS
# ======================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "alta_colaboradores.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ======================================
# DB
# ======================================
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ======================================
# UTILIDAD
# ======================================
def normalizar_texto(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

# ======================================
# MANY TO MANY
# ======================================
colaborador_recurso = Table(
    "colaborador_recurso",
    Base.metadata,
    Column("colaborador_id", ForeignKey("colaboradores.id")),
    Column("recurso_id", ForeignKey("recursos_ti.id"))
)

colaborador_programa = Table(
    "colaborador_programa",
    Base.metadata,
    Column("colaborador_id", ForeignKey("colaboradores.id")),
    Column("programa_id", ForeignKey("programas.id"))
)

# ======================================
# MODELOS
# ======================================
class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True)
    nombre_normalizado = Column(String(100), unique=True)

    puestos = relationship("Puesto", back_populates="area")

class Puesto(Base):
    __tablename__ = "puestos"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))
    area_id = Column(Integer, ForeignKey("areas.id"))

    area = relationship("Area", back_populates="puestos")

class Colaborador(Base):
    __tablename__ = "colaboradores"
    id = Column(Integer, primary_key=True)

    nombre = Column(String(100))
    apellido = Column(String(100))
    correo = Column(String(150))

    edad = Column(Integer)
    estado_civil = Column(String(50))
    domicilio = Column(Text)
    telefono = Column(String(20))

    rfc = Column(String(13))
    curp = Column(String(18))
    nss = Column(String(15))
    fecha_alta = Column(Date)

    sueldo = Column(Integer)
    comentarios = Column(Text)

    rol_comercial = Column(String(100))
    comisionista = Column(Boolean)

    tiene_infonavit = Column(Boolean)
    infonavit_credito = Column(String(50))
    tiene_fonacot = Column(Boolean)
    fonacot_credito = Column(String(50))

    area_id = Column(Integer, ForeignKey("areas.id"))
    puesto_id = Column(Integer, ForeignKey("puestos.id"))

    area = relationship("Area")
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
        back_populates="colaborador",
        cascade="all, delete-orphan"
    )

class RecursoTI(Base):
    __tablename__ = "recursos_ti"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True)

    colaboradores = relationship(
        "Colaborador",
        secondary=colaborador_recurso,
        back_populates="recursos"
    )

class Programa(Base):
    __tablename__ = "programas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True)

    colaboradores = relationship(
        "Colaborador",
        secondary=colaborador_programa,
        back_populates="programas"
    )

class Documento(Base):
    __tablename__ = "documentos"
    id = Column(Integer, primary_key=True)
    colaborador_id = Column(Integer, ForeignKey("colaboradores.id"))
    nombre_archivo = Column(String(200))
    ruta_archivo = Column(String(300))
    tipo = Column(String(50))

    colaborador = relationship("Colaborador", back_populates="documentos")

# ======================================
# CREAR TABLAS
# ======================================
Base.metadata.create_all(engine)

# ======================================
# CARGA INICIAL
# ======================================
def cargar_datos():
    db = Session()
    if db.query(Area).count() > 0:
        db.close()
        return

    areas_puestos = {
        "Administración": ["Gerente","Coordinador","Analista","Auxiliar"],
        "Comercial": ["Asesor","Asesor externo","Gerente ventas"],
        "Tecnologías de la Información": ["Soporte TI","Desarrollador","Analista BI"]
    }

    recursos = ["Laptop","PC","Celular","Tableta"]
    programas = ["Paquetería 365","Chrome","Adobe","Ringover"]

    for nombre_area, puestos in areas_puestos.items():
        area = Area(
            nombre=nombre_area,
            nombre_normalizado=normalizar_texto(nombre_area)
        )
        db.add(area)
        db.flush()

        for p in puestos:
            db.add(Puesto(nombre=p, area_id=area.id))

    for r in recursos:
        db.add(RecursoTI(nombre=r))

    for p in programas:
        db.add(Programa(nombre=p))

    db.commit()
    db.close()

cargar_datos()

# ======================================
# FORMULARIO
# ======================================
@app.route("/", methods=["GET","POST"])
def alta():
    db = Session()
    areas = db.query(Area).all()
    recursos = db.query(RecursoTI).all()
    programas = db.query(Programa).all()

    if request.method == "POST":
        area = db.get(Area, int(request.form["area"]))
        es_comercial = "comercial" in area.nombre_normalizado

        col = Colaborador(
            nombre=request.form.get("nombre"),
            apellido=request.form.get("apellido"),
            correo=request.form.get("correo"),
            edad=request.form.get("edad") or None,
            estado_civil=request.form.get("estado_civil"),
            domicilio=request.form.get("domicilio"),
            telefono=request.form.get("telefono"),
            rfc=request.form.get("rfc"),
            curp=request.form.get("curp"),
            nss=request.form.get("nss"),
            fecha_alta=datetime.strptime(
                request.form.get("fecha_alta"), "%Y-%m-%d"
            ),
            sueldo=request.form.get("sueldo") or None,
            comentarios=request.form.get("comentarios"),
            rol_comercial=request.form.get("rol_comercial") if es_comercial else None,
            comisionista=request.form.get("comisionista") == "Sí" if es_comercial else None,
            tiene_infonavit=request.form.get("infonavit") == "Sí",
            infonavit_credito=request.form.get("infonavit_credito"),
            tiene_fonacot=request.form.get("fonacot") == "Sí",
            fonacot_credito=request.form.get("fonacot_credito"),
            area_id=area.id,
            puesto_id=int(request.form.get("puesto"))
        )

        db.add(col)
        db.commit()  # NECESARIO PARA ID

        # ===== RECURSOS TI =====
        for rid in request.form.getlist("equipo[]"):
            recurso = db.get(RecursoTI, int(rid))
            if recurso:
                col.recursos.append(recurso)

        # ===== PROGRAMAS =====
        for pid in request.form.getlist("programas[]"):
            programa = db.get(Programa, int(pid))
            if programa:
                col.programas.append(programa)

        # ===== DOCUMENTOS =====
        carpeta = os.path.join(
            app.config["UPLOAD_FOLDER"],
            f"colaborador_{col.id}"
        )
        os.makedirs(carpeta, exist_ok=True)

        for f in request.files.getlist("documentos[]"):
            if f and f.filename:
                nombre = secure_filename(f.filename)
                ruta = os.path.join(carpeta, nombre)
                f.save(ruta)

                db.add(Documento(
                    colaborador_id=col.id,
                    nombre_archivo=nombre,
                    ruta_archivo=ruta,
                    tipo="General"
                ))

        db.commit()
        db.close()
        return redirect(url_for("dashboard"))

    return render_template(
        "alta_colaborador.html",
        areas=areas,
        recursos=recursos,
        programas=programas
    )

# ======================================
# PUESTOS
# ======================================
@app.route("/puestos/<int:area_id>")
def puestos_por_area(area_id):
    db = Session()
    puestos = db.query(Puesto).filter_by(area_id=area_id).all()
    return jsonify([{"id":p.id,"nombre":p.nombre} for p in puestos])

# ======================================
# DASHBOARD
# ======================================
@app.route("/dashboard")
def dashboard():
    db = Session()
    colaboradores = db.query(Colaborador).all()
    total = db.query(Colaborador).count()
    return render_template(
        "dashboard.html",
        colaboradores=colaboradores,
        total=total
    )

# ======================================
# VER DOCUMENTO
# ======================================
@app.route("/documento/<int:id>")
def ver_documento(id):
    db = Session()
    doc = db.get(Documento, id)
    return send_file(doc.ruta_archivo)

# ======================================
# MAIN
# ======================================
if __name__ == "__main__":
    app.run(debug=True)
