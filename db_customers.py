# db_customers.py
import sqlite3

conn = sqlite3.connect("customers.sqlite")
cursor = conn.cursor()

# Activar FKs
cursor.execute("PRAGMA foreign_keys = ON;")

# Tabla principal de clientes
cursor.execute("""CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY,
  nombre TEXT NOT NULL,
  apellido TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  telefono_e164 TEXT,
  email_verified_at TEXT,
  consent_marketing INTEGER DEFAULT 0,
  consent_terminos INTEGER DEFAULT 0,
  consent_privacidad INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
""")

# Direcciones (1..n)
cursor.execute("""CREATE TABLE IF NOT EXISTS addresses (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  linea1 TEXT NOT NULL,
  linea2 TEXT,
  distrito TEXT,
  provincia TEXT,
  region TEXT,
  pais TEXT NOT NULL,
  codigo_postal TEXT,
  tipo TEXT CHECK (tipo IN ('envio','facturacion','principal')) DEFAULT 'principal',
  es_principal INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
""")

# Métodos de pago tokenizados (sin PAN)
cursor.execute("""CREATE TABLE IF NOT EXISTS payment_methods (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  gateway TEXT NOT NULL,   -- p.ej. Culqi/Stripe/MercadoPago
  token TEXT NOT NULL,     -- token del gateway
  brand TEXT,              -- VISA/MASTERCARD/etc.
  last4 CHAR(4),
  exp_month INTEGER,
  exp_year INTEGER,
  billing_name TEXT,
  billing_address_id INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (billing_address_id) REFERENCES addresses(id) ON DELETE SET NULL
);
""")

# Índices
cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_addresses_customer ON addresses(customer_id);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_customer ON payment_methods(customer_id);")

conn.commit()
conn.close()
print("BD customers.sqlite creada/actualizada correctamente.")
