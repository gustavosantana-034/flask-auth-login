import bcrypt
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
# Essa chave assina o cookie de sessão; em produção, carregar um segredo por variável de ambiente.
app.config["SECRET_KEY"] = "your_secret_key"
# provedor
# Formato da conexão: driver://usuario:senha@host:porta/banco (apenas duas barras após os dois-pontos).
# Aqui usamos MySQL; o arquivo instance/database.db do SQLite não é consultado por esta conexão.
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:admin123@127.0.0.1:3306/flask-application"
)

login_manager = LoginManager()  # inferindo que iremos usar tal classe
db.init_app(
    app
)  # função para inicializar nossa aplicação apontando para o Flask-SQL-Alchemy
login_manager.init_app(
    app
)  # função para inicializar nossa aplicação apontando para o Flask-Login

# View login
# Atenção: o redirecionamento de login_required faz GET, mas /login aceita somente POST nesta API.
login_manager.login_view = "login"  # rota para aonde usuários não autenticados devem bater caso os mesmos não sejam autenticados


# função para podermos gerenciar nossos usuários dentro do banco de dados através do id dos mesmos
@login_manager.user_loader
def load_user(user_id):
    # Nas próximas requisições, o Flask-Login usa o id salvo na sessão para carregar o usuário.
    # Para revisar depois: db.session.get(User, user_id) é a alternativa atual a Query.get().
    return User.query.get(user_id)


@app.route("/login", methods=["POST"])
def login():
    # No Insomnia, selecionar corpo JSON e enviar Content-Type: application/json.
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        user = User.query.filter_by(
            username=username
        ).first()  # uma query do banco para podermos buscar tal usuário e autentica-lo pegando seu primeiro registro em banco através de sua primeira aparição

        # O "and" só verifica a senha se encontrou o usuário; bcrypt compara a senha com o hash salvo.
        # encode transforma texto em bytes, que é o formato esperado pelo bcrypt.
        if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
            login_user(user)  # chamando essa função para logar o usuário autenticado
            print(current_user.is_authenticated)
            return jsonify({"message": "Sucesso ao autenticar"}), 200

    return jsonify({"message": "Credenciais invalidas"}), 400


@app.shell_context_processor
def shell_context():
    # Disponibiliza db e User no flask shell, evitando importar os dois manualmente.
    return {"db": db, "User": User}


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()  # seguindo a lógica função usada para deslogar um usuário já  autenticado
    return jsonify({"message": "Logout realizado com sucesso!"})


@app.route("/user", methods=["POST"])
# Cadastro público permite criar a primeira conta mesmo quando o banco está vazio.
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        # O salt aleatório permite gerar hashes diferentes mesmo para senhas iguais.
        # Hash não é uma senha que vamos descriptografar: no login usamos checkpw para conferir.
        hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
        # Revisar: hashpw retorna bytes; para uma coluna String, prefira salvar o hash com .decode("utf-8").
        # O role fica definido no servidor, impedindo que o cadastro escolha se tornar admin pelo JSON.
        user = User(
            username=username, password=hashed_password, role="user"
        )  # aqui no nosso model precisamos de tal informações para inserção em banco, então pegaremos essas informações da request e passaremos como parâmetros
        db.session.add(
            user
        )  # uma vez que obtivermos exito, registraremos a sessão atual ao banco
        db.session.commit()  # e depois mandar todas as alterações ao banco confirmando sucesso
        return jsonify({"message": "Usuário cadastrado com sucesso"})

    return jsonify({"message": "Dados inválidos"}), 400


@app.route("/user/<int:id_user>", methods=["GET"])
# O conversor int recebe o id da URL como inteiro; login_required exige uma sessão autenticada.
@login_required
def read_user(id_user):
    user = User.query.get(id_user)

    if user:
        # Retornamos apenas o nome: senha e hash não devem aparecer na resposta da API.
        return {"username": user.username}

    return jsonify({"message": "Usuário não encontrado!"}), 404


@app.route("/user/<int:id_user>", methods=["PUT"])
@login_required
def update_user(id_user):
    data = request.json
    user = User.query.get(id_user)

    # Se caso o usuário em questão quiser modificar um id diferente do dele e ele não sendo admin, vai dar ruim
    # Autenticação verifica quem entrou; esta condição de autorização verifica o que ele pode fazer.
    if id_user != current_user.id and current_user.role == "user":
        return jsonify({"message": "Operação não permitida!"}), 403

    if user and data.get("password"):
        # ATENÇÃO PARA REVISÃO: esta atribuição ainda salva texto puro; precisa gerar hash como no cadastro.
        # Caso contrário, a senha alterada não terá o formato que bcrypt.checkpw espera no login.
        user.password = data.get("password")
        db.session.commit()  # ! Sempre que mexer em algo na base dados sempre usar este método

        return jsonify({"message": f"Usuário {id_user} atualizado com sucesso!"})

    return jsonify({"message": "Usuário não encontrado!"}), 404


@app.route("/user/<int:id_user>", methods=["DELETE"])
@login_required
def delete_user(id_user):
    user = User.query.get(id_user)

    # usuários comuns não podem deletar outro usuários na aplicação, somente os admins
    if current_user.role != "admin":
        return jsonify({"message": "Operação não permitida!"}), 403

    # garantindo que o usuário não consiga se auto deletar
    if id_user == current_user.id:
        return jsonify({"message": "Deleção não permitida"}), 403

    if user:
        db.session.delete(user)
        # add/delete preparam alterações na sessão; commit confirma a transação no banco.
        db.session.commit()
        return jsonify({"message": f"Usuário {id_user} deletado com sucesso!"})

    return jsonify({"message": "Usuário não encontrado!"}), 404


if __name__ == "__main__":
    # Executa ao rodar este arquivo diretamente; debug=True é uma configuração de desenvolvimento.
    app.run(debug=True)
