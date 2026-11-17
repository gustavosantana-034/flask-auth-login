from flask_sqlalchemy import SQLAlchemy

# Criamos a extensão aqui e a conectamos ao Flask com db.init_app(app) em app.py.
# Assim os models importam db sem precisar importar app e criar um ciclo de imports.
db = SQLAlchemy()
