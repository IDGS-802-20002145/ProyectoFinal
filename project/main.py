import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from . import db
from project.models import Role, Producto
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('flask.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Definimos las rutas

# Definimos la ruta para la página principal
@main.route('/')
def index():
    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info('Se inicio la aplicación'+ ' el dia '+ fecha_actual)
    return render_template('index.html')





@main.route('/principalAd',methods=["GET","POST"])
@login_required
def principalAd():
    productos = Producto.query.filter_by(estatus=1).all()
    
    if len(productos) == 0:
        productos = 0

    print(current_user.admin)

    return render_template('principalAd.html', productos=productos)
