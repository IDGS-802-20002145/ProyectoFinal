import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from . import db
from project.models import Producto, Role, User, InventarioMateriaPrima, ExplotacionMaterial, Proveedor,DetCompra,Compra
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

# Definimos la ruta para la página de perfil de usuairo


@main.route('/administrador')
@login_required
@roles_required('admin')
def admin():
    productos = Producto.query.filter_by(estatus=1).all()
    materiales = InventarioMateriaPrima.query.all()
    print(materiales)
    return render_template('RopaCrud.html', productos=productos,materiales=materiales, enumerate=enumerate)


@main.route('/administrador', methods=['POST'])
def administrador():
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



@main.route('/modificar', methods=['GET', 'POST'])
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
        
@main.route('/actualizarStock', methods=['GET', 'POST'])
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

@main.route('/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar():
    id = request.args.get('id')
    producto = Producto.query.get(id)
    if producto is None:
        flash("El producto no existe", "error")
        return redirect(url_for('main.admin'))
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

# Ruta para la página principal del panel de control del administrador
@main.route('/principalAd',methods=["GET","POST"])
@login_required
def principalAd():
    productos = Producto.query.filter_by(estatus=1).all()
    
    if len(productos) == 0:
        productos = 0

    print(current_user.admin)

    return render_template('principalAd.html', productos=productos)

@main.route('/inventarios', methods=['GET', 'POST'])
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

#FUNCIONES PARA EL MODULO DE COMPRAS
@main.route('/compras', methods=['GET', 'POST'])
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
        return redirect(url_for('main.inventarios'))


@main.route('/catalogoCompras', methods=['GET', 'POST'])
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
        return redirect(url_for('main.inventarios', id=idCompra, idM=idMaterial, cant=cantidad))
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



#FUNCIONES PARA EL MODULO DE MATERIA PRIMA
@main.route('/materiales', methods=['GET', 'POST'])
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
        return redirect(url_for('main.inventarios'))
    
@main.route('/modificarMaterial', methods=['GET', 'POST'])
@login_required
def modificarMaterial():
    id = request.args.get('id')
    material = InventarioMateriaPrima.query.get(id)
    if material is None:
        flash("El material no existe", "error")
        return redirect(url_for('main.inventarios'))
    if request.method == 'POST':
        material.nombre = request.form.get('nombre')
        material.descripcion = request.form.get('descripcion')
        material.cantidad = request.form.get('cantidad')
        material.stock_minimo = request.form.get('stock_minimo')
        db.session.add(material)
        db.session.commit()
        flash("El registro se ha modificado exitosamente.", "success")
        return redirect(url_for('main.inventarios'))
    elif request.method == 'GET':
        return render_template('modificarMateriaPrima.html', material=material, id=id)
    
@main.route('/eliminarMaterial', methods=['GET', 'POST'])
@login_required
def eliminarMaterial():
    id = request.args.get('id')
    material = InventarioMateriaPrima.query.get(id)
    if material is None:
        flash("El material no existe", "error")
        return redirect(url_for('main.inventarios'))
    if request.method == 'POST':
        material.estatus = 0
        db.session.add(material)
        db.session.commit()
        flash("El registro se ha eliminado exitosamente.", "success")
        return redirect(url_for('main.inventarios'))
    elif request.method == 'GET':
        return render_template('eliminarMateriaPrima.html', material=material, id=id)

    
    