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


administrador = Blueprint('administrador', __name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('flask.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


# Definimos la ruta para la página de perfil de usuairo
@administrador.route('/administrador')
@login_required
@roles_required('admin')
def admin():
    productos = Producto.query.filter_by(estatus=1).all()
    materiales = InventarioMateriaPrima.query.all()
    print(materiales)
    return render_template('RopaCrud.html', productos=productos,materiales=materiales, enumerate=enumerate)


@administrador.route('/administrador', methods=['POST'])
@login_required
@roles_required('admin')
def admin_post():
    if request.method == 'POST':
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
    

@administrador.route('/modificar', methods=['GET', 'POST'])
@login_required
def modificar():
    id = request.args.get('id')
    producto = Producto.query.get(id)
    if producto is None:
        flash("El producto no existe", "error")
        return redirect(url_for('main.admin'))
    if not producto.imagen:
        producto.imagen = 'default.png' # o cualquier otro valor predeterminado para la imagen
    if request.method == 'POST':
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
    
    elif request.method == 'GET':
        materiales = InventarioMateriaPrima.query.all()
        explotacion = ExplotacionMaterial.query.filter_by(producto_id=producto.id).all()
        cantidades = {exp.material_id: exp.cantidadIndividual for exp in explotacion}

        return render_template('modificar.html', producto=producto, id=id, 
                            materiales=materiales, explotacion=explotacion, 
                            cantidades=cantidades)


@administrador.route('/actualizarStock', methods=['GET', 'POST'])
@login_required
def actualizarStock():
    id = request.args.get('id')
    producto = Producto.query.get(id)
    materialesU = request.form.getlist('materiales')
    cantidad_usada = list(filter(bool, request.form.getlist('cantidad_usada[]')))
    cantidades_individuales = cantidad_usada
    print (cantidad_usada)
    
    if producto is None:
        flash("El producto no existe", "error")
        return redirect(url_for('main.admin'))
    
    if request.method == 'POST':
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
    
    elif request.method == 'GET':
        materiales = InventarioMateriaPrima.query.all()
        explotacion = ExplotacionMaterial.query.filter_by(producto_id=producto.id).all()
        cantidades = {exp.material_id: exp.cantidadIndividual for exp in explotacion}

    return render_template('actualizarStock.html', producto=producto, id=id, 
                            materiales=materiales, explotacion=explotacion, 
                            cantidades=cantidades)





@administrador.route('/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar():
    id = request.args.get('id')
    producto = Producto.query.get(id)
    if producto is None:
        flash("El producto no existe", "error")
        return redirect(url_for('administrador.admin'))
    if request.method == 'POST':
        producto.estatus = 0
        db.session.add(producto)
        db.session.commit()
        flash("El registro se ha eliminado exitosamente.", "success")
        return redirect(url_for('main.principalAd'))
    elif request.method == 'GET':
        materiales = InventarioMateriaPrima.query.all()
        print(producto.explotacion_material)
        explotacion= ExplotacionMaterial.query.all()
        return render_template('eliminar.html', producto=producto, id=id)
    

###################### Modulo de inventarios ######################


@administrador.route('/inventarios', methods=['GET', 'POST'])
@login_required
def inventarios():  
    materiales= InventarioMateriaPrima.query.filter_by(estatus=1).all()
    print(materiales)
    td_style = ""
    td_style2=""
    for material in materiales:
        if material.cantidad <= material.stock_minimo:
            td_style = "bg-danger"
            td_style2 = "fas fa-grimace"  
        elif material.cantidad > material.stock_minimo:
            td_style = "bg-primary"
            td_style2 ="fas fa-grin-alt"
    return render_template('inventarios.html', materiales=materiales,td_style=td_style,td_style2=td_style2)




###################### Modulo de Compras ######################

#FUNCIONES PARA EL MODULO DE COMPRAS
@administrador.route('/compras', methods=['GET', 'POST'])
@login_required
def compras():
    id = request.args.get('id')
    if request.method == 'GET':
        materiales = InventarioMateriaPrima.query.all()
        proveedores = Proveedor.query.all()
        return render_template('compras.html', materiales=materiales, id=id, proveedores=proveedores)
    elif request.method == 'POST':
        material = InventarioMateriaPrima.query.get(id)
        proveedor = request.form.get('proveedor')
        cantidad = request.form.get('cantidad')
        fecha = request.form.get('fecha')
        precio= request.form.get('precio')
        compra = Compra(proveedor_id=proveedor, fecha=fecha, estatus=0)
        db.session.add(compra)
        
        # Obtener el objeto Producto creado en la sesión de la base de datos
        compraNow = db.session.query(Compra).order_by(Compra.id.desc()).first()
        print(f"Producto: {compraNow.id}")
        # Crear un nuevo objeto CompraMaterial para cada material comprado
        materialC= DetCompra(compra_id=compraNow.id, material_id=material.id, cantidad=cantidad, precio=precio)
        db.session.add(materialC)
        db.session.commit()
        
        flash("La compra esta pendiente por revisar", "warning")
        return redirect(url_for('administrador.inventarios'))

@administrador.route('/catalogoCompras', methods=['GET', 'POST'])
@login_required
def catalogoCompras():

    fecha = request.form.get('fecha')
    fechaR= request.form.get('fechaR')
    conteoComprasR=0
    conteoComprasP=0
    comprasP = False
    comprasR = False
    
    if request.method == 'POST' and 'confirmar' in request.form:
        idCompra = request.form.get('idCompra')
        idMaterial = request.form.get('idMaterial')
        cantidad = request.form.get('cantidad')
    
        material= InventarioMateriaPrima.query.get(idMaterial)
        compra = Compra.query.get(idCompra)
        compra.estatus = 1
        db.session.add(compra)
        # Aumentar la cantidad de material en el inventario correspondiente
        material.cantidad += int(cantidad)
        db.session.add(material)
        db.session.commit()
        flash("Compra realizada con exito", "success")
        return redirect(url_for('administrador.inventarios', id=idCompra, idM=idMaterial, cant=cantidad))
    if request.method == 'GET':
        compras = db.session.query(Compra, DetCompra, InventarioMateriaPrima, Proveedor)\
                    .join(DetCompra, Compra.id == DetCompra.compra_id)\
                    .outerjoin(InventarioMateriaPrima, DetCompra.material_id == InventarioMateriaPrima.id)\
                    .join(Proveedor, Compra.proveedor_id == Proveedor.id)\
                    .filter(Compra.estatus==0)\
                    .all()
        conteoComprasR= Compra.query.filter_by(estatus=1).count()
        comprasRealizadas = db.session.query(Compra, DetCompra, InventarioMateriaPrima, Proveedor)\
                    .join(DetCompra, Compra.id == DetCompra.compra_id)\
                    .outerjoin(InventarioMateriaPrima, DetCompra.material_id == InventarioMateriaPrima.id)\
                    .join(Proveedor, Compra.proveedor_id == Proveedor.id)\
                    .filter(Compra.estatus==1)\
                    .all()
        conteoComprasP= Compra.query.filter_by(estatus=0).count()
        return render_template('catalogoCompras.html', compras=compras,
                        comprasRealizadas=comprasRealizadas,conteoComprasR=conteoComprasR,
                        conteoComprasP=conteoComprasP,comprasP=comprasP,comprasR=comprasR)





###################### Modulo de Materia Prima ######################

@administrador.route('/materiales', methods=['GET', 'POST'])
@login_required
def materiales():
    if request.method == 'GET':
        materiales= InventarioMateriaPrima.query.all()
        return render_template('MateriaPrimaCrud.html', materiales=materiales)
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        cantidad = request.form.get('cantidad')
        stock_minimo = request.form.get('stock_minimo')
        material = InventarioMateriaPrima(nombre=nombre, descripcion=descripcion, cantidad=cantidad, stock_minimo=stock_minimo)
        db.session.add(material)
        db.session.commit()
        flash("El material ha sido agregado exitosamente.", "success")
        return redirect(url_for('administrador.inventarios'))
    
@administrador.route('/modificarMaterial', methods=['GET', 'POST'])
@login_required
def modificarMaterial():
    id = request.args.get('id')
    material = InventarioMateriaPrima.query.get(id)
    if material is None:
        flash("El material no existe", "error")
        return redirect(url_for('administrador.inventarios'))
    if request.method == 'POST':
        material.nombre = request.form.get('nombre')
        material.descripcion = request.form.get('descripcion')
        material.cantidad = request.form.get('cantidad')
        material.stock_minimo = request.form.get('stock_minimo')
        db.session.add(material)
        db.session.commit()
        flash("El registro se ha modificado exitosamente.", "success")
        return redirect(url_for('administrador.inventarios'))
    elif request.method == 'GET':
        return render_template('modificarMateriaPrima.html', material=material, id=id)

@administrador.route('/eliminarMaterial', methods=['GET', 'POST'])
@login_required
def eliminarMaterial():
    id = request.args.get('id')
    material = InventarioMateriaPrima.query.get(id)
    if material is None:
        flash("El material no existe", "error")
        return redirect(url_for('administrador.inventarios'))
    if request.method == 'POST':
        material.estatus = 0
        db.session.add(material)
        db.session.commit()
        flash("El registro se ha eliminado exitosamente.", "success")
        return redirect(url_for('administrador.inventarios'))
    elif request.method == 'GET':
        return render_template('eliminarMateriaPrima.html', material=material, id=id)



###################### Modulo de proveedores ######################
    
@administrador.route('/proveedores', methods=['GET'])
@login_required
def proveedores():   
    proveedores = Proveedor.query.filter_by(active=1).all()
    return render_template('proveedores.html', proveedores=proveedores)

@administrador.route('/insertar_prov', methods=['GET','POST'])
@login_required
def proveedores_insertar():
    if request.method == 'POST':
       return insertar_proveedor()
    return render_template('insertar_proveedor.html')

@administrador.route('/modificar_prov', methods=['GET','POST'])
@login_required
def modificar_prov():
    if request.method == 'GET':
        return modificar_proveedor_get()
    elif request.method == 'POST':
       return modificar_proveedor_post()
    
@administrador.route('/eliminar_prov', methods=['GET','POST'])
@login_required
def eliminar_prov():
    if request.method == 'GET':
        return eliminar_proveedor_get()
    elif request.method == 'POST':
       return eliminar_proveedor_post()
    
##################################################################



################################### Gestion de Usuarios #############################



@administrador.route('/getAllUsers',methods=["GET","POST"])
@login_required
def getAllUsers():
    users = User.query.all()

    if len(users) == 0:
        users = 0
    return render_template('users.html', users=users)

@administrador.route('/addUser', methods=['GET','POST'])
@login_required
def addUser():   
    if request.method == 'POST':
        
        email=request.form.get('txtEmailUser')
        name=request.form.get('txtNombreUser')
        password=request.form.get('txtContrasenaUser')
        
        #consultamos si existe un usuario ya registrado con ese email.
        user=User.query.filter_by(email=email).first()
        
        if user:
           # logger.info('Registro denagado, el correo: '+ email +' ya fue registrado anteriormente' + ' '+ fecha_actual)
            flash('Ese correo ya esta en uso')
            return redirect(url_for('auth.register'))
        
        #Creamos un nuevo usuario y lo guardamos en la bd.
        #new_user=User(email=email,name=name,password=generate_password_hash(password,method='sha256'))
        
        userDataStore.create_user(name=name,email=email,password=generate_password_hash(password,method='sha256'))
        
        db.session.commit()
        #logger.info('Usuario(cliente) registrado: '+ email + ' el dia '+ fecha_actual)
        
        if request.form.get('rolUser') == 'cliente':
            try:
                
                print(email)
                connection = db.engine.raw_connection()
                cursor = connection.cursor()
                cursor.callproc('agregarCliente', [email])  

                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('administrador.getAllUsers'))
                    
            except Exception as ex:
                        print(ex)
        else:
            try:
                print(email)
                connection = db.engine.raw_connection()
                cursor = connection.cursor()
                cursor.callproc('agregarEmpleado', [email])  

                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('administrador.getAllUsers'))
                    
            except Exception as ex:
                        print(ex)
    else:
        return render_template('agregarUser.html')
    
@administrador.route('/updateUser', methods=['GET','POST'])
@login_required
def updateUser():
    id = request.args.get('id')
    user = User.query.get(id)        
    
    if request.method == 'POST':   
        user.name = request.form.get('txtNombreUser')
        user.email = request.form.get('txtEmailUser')
        user.password = request.form.get('txtContrasenaUser')
        
        nCont = request.form.get('txtNuevaCont')
        if nCont != '':
            user.password = generate_password_hash(request.form.get('txtNuevaCont'),method='sha256')                      
    
        if request.form.get('rolUser') == '0':
            user.empleado = False
        else:
            user.empleado = True
            
        db.session.commit()
        
        if user.empleado:
            try:  
                print("Se intenta cambiar a empleado")   
                print(user.id)               
                connection = db.engine.raw_connection()
                cursor = connection.cursor()
                cursor.callproc('cambiarAEmp', [int(user.id)])  
                
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('administrador.getAllUsers'))
                        
            except Exception as ex:
                print(ex)
        else:
            try:
                print(user.id)
                print("Se intenta cambiar a cliente")                   
                connection = db.engine.raw_connection()
                cursor = connection.cursor()
                cursor.callproc('cambiarACli', [int(user.id)])  
                 
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('administrador.getAllUsers'))
                        
            except Exception as ex:
                print(ex)
        return redirect(url_for('administrador.getAllUsers'))
    
    return render_template('modificarUser.html', user = user)

@administrador.route('/deleteUser', methods=['GET','POST'])
@login_required 
def deleteUser():
    id = request.args.get('id')
    user = User.query.get(id)        
    
    if request.method == 'POST':   
        user.active = False            
        db.session.commit()
        return redirect(url_for('administrador.getAllUsers'))
        
        
    return render_template('eliminarUser.html', user = user)

@administrador.route('/findUser', methods=['GET','POST'])
@login_required
def findUser():
    if request.method == 'POST':   
        search_term = request.form.get('search')
        users = User.query.filter(or_(User.name.ilike(f'%{search_term}%'),
                                      User.email.ilike(f'%{search_term}%'))).all()
        if not users:
            flash("El usuario no existe", "error")
            return redirect(url_for('main.getAllUsers'))
        return render_template('users.html', users=users)
    else:
        return redirect(url_for('administrador.getAllUsers'))


################################################################################




################################### Gestion de Finanzas #############################

@administrador.route("/finanzas", methods=['GET','POST'])
@login_required
def finanzas():
    ventas = db.session.query(func.sum(DetVenta.cantidad * DetVenta.precio).label('total'), 
                              func.date_trunc('month', Venta.fecha).label('mes')).join(Venta).group_by('mes').all()
    fechas = [venta.mes.strftime("%b-%Y") for venta in ventas]
    totales = [venta.total for venta in ventas]

    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(fechas, totales)
    axis.set_xlabel("Fechas")
    axis.set_ylabel("Ventas totales")

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'

    return render_template('finanzas.html', response=response)



#####################################################################################

################################### Gestion de Ventas #############################

@administrador.route('/ventas', methods=['GET', 'POST'])
@login_required
def ventas_por_aprobar():
    # Obtener ventas pendientes
    ventas_pendientes = db.session.query(Venta, User).\
        join(User, Venta.user_id == User.id).\
        filter(Venta.estatus == 0).all()

    conteo_ventas_pendientes= db.session.query(func.count()).filter(Venta.estatus == 0).scalar()


    # Obtener ventas enviadas
    ventas_enviadas =  db.session.query(Venta, User).\
        join(User, Venta.user_id == User.id).\
        filter(Venta.estatus == 1).all()
        
    conteo_ventas_enviadas= db.session.query(func.count()).filter(Venta.estatus == 1).scalar()
        
    print(ventas_pendientes)

        
    if request.method == 'POST':
        id_venta = request.form.get('id')
        print(id_venta, " ID Venta")
        venta = Venta.query.filter_by(id=id_venta).first()
        venta.estatus = True        
        db.session.commit()

        flash('Se ha confirmado el envío', 'success')

        return redirect(url_for('administrador.ventas'))

    return render_template('ventas.html', ventas_pendientes=ventas_pendientes, ventas_enviadas=ventas_enviadas,
                           conteo_ventas_pendientes=conteo_ventas_pendientes, 
                           conteo_ventas_enviadas=conteo_ventas_enviadas)

@administrador.route('/detalleVenta', methods=['GET', 'POST'])
@login_required
def detalleVenta():  
    if request.method == 'GET':
        id_venta = request.args.get('id')
        estatus = request.args.get('estatus')
        print(estatus, "ESTATUS")
        detalle_ventas = db.session.query(Venta, DetVenta, Producto)\
        .join(DetVenta, Venta.id == DetVenta.venta_id)\
        .join(Producto, DetVenta.producto_id == Producto.id)\
        .filter(Venta.id == id_venta).all()

        # Creamos un diccionario para almacenar los productos y sus cantidades
        productos = {}
        for venta, det_venta, producto in detalle_ventas:
            if producto.nombre in productos and producto.talla == productos[producto.nombre]['talla']:
                productos[producto.nombre]['cantidad'] += det_venta.cantidad
                productos[producto.nombre]['precio'] += det_venta.precio
            else:
                productos[producto.nombre] = {
                    'talla': producto.talla,
                    'color': producto.color,
                    'modelo': producto.modelo,
                    'precio': det_venta.precio,
                    'cantidad': det_venta.cantidad,
                }

        # Convertimos el diccionario a una lista para pasarlo al template
        lista_productos = []
        for nombre, producto in productos.items():
            lista_productos.append({
                'nombre': nombre,
                'talla': producto['talla'],
                'color': producto['color'],
                'modelo': producto['modelo'],
                'precio': producto['precio'],
                'cantidad': producto['cantidad'],
            })

    if request.method == 'POST':
        id_venta_post = request.form.get('idDetVent')
        print(id_venta_post, " ID Venta")
        venta = Venta.query.filter_by(id=id_venta_post).first()
        venta.estatus = True        
        db.session.commit()

        flash('Se ha confirmado el envío', 'success')

        return redirect(url_for('administrador.ventas'))

    return render_template('detalleVenta.html', detalle_ventas=lista_productos, estatus=estatus, id_venta=id_venta)







#####################################################################################