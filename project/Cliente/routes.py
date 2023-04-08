import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from ..models import db
from project.models import Pedido, Producto, DetPedido, Venta, DetVenta
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


cliente = Blueprint('cliente', __name__)

###################### Modulo de pedidos ######################

@cliente.route('/pedidos', methods=['GET', 'POST'])
@login_required
def pedidos(): 
    if request.method == 'GET':
        pedidos = Pedido.query.filter_by(user_id=current_user.id).all() 
    return render_template('pedidos.html', pedidos=pedidos)

@cliente.route('/detallePedido', methods=['GET', 'POST'])
@login_required
def detallePedido():
    if request.method == 'GET':
        id = request.args.get('id')
        pedido = Pedido.query.filter_by(id=id, estatus=1).first()
        productos = DetPedido.query.filter_by(pedido_id=id).all()        
        detProductos = []
        for producto in productos:
            prod = Producto.query.filter_by(id=producto.producto_id).first()
            detProductos.append(prod)
    return render_template('detallePedido.html', pedido=pedido, productos=productos, detProductos=detProductos)


##############################################################



###################### Modulo de ventas ######################

@cliente.route('/pagar', methods=['GET', 'POST'])
@login_required
def pagar():       
    id = request.args.get('id') 
    pedido = Pedido.query.filter_by(id=id, estatus=1).first()
    productos = DetPedido.query.filter_by(pedido_id=id).all()        
    detProductos = []
    total = 0
    for producto in productos:
         prod = Producto.query.filter_by(id=producto.producto_id).first()
         total+=prod.precio * producto.cantidad
         prod.cantidad = producto.cantidad
         print(prod.cantidad)
         detProductos.append(prod)
   
    return render_template('pagar.html', pedido=pedido, productos=productos, detProductos=detProductos, total=total)


    






##############################################################