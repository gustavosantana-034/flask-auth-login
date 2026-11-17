from database import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    # db.Model mapeia a classe para uma tabela; UserMixin fornece os métodos esperados pelo Flask-Login.
    # id (int), username (text), password (text), role(text)
    id = db.Column(db.Integer, primary_key=True)
    # nullable=False proíbe NULL; unique=True impede repetir o mesmo username no banco.
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    # role representa a permissão na aplicação; não é o usuário de conexão do MySQL.
    role = db.Column(db.String(80), nullable=False, default="user")
    # Revisão: create_all cria tabelas ausentes, mas não adiciona colunas em tabelas existentes.
    # Para evoluir o schema preservando os dados, estudar migrations em vez de drop_all.
