import sqlite3

EMAIL_DO_ADMIN = "erikgaspar88@gmail.com"  # 🔁 troque aqui pelo seu e-mail real

try:
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()

    # Verifica se a coluna 'is_admin' já existe
    cursor.execute("PRAGMA table_info(usuarios)")
    colunas = [col[1] for col in cursor.fetchall()]
    if "is_admin" not in colunas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN is_admin INTEGER DEFAULT 0")
        print("✅ Coluna 'is_admin' adicionada com sucesso.")
    else:
        print("ℹ️ A coluna 'is_admin' já existe.")

    # Atualiza o e-mail informado como admin
    cursor.execute("UPDATE usuarios SET is_admin = 1 WHERE email = ?", (EMAIL_DO_ADMIN,))
    if cursor.rowcount == 0:
        print("⚠️ Nenhum usuário com esse e-mail encontrado.")
    else:
        print("✅ Usuário promovido a administrador.")

    conn.commit()
    conn.close()
except Exception as e:
    print("❌ Erro:", e)
