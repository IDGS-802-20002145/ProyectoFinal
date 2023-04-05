from operator import or_
import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from . import db, userDataStore
from werkzeug.security import generate_password_hash, check_password_hash
from project.models import Products, Role, User
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
    productos = Products.query.all()
    return render_template('RopaCrud.html', productos=productos)


@main.route('/administrador', methods=['POST'])
@login_required
@roles_required('admin')
def admin_post():
    img=str(uuid.uuid4())+'.png'
    imagen=request.files['image']
    ruta_imagen = os.path.abspath('project\\static\\img')
    imagen.save(os.path.join(ruta_imagen,img))       
    alum=Products(nombre=request.form.get('txtNombre'),
                    descripcion=request.form.get('txtDescripcion'),
                    estilo=request.form.get('txtEstilo'),
                    precio=request.form.get('txtPrecio'),
                    image=img)
        #Con esta instruccion guardamos los datos en la bd
    db.session.add(alum)
    db.session.commit()
    flash("El registro se ha guardado exitosamente.", "exito")
    return redirect(url_for('main.principalAd'))
    

@main.route('/modificar', methods=['GET', 'POST'])
@login_required
def modificar():
    if request.method == 'GET':
        id = request.args.get('id')
        producto = Products.query.get(id)
        print(producto)
        if producto is None:
            flash("El pzroducto no existe", "error")
            return redirect(url_for('main.admin'))
        if not producto.image:
            producto.image = 'default.png' # o cualquier otro valor predeterminado para la imagen
        return render_template('modificar.html', producto=producto,id=id)
    elif request.method == 'POST':
        id = request.args.get('id')
        producto = Products.query.get(id)
        print(producto)
        if producto is None:
            flash("El producto no existe", "error")
            return redirect(url_for('main.admin'))
        producto.nombre = request.form.get('txtNombre')
        producto.estilo = request.form.get('txtEstilo')
        producto.descripcion = request.form.get('txtDescripcion')
        producto.precio = request.form.get('txtPrecio')
        imagen = request.files.get('image')
        ruta_imagen = os.path.abspath('project\\static\\img')
        if imagen:
            # Eliminar la imagen anterior
            os.remove(os.path.join(ruta_imagen, producto.image))
            # Guardar la nueva imagen
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(ruta_imagen, filename))
            producto.image = filename
        db.session.commit()
        flash("El registro se ha modificado exitosamente.", "exito")
        return redirect(url_for('main.principalAd'))

@main.route('/eliminar', methods=['GET', 'POST'])
@login_required
def eliminar():
    if request.method == 'GET':
        id = request.args.get('id')
        producto = Products.query.get(id)
        print(producto)
        if producto is None:
            flash("El producto no existe", "error")
            return redirect(url_for('main.admin'))
        if not producto.image:
            producto.image = 'default.png' # o cualquier otro valor predeterminado para la imagen
        return render_template('eliminar.html', producto=producto,id=id)
    elif request.method == 'POST':
        id = request.args.get('id')
        producto = Products.query.get(id)
        print(producto)
        if producto is None:
            flash("El producto no existe", "error")
            return redirect(url_for('main.admin'))
        producto.nombre = request.form.get('txtNombre')
        producto.estilo = request.form.get('txtEstilo')
        producto.descripcion = request.form.get('txtDescripcion')
        producto.precio = request.form.get('txtPrecio')
        imagen = request.files.get('image')
        ruta_imagen = os.path.abspath('project\\static\\img')
        if imagen:
            # Eliminar la imagen anterior
            os.remove(os.path.join(ruta_imagen, producto.image))
            # Guardar la nueva imagen
            filename = secure_filename(imagen.filename)
            imagen.save(os.path.join(ruta_imagen, filename))
            producto.image = filename
        db.session.delete(producto)
        db.session.commit()
        flash("El registro se ha eliminado exitosamente.", "exito")
        return redirect(url_for('main.principalAd'))

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

