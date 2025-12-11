from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

# -----------------------------------------
# CONEXIÓN A LA BASE DE DATOS
# -----------------------------------------
def get_db_connection():
    conn = sqlite3.connect("seguimiento_egresados.db")
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------------------
# RUTA PRINCIPAL
# -----------------------------------------
@app.route("/")
def index():
    error = session.pop("error", None)   # Recupera error solo una vez
    return render_template("index.html", error=error, abrir_modal=bool(error))


# -----------------------------------------
# LOGIN
# -----------------------------------------
@app.route("/login", methods=["POST"])
def login():
    correo = request.form["correo"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM admin WHERE correo=? AND password=?", (correo, password))
    admin = cursor.fetchone()

    conn.close()

    # SI LOGIN CORRECTO
    if admin:
        session["admin"] = correo
        return redirect("/dashboard")

    # SI LOGIN INCORRECTO
    session["error"] = "Datos incorrectos: usuario o contraseña"
    return redirect("/")



# -----------------------------------------
# DASHBOARD (PROTEGIDO)
# -----------------------------------------
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard_egresados.html")

# -----------------------------------------
# CERRAR SESIÓN
# -----------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
