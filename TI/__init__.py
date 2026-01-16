from flask import Blueprint

ti_bp = Blueprint(
    'ti',  # Nombre del blueprint
    __name__,  # Nombre del módulo
    template_folder='templates',  # Flask buscará en ti/templates/
    static_folder='static',  # Flask buscará en ti/static/
    static_url_path='/ti/static'  # URL para archivos estáticos
)

# Importar rutas después de crear el blueprint
from . import routes