from flask import render_template, jsonify, request, flash, redirect, url_for
from . import ti_bp
import logging

logger = logging.getLogger(__name__)

# ======================================
# RUTAS PRINCIPALES DE TI
# ======================================

@ti_bp.route('/')
def index():
    """Página principal del módulo TI"""
    return render_template('ti/dashboard.html')

@ti_bp.route('/dashboard')
def dashboard():
    """Dashboard de TI"""
    return render_template('ti/dashboard.html')

@ti_bp.route('/recursos')
def recursos():
    """Gestión de recursos TI"""
    return render_template('ti/templates/dashboard_templates.html')

@ti_bp.route('/equipos')
def equipos():
    """Gestión de equipos"""
    return render_template('ti/equipos.html')

@ti_bp.route('/baja-colaboradores')
def baja_colaboradores():
    """Baja de colaboradores específica para TI"""
    return render_template('baja_colaboradores_ti.html')

# ======================================
# RUTAS PARA MODALS
# ======================================

@ti_bp.route('/modal/dashboard')
def modal_dashboard():
    """Modal del dashboard"""
    return render_template('ti/modals/dashboard_modals.html')

@ti_bp.route('/modal/agregar-equipo')
def modal_agregar_equipo():
    """Modal para agregar equipo"""
    return render_template('ti/modals/agregar_equipo_modal.html')

# ======================================
# APIS ESPECÍFICAS DE TI
# ======================================

@ti_bp.route('/api/equipos')
def api_equipos():
    """API para obtener equipos TI"""
    try:
        # Datos de ejemplo
        equipos = [
            {"id": 1, "nombre": "Laptop Dell XPS", "usuario": "Juan Pérez"},
            {"id": 2, "nombre": "PC Workstation", "usuario": "María López"}
        ]
        return jsonify({"equipos": equipos})
    except Exception as e:
        logger.error(f"Error en api_equipos: {e}")
        return jsonify({"error": str(e)}), 500

@ti_bp.route('/api/recursos')
def api_recursos():
    """API para recursos TI"""
    try:
        recursos = [
            {"id": 1, "tipo": "Software", "nombre": "Windows 10"},
            {"id": 2, "tipo": "Hardware", "nombre": "Monitor 24\""}
        ]
        return jsonify({"recursos": recursos})
    except Exception as e:
        logger.error(f"Error en api_recursos: {e}")
        return jsonify({"error": str(e)}), 500

# ======================================
# RUTAS PARA PRUEBAS
# ======================================

@ti_bp.route('/test/static')
def test_static():
    """Página para probar archivos estáticos"""
    return render_template('ti/test_static.html')

@ti_bp.route('/test/template')
def test_template():
    """Página para probar templates"""
    return render_template('ti/templates/dashboard_templates.html')