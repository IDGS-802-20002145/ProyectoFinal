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
from project.models import Pedido, Producto, DetPedido, Venta, DetVenta
from werkzeug.utils import secure_filename
from datetime import datetime, date

def redireccionamiento():
    print(1)
    return redirect(url_for('cliente.pedidos'))