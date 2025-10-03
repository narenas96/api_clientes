# app_customers.py
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def db_connection():
    conn = sqlite3.connect('customers.sqlite')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def body():
    if request.is_json:
        return request.get_json(silent=True) or {}
    # fallback a form-data
    return {k: v for k, v in request.form.items()}

# ---------- Customers ----------
@app.route("/customers", methods=["GET", "POST"])
def customers():
    conn = db_connection()
    cur = conn.cursor()

    if request.method == "GET":
        rows = cur.execute("""          SELECT id, nombre, apellido, email, telefono_e164, created_at, updated_at
          FROM customers ORDER BY id DESC
        """).fetchall()
        return jsonify([dict(r) for r in rows])

    if request.method == "POST":
        data = body()
        nombre  = data.get("nombre")
        apellido = data.get("apellido")
        email   = data.get("email")
        telefono = data.get("telefono_e164")
        consent_marketing = int(data.get("consent_marketing", 0))
        consent_terminos  = int(data.get("consent_terminos", 0))
        consent_privacidad = int(data.get("consent_privacidad", 1))

        if not (nombre and apellido and email):
            return jsonify({"error": "nombre, apellido y email son obligatorios"}), 400

        try:
            cur.execute("""              INSERT INTO customers (nombre, apellido, email, telefono_e164,
                                     consent_marketing, consent_terminos, consent_privacidad)
              VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nombre, apellido, email, telefono, consent_marketing, consent_terminos, consent_privacidad))
            conn.commit()
        except sqlite3.IntegrityError as e:
            return jsonify({"error": "email duplicado o constraint violada", "detail": str(e)}), 409

        return jsonify({"id": cur.lastrowid, "message": "Cliente creado"}), 201

# CRUD un cliente
@app.route("/customer/<int:id>", methods=["GET", "PUT", "DELETE"])
def customer(id):
    conn = db_connection()
    cur = conn.cursor()

    if request.method == "GET":
        c = cur.execute("SELECT * FROM customers WHERE id=?;", (id,)).fetchone()
        if not c:
            return jsonify({"error": "No existe"}), 404

        addrs = [dict(r) for r in cur.execute("SELECT * FROM addresses WHERE customer_id=?;", (id,)).fetchall()]
        pays  = [dict(r) for r in cur.execute("""                SELECT id, gateway, token, brand, last4, exp_month, exp_year, billing_name, billing_address_id, created_at
                FROM payment_methods WHERE customer_id=?;
            """, (id,)).fetchall()]

        return jsonify({
            "customer": dict(c),
            "addresses": addrs,
            "payment_methods": pays
        })

    if request.method == "PUT":
        data = body()
        # solo campos permitidos
        fields = ["nombre", "apellido", "email", "telefono_e164",
                  "email_verified_at", "consent_marketing", "consent_terminos", "consent_privacidad"]
        sets, vals = [], []
        for f in fields:
            if f in data and data[f] is not None:
                sets.append(f"{f}=?")
                vals.append(data[f])

        if not sets:
            return jsonify({"error": "Nada que actualizar"}), 400

        vals.append(id)
        try:
            cur.execute(f"""                UPDATE customers SET {", ".join(sets)}, updated_at = datetime('now') WHERE id=?;
            """, vals)
            conn.commit()
        except sqlite3.IntegrityError as e:
            return jsonify({"error": "email duplicado o constraint violada", "detail": str(e)}), 409

        return jsonify({"id": id, "message": "Cliente actualizado"})

    if request.method == "DELETE":
        cur.execute("DELETE FROM customers WHERE id=?;", (id,))
        conn.commit()
        return jsonify({"message": f"Cliente {id} eliminado"}), 200

# ---------- Addresses ----------
@app.route("/customers/<int:id>/addresses", methods=["GET", "POST"])
def customer_addresses(id):
    conn = db_connection()
    cur = conn.cursor()

    # validar cliente
    if not cur.execute("SELECT 1 FROM customers WHERE id=?;", (id,)).fetchone():
        return jsonify({"error": "Cliente no existe"}), 404

    if request.method == "GET":
        rows = cur.execute("SELECT * FROM addresses WHERE customer_id=?;", (id,)).fetchall()
        return jsonify([dict(r) for r in rows])

    if request.method == "POST":
        data = body()
        linea1 = data.get("linea1")
        pais   = data.get("pais")
        if not (linea1 and pais):
            return jsonify({"error": "linea1 y pais son obligatorios"}), 400

        linea2 = data.get("linea2")
        distrito = data.get("distrito")
        provincia = data.get("provincia")
        region = data.get("region")
        codigo_postal = data.get("codigo_postal")
        tipo = data.get("tipo", "principal")
        es_principal = int(data.get("es_principal", 0))

        cur.execute("""          INSERT INTO addresses (customer_id, linea1, linea2, distrito, provincia, region, pais,
                                 codigo_postal, tipo, es_principal)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id, linea1, linea2, distrito, provincia, region, pais, codigo_postal, tipo, es_principal))
        conn.commit()
        return jsonify({"id": cur.lastrowid, "message": "Dirección creada"}), 201

# ---------- Payment Methods (tokenizados) ----------
@app.route("/customers/<int:id>/payment-methods", methods=["GET", "POST"])
def customer_payments(id):
    conn = db_connection()
    cur = conn.cursor()

    # validar cliente
    if not cur.execute("SELECT 1 FROM customers WHERE id=?;", (id,)).fetchone():
        return jsonify({"error": "Cliente no existe"}), 404

    if request.method == "GET":
        rows = cur.execute("""            SELECT id, gateway, token, brand, last4, exp_month, exp_year,
                   billing_name, billing_address_id, created_at
            FROM payment_methods WHERE customer_id=?;
        """, (id,)).fetchall()
        return jsonify([dict(r) for r in rows])

    if request.method == "POST":
        data = body()
        gateway = data.get("gateway")
        token   = data.get("token")
        brand   = data.get("brand")
        last4   = data.get("last4")
        exp_month = data.get("exp_month")
        exp_year  = data.get("exp_year")
        billing_name = data.get("billing_name")
        billing_address_id = data.get("billing_address_id")

        if not (gateway and token):
            return jsonify({"error": "gateway y token son obligatorios"}), 400

        cur.execute("""          INSERT INTO payment_methods (customer_id, gateway, token, brand, last4, exp_month, exp_year,
                                       billing_name, billing_address_id)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id, gateway, token, brand, last4, exp_month, exp_year, billing_name, billing_address_id))
        conn.commit()
        return jsonify({"id": cur.lastrowid, "message": "Método de pago registrado"}), 201

if __name__ == '__main__':
    # igual que tu app: expuesto en 0.0.0.0:8000
    app.run(host='0.0.0.0', port=8000, debug=False)
