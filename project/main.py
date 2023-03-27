import os
import uuid
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from . import db
from project.models import Products, Role
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



@main.route('/principalAd',methods=["GET","POST"])
@login_required
def principalAd():
    productos = Products.query.all()

    if len(productos) == 0:
        productos = 0

    print(current_user.admin)

    return render_template('principalAd.html', productos=productos)
