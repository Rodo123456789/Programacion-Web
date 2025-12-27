from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import math
from werkzeug.utils import secure_filename
from flask import jsonify



app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

app.config["UPLOAD_FOLDER"] = "static/uploads/egresados"

# crear carpeta si no existe
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


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
    error = session.pop("error", None)
    error2 = session.pop("error2", None)

    return render_template(
        "index.html",
        error=error,
        error2=error2,
        abrir_modal=bool(error),
        abrir_modal2=bool(error2)
    )


# -----------------------------------------
# LOGIN NORMAL
# -----------------------------------------
@app.route("/login", methods=["POST"])
def login():
    correo = request.form["correo"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_admin, nombre
        FROM admin
        WHERE correo=? AND password=?
    """, (correo, password))

    admin = cursor.fetchone()
    conn.close()

    if admin:
        session["admin_id"] = admin["id_admin"]
        session["nombre_admin"] = admin["nombre"]
        return redirect("/dashboard")

    session["error"] = "Datos incorrectos: usuario o contraseña"
    return redirect("/")


@app.route("/login2", methods=["POST"])
def login2():
    correo = request.form["correo"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_admin, nombre
        FROM admin
        WHERE correo=? AND password=?
    """, (correo, password))

    admin = cursor.fetchone()
    conn.close()

    # -------- SOLO ADMIN ID = 1 --------
    if admin and admin["id_admin"] == 1:
        session["admin_id"] = admin["id_admin"]
        session["nombre_admin"] = admin["nombre"]
        return redirect("/administradores")

    # -------- ERROR --------
    session["error2"] = "Acceso restringido"
    session["abrir_modal2"] = True
    return redirect("/dashboard")


# -----------------------------------------
# DASHBOARD (PROTEGIDO)
# -----------------------------------------
@app.route("/dashboard")
def dashboard():
    if "admin_id" not in session:
        return redirect(url_for("index"))

    return render_template(
    "dashboard_egresados.html",
    nombre_admin=session.get("nombre_admin", "Administrador"),
    error2=session.pop("error2", None),
    abrir_modal2=session.pop("abrir_modal2", False)
)



# -----------------------------------------
# ADMINISTRADORES (PROTEGIDO)
# -----------------------------------------
@app.route("/administradores")
def administradores():
    if "admin_id" not in session:
        return redirect(url_for("index"))

    import math
    buscar = request.args.get("buscar", "")
    pagina = int(request.args.get("pagina", 1))
    por_pagina = 4
    offset = (pagina - 1) * por_pagina

    conn = sqlite3.connect("seguimiento_egresados.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # ---------- CONTAR ----------
    if buscar:
        cursor.execute("""
            SELECT COUNT(*) FROM admin
            WHERE nombre LIKE ? 
            OR apellido_paterno LIKE ?
            OR apellido_materno LIKE ?
            OR correo LIKE ?
        """, (f"%{buscar}%",)*4)
    else:
        cursor.execute("SELECT COUNT(*) FROM admin")

    total = cursor.fetchone()[0]
    total_paginas = math.ceil(total / por_pagina)

    # ---------- OBTENER REGISTROS ----------
    if buscar:
        cursor.execute("""
            SELECT * FROM admin
            WHERE nombre LIKE ? 
            OR apellido_paterno LIKE ?
            OR apellido_materno LIKE ?
            OR correo LIKE ?
            LIMIT ? OFFSET ?
        """, (f"%{buscar}%",)*4 + (por_pagina, offset))
    else:
        cursor.execute("""
            SELECT * FROM admin
            LIMIT ? OFFSET ?
        """, (por_pagina, offset))

    administradores = cursor.fetchall()
    conn.close()

    return render_template(
        "administradores.html",
        administradores=administradores,
        pagina=pagina,
        total_paginas=total_paginas,
        buscar=buscar,
        nombre_admin=session.get("nombre_admin", "Administrador")
    )


@app.route("/egresados")
def egresados():
    
    if "admin_id" not in session:
        return redirect(url_for("index"))

    import math
    buscar = request.args.get("buscar", "")
    pagina = int(request.args.get("pagina", 1))
    por_pagina = 3
    offset = (pagina - 1) * por_pagina

    conn = get_db_connection()
    cursor = conn.cursor()

    # ---------- CARRERAS ----------
    cursor.execute("""
        SELECT id_carrera, nombre_carrera
        FROM carreras
    """)
    carreras = cursor.fetchall()

    # ---------- MUNICIPIOS ----------
    cursor.execute("""
        SELECT id_municipio, nombre_municipio
        FROM municipios
    """)
    municipios = cursor.fetchall()

    # ---------- LOCALIDADES ----------
    cursor.execute("""
        SELECT id_localidad,
               nombre_localidad,
               id_municipio
        FROM localidades
    """)
    localidades = cursor.fetchall()

    # ---------- CONTAR ----------
    if buscar:
        cursor.execute("""
            SELECT COUNT(*)
            FROM egresados e
            JOIN carreras c ON e.id_carrera = c.id_carrera
            JOIN municipios m ON e.id_municipio = m.id_municipio
            JOIN localidades l ON e.id_localidad = l.id_localidad
            WHERE e.nombre_completo LIKE ?
               OR e.matricula LIKE ?
               OR c.nombre_carrera LIKE ?
        """, (f"%{buscar}%",)*3)
    else:
        cursor.execute("SELECT COUNT(*) FROM egresados")

    total = cursor.fetchone()[0]
    total_paginas = math.ceil(total / por_pagina)

    # ---------- OBTENER REGISTROS ----------
    if buscar:
        cursor.execute("""
            SELECT
                e.id_egresado,
                e.nombre_completo,
                c.nombre_carrera,
                e.matricula,
                e.generacion,
                e.modalidad,
                m.nombre_municipio,
                l.nombre_localidad,
                e.genero,
                e.telefono,
                e.correo,
                e.estatus,
                e.fotografia
            FROM egresados e
            JOIN carreras c ON e.id_carrera = c.id_carrera
            JOIN municipios m ON e.id_municipio = m.id_municipio
            JOIN localidades l ON e.id_localidad = l.id_localidad
            WHERE e.nombre_completo LIKE ?
               OR e.matricula LIKE ?
               OR c.nombre_carrera LIKE ?
            ORDER BY e.id_egresado DESC
            LIMIT ? OFFSET ?
        """, (f"%{buscar}%",)*3 + (por_pagina, offset))
    else:
        cursor.execute("""
            SELECT
                e.id_egresado,
                e.nombre_completo,
                c.nombre_carrera,
                e.matricula,
                e.generacion,
                e.modalidad,
                m.nombre_municipio,
                l.nombre_localidad,
                e.genero,
                e.telefono,
                e.correo,
                e.estatus,
                e.fotografia
            FROM egresados e
            JOIN carreras c ON e.id_carrera = c.id_carrera
            JOIN municipios m ON e.id_municipio = m.id_municipio
            JOIN localidades l ON e.id_localidad = l.id_localidad
            ORDER BY e.id_egresado DESC
            LIMIT ? OFFSET ?
        """, (por_pagina, offset))

    egresados = cursor.fetchall()
    conn.close()

    return render_template(
        "egresados.html",
        egresados=egresados,
        carreras=carreras,
        municipios=municipios,
        localidades=localidades,
        pagina=pagina,
        total_paginas=total_paginas,
        buscar=buscar,
        nombre_admin=session.get("nombre_admin", "Administrador")
    )




# -----------------------------------------
# LOGOUT
# -----------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#...............................................................................................

@app.route("/registrar_admin", methods=["POST"])
def registrar_admin():

    correo = request.form["correo"]
    telefono = request.form["telefono"]

    errores = {}

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM admin WHERE correo = ?", (correo,))
    if cursor.fetchone():
        errores["correo"] = "Este correo ya está registrado"

    cursor.execute("SELECT 1 FROM admin WHERE telefono = ?", (telefono,))
    if cursor.fetchone():
        errores["telefono"] = "Este teléfono ya está registrado"

    if errores:
        return jsonify({
            "status": "error",
            "errores": errores
        })

    cursor.execute("""
        INSERT INTO admin
        (nombre, apellido_paterno, apellido_materno, cargo, correo, telefono, password)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["nombre"],
        request.form["apellido_paterno"],
        request.form["apellido_materno"],
        request.form["cargo"],
        correo,
        telefono,
        request.form["password"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})


@app.route("/obtener_admin/<int:id>")
def obtener_admin(id):
    con = sqlite3.connect("seguimiento_egresados.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("SELECT * FROM admin WHERE id_admin=?", (id,))
    admin = cur.fetchone()

    return jsonify(dict(admin))


@app.route("/actualizar_admin", methods=["POST"])
def actualizar_admin():

    id_admin = request.form["id_admin"]
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    telefono = request.form["telefono"]

    conn = sqlite3.connect("seguimiento_egresados.db")
    cur = conn.cursor()

    errores = {}

    # 🔍 Validar correo duplicado
    cur.execute("""
        SELECT id_admin FROM admin
        WHERE correo = ? AND id_admin != ?
    """, (correo, id_admin))
    
    if cur.fetchone():
        errores["correo"] = "Este correo ya está registrado"

    # 🔍 Validar teléfono duplicado
    cur.execute("""
        SELECT id_admin FROM admin
        WHERE telefono = ? AND id_admin != ?
    """, (telefono, id_admin))
    
    if cur.fetchone():
        errores["telefono"] = "Este teléfono ya está registrado"

    # 🟥 Si hay errores
    if errores:
        conn.close()
        return jsonify({
            "status": "error",
            "errores": errores
        })

    # 🟩 Actualizar datos
    cur.execute("""
        UPDATE admin
        SET nombre = ?, correo = ?, telefono = ?
        WHERE id_admin = ?
    """, (nombre, correo, telefono, id_admin))

    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})

@app.route("/eliminar_admin/<int:id_admin>", methods=["POST"])
def eliminar_admin(id_admin):

    conn = sqlite3.connect("seguimiento_egresados.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM admin WHERE id_admin = ?", (id_admin,))
    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})



@app.route("/registrar_egresado", methods=["POST"])
def registrar_egresado():

    datos = {
        "nombre": request.form.get("nombre_completo",""),
        "matricula": request.form.get("matricula",""),
        "telefono": request.form.get("telefono",""),
        "correo": request.form.get("correo",""),
        "id_carrera": request.form.get("id_carrera",""),
        "generacion": request.form.get("generacion",""),
        "modalidad": request.form.get("modalidad") or "No aplica",
        "id_municipio": request.form.get("id_municipio") or "No aplica",
        "id_localidad": request.form.get("id_localidad") or "No aplica",
        "genero": request.form.get("genero",""),
        "estatus": request.form.get("estatus","")
    }

    conn = get_db_connection()
    cursor = conn.cursor()

    errores = {}

    # 1️⃣ MATRÍCULA
    cursor.execute("SELECT 1 FROM egresados WHERE matricula = ?", (datos["matricula"],))
    if cursor.fetchone():
        errores["matricula"] = "Esta matrícula ya está registrada"
        conn.close()
        return {"ok": False, "errores": errores}

    # 2️⃣ TELÉFONO
    cursor.execute("SELECT 1 FROM egresados WHERE telefono = ?", (datos["telefono"],))
    if cursor.fetchone():
        errores["telefono"] = "Este teléfono ya está registrado"
        conn.close()
        return {"ok": False, "errores": errores}

    # 3️⃣ CORREO
    cursor.execute("SELECT 1 FROM egresados WHERE correo = ?", (datos["correo"],))
    if cursor.fetchone():
        errores["correo"] = "Este correo ya está registrado"
        conn.close()
        return {"ok": False, "errores": errores}

    # 📸 FOTO
    foto = request.files.get("fotografia")
    nombre_foto = None

    if foto and foto.filename != "":
        extension = foto.filename.rsplit(".", 1)[1].lower()
        if extension in ["jpg", "jpeg", "png", "webp", "avif", "jfif",]:
            nombre_foto = secure_filename(f"{datos['matricula']}.{extension}")
            ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto)
            foto.save(ruta)

    # INSERT
    cursor.execute("""
        INSERT INTO egresados
        (nombre_completo, matricula, id_carrera, generacion,
        modalidad, id_municipio, id_localidad, genero,
        telefono, correo, estatus, fotografia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (datos["nombre"], datos["matricula"], datos["id_carrera"], datos["generacion"],
     datos["modalidad"], datos["id_municipio"], datos["id_localidad"], datos["genero"],
     datos["telefono"], datos["correo"], datos["estatus"], nombre_foto)
    )

    conn.commit()
    conn.close()

    return {"ok": True}




@app.route("/api/egresado/<int:id>")
def api_egresado(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM egresados WHERE id_egresado=?",
        (id,)
    )
    eg = cursor.fetchone()
    conn.close()

    return jsonify(dict(eg))



@app.route("/actualizar_egresado", methods=["POST"])
def actualizar_egresado():

    datos = {
        "id_egresado": request.form["id_egresado"],
        "nombre": request.form["nombre_completo"],
        "matricula": request.form["matricula"],
        "generacion": request.form["generacion"],
        "telefono": request.form["telefono"],
        "correo": request.form["correo"],
        "estatus": request.form["estatus"],
        "id_carrera": request.form["id_carrera"],
        "modalidad": request.form.get("modalidad") or "No aplica",
        "id_municipio": request.form.get("id_municipio") or "No aplica",
        "id_localidad": request.form.get("id_localidad") or "No aplica",
        "genero": request.form["genero"]
    }

    conn = get_db_connection()
    cursor = conn.cursor()
    errores = {}

    # 🔴 MATRÍCULA DUPLICADA
    cursor.execute("""
        SELECT 1 FROM egresados
        WHERE matricula = ? AND id_egresado != ?
    """, (datos["matricula"], datos["id_egresado"]))
    if cursor.fetchone():
        errores["matricula"] = "Esta matrícula ya está registrada"

    # 🔴 TELÉFONO DUPLICADO
    cursor.execute("""
        SELECT 1 FROM egresados
        WHERE telefono = ? AND id_egresado != ?
    """, (datos["telefono"], datos["id_egresado"]))
    if cursor.fetchone():
        errores["telefono"] = "Este teléfono ya está registrado"

    # 🔴 CORREO DUPLICADO
    cursor.execute("""
        SELECT 1 FROM egresados
        WHERE correo = ? AND id_egresado != ?
    """, (datos["correo"], datos["id_egresado"]))
    if cursor.fetchone():
        errores["correo"] = "Este correo ya está registrado"

    if errores:
        conn.close()
        return {"ok": False, "errores": errores}

    # 📸 FOTO
    cursor.execute(
        "SELECT fotografia FROM egresados WHERE id_egresado = ?",
        (datos["id_egresado"],)
    )
    eg = cursor.fetchone()
    nombre_foto = eg["fotografia"]

    nueva_foto = request.files.get("fotografia")
    if nueva_foto and nueva_foto.filename != "":
        if nombre_foto:
            ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto)
            if os.path.exists(ruta):
                os.remove(ruta)

        ext = nueva_foto.filename.rsplit(".", 1)[1].lower()
        nombre_foto = secure_filename(f"{datos['matricula']}.{ext}")
        nueva_foto.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto))

    # 🔹 UPDATE
    cursor.execute("""
        UPDATE egresados SET
            nombre_completo = ?,
            matricula = ?,
            generacion = ?,
            telefono = ?,
            correo = ?,
            estatus = ?,
            id_carrera = ?,
            modalidad = ?,
            id_municipio = ?,
            id_localidad = ?,
            genero = ?,
            fotografia = ?
        WHERE id_egresado = ?
    """, (
        datos["nombre"],
        datos["matricula"],
        datos["generacion"],
        datos["telefono"],
        datos["correo"],
        datos["estatus"],
        datos["id_carrera"],
        datos["modalidad"],
        datos["id_municipio"],
        datos["id_localidad"],
        datos["genero"],
        nombre_foto,
        datos["id_egresado"]
    ))

    conn.commit()
    conn.close()

    return {"ok": True}




@app.route("/eliminar_egresado/<int:id>")
def eliminar_egresado(id):

    if "admin_id" not in session:
        return redirect(url_for("index"))

    # 🔹 página y búsqueda actual
    pagina = int(request.args.get("pagina", 1))
    buscar = request.args.get("buscar", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔹 obtener nombre de la foto
    cursor.execute(
        "SELECT fotografia FROM egresados WHERE id_egresado = ?",
        (id,)
    )
    egresado = cursor.fetchone()

    if egresado and egresado["fotografia"]:
        ruta_foto = os.path.join(
            app.config["UPLOAD_FOLDER"],
            egresado["fotografia"]
        )

        # eliminar archivo físico
        if os.path.exists(ruta_foto):
            os.remove(ruta_foto)

    # 🔹 eliminar registro
    cursor.execute(
        "DELETE FROM egresados WHERE id_egresado = ?",
        (id,)
    )
    conn.commit()

    # 🔢 contar registros restantes
    if buscar:
        cursor.execute("""
            SELECT COUNT(*)
            FROM egresados e
            JOIN carreras c ON e.id_carrera = c.id_carrera
            WHERE e.nombre_completo LIKE ?
               OR e.matricula LIKE ?
               OR c.nombre_carrera LIKE ?
        """, (f"%{buscar}%",)*3)
    else:
        cursor.execute("SELECT COUNT(*) FROM egresados")

    total = cursor.fetchone()[0]
    conn.close()

    por_pagina = 3
    total_paginas = max(1, math.ceil(total / por_pagina))

    # 🔁 si la página ya no existe, regresar una
    if pagina > total_paginas:
        pagina = total_paginas

    return redirect(url_for("egresados", pagina=pagina, buscar=buscar))



if __name__ == "__main__":
    app.run(debug=True)
