from flask import Flask, render_template_string, request, redirect, send_file
import sqlite3
import openpyxl
import os

app = Flask(__name__)

# ===============================
# CONEXÃO COM BANCO
# ===============================
def conectar():
    conn = sqlite3.connect("cftv.db")
    conn.row_factory = sqlite3.Row
    return conn

# Criar tabela se não existir
conn = conectar()
conn.execute("""
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT,
    ip TEXT,
    local TEXT,
    usuario TEXT,
    senha TEXT
)
""")
conn.commit()
conn.close()

# ===============================
# HTML COMPLETO
# ===============================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sistema CFTV</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 20px; }
        h1 { text-align: center; }
        input { padding: 8px; margin: 5px 0; width: 100%; }
        button { padding: 8px; margin-top: 5px; width: 100%; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 14px; }
        th, td { border: 1px solid #ccc; padding: 6px; text-align: center; }
        th { background: #f2f2f2; }
        .top-buttons { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .link { text-decoration: none; padding: 6px 10px; background: #2196F3; color: white; border-radius: 4px; }
        .delete { background: red; }
        .edit { background: orange; }
        form { margin-bottom: 15px; }
    </style>
</head>
<body>

<h1>📷 Sistema CFTV</h1>

<div class="top-buttons">
    <a class="link" href="/">🏠 Início</a>
    <a class="link" href="/exportar">📊 Exportar Excel</a>
</div>

<h3>➕ Cadastro de Câmera</h3>
<form method="post" action="/salvar">
    <input name="id" type="hidden" value="{{ camera.id if camera }}">
    <input name="numero" placeholder="Número da câmera" required value="{{ camera.numero if camera }}">
    <input name="ip" placeholder="IP da câmera" required value="{{ camera.ip if camera }}">
    <input name="local" placeholder="Local da câmera" required value="{{ camera.local if camera }}">
    <input name="usuario" placeholder="Usuário" required value="{{ camera.usuario if camera }}">
    <input name="senha" placeholder="Senha" required value="{{ camera.senha if camera }}">
    <button type="submit">💾 Salvar</button>
</form>

<h3>🔎 Buscar</h3>
<form method="get">
    <input name="q" placeholder="Pesquisar por número, IP ou local">
    <button type="submit">Buscar</button>
</form>

<h3>📋 Lista de Câmeras</h3>
<table>
<tr>
    <th>Número</th>
    <th>IP</th>
    <th>Local</th>
    <th>Usuário</th>
    <th>Senha</th>
    <th>Ações</th>
</tr>

{% for cam in cameras %}
<tr>
    <td>{{ cam.numero }}</td>
    <td>{{ cam.ip }}</td>
    <td>{{ cam.local }}</td>
    <td>{{ cam.usuario }}</td>
    <td>{{ cam.senha }}</td>
    <td>
        <a class="link edit" href="/editar/{{ cam.id }}">✏️ Editar</a>
        <a class="link delete" href="/excluir/{{ cam.id }}">🗑 Excluir</a>
    </td>
</tr>
{% endfor %}
</table>

</body>
</html>
"""

# ===============================
# ROTAS
# ===============================

@app.route("/")
def index():
    q = request.args.get("q", "")
    conn = conectar()
    cameras = conn.execute("""
        SELECT * FROM cameras
        WHERE numero LIKE ? OR ip LIKE ? OR local LIKE ?
        ORDER BY id DESC
    """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    conn.close()
    return render_template_string(HTML, cameras=cameras, camera=None)

@app.route("/salvar", methods=["POST"])
def salvar():
    conn = conectar()
    if request.form["id"]:
        conn.execute("""
            UPDATE cameras
            SET numero=?, ip=?, local=?, usuario=?, senha=?
            WHERE id=?
        """, (
            request.form["numero"],
            request.form["ip"],
            request.form["local"],
            request.form["usuario"],
            request.form["senha"],
            request.form["id"]
        ))
    else:
        conn.execute("""
            INSERT INTO cameras (numero, ip, local, usuario, senha)
            VALUES (?,?,?,?,?)
        """, (
            request.form["numero"],
            request.form["ip"],
            request.form["local"],
            request.form["usuario"],
            request.form["senha"]
        ))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/editar/<int:id>")
def editar(id):
    conn = conectar()
    camera = conn.execute("SELECT * FROM cameras WHERE id=?", (id,)).fetchone()
    cameras = conn.execute("SELECT * FROM cameras ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(HTML, cameras=cameras, camera=camera)

@app.route("/excluir/<int:id>")
def excluir(id):
    conn = conectar()
    conn.execute("DELETE FROM cameras WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/exportar")
def exportar():
    conn = conectar()
    cameras = conn.execute("SELECT * FROM cameras").fetchall()
    conn.close()

    arquivo = "cameras_exportadas.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Número", "IP", "Local", "Usuário", "Senha"])

    for cam in cameras:
        ws.append([cam["numero"], cam["ip"], cam["local"], cam["usuario"], cam["senha"]])

    wb.save(arquivo)
    return send_file(arquivo, as_attachment=True)

# ===============================
# INICIAR SERVIDOR
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)