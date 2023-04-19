import os
from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from ..models import db
from project.models import Proveedor


def insertar_proveedor():
   proveedor = Proveedor(nombre=request.form.get('txtNombre'),
                          email=request.form.get('txtEmail'),
                          telefono=request.form.get('txtTelefono'),
                          direccion=request.form.get('txtDireccion'))
   db.session.add(proveedor)
   db.session.commit()
   flash("El registro se ha guardado exitosamente.", "exito")
   return redirect(url_for('administrador.proveedores'))

def modificar_proveedor_get():
    id = request.args.get('id')
    proveedor = Proveedor.query.get(id)
    print(proveedor)
    if proveedor is None:
        flash("El proveedor no existe", "error")
        return redirect(url_for('administrador.proveedores'))
    return render_template('modificar_proveedor.html', proveedor=proveedor, id=id)


def modificar_proveedor_post():
    id = int(request.form.get('id'))
    proveedor = Proveedor.query.get(id)
    if proveedor is None:
        flash("El proveedor no existe", "error")
        return redirect(url_for('administrador.proveedores'))
    proveedor.nombre = request.form.get('txtNombre')
    proveedor.email = request.form.get('txtEmail')
    proveedor.telefono = request.form.get('txtTelefono')
    proveedor.direccion = request.form.get('txtDireccion')
    db.session.commit()
    flash("El registro se ha modificado exitosamente.", "exito")
    return redirect(url_for('administrador.proveedores'))

def eliminar_proveedor_get():
    id = request.args.get('id')
    proveedor = Proveedor.query.get(id)
    print(proveedor)
    if proveedor is None:
        flash("El proveedor no existe", "error")
        return redirect(url_for('administrador.proveedores'))
    return render_template('eliminar_proveedor.html', proveedor=proveedor, id=id)

def eliminar_proveedor_post():
    id = int(request.form.get('id'))
    proveedor = Proveedor.query.get(id)
    if proveedor is None:
        flash("El proveedor no existe", "error")
        return redirect(url_for('administrador.proveedores'))
        
    proveedor.active = 0
    db.session.commit()
    flash("El registro se ha eliminado exitosamente.", "exito")
    return redirect(url_for('administrador.proveedores'))

             
                          
                          
