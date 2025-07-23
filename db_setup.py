import sqlite3
from datetime import datetime

# Conecta (ou cria) o banco de dados chamado 'usuarios.db'
conn = sqlite3.connect('usuarios.db')
cursor = conn.cursor()

# Cria a tabela de usuários, se ela ainda não existir
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pendente',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

print("✅ Tabela 'usuarios' criada com sucesso.")
conn.commit()
conn.close()
