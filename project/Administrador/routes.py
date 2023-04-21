import os 
from operator import or_
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app, make_response, send_file, Response
from flask_security import login_required, current_user
from flask_security.decorators import roles_required, roles_accepted
from flask_excel import make_response_from_query_sets
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from tempfile import NamedTemporaryFile
from ..models import db
from .. import userDataStore, db
from .productosAdmin import ad_post, modificar_poducto, modificar_producto_get, actualizar_stock_post
from .proveedores import insertar_proveedor, modificar_proveedor_get, modificar_proveedor_post, eliminar_proveedor_get, eliminar_proveedor_post
from project.models import  Producto, User, InventarioMateriaPrima, ExplotacionMaterial, Proveedor,DetCompra,Compra, DetVenta, Venta
from werkzeug.security import generate_password_hash
import io 
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from sqlalchemy import func



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

    return render_template('RopaCrud.html', productos=productos,materiales=materiales, enumerate=enumerate)


@administrador.route('/administrador', methods=['POST'])
@login_required
@roles_required('admin')
def admin_post():
    if request.method == 'POST':
       return ad_post()
    

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
      return modificar_poducto(producto)
    elif request.method == 'GET':
        return modificar_producto_get(producto)


@administrador.route('/actualizarStock', methods=['GET', 'POST'])
@login_required
def actualizarStock():
    id = request.args.get('id')
    producto = Producto.query.get(id)
    materialesU = request.form.getlist('materiales')
    cantidad_usada = list(filter(bool, request.form.getlist('cantidad_usada[]')))
    cantidades_individuales = cantidad_usada    
    if producto is None:
        flash("El producto no existe", "error")
        return redirect(url_for('main.admin'))
    
    if request.method == 'POST':
        return actualizar_stock_post(producto, materialesU, cantidades_individuales, cantidad_usada)
    
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
        return redirect(url_for('main.admin'))
    if request.method == 'POST':
        # Eliminar la imagen del producto del sistema de archivos
        if producto.imagen:
            imagen_path = os.path.join(current_app.root_path, 'static/img', producto.imagen)
            if os.path.exists(imagen_path):
                os.remove(imagen_path)
        # Actualizar el registro en la base de datos
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
        precioTotal= float(cantidad) * float(precio)
        materialC= DetCompra(compra_id=compraNow.id, material_id=material.id, cantidad=cantidad, precio=precioTotal)
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
    ventas_por_mes = db.session.query(
                func.date_format(Venta.fecha, '%Y-%m').label('mes'),
                func.sum(DetVenta.cantidad * DetVenta.precio).label('total')
            ).join(DetVenta).filter(
                Venta.estatus == True
            ).group_by('mes').all()
            
    compras_por_mes = db.session.query(
                func.date_format(Compra.fecha, '%Y-%m').label('mes'),
                func.sum(DetCompra.precio).label('total')
            ).join(DetCompra).filter(
                Compra.estatus == True
            ).group_by('mes').all()


    utilidad_mensual = []
    for venta, compra in zip(ventas_por_mes, compras_por_mes):
        if venta.mes == compra.mes:
            utilidad_mensual.append({
                'mes': venta.mes,
                'utilidad': venta.total - compra.total
            })
    return render_template('finanzas.html', ventas_por_mes=ventas_por_mes, compras_por_mes=compras_por_mes,  utilidad_mensual=utilidad_mensual)






@administrador.route("/reportesFinanzas", methods=['GET','POST'])
@login_required
def reportesFinanzas():
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        radio_btn = request.form['radio_btn']

        if radio_btn == 'ventas':
            ventas = db.session.query(
                    Venta.fecha,
                    Producto.nombre,
                    Producto.modelo,
                    DetVenta.cantidad,
                    DetVenta.precio,
                    (DetVenta.cantidad * DetVenta.precio).label("total")
                ).select_from(Venta).join(DetVenta).join(Producto).filter(
                    Venta.fecha.between(fecha_inicio, fecha_fin)
                ).all()
            ventas_total = sum([v[5] for v in ventas])
            encabezados = ['Fecha', 'Producto', 'Modelo', 'Cantidad', 'Precio Unitario', 'Total']
            detalles = [encabezados] + [[
                venta.fecha,
                venta.nombre,
                venta.modelo,
                venta.cantidad,
                venta.precio,
                venta.total
            ] for venta in ventas]

            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Negrita', fontName='Helvetica-Bold', fontSize=14))

            Story = []           
            

            # Agregar encabezado
            im = Image("C:/Users/zende/OneDrive/Escritorio/Rama Sergio/ProyectoFinal/project/static/images/Logo3S.png", width=300, height=150)
            Story.append(im)          
            Story.append(Spacer(1, 12))
            Story.append(Paragraph("Sartorial Reporte de Ventas", styles["Title"]))
            Story.append(Spacer(1, 12))
            Story.append(Paragraph(f"Fecha de Impresión: {datetime.now().date()}", styles["Normal"]))
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
            Story.append(Paragraph(f"Reporte del {fecha_inicio} al {fecha_fin}", styles["Negrita"]))
            Story.append(Spacer(1, 12))    
            Story.append(Spacer(1, 12))

            # Agregar tabla de detalles
            tableStyle = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 14),
                ('TOPPADDING', (0, -1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
                ])
            t = Table(detalles)
            t.setStyle(tableStyle)
            Story.append(t)
            Story.append(Spacer(1, 12))
            # Agregar total de ventas
            Story.append(Paragraph(f"Total de ventas: {ventas_total}", styles["Negrita"]))

            # Construir PDF
            doc.build(Story)
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers.set('Content-Disposition', 'attachment', filename=f'Rep_Ventas_{datetime.now().date()}.pdf')
            response.headers.set('Content-Type', 'application/pdf')
                        
            return response
        
        elif radio_btn == 'compras':
            
            # Generar reporte de compras
            compras = db.session.query(
                Compra.fecha,
                Proveedor.nombre.label("nombre_proveedor"),
                InventarioMateriaPrima.nombre,
                DetCompra.cantidad,
                DetCompra.precio
            ).select_from(Compra).join(DetCompra).join(InventarioMateriaPrima).join(Proveedor).filter(
                Compra.fecha.between(fecha_inicio, fecha_fin)
            ).all()
            compras_total = sum([c[4] for c in compras])

            encabezados = ['Fecha', 'Proveedor', 'Material', 'Cantidad', 'Total']
            detalles = [encabezados] + [[
                compra.fecha,
                compra.nombre_proveedor,
                compra.nombre,
                compra.cantidad,
                f"{compra.precio:.2f}",
            ] for compra in compras]

            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=inch/2, leftMargin=inch/2, topMargin=inch/2, bottomMargin=inch/2)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Negrita', fontName='Helvetica-Bold', fontSize=14))

            Story = []

            # Agregar encabezado
            im = Image("C:/Users/zende/OneDrive/Escritorio/Rama Sergio/ProyectoFinal/project/static/images/Logo3S.png", width=300, height=150)
            Story.append(im)          
            Story.append(Spacer(1, 12))
            Story.append(Paragraph("Sartorial Reporte de Compras", styles["Title"]))
            Story.append(Spacer(1, 12))
                # Agregar fechas
            Story.append(Paragraph(f"Fecha de Impresión: {datetime.now().date()}", styles["Normal"]))
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
            Story.append(Paragraph(f"Reporte del {fecha_inicio} al {fecha_fin}", styles["Negrita"]))
            Story.append(Spacer(1, 12))

            # Agregar tabla de detalles
            tabla = Table(detalles, colWidths=[80, 120, 120, 100, 70, 70, 70])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 14),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
                ('ALIGN', (0,1), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,1), (-1,-1), 12),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                ('BOX', (0,0), (-1,-1), 0.25, colors.black)
            ]))
            Story.append(tabla)

            # Agregar total
            Story.append(Spacer(1, 12))
            Story.append(Paragraph(f"Total de Compras: ${compras_total:.2f}", styles["Negrita"]))

            doc.build(Story)
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers.set('Content-Disposition', 'attachment', filename=f'Rep_Compras_{datetime.now().date()}.pdf')
            response.headers.set('Content-Type', 'application/pdf')
            return response
            
            
                        








#####################################################################################

################################### Gestion de Ventas #############################

@administrador.route('/ventas', methods=['GET', 'POST'])
@login_required
def ventas():
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
            clave_producto = (producto.modelo, producto.talla, producto.color)
            if clave_producto in productos:
                productos[clave_producto]['cantidad'] += det_venta.cantidad
                productos[clave_producto]['precio'] += det_venta.precio
            else:
                productos[clave_producto] = {
                    'talla': producto.talla,
                    'color': producto.color,
                    'modelo': producto.modelo,
                    'precio': det_venta.precio,
                    'cantidad': det_venta.cantidad,
                }

        # Convertimos el diccionario a una lista para pasarlo al template
        lista_productos = []
        for (modelo, talla, color), producto in productos.items():
            nombre_producto = Producto.query.filter_by(
                modelo=modelo,
                talla=talla,
                color=color
            ).first().nombre
            lista_productos.append({
                'nombre': nombre_producto,
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