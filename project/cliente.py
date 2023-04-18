import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from sqlalchemy import and_, func, text
from . import db
from project.models import DetPedido, Pedido, Producto, Products, Role
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler
from datetime import date, datetime

cliente = Blueprint('cliente', __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('flask.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

@cliente.route('/principalAd',methods=["GET","POST"])
@login_required
def principalAd():
    productos = Products.query.all()

    if len(productos) == 0:
        productos = 0
    
    print(current_user.admin)

    return render_template('principalAd.html', productos=productos)

@cliente.route('/pedidos',methods=["GET","POST"])
@login_required
def pedidos():
    
    ids_pedidos = Pedido.query.with_entities(Pedido.id).filter_by(user_id= current_user.id).all()
    detPed = DetPedido.query.filter(DetPedido.pedido_id.in_([id_pedido[0] for id_pedido in ids_pedidos])).all()
    producto_ids = [dp.producto_id for dp in detPed]

    # Hacer la consulta para obtener solo los productos con las IDs correspondientes
    productos = Producto.query.filter(Producto.id.in_(producto_ids)).all()
    
    if request.method == 'POST':
        #Datos del pedido
        userID = current_user.id
        cantidad = request.args.get('cantidad')
        fecha_actual = date.today()
        fecha_actual_str = fecha_actual.strftime('%Y-%m-%d')
        #obten la fecha actual sin la hora
        # 1 Es pedido , 2 es compra y 0 es eliminado
        estatus = 1
        print(userID)
        pedido = Pedido(user_id = userID,
                        cantidad = cantidad,
                        fecha = fecha_actual_str,
                        estatus = estatus)
        db.session.add(pedido)
        db.session.commit()
        
        #Datos del detalle del pedido
        consPedido = Pedido.query.filter_by(id=pedido.id).first()
        if consPedido:
            id_obtenido = consPedido.id
        pedidoID = id_obtenido
        productoID = request.args.get('idProducto')
        cantidad = pedido.cantidad
                 
        detPed = DetPedido(pedido_id = pedidoID, producto_id = productoID,cantidad = cantidad)
        db.session.add(detPed)
        db.session.commit()
        return redirect(url_for('cliente.catalogoC'))
    
    return render_template('./pedidos/pedidos.html', detPed = detPed, productos = productos)

@cliente.route('/eliminarPedido',methods=["GET","POST"])
@login_required
def eliminarPedido():
    idPedido = request.args.get('id')
    detPed = DetPedido.query.filter_by(pedido_id=idPedido).first()
    if request.method == 'POST':
        pedido = Pedido.query.filter_by(id=idPedido).first()
        pedido.estatus = 0
        db.session.commit()
        return redirect(url_for('cliente.pedidos'))
    
    return render_template('./pedidos/eliminarPedido.html', detPed = detPed)
#arreglar buscar pedido
@cliente.route('/buscarPedido',methods=["GET","POST"])
@login_required
def buscarPedido():
    ids_pedidos = Pedido.query.with_entities(Pedido.id).filter_by(user_id= current_user.id).all()
    detPed = DetPedido.query.filter(DetPedido.pedido_id.in_([id_pedido[0] for id_pedido in ids_pedidos])).all()
    
    if request.method == 'POST':   
        search_term = request.form.get('search')
        detPedR = DetPedido.query.filter(DetPedido.pedido_id.ilike(f'%{search_term}%')).first()                      
        if not detPed:
            flash("El pedido no existe", "error")
            return redirect(url_for('cliente.pedidos'))
        return render_template('./pedidos/pedidos.html', detPed = detPedR)
    
    return render_template('./pedidos/pedidos.html', detPed = detPed)

@cliente.route('/catalogoC',methods=["GET","POST"])
def catalogoC():

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

    return render_template('catalogoCliente.html', productos_por_modelo = productos_por_modelo, otrosAtributos = otrosAtributos)

@cliente.route('/verModelos',methods=["GET","POST"])
def verModelos():
        prods = Producto.query.filter(
            Producto.modelo == request.args.get('modelo')
            ).group_by(Producto.color).all() 
               
        return render_template('catalogoPorModelo.html', productos = prods)

@cliente.route('/verProducto',methods=["GET","POST"])
def verProducto():
    if request.method == 'POST':

        prods = Producto.query.filter(and_(Producto.modelo == request.args.get('modelo'), 
                                    Producto.color == request.args.get('color'))).all()

        print(request.args.get('modelo'), request.args.get('color'))
        color = request.args.get('color')
        return render_template('productoDetalle.html', productos = prods, color = color)
    
@cliente.route('/filtrarProducto',methods=["GET","POST"])
def filtrarProducto():    
    if request.method == 'POST':   
        nombre = request.args.get('nombre')
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
    return render_template('catalogoClienteFiltrado.html', productos_por_modelo = productos_por_modelo, otrosAtributos = otrosAtributos)


