from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from psycopg2 import OperationalError
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'clave-secreta-123'   # Cámbiala cuando quieras


# ====================================================
#  CONEXIÓN A TU BASE DE DATOS POSTGRESQL
# ====================================================
try:
    conn = psycopg2.connect(
        host="localhost",
        database="prueba",
        user="postgres",
        password="123456",
        port="5432"
    )
    print("✅ Conexión a la base de datos exitosa")
except OperationalError as e:
    print("❌ Error al conectar a PostgreSQL:", e)
    conn = None


# ====================================================
#  RUTA PRINCIPAL — LOGIN
# ====================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if conn is None:
            return "Error: No hay conexión con la base de datos"

        cur = conn.cursor()
        cur.execute("SELECT password FROM usuarios WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        # Validar usuario y contraseña
        if user and user[0] == password:
            session["username"] = username
            return redirect(url_for("bienvenido"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


# ====================================================
#  RUTA DE BIENVENIDA
# ====================================================
@app.route("/bienvenido")
def bienvenido():
    if "username" not in session:
        return redirect("/")
    return render_template("bienvenido.html", username=session["username"])


# ====================================================
#  EJECUCIÓN LOCAL
# ====================================================
if __name__ == "__main__":
    app.run(debug=True)
