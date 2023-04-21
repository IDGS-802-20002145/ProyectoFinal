import os 
import uuid
import base64, json
from operator import or_
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app, make_response, send_file
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from ..models import db
from .. import userDataStore, db
from .proveedores import insertar_proveedor, modificar_proveedor_get, modificar_proveedor_post, eliminar_proveedor_get, eliminar_proveedor_post
from project.models import  Producto, Role, User, InventarioMateriaPrima, ExplotacionMaterial, Proveedor,DetCompra,Compra, DetVenta, Venta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash 
import pandas as pd
from itertools import groupby
import cufflinks as cf
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import plotly.graph_objs as go
import io 
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO
import matplotlib
from sqlalchemy import func
matplotlib.use('Agg')


def ad_post():
    # Obtener los datos del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        talla = request.form['talla']
        color = request.form['color']
        modelo = request.form['modelo']
        precio = request.form['precio']
        img = str(uuid.uuid4()) + '.png'
        imagen = request.files['imagen']
        ruta_imagen = os.path.abspath('project\\static\\img')
        imagen.save(os.path.join(ruta_imagen, img))
        stock_existencia = request.form['stock_existencia']
        materiales=request.form.getlist('materiales')
        cantidad_usada = list(filter(bool, request.form.getlist('cantidad_usada[]')))
        print(materiales)
        print (cantidad_usada)
        cantidades_individuales = cantidad_usada
        print (cantidades_individuales)
        inventarioM=InventarioMateriaPrima.query.all()
        print (inventarioM)
        # Validar que se haya escogido al menos un material
        if not materiales or not cantidad_usada:
            flash("Debe escoger al menos un material para crear el producto.", "error")
            return redirect(url_for('main.principalAd'))
        
        # Actualizar el inventario de los materiales utilizados en la creación del producto
        cantidad_utilizada_por_material = {}
        for material_id, cantidad_utilizada, cantidadesIndi in zip(materiales, cantidad_usada, cantidades_individuales):
            if cantidad_utilizada:
                cantidad_utilizada_por_material[int(material_id)] = (float(cantidad_utilizada), float(cantidadesIndi))
                print(f"Material: {material_id}, Cantidad utilizada: {cantidad_utilizada}, Cantidad individual: {cantidadesIndi}")

        for material_id, (cantidad_utilizada, cantidadesIndi) in cantidad_utilizada_por_material.items():
            materiales = InventarioMateriaPrima.query.filter_by(id=material_id).all()
            if not materiales:
                flash("No existe el material en el inventario.", "error")
                return redirect(url_for('main.principalAd'))
            for material in materiales:
                if material is None:
                    db.session.rollback()
                    flash(f"No se encontró el material con la identificación {material_id}.", "error")
                    return redirect(url_for('main.principalAd'))
                if material.cantidad < cantidad_utilizada:
                    db.session.rollback()
                    flash(f"No hay suficiente cantidad de {material.nombre} para crear el producto.", "error")
                    return redirect(url_for('main.principalAd'))
                
                if cantidadesIndi < 0:
                    db.session.rollback()
                    flash(f"La cantidad utilizada de {material.nombre} no puede ser negativa.", "error")
                    return redirect(url_for('main.principalAd'))
                print(materiales)
            
        # Crear una instancia del objeto Producto con los datos recibidos
        nuevo_producto = Producto(nombre=nombre, descripcion=descripcion, talla=talla, color=color, modelo=modelo,
                                        precio=precio, imagen=img, stock_existencia=stock_existencia)
        # Agregar el nuevo producto a la sesión de la base de datos
        db.session.add(nuevo_producto)
        
        # Obtener el objeto Producto creado en la sesión de la base de datos
        producto = db.session.query(Producto).order_by(Producto.id.desc()).first()
        print(f"Producto: {producto.id}")    
        for material_id, (cantidad_utilizada, cantidadesIndi) in cantidad_utilizada_por_material.items():
            materiales = InventarioMateriaPrima.query.filter_by(id=material_id).all()
            for material in materiales:
                #crea una validacion para que no se pueda crear un producto cuando el material se encuentre en su minimo
                if material.cantidad <= material.stock_minimo:
                    flash(f"No se puede crear el producto porque el material {material.nombre} se encuentra en su minimo.", "error")
                    db.session.rollback()
                    return redirect(url_for('main.principalAd'))
                
                cantidad_utilizada_total = cantidad_utilizada * float(stock_existencia)
                print ("Esta es la cantidad total utilizada -----------------"+str(cantidad_utilizada_total))
                if cantidad_utilizada_total > material.cantidad:
                    db.session.rollback()
                    flash(f"No hay suficiente cantidad de {material.nombre} para crear el producto.", "error")
                    return redirect(url_for('main.principalAd'))
                
                if cantidad_utilizada_total < 0:
                    db.session.rollback()
                    flash(f"La cantidad utilizada de {material.nombre} no puede ser negativa.", "error")
                    return redirect(url_for('main.principalAd'))
                
                explotacion_material = ExplotacionMaterial(producto_id=producto.id, material_id=material.id, cantidad_usada=cantidad_utilizada_total, cantidadIndividual=cantidadesIndi)
                db.session.add(explotacion_material)
                db.session.commit()  # guardar cambios aquí

                material.cantidad -= cantidad_utilizada_total
                db.session.add(material)

                # Mensaje de depuración
                print(f"Producto: {producto.id}, Material: {material_id}, Cantidad utilizada: {cantidad_utilizada_total}")

        # Guardar los cambios en la sesión de la base de datos
        db.session.commit()

        #Redirigir al administrador a la página principal del panel de control
        flash("El producto ha sido agregado exitosamente.", "success")
        return redirect(url_for('main.principalAd'))
    


def modificar_producto_get(producto):
        materiales = InventarioMateriaPrima.query.all()
        explotacion = ExplotacionMaterial.query.filter_by(producto_id=producto.id).all()
        cantidades = {exp.material_id: exp.cantidadIndividual for exp in explotacion}

        return render_template('modificar.html', producto=producto, id=id, 
                            materiales=materiales, explotacion=explotacion, 
                            cantidades=cantidades)

def modificar_poducto(producto):
        producto.nombre = request.form.get('nombre')
        producto.descripcion = request.form.get('descripcion')
        producto.talla = request.form.get('talla')
        producto.color = request.form.get('color')
        producto.modelo = request.form.get('modelo')
        producto.precio = request.form.get('precio')
        producto.stock_existencia = request.form.get('stock')
        print (producto.stock_existencia)
        imagen = request.files.get('imagen')
        ruta_imagen = os.path.abspath('project\\static\\img')
        
        if imagen:
            # Eliminar la imagen anterior
            os.remove(os.path.join(ruta_imagen, producto.imagen))
            # Guardar la nueva imagen
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(ruta_imagen, filename))
            producto.imagen = filename
        db.session.commit()
        flash("El registro se ha modificado exitosamente.", "success")
        return redirect(url_for('main.principalAd'))
    
    
def actualizar_stock_post(producto, materialesU, cantidades_individuales, cantidad_usada):
        nuevo_stock = request.form.get('cantidad')
        stock_anterior = producto.stock_existencia
        print ("este es el stock anterior----------------------------", stock_anterior)
        # Actualizar el inventario de los materiales utilizados en la creación del producto
        cantidad_utilizada_por_material = {}
        for material_id, cantidad_utilizada, cantidadesIndi in zip(materialesU, cantidad_usada, cantidades_individuales):
            if cantidad_utilizada:
                cantidad_utilizada_por_material[int(material_id)] = (float(cantidad_utilizada), float(cantidadesIndi))
                print(f"Material: {material_id}, Cantidad utilizada: {cantidad_utilizada}, Cantidad individual: {cantidadesIndi}")

        for material_id, (cantidad_utilizada, cantidadesIndi) in cantidad_utilizada_por_material.items():
            materiales = InventarioMateriaPrima.query.filter_by(id=material_id).all()
            if not materiales:
                flash("No existe el material en el inventario.", "error")
                return redirect(url_for('main.principalAd'))
            for material in materiales:
                if material is None:
                    flash(f"No se encontró el material con la identificación {material_id}.", "error")
                    return redirect(url_for('main.principalAd'))
                if material.cantidad < cantidad_utilizada:
                    flash(f"No hay suficiente cantidad de {material.nombre} para crear el producto.", "error")
                    return redirect(url_for('main.principalAd'))
                
                if cantidadesIndi < 0:
                    flash(f"La cantidad utilizada de {material.nombre} no puede ser negativa.", "error")
                    return redirect(url_for('main.principalAd'))
                print("estos son los materiales", materiales)
        # Actualizar el stock del producto
        print("este es el stock anterior" + str(stock_anterior))	
        print("este es el nuevo stock" + str(nuevo_stock))
        producto.stock_existencia += int(nuevo_stock)
        print("esta es la suma" + str(producto.stock_existencia))
        db.session.add(producto)
        for material_id, (cantidad_utilizada, cantidadesIndi) in cantidad_utilizada_por_material.items():
            materiales = InventarioMateriaPrima.query.filter_by(id=material_id).all()
            
            for material in materiales:
                cantidad_utilizada_total = cantidad_utilizada * float(nuevo_stock)
                
                if cantidad_utilizada_total > material.cantidad:
                    flash(f"No hay suficiente cantidad de {material.nombre} para crear el producto.", "error")
                    return redirect(url_for('main.principalAd'))
                
                if cantidad_utilizada_total < 0:
                    flash(f"La cantidad utilizada de {material.nombre} no puede ser negativa.", "error")
                    return redirect(url_for('main.principalAd'))
                
                #crea una validacion para que no se pueda crear un producto cuando el material se encuentre en su minimo
                if material.cantidad <= material.stock_minimo:
                    flash(f"No se puede crear el producto porque el material {material.nombre} se encuentra en su minimo.", "error")
                    return redirect(url_for('main.principalAd'))
                
                explotacion_material = ExplotacionMaterial(producto_id=producto.id, material_id=material.id, cantidad_usada=cantidad_utilizada_total, cantidadIndividual=cantidadesIndi)
                db.session.add(explotacion_material)

                material.cantidad -= cantidad_utilizada_total
                db.session.add(material)
        
        # Guardar los cambios en la sesión de la base de datos
        db.session.commit()
        flash("El stock se actualizó con éxito", "success")
        return redirect(url_for('main.principalAd'))