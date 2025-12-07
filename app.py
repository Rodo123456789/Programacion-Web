from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def validar_usuario(username, password):
    conn = sqlite3.connect("base.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (username, password))
    usuario = cursor.fetchone()

    conn.close()
    return usuario


@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        if validar_usuario(user, pwd):
            return redirect(url_for("bienvenido", username=user))
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)


@app.route("/bienvenido/<username>")
def bienvenido(username):
    return render_template("bienvenido.html", username=username)


@app.route("/logout")
def logout():
    return redirect(url_for("login"))

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("base.db")
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        existe = cursor.fetchone()

        if existe:
            conn.close()
            return render_template("registro.html", error="El usuario ya existe.")

        # Insertar nuevo usuario
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)",
                       (username, password))

        conn.commit()
        conn.close()

        return redirect("/")  # vuelve al login

    return render_template("registro.html")



if __name__ == "__main__":
    app.run(debug=True)
