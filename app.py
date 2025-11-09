from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import mysql.connector
from datetime import datetime
from flask_bcrypt import Bcrypt
from functools import wraps
import os
import io
import openpyxl
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "soucidadao123")
bcrypt = Bcrypt(app)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="soucidadao123",
    database="stockhub_db"
)

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Rota inicial - index
@app.route('/')
@login_required
def index():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipamentos")
        equipamentos = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('index.html', equipamentos=equipamentos)
    except Exception as e:
        app.logger.error("Erro na rota '/': %s", e)
        return "Erro interno no servidor"

# Registro de equipamento
@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == "POST":
        try:
            modelo = request.form['modelo']
            numero_serie = request.form['numero_serie']
            cliente_nome = request.form['cliente_nome']
            data_instalacao = datetime.now().strftime('%Y-%m-%d')

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "INSERT INTO equipamentos (modelo, numero_serie, cliente_nome, data_instalacao) VALUES (%s, %s, %s, %s)",
                (modelo, numero_serie, cliente_nome, data_instalacao)
            )
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for("index"))
        except Exception as e:
            app.logger.error("Erro ao registrar equipamento: %s", e)
            return "Erro ao registrar equipamento"

    return render_template('register.html')

# Busca
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    resultados = []
    if request.method == "POST":
        termo = request.form['termo']
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM equipamentos WHERE modelo LIKE %s OR cliente_nome LIKE %s",
                           (f"%{termo}%", f"%{termo}%"))
            resultados = cursor.fetchall()
            cursor.close()
            db.close()
        except Exception as e:
            app.logger.error("Erro na busca: %s", e)

    return render_template('search.html', resultados=resultados)

# Excluir equipamento
@app.route('/delete/<int:equipamento_id>')
@login_required
def delete_item(equipamento_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM equipamentos WHERE id = %s", (equipamento_id,))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error("Erro ao excluir equipamento: %s", e)
        return "Erro ao excluir equipamento"

# Relatório JSON
@app.route('/report')
@login_required
def generate_report():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipamentos")
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(data)
    except Exception as e:
        app.logger.error("Erro ao gerar relatório JSON: %s", e)
        return jsonify({"erro": "Falha ao gerar relatório"})

# Relatório HTML
@app.route('/relatorio')
@login_required
def relatorio_html():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipamentos")
        equipamentos = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("relatorio.html", equipamentos=equipamentos)
    except Exception as e:
        app.logger.error("Erro ao renderizar relatório HTML: %s", e)
        return "Erro ao renderizar relatório"

# Relatório Excel
@app.route('/relatorio_excel')
@login_required
def relatorio_excel():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipamentos")
        equipamentos = cursor.fetchall()
        cursor.close()
        db.close()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Equipamentos"

        ws.append(["ID", "Modelo", "Nº Série", "Cliente", "Data"])
        for eq in equipamentos:
            ws.append([eq["id"], eq["modelo"], eq["numero_serie"], eq["cliente_nome"], str(eq["data_instalacao"])])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name="relatorio_stockhub.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        app.logger.error("Erro ao gerar Excel: %s", e)
        return "Erro ao gerar Excel"

# Relatório PDF
@app.route('/relatorio_pdf')
@login_required
def relatorio_pdf():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM equipamentos")
        equipamentos = cursor.fetchall()
        cursor.close()
        db.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        styles = getSampleStyleSheet()
        elements = []

        # Cabeçalho com logo
        logo_path = os.path.join("static", "vem-pra-pixel.png")
        if os.path.exists(logo_path):
            elements.append(Paragraph('<para align=center><img src="{}" width="100" height="100"/></para>'.format(logo_path), styles['Normal']))

        elements.append(Paragraph("Relatório de Equipamentos - StockHub", styles['Title']))
        elements.append(Paragraph("Pixel Internet", styles['Heading2']))
        elements.append(Paragraph(" ", styles['Normal']))

        # Montar tabela
        data = [["ID", "Modelo", "Nº Série", "Cliente", "Data"]]
        for eq in equipamentos:
            data.append([eq["id"], eq["modelo"], eq["numero_serie"], eq["cliente_nome"], str(eq["data_instalacao"])])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00A19A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

        # Marca d'água
        def add_watermark(canvas_obj, doc_obj):
            if os.path.exists(logo_path):
                watermark = ImageReader(logo_path)
                canvas_obj.saveState()
                canvas_obj.translate(300, 400)
                canvas_obj.rotate(30)
                canvas_obj.drawImage(watermark, -200, -200, width=400, height=400, mask='auto')
                canvas_obj.restoreState()

        doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="relatorio_stockhub.pdf", mimetype="application/pdf")
    except Exception as e:
        app.logger.error("Erro ao gerar PDF: %s", e)
        return "Erro ao gerar PDF"

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            cursor.close()
            db.close()

            if usuario and bcrypt.check_password_hash(usuario["senha"], senha):
                session["usuario_id"] = usuario["id"]
                session["nome"] = usuario["nome"]
                return redirect(url_for("index"))
            else:
                erro = "E-mail ou senha inválidos."
        except Exception as e:
            erro = f"Erro ao tentar logar: {str(e)}"

    return render_template("login.html", erro=erro)

# Registro de novos usuários
@app.route('/user_register', methods=['GET', 'POST'])
@login_required
def user_register():
    if request.method == "POST":
        try:
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
                           (nome, email, senha_hash))
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for("index"))
        except Exception as e:
            app.logger.error("Erro ao registrar usuário: %s", e)
            return "Erro ao registrar usuário"
    return render_template("user_register.html")

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
