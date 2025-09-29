from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from datetime import datetime
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'soucidadao123' 
bcrypt = Bcrypt(app)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="stockhub_db"
)

cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    try:
        cursor.execute("SELECT * FROM equipamentos")
        equipamentos = cursor.fetchall()
        return render_template('index.html', equipamentos=equipamentos)
    except Exception as e:
        print("Erro na rota '/':", e)
        return "Erro interno no servidor"

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')

@app.route('/add', methods=['POST'])
def add_item():
    try:
        modelo = request.form['modelo']
        numero_serie = request.form['numero_serie']
        cliente_nome = request.form['cliente_nome']
        data_instalacao = datetime.now().strftime('%Y-%m-%d')

        cursor.execute(
            "INSERT INTO equipamentos (modelo, numero_serie, cliente_nome, data_instalacao) VALUES (%s, %s, %s, %s)",
            (modelo, numero_serie, cliente_nome, data_instalacao)
        )
        db.commit()
        return redirect('/')
    except Exception as e:
        print("Erro ao adicionar equipamento:", e)
        return "Erro ao adicionar equipamento"

@app.route('/delete/<int:id>')
def delete_item(id):
    try:
        cursor.execute("DELETE FROM equipamentos WHERE id = %s", (id,))
        db.commit()
        return redirect('/')
    except Exception as e:
        print("Erro ao excluir equipamento:", e)
        return "Erro ao excluir equipamento"

@app.route('/report')
def generate_report():
    try:
        cursor.execute("SELECT * FROM equipamentos")
        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        print("Erro ao gerar relatório:", e)
        return jsonify({"erro": "Falha ao gerar relatório"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        try:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()

            if usuario and bcrypt.check_password_hash(usuario["senha"], senha):
                session["usuario_id"] = usuario["id"]
                session["nome"] = usuario["nome"]
                return redirect(url_for("index"))  
            else:
                erro = "E-mail ou senha inválidos."
        except Exception as e:
            erro = f"Erro ao tentar logar: {str(e)}"

    return render_template("login.html", erro=erro)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
