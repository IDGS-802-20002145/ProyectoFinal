import os
from flask import Flask
from flask_security  import Security, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy

#Creamos una instancia de 
db = SQLAlchemy()
from .models import User, Role
#Creamos un objeto de SQLAchemyUserDataStore
userDataStore = SQLAlchemyUserDatastore(db, User, Role)

#Métodos de inicio de la aplicación
def create_app():
    #Creamos nuestra aplicación de Flask
    app = Flask(__name__)
    #Configuraciones necesarias 
    app.config['SQLAlchemy_TRACK_MODIFICATIONS']= False
    app.config['SECRET_KEY'] =  os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:3308/urbanMode'
    app.config['SECURITY_PASSWORD_HASH'] =  'pbkdf2_sha512'
    app.config['SECURITY_PASSWORD_SALT'] =  'secretsalt'
    app.config['UPLOAD_FOLDER'] = '/static/img'

    db.init_app(app)
    #metodo para crear la bd en la primera peticion
    @app.before_first_request
    def create_all():
        db.create_all()

    #Conectamos los modelos de Flask-security usando SQLALCHEMYUSERDATASTORE
    security = Security(app, userDataStore)

    

    #Registramos 2 blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from .cliente import cliente as cliente_blueprint
    app.register_blueprint(cliente_blueprint)

    return app