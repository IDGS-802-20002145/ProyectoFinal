import os
import uuid
import io
from reportlab.pdfgen import canvas
from flask import make_response, send_file
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_security import login_required, current_user
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from flask_security.decorators import roles_required, roles_accepted
from ..models import db
from ..Cliente.pedidos import redireccionamiento
from project.models import Pedido, Producto, DetPedido, Venta, DetVenta
from werkzeug.utils import secure_filename
from datetime import datetime, date


cliente = Blueprint('cliente', __name__)


@cliente.route('/catalogoC',methods=["GET","POST"])
@login_required
def catalogoC():
    prod = Producto.query.all()
    modelos = db.session.query(Producto.modelo).distinct().all()
    return render_template('catalogoCliente.html', productos = prod, modelos=modelos)

###################### Modulo de pedidos ######################

@cliente.route('/pedidos',methods=["GET","POST"])
@login_required
def pedidos():
    
    ids_pedidos = Pedido.query.with_entities(Pedido.id).filter_by(user_id= current_user.id, estatus=1).all()
    detPed = DetPedido.query.filter(DetPedido.pedido_id.in_([id_pedido[0] for id_pedido in ids_pedidos])).all()
    producto_ids = [dp.producto_id for dp in detPed]

    # Hacer la consulta para obtener solo los productos con las IDs correspondientes
    productos = Producto.query.filter(Producto.id.in_(producto_ids)).all()
    
    if request.method == 'POST':
        #Datos del pedido
        userID = current_user.id
        fecha_actual = date.today()
        fecha_actual_str = fecha_actual.strftime('%Y-%m-%d')
        #obten la fecha actual sin la hora
        # 1 Es pedido , 2 es compra y 0 es eliminado
        estatus = 1
        print(userID)
        pedido = Pedido(user_id = userID,
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
        cantidad = 1
                 
        detPed = DetPedido(pedido_id = pedidoID, producto_id = productoID,cantidad = cantidad)
        db.session.add(detPed)
        db.session.commit()
        return redirect(url_for('cliente.catalogoC'))
    
    return render_template('pedidos.html', detPed=detPed, productos=productos)

@cliente.route('/eliminarPedido',methods=["GET","POST"])
@login_required
def eliminarPedido():
    print("entro a eliminar")
    idPedido = request.args.get('id')
    print(idPedido)
    detPed = DetPedido.query.filter_by(pedido_id=idPedido).first()
    if request.method == 'POST':
        pedido = Pedido.query.filter_by(id=idPedido).first()
        pedido.estatus = 0
        db.session.commit()
        return redirect(url_for('cliente.pedidos'))
    
    return render_template('eliminarPedido.html', detPed = detPed)
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
        return render_template('/pedidos.html', detPed = detPedR)
    
    return render_template('pedidos.html', detPed = detPed)



##############################################################



###################### Modulo de ventas ######################


@cliente.route('/pagar', methods=['GET', 'POST'])
@login_required
def pagar():
    if request.method == 'GET':
        id = request.args.get('id')
        pedido = Pedido.query.filter_by(id=id, estatus=1).first()
        productos = DetPedido.query.filter_by(pedido_id=id).all()        
        detProductos = []
        total = 0
        for producto in productos:
            prod = Producto.query.filter_by(id=producto.producto_id).first()
            total += prod.precio * producto.cantidad
            prod.cantidad = producto.cantidad
            detProductos.append(prod)

    if request.method == 'POST':
        id = request.form.get('id')
        pedido = Pedido.query.filter_by(id=id, estatus=1).first()
        if request.form['metodo_pago'] == 'efectivo':
            id = request.form.get('id')
            print(id, " Es el id del pedido")
            pedido = Pedido.query.filter_by(id=id).first()
            print(pedido, " Es el pedido")
            # Cambiar estatus del pedido a 2
            pedido.estatus = 2
            db.session.commit()
            
            # Insertar en tabla venta
            venta = Venta(user_id=current_user.id, fecha=datetime.now().date())
            db.session.add(venta)
            db.session.commit()
            
            productos = DetPedido.query.filter_by(pedido_id=id).all()
            # Insertar detalle en tabla detventa
            for producto in productos:
                prod = Producto.query.filter_by(id=producto.producto_id).first()
                detventa = DetVenta(venta_id=venta.id, producto_id=prod.id, cantidad=producto.cantidad, precio=prod.precio)
                db.session.add(detventa)
                prod.stock_existencia -= producto.cantidad
                db.session.commit()
            
             # Generar archivo PDF
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            styles = getSampleStyleSheet()
            Story = []
            # Agregar encabezado
            #im = Image("../static/img/logo_size_invert.jpg", width=150, height=150)
            #Story.append(im)
            Story.append(Spacer(1, 12))
            Story.append(Paragraph("Sartorial", styles["Title"]))
            Story.append(Spacer(1, 12))
            Story.append(Paragraph(f"Fecha: {datetime.now().date()}", styles["Normal"]))
            Story.append(Paragraph(f"Cliente: {current_user.name}", styles["Normal"]))
            Story.append(Spacer(1, 12))
            # Agregar detalles del pedido
            detProductos = []
            totalFac = 0
            for producto in productos:
                prod = Producto.query.filter_by(id=producto.producto_id).first()
                totalFac += prod.precio * producto.cantidad
                prod.cantidad = producto.cantidad
                detProductos.append([prod.nombre, f"${prod.precio}", f"{producto.cantidad}"])
            tableStyle = [('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
                        ('TOPPADDING', (0, -1), (-1, -1),12)]
            t = Table([["Producto", "Precio", "Cantidad"]] + detProductos)
            t.setStyle(tableStyle)
            Story.append(t)
            Story.append(Spacer(1, 12))
            #Agregar total a pagar

            Story.append(Paragraph(f"Total a pagar: ${totalFac}", styles["Normal"]))
            doc.build(Story)
            
            #Descargar archivo PDF
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers.set('Content-Disposition', 'attachment', filename=f'ticket{datetime.now().date()}.pdf')
            response.headers.set('Content-Type', 'application/pdf')
            flash("El pedido se ha pagado con éxito", "success")
                        
            return response
                   
        elif request.form['metodo_pago'] == 'tarjeta':
            id = request.form.get('id')
            return render_template('pago_tarjeta.html', id=id)
    return render_template('pagar.html', pedido=pedido, productos=productos, detProductos=detProductos, total=total, id=id)
   


@cliente.route('/pago_tarjeta', methods=['POST'])
@login_required
def pago_tarjeta():
    if request.method == 'POST':
        id = request.form.get('id')
        print(id, " Es el id del pedido")
        pedido = Pedido.query.filter_by(id=id).first()
        print(pedido, " Es el pedido")
        # Cambiar estatus del pedido a 2
        pedido.estatus = 2
        db.session.commit()
            
        # Insertar en tabla venta
        venta = Venta(user_id=current_user.id, fecha=datetime.now().date())
        db.session.add(venta)
        db.session.commit()
          
        productos = DetPedido.query.filter_by(pedido_id=id).all()
        # Insertar detalle en tabla detventa
        for producto in productos:
            prod = Producto.query.filter_by(id=producto.producto_id).first()
            detventa = DetVenta(venta_id=venta.id, producto_id=prod.id, cantidad=producto.cantidad, precio=prod.precio)
            db.session.add(detventa)
            prod.stock_existencia -= producto.cantidad
            db.session.commit()

        ultimos4digitos = request.form.get('card-number-3')
            
        # Generar archivo PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        Story = []
        # Agregar encabezado
        #im = Image("../static/img/logo_size_invert.jpg", width=150, height=150)
        #Story.append(im)
        Story.append(Spacer(1, 12))
        Story.append(Paragraph("Sartorial", styles["Title"]))
        Story.append(Spacer(1, 12))
        Story.append(Paragraph(f"Fecha: {datetime.now().date()}", styles["Normal"]))
        Story.append(Paragraph(f"Cliente: {current_user.name}", styles["Normal"]))
        Story.append(Paragraph(f"Tarjeta de Pago: **** **** **** {ultimos4digitos}", styles["Normal"]))
        Story.append(Spacer(1, 12))
        # Agregar detalles del pedido
        detProductos = []
        totalFac = 0
        for producto in productos:
                prod = Producto.query.filter_by(id=producto.producto_id).first()
                totalFac += prod.precio * producto.cantidad
                prod.cantidad = producto.cantidad
                detProductos.append([prod.nombre, f"${prod.precio}", f"{producto.cantidad}"])
        tableStyle = [('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
                        ('TOPPADDING', (0, -1), (-1, -1),12)]
        t = Table([["Producto", "Precio", "Cantidad"]] + detProductos)
        t.setStyle(tableStyle)
        Story.append(t)
        Story.append(Spacer(1, 12))
        #Agregar total a pagar

        Story.append(Paragraph(f"Total a pagar: ${totalFac}", styles["Normal"]))
        doc.build(Story)
            
        #Descargar archivo PDF
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers.set('Content-Disposition', 'attachment', filename=f'ticket{datetime.now().date()}.pdf')
        response.headers.set('Content-Type', 'application/pdf')
        flash("El pedido se ha pagado con éxito", "success")
                        
        return response








##############################################################