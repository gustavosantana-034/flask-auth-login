from database import db
from flask import Flask, jsonify, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from models.user import User

app = Flask(__name__)
# Configuração da nossa secret-key
app.config["SECRET_KEY"] = "your_secret_key"
# provedor
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

login_manager = LoginManager()  # inferindo que iremos usar tal classe
db.init_app(
    app
)  # função para inicializar nossa aplicação apontando para o Flask-SQL-Alchemy
login_manager.init_app(
    app
)  # função para inicializar nossa aplicação apontando para o Flask-Login

# View login
login_manager.login_view = "login"  # rota para aonde usuários não autenticados devem bater caso os mesmos não sejam autenticados


# função para podermos gerenciar nossos usuários dentro do banco de dados através do id dos mesmos
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        user = User.query.filter_by(
            username=username
        ).first()  # uma query do banco para podermos buscar tal usuário e autentica-lo pegando seu primeiro registro em banco através de sua primeira aparição

        if user and user.password == password:
            login_user(user)  # chamando essa função para logar o usuário autenticado
            print(current_user.is_authenticated)
            return jsonify({"message": "Sucesso ao autenticar"}), 200

    return jsonify({"message": "Credenciais invalidas"}), 400


@app.shell_context_processor
def shell_context():
    return {"db": db, "User": User}


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()  # seguindo a lógica função usada para deslogar um usuário já  autenticado
    return jsonify({"message": "Logout realizado com sucesso!"})


@app.route("/user", methods=["POST"])
@login_required
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        user = User(
            username=username, password=password
        )  # aqui no nosso model precisamos de tal informações para inserção em banco, então pegaremos essas informações da request e passaremos como parâmetros
        db.session.add(
            user
        )  # uma vez que obtivermos exito, registraremos a sessão atual ao banco
        db.session.commit()  # e depois mandar todas as alterações ao banco confirmando sucesso
        return jsonify({"message": "Usuário cadastrado com sucesso"})

    return jsonify({"message": "Dados inválidos"}), 400


@app.route("/user/<int:id_user>", methods=["GET"])
@login_required
def read_user(id_user):
    user = User.query.get(id_user)

    if user:
        return {"username": user.username}

    return jsonify({"message": "Usuário não encontrado!"}), 404


@app.route("/user/<int:id_user>", methods=["PUT"])
@login_required
def update_user(id_user):
    data = request.json
    user = User.query.get(id_user)

    if user and data.get("password"):
        user.password = data.get("password")
        db.session.commit()  # ! Sempre que mexer em algo na base dados sempre usar este método

        return jsonify({"message": f"Usuário {id_user} atualizado com sucesso!"})

    return jsonify({"message": "Usuário não encontrado!"}), 404


@app.route("/user/<int:id_user>", methods=["DELETE"])
@login_required
def delete_user(id_user):
    user = User.query.get(id_user)

    # garantindo que o usuário não consiga se auto deletar
    if id_user == current_user.id:
        return jsonify({"message": "Deleção não permitida"}), 403

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"Usuário {id_user} deletado com sucesso!"})

    return jsonify({"message": "Usuário não encontrado!"}), 404


if __name__ == "__main__":
    app.run(debug=True)
