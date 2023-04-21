import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from . import db
from sqlalchemy import and_, func, text
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
    prod = Producto.query.filter(Producto.estatus == 1).all()
    modelos = db.session.query(Producto.modelo).distinct().all()
    otrosAtributos = db.session.query(
        Producto.modelo,
        func.max(Producto.imagen).label('imagen'),  # Utiliza func.max() para obtener la imagen
        func.max(Producto.nombre).label('nombre'),  # Utiliza func.max() para obtener el nombre
        func.max(Producto.precio).label('precio'),  # Utiliza func.max() para obtener el precio
        func.max(Producto.color).label('color'),  # Utiliza func.max() para obtener el color
        func.max(Producto.descripcion).label('descripcion'),  # Utiliza func.max() para obtener la descripción
        func.max(Producto.stock_existencia).label('stock_existencia'),  # Utiliza func.max() para obtener el stock_existencia
        func.max(Producto.estatus).label('estatus')  # Utiliza func.max() para obtener el estatus
    ).group_by(Producto.modelo).all()
    
    print(otrosAtributos)
    productos_por_modelo = {}
    
    for modelo in modelos:
        productos_por_modelo[modelo[0]] = []

    for producto in prod:
        modelo = producto.modelo
        productos_por_modelo[modelo].append({
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': producto.precio,
            'tallas': producto.talla,
            'stock_existencia': producto.stock_existencia
        })

    return render_template('index.html', productos_por_modelo = productos_por_modelo, otrosAtributos = otrosAtributos, prod = prod)

@main.route('/filtrarProducto',methods=["GET","POST"])
def filtrarProducto():    
    if request.method == 'POST':   
        nombre = request.args.get('nombre')
        prod2 = Producto.query.filter(Producto.estatus == 1).all()
        prod = Producto.query.filter(and_(Producto.estatus == 1),
                                     (Producto.nombre.ilike(f"%{nombre}%"))).all()
        modelos = db.session.query(
            Producto.modelo).filter(Producto.nombre.ilike(f"%{nombre}%")).distinct().all()
        print(modelos)
        otrosAtributos = db.session.query(
            Producto.modelo,
            func.max(Producto.imagen).label('imagen'),  # Utiliza func.max() para obtener la imagen
            func.max(Producto.nombre).label('nombre'),  # Utiliza func.max() para obtener el nombre
            func.max(Producto.precio).label('precio'),  # Utiliza func.max() para obtener el precio
            func.max(Producto.color).label('color'),  # Utiliza func.max() para obtener el color
            func.max(Producto.descripcion).label('descripcion'),  # Utiliza func.max() para obtener la descripción
            func.max(Producto.stock_existencia).label('stock_existencia'),  # Utiliza func.max() para obtener el stock_existencia
            func.max(Producto.estatus).label('estatus')  # Utiliza func.max() para obtener el estatus
        ).filter(Producto.nombre.ilike(f"%{nombre}%")).group_by(Producto.modelo).all()
        
        print(otrosAtributos)
        productos_por_modelo = {}
        
        for modelo in modelos:
            productos_por_modelo[modelo[0]] = []

        for producto in prod:
            modelo = producto.modelo
            productos_por_modelo[modelo].append({
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio': producto.precio,
                'tallas': producto.talla,
                'stock_existencia': producto.stock_existencia
            })
    return render_template('index_filtro.html', productos_por_modelo = productos_por_modelo, otrosAtributos = otrosAtributos,)


@main.route('/verProducto',methods=["GET","POST"])
def verProducto():
    if request.method == 'POST':

        prods = Producto.query.filter(and_(Producto.modelo == request.args.get('modelo'), 
                                    Producto.color == request.args.get('color'))).all()

        print(request.args.get('modelo'), request.args.get('color'))
        color = request.args.get('color')
        return render_template('productoDetalle.html', productos = prods, color = color)

@main.route('/verModelos',methods=["GET","POST"])
def verModelos():
     prods = Producto.query.filter(
            Producto.modelo == request.args.get('modelo')
            ).group_by(Producto.color).all()
               
     return render_template('catalogoPorModelo.html', productos = prods)

@main.route('/principalAd',methods=["GET","POST"])
@login_required
def principalAd():
    productos = Producto.query.filter_by(estatus=1).all()
    
    if len(productos) == 0:
        productos = 0

    print(current_user.admin)

    return render_template('principalAd.html', productos=productos)
