from operator import or_
import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from . import db, userDataStore
from werkzeug.security import generate_password_hash, check_password_hash
from project.models import ExplotacionMaterial, InventarioMateriaPrima, Producto, Products, Role, User
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
        
        # Validar que se haya escogido al menos un material
        if not materiales or not cantidad_usada:
            flash("Debe escoger al menos un material para crear el producto.", "error")
            return redirect(url_for('main.principalAd'))
        
        # Crear una instancia del objeto Producto con los datos recibidos
        nuevo_producto = Producto(nombre=nombre, descripcion=descripcion, talla=talla, color=color, modelo=modelo,
                                        precio=precio, imagen=img, stock_existencia=stock_existencia)
        # Agregar el nuevo producto a la sesión de la base de datos
        db.session.add(nuevo_producto)
        

        # Obtener el objeto Producto creado en la sesión de la base de datos
        producto = db.session.query(Producto).order_by(Producto.id.desc()).first()
        print(f"Producto: {producto.id}")

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
                    flash(f"No se encontró el material con la identificación {material_id}.", "error")
                    return redirect(url_for('main.principalAd'))
                if material.cantidad < cantidad_utilizada:
                    flash(f"No hay suficiente cantidad de {material.nombre} para crear el producto.", "error")
                    return redirect(url_for('main.principalAd'))
                if cantidad_utilizada < 0:
                    flash(f"La cantidad utilizada de {material.nombre} no puede ser negativa.", "error")
                    return redirect(url_for('main.principalAd'))
                if cantidadesIndi < 0:
                    flash(f"La cantidad utilizada de {material.nombre} no puede ser negativa.", "error")
                    return redirect(url_for('main.principalAd'))
                print(materiales)

                cantidad_utilizada_total = cantidad_utilizada * float(stock_existencia)
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
        imagen = request.files.get('imagen')
        ruta_imagen = os.path.abspath('project\\static\\img')
        if imagen:
            # Eliminar la imagen anterior
            os.remove(os.path.join(ruta_imagen, producto.imagen))
            # Guardar la nueva imagen
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(ruta_imagen, filename))
            producto.imagen = filename
        
        # Obtener el stock anterior y el nuevo stock
        stock_anterior = producto.stock_existencia
        nuevo_stock = request.form.get('stock_existencia')
        print(stock_anterior)

        # Calcular la cantidad de materia prima necesaria para producir el nuevo stock
        explotacion_materiales = ExplotacionMaterial.query.filter_by(producto_id=producto.id).all()
        for em in explotacion_materiales:
            cantidad_material = em.cantidadIndividual * int(nuevo_stock)
            if cantidad_material > 0:
                # Crear un nuevo objeto ExplotacionMaterial para cada material utilizado
                nuevo_em = ExplotacionMaterial(producto_id=producto.id, material_id=em.material_id,cantidad_usada=cantidad_material ,cantidadIndividual=em.cantidadIndividual)
                db.session.add(nuevo_em)

                # Disminuir la cantidad de material en el inventario correspondiente
                inventario_material = InventarioMateriaPrima.query.get(em.material_id)
                inventario_material.cantidad -= abs(cantidad_material)
                db.session

        # Actualizar el stock del producto
        producto.stock_existencia = nuevo_stock

        # Guardar todos los objetos creados y modificados
        db.session.add(producto)
        db.session.commit()
        flash("El registro se ha modificado exitosamente.", "exito")
        return redirect(url_for('main.principalAd'))
    
    elif request.method == 'GET':
        materiales = InventarioMateriaPrima.query.all()
        explotacion = ExplotacionMaterial.query.filter_by(producto_id=producto.id).all()
        cantidades = {exp.material_id: exp.cantidadIndividual for exp in explotacion}

        return render_template('modificar.html', producto=producto, id=id, 
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
        flash("El registro se ha eliminado exitosamente.", "exito")
        return redirect(url_for('main.principalAd'))
    elif request.method == 'GET':
        materiales = InventarioMateriaPrima.query.all()
        print(producto.explotacion_material)
        explotacion= ExplotacionMaterial.query.all()
        return render_template('eliminar.html', producto=producto, id=id)


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
    materiales= InventarioMateriaPrima.query.all()
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
        return render_template('compras.html', materiales=materiales, id=id)

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
        flash("El registro se ha modificado exitosamente.", "exito")
        return redirect(url_for('main.inventarios'))
    elif request.method == 'GET':
        return render_template('modificarMateriaPrima.html', material=material, id=id)


@main.route('/getAllUsers',methods=["GET","POST"])
@login_required
@roles_required('empleado')
def getAllUsers():
    users = User.query.all()

    if len(users) == 0:
        users = 0
    return render_template('./users/users.html', users=users)

@main.route('/addUser', methods=['GET','POST'])
@login_required
@roles_required('empleado')
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
                return redirect(url_for('main.getAllUsers'))
                    
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
                return redirect(url_for('main.getAllUsers'))
                    
            except Exception as ex:
                        print(ex)
    else:
        return render_template('./users/agregarUser.html')
    
@main.route('/updateUser', methods=['GET','POST'])
@login_required
@roles_required('empleado')
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
                return redirect(url_for('main.getAllUsers'))
                        
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
                return redirect(url_for('main.getAllUsers'))
                        
            except Exception as ex:
                print(ex)
        return redirect(url_for('main.getAllUsers'))
    
    return render_template('./users/modificarUser.html', user = user)

@main.route('/deleteUser', methods=['GET','POST'])
@login_required
@roles_required('empleado')
def deleteUser():
    id = request.args.get('id')
    user = User.query.get(id)        
    
    if request.method == 'POST':   
        user.active = False            
        db.session.commit()
        return redirect(url_for('main.getAllUsers'))
        
        
    return render_template('./users/eliminarUser.html', user = user)

@main.route('/findUser', methods=['GET','POST'])
@login_required
@roles_required('empleado')
def findUser():
    if request.method == 'POST':   
        search_term = request.form.get('search')
        users = User.query.filter(or_(User.name.ilike(f'%{search_term}%'),
                                      User.email.ilike(f'%{search_term}%'))).all()
        if not users:
            flash("El usuario no existe", "error")
            return redirect(url_for('main.getAllUsers'))
        return render_template('./users/users.html', users=users)
    else:
        return redirect(url_for('main.getAllUsers'))

