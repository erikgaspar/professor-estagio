import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document
from werkzeug.security import check_password_hash

# 1) Configurações iniciais
load_dotenv()
API_KEY  = os.getenv("OPENAI_API_KEY")
MODEL_ID = "gpt-4o"

SYSTEM_PROMPT = """
Você é o Professor Estágio — um professor experiente, empolgado e de confiança. Seu papel é ajudar com dúvidas sobre estágios, respondendo **apenas com base nos documentos fornecidos**, como a Lei nº 11.788/2008 e normas internas do IEL Paraná. Você **não pode usar conhecimento externo ou inventar respostas** — mesmo que saiba, só vale o que está nos arquivos.

Seu jeito de conversar é leve, simpático e direto. Você fala como um bom professor explicando pra um colega nos corredores da instituição: com clareza, empolgação, paciência e aquele toque de “relaxa que eu te explico!”. Pode usar expressões como:
- “Boa pergunta!”
- “Isso aí dá confusão se não seguir direitinho...”
- “Quer que eu mostre com um exemplo?”
- “Tá na lei sim, olha só:”

Mas evite gírias exageradas, memes ou emojis. Nada que tire a credibilidade da resposta.

### ⚠️ Regras fundamentais:
- **Nunca** use conhecimento geral ou da internet (ex: “quem é o Pikachu”, “quantos habitantes tem o Brasil” — recuse educadamente).
- **Sempre** fundamente a resposta com base em trecho ou artigo dos documentos fornecidos.
- Se a pergunta **não estiver nos arquivos**, diga com franqueza:  
  **"Desculpe, não encontrei essa informação nos arquivos fornecidos. Prefiro não responder sem base oficial."**
- Se a pergunta for **vaga**, diga:  
  **"Me dá um pouquinho mais de contexto que eu tento te ajudar certinho com base na lei."**
- Se o usuário quiser mais detalhes ou exemplos, aprofunde com empolgação — mas **sempre dentro dos documentos.**

---

### ✅ Formato padrão de resposta:

1. Comece com uma resposta direta, clara e curta (1 ou 2 frases).
2. Se necessário, complemente com explicações simples e bem separadas.
3. Sempre finalize com a fonte legal da informação, em uma nova linha.

**Exemplo de resposta ideal:**

> “Pode sim! O estagiário tem direito a um recesso de 30 dias após 1 ano de estágio.”  
> “Se o estágio durar menos de um ano, o recesso é proporcional.”  
> **Fonte:** Art. 13 da Lei nº 11.788/2008

Evite parágrafos longos. Quebre a resposta em blocos curtos para facilitar a leitura. Nunca escreva um textão corrido.

---

Seu diferencial é ser confiável, bem-humorado na medida certa e 100% baseado em fontes seguras.


"""

# 2) Carrega somente o documento da Lei
def load_knowledge():
    pasta = "knowledge"
    for fname in os.listdir(pasta):
        if fname.lower().endswith((".docx", ".pdf", ".txt")):
            path = os.path.join(pasta, fname)
            if fname.lower().endswith(".docx"):
                doc = Document(path)
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            elif fname.lower().endswith(".pdf"):
                reader = PdfReader(path)
                return "\n".join(p.extract_text() or "" for p in reader.pages)
            elif fname.lower().endswith(".txt"):
                with open(path, encoding="utf-8") as f:
                    return f.read()
    return ""

# 3) Carrega o conteúdo da lei na memória
LAW_TEXT = load_knowledge()

# 4) Inicia a aplicação Flask e OpenAI
client = OpenAI(api_key=API_KEY)
app    = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "chave-super-secreta-123"  # você pode trocar por algo mais seguro depois

# Página inicial
@app.route("/")
def home():
    return redirect(url_for("login"))

# Rota de chat com a OpenAI
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    history = data.get("history", [])
    if not isinstance(history, list) or not history:
        return jsonify(error="Envie o histórico de chat"), 400

    messages = [
        {"role": "system", "content": f"Base legal completa (Lei 11.788/2008):\n{LAW_TEXT}"},
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    for m in history:
        messages.append({"role": m["role"], "content": m["content"]})

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=messages,
            user="colaborador_iel"
        )
        bot_reply = response.choices[0].message.content
        return jsonify(reply=bot_reply)
    except Exception as e:
        return jsonify(error=str(e)), 500

# Rota de cadastro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome  = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        if not nome or not email or not senha:
            return "Por favor, preencha todos os campos.", 400

        senha_hash = generate_password_hash(senha)

        try:
            conn = sqlite3.connect("usuarios.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                           (nome, email, senha_hash))
            conn.commit()
            conn.close()
            return "Cadastro realizado com sucesso! Aguarde a aprovação de um administrador."
        except sqlite3.IntegrityError:
            return "Erro: E-mail já cadastrado.", 400
        except Exception as e:
            return f"Erro ao cadastrar: {str(e)}", 500

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        if not email or not senha:
            return "Preencha todos os campos.", 400

        try:
            conn = sqlite3.connect("usuarios.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, senha_hash, status FROM usuarios WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                return "Usuário não encontrado.", 400

            user_id, nome, senha_hash, status = user

            if not check_password_hash(senha_hash, senha):
                return "Senha incorreta.", 400

            if status != "aprovado":
                return "Seu cadastro ainda não foi aprovado por um administrador.", 403

            # Login bem-sucedido
            session["user_id"] = user_id
            session["user_nome"] = nome

            resp = redirect(url_for("chat_page"))
            if request.form.get("lembrar"):
                resp.set_cookie("user_id", str(user_id), max_age=60*60*24*30)
                resp.set_cookie("user_nome", nome, max_age=60*60*24*30)
            return resp

        except Exception as e:
            return f"Erro ao fazer login: {str(e)}", 500

    return render_template("login.html")

@app.route("/chat-ui")
def chat_page():
    if "user_id" not in session:
        # tenta recuperar dos cookies
        user_id = request.cookies.get("user_id")
        user_nome = request.cookies.get("user_nome")
        if user_id and user_nome:
            session["user_id"] = user_id
            session["user_nome"] = user_nome
        else:
            return redirect(url_for("login"))
            
    return render_template("index.html")


# Painel do administrador
@app.route("/admin")
def admin():
    try:
        conn = sqlite3.connect("usuarios.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE status = 'pendente'")
        usuarios_pendentes = cursor.fetchall()
        conn.close()
        return render_template("admin.html", usuarios=usuarios_pendentes)
    except Exception as e:
        return f"Erro ao carregar painel: {str(e)}", 500

# Aprovar usuário
@app.route("/aprovar/<int:user_id>", methods=["POST"])
def aprovar(user_id):
    try:
        conn = sqlite3.connect("usuarios.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET status = 'aprovado' WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))
    except Exception as e:
        return f"Erro ao aprovar usuário: {str(e)}", 500

# Rejeitar (deletar) usuário
@app.route("/rejeitar/<int:user_id>", methods=["POST"])
def rejeitar(user_id):
    try:
        conn = sqlite3.connect("usuarios.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))
    except Exception as e:
        return f"Erro ao rejeitar usuário: {str(e)}", 500
    
@app.route("/logout")
def logout():
    session.clear()  # remove todas as informações da sessão
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)