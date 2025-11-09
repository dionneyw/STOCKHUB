#!/usr/bin/env python3
"""
create_user.py

Uso:
    python create_user.py
"""

from flask import Flask
from flask_bcrypt import Bcrypt
from getpass import getpass
import mysql.connector
import os
import sys

# Configurações do banco (ajuste se necessário)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "123")
DB_NAME = os.getenv("DB_NAME", "stockhub_db")

# Inicializa Flask-Bcrypt (precisa de um app Flask)
app = Flask(__name__)
bcrypt = Bcrypt(app)

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def main():
    print("=== Criar novo usuário para StockHub ===")
    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip()

    if not nome or not email:
        print("Nome e e-mail são obrigatórios.")
        sys.exit(1)

    senha = getpass("Senha: ")
    senha2 = getpass("Confirme a senha: ")
    if senha != senha2:
        print("Senhas não conferem. Abortando.")
        sys.exit(1)
    if len(senha) < 6:
        print("Aviso: recomenda-se senha com pelo menos 6 caracteres.")

    # gerar hash bcrypt
    senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

    # inserir no banco
    try:
        db = get_db_connection()
        cursor = db.cursor()
        sql = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nome, email, senha_hash))
        db.commit()
        cursor.close()
        db.close()
        print(f"Usuário '{email}' criado com sucesso.")
    except mysql.connector.Error as err:
        print("Erro ao inserir no banco:", err)
        sys.exit(1)

if __name__ == "__main__":
    main()
