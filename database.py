import sqlite3
import os

from config import DATABASE_PATH


# =========================
# CONNECTION
# =========================

def get_connection():
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    try:
        conn = sqlite3.connect(
            DATABASE_PATH,
            timeout=10.0
        )
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    except sqlite3.OperationalError as e:
        raise Exception(f"Failed to open database at {DATABASE_PATH}: {str(e)}")

# =========================
# AUTO MIGRATIONS
# =========================

def column_exists(
    table_name,
    column_name
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(f"""
    PRAGMA table_info({table_name})
    """)

    columns = cursor.fetchall()

    conn.close()

    for column in columns:

        if column[1] == column_name:
            return True

    return False


# =========================
# AUTO MIGRATIONS
# =========================

def column_exists(
    table_name,
    column_name
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(f"""
    PRAGMA table_info({table_name})
    """)

    columns = cursor.fetchall()

    conn.close()

    for column in columns:

        if column[1] == column_name:
            return True

    return False


def run_migrations():

    conn = get_connection()

    cursor = conn.cursor()

    # =========================
    # INVOICES TABLE
    # =========================

    if not column_exists(
        "invoices",
        "invoice_number"
    ):

        cursor.execute("""
        ALTER TABLE invoices
        ADD COLUMN invoice_number TEXT
        """)

    if not column_exists(
        "invoices",
        "invoice_date"
    ):

        cursor.execute("""
        ALTER TABLE invoices
        ADD COLUMN invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)

    if not column_exists(
        "invoices",
        "note"
    ):

        cursor.execute("""
        ALTER TABLE invoices
        ADD COLUMN note TEXT DEFAULT ''
        """)

    # =========================
    # PRODUCTS TABLE
    # =========================

    if not column_exists(
        "products",
        "category"
    ):

        cursor.execute("""
        ALTER TABLE products
        ADD COLUMN category TEXT
        """)

    if not column_exists(
        "products",
        "unit"
    ):

        cursor.execute("""
        ALTER TABLE products
        ADD COLUMN unit TEXT
        """)

    if not column_exists(
        "products",
        "discount_base"
    ):

        cursor.execute("""
        ALTER TABLE products
        ADD COLUMN discount_base TEXT DEFAULT 'Price'
        """)

    # =========================
    # CUSTOMERS TABLE
    # =========================

    if not column_exists(
        "customers",
        "phone"
    ):

        cursor.execute("""
        ALTER TABLE customers
        ADD COLUMN phone TEXT
        """)

    if not column_exists(
        "customers",
        "address"
    ):

        cursor.execute("""
        ALTER TABLE customers
        ADD COLUMN address TEXT
        """)

    # =========================
    # INVOICE ITEMS TABLE
    # =========================

    if not column_exists(
        "invoice_items",
        "total"
    ):

        cursor.execute("""
        ALTER TABLE invoice_items
        ADD COLUMN total REAL
        """)

    if not column_exists(
        "invoice_items",
        "unit"
    ):

        cursor.execute("""
        ALTER TABLE invoice_items
        ADD COLUMN unit TEXT
        """)

    if not column_exists(
        "invoice_items",
        "custom_price"
    ):

        cursor.execute("""
        ALTER TABLE invoice_items
        ADD COLUMN custom_price REAL
        """)

    if not column_exists(
        "invoice_items",
        "discount_base"
    ):

        cursor.execute("""
        ALTER TABLE invoice_items
        ADD COLUMN discount_base TEXT DEFAULT 'Price'
        """)

    if not column_exists(
        "invoice_items",
        "mrp"
    ):

        cursor.execute("""
        ALTER TABLE invoice_items
        ADD COLUMN mrp REAL
        """)

    conn.commit()

    conn.close()

# =========================
# CREATE TABLES
# =========================

def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    # PRODUCTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        name TEXT,
        mrp REAL,
        purchase_price TEXT,
        selling_price REAL,
        stock INTEGER,
        discount_base TEXT DEFAULT 'Price'
    )
    """)

    # CUSTOMERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    # INVOICES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        total REAL,
        paid REAL,
        pending REAL,
        invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        note TEXT DEFAULT ''
    )
    """)

    # INVOICE ITEMS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        mrp REAL,
        price REAL,
        discount REAL,
        total REAL,
        discount_base TEXT DEFAULT 'Price'
    )
    """)

    # CATEGORIES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    conn.commit()

    conn.close()


def reset_application_data():
    """Clear all transactional and inventory data so the app starts fresh."""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM invoice_items")
    cursor.execute("DELETE FROM invoices")
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM categories")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if cursor.fetchone():
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('products', 'customers', 'invoices', 'invoice_items', 'categories')")

    conn.commit()
    conn.close()


# =========================
# CATEGORY FUNCTIONS
# =========================

def add_category(category_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO categories(name)
    VALUES(?)
    """, (
        category_name,
    ))

    conn.commit()

    conn.close()


def get_all_categories():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT name
    FROM categories
    ORDER BY name
    """)

    data = cursor.fetchall()

    conn.close()

    return [row[0] for row in data]


# =========================
# PRODUCT FUNCTIONS
# =========================

def add_product(
    name,
    mrp,
    purchase_price,
    selling_price,
    stock,
    discount_base="Price"
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO products(
        name,
        mrp,
        purchase_price,
        selling_price,
        unit,
        stock,
        COALESCE(discount_base, 'Price')
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        mrp,
        purchase_price,
        selling_price,
        stock,
        discount_base
    ))

    conn.commit()

    conn.close()


def get_all_products():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        category,
        name,
        mrp,
        purchase_price,
        selling_price,
        stock,
        discount_base
    FROM products
    """)

    products = cursor.fetchall()

    conn.close()

    return products


def get_product_names():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        category,
        name
    FROM products
    WHERE stock > 0
    ORDER BY category, name
    """)

    data = cursor.fetchall()

    conn.close()

    formatted_products = []

    for row in data:

        category = row[0] if row[0] else "General"

        name = row[1]

        formatted_products.append(
            f"{category} - {name}"
        )

    return formatted_products


def get_product_by_name(product_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        name,
        selling_price,
        stock
    FROM products
    WHERE name = ?
    """, (
        product_name,
    ))

    product = cursor.fetchone()

    conn.close()

    return product


def update_stock(product_id, new_stock):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    UPDATE products
    SET stock = ?
    WHERE id = ?
    """, (
        new_stock,
        product_id
    ))

    conn.commit()

    conn.close()


# =========================
# CUSTOMER FUNCTIONS
# =========================

def get_or_create_customer(customer_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM customers
    WHERE name = ?
    """, (
        customer_name,
    ))

    customer = cursor.fetchone()

    if customer:

        customer_id = customer[0]

    else:

        cursor.execute("""
        INSERT INTO customers(name)
        VALUES(?)
        """, (
            customer_name,
        ))

        conn.commit()

        customer_id = cursor.lastrowid

    conn.close()

    return customer_id


def get_customer_names_with_phone():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        name,
        phone
    FROM customers
    ORDER BY name
    """)

    data = cursor.fetchall()

    conn.close()

    formatted = []

    for row in data:

        name = row[0]

        phone = (
            row[1]
            if row[1]
            else ""
        )

        formatted.append(
            f"{name} ({phone})"
        )

    return formatted


# =========================
# SAVE COMPLETE INVOICE
# =========================

def save_complete_invoice(
    customer_name,
    cart_items,
    grand_total,
    paid_amount,
    note=""
):

    customer_id = get_or_create_customer(
        customer_name
    )

    pending = (
        grand_total - paid_amount
    )

    conn = get_connection()

    cursor = conn.cursor()

# GENERATE DAILY INVOICE NUMBER 
    invoice_number = generate_invoice_number() 
    # CREATE INVOICE 
    cursor.execute(""" INSERT INTO invoices( invoice_number, customer_id, total, paid, pending, note 
    )                    
    VALUES (?, ?, ?, ?, ?, ?) """, ( invoice_number, customer_id, grand_total, paid_amount, pending, note )
    )

    invoice_id = cursor.lastrowid

    # SAVE ITEMS
    for item in cart_items:

        cursor.execute("""
        INSERT INTO invoice_items(
            invoice_id,
            product_id,
            quantity,
            mrp,
            price,
            discount,
            total,
            discount_base
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            item["product_id"],
            item["quantity"],
            item["mrp"],
            item["price"],
            item["discount"],
            item["total"],
            item.get("discount_base", "Price")
        ))

        # UPDATE STOCK
        cursor.execute("""
        SELECT stock
        FROM products
        WHERE id = ?
        """, (
            item["product_id"],
        ))

        old_stock = cursor.fetchone()[0]

        new_stock = (
            old_stock - item["quantity"]
        )

        cursor.execute("""
        UPDATE products
        SET stock = ?
        WHERE id = ?
        """, (
            new_stock,
            item["product_id"]
        ))

    conn.commit()

    conn.close()

    return invoice_number


# =========================
# LEDGER
# =========================

def get_ledger_data():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        invoices.id,
        customers.name,
        invoices.total,
        invoices.paid,
        invoices.pending,
        invoices.invoice_date

    FROM invoices

    JOIN customers
    ON invoices.customer_id = customers.id

    ORDER BY invoices.id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


# =========================
# CUSTOMER HISTORY
# =========================

def get_customer_history(customer_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        invoices.id,
        invoices.invoice_date,
        products.name,
        invoice_items.quantity,
        invoices.total,
        invoices.paid,
        invoices.pending

    FROM invoices

    JOIN customers
    ON invoices.customer_id = customers.id

    JOIN invoice_items
    ON invoices.id = invoice_items.invoice_id

    JOIN products
    ON invoice_items.product_id = products.id

    WHERE customers.name = ?

    ORDER BY invoices.id DESC
    """, (
        customer_name,
    ))

    data = cursor.fetchall()

    conn.close()

    return data


# =========================
# DASHBOARD
# =========================

def get_total_products():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM products
    """)

    total = cursor.fetchone()[0]

    conn.close()

    return total


def get_total_customers():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(DISTINCT name)
    FROM customers
    """)

    total = cursor.fetchone()[0]

    conn.close()

    return total


def get_total_pending_amount():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT SUM(pending)
    FROM invoices
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result if result else 0


def get_today_sales():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT SUM(total)
    FROM invoices
    WHERE date(invoice_date) = date('now')
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result if result else 0


def get_low_stock_items():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        name,
        stock
    FROM products
    WHERE stock <= 5
    ORDER BY stock ASC
    """)

    data = cursor.fetchall()

    conn.close()

    return data

def get_customer_ledger():

    return get_ledger_data()

def get_total_pending(customer_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT SUM(invoices.pending)

    FROM invoices

    JOIN customers
    ON invoices.customer_id = customers.id

    WHERE customers.name = ?
    """, (
        customer_name,
    ))

    result = cursor.fetchone()[0]

    conn.close()

    return result if result else 0

def get_product_complete_details(product_name):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        name,
        mrp,
        selling_price,
        stock,
        unit,
        COALESCE(discount_base, 'Price')
    FROM products
    WHERE name = ?
    """, (product_name,))

    product = cursor.fetchone()

    conn.close()

    return product


# =====================================
# GET CUSTOMER NAMES
# =====================================

def get_customer_names():

    conn = sqlite3.connect(
        "database/business.db"
    )

    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT customer_name
        FROM invoices
        ORDER BY customer_name
    """)

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]

# =====================================
# GENERATE DAILY INVOICE NUMBER
# =====================================

from datetime import datetime


def generate_invoice_number():

    conn = get_connection()

    cursor = conn.cursor()

    today = datetime.now().strftime("%d%m%y")

    pattern = f"{today}_%"

    cursor.execute(
        """
        SELECT invoice_number
        FROM invoices
        WHERE invoice_number LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (pattern,)
    )

    last_invoice = cursor.fetchone()

    if last_invoice and last_invoice[0]:

        last_number = int(
            last_invoice[0].split("_")[1]
        )

        next_number = last_number + 1

    else:

        next_number = 1

    invoice_number = (
        f"{today}_{next_number:02d}"
    )

    conn.close()

    return invoice_number


# =====================================
# LEDGER OPTIMIZATION FUNCTIONS
# =====================================

def get_customers_with_pending():
    """Get list of unique customers with their total pending amounts"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        customers.name,
        SUM(invoices.pending) as total_pending,
        COUNT(invoices.id) as invoice_count
    FROM customers
    JOIN invoices ON customers.id = invoices.customer_id
    WHERE invoices.pending > 0
    GROUP BY customers.id, customers.name
    ORDER BY total_pending DESC
    """)

    data = cursor.fetchall()
    conn.close()
    return data


def get_customer_invoices(customer_name):
    """Get all invoices for a specific customer"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        invoices.id,
        invoices.invoice_number,
        COALESCE(strftime('%d-%m-%Y', invoices.invoice_date), 'N/A'),
        invoices.total,
        invoices.paid,
        invoices.pending,
        COALESCE(invoices.note, '')
    FROM invoices
    JOIN customers ON invoices.customer_id = customers.id
    WHERE customers.name = ?
    ORDER BY invoices.id DESC
    """, (customer_name,))

    data = cursor.fetchall()
    conn.close()
    return data


def update_invoice_payment(invoice_id, new_paid_amount):
    """Update payment amount for an invoice"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get current total
    cursor.execute("""
    SELECT total FROM invoices WHERE id = ?
    """, (invoice_id,))

    total = cursor.fetchone()[0]

    # Calculate pending
    new_pending = max(0, total - new_paid_amount)

    # Update invoice
    cursor.execute("""
    UPDATE invoices
    SET paid = ?, pending = ?
    WHERE id = ?
    """, (new_paid_amount, new_pending, invoice_id))

    conn.commit()
    conn.close()


def get_invoice_details_by_id(invoice_id):
    """Get complete invoice details by ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        invoices.id,
        invoices.invoice_number,
        customers.name,
        COALESCE(strftime('%d-%m-%Y', invoices.invoice_date), 'N/A'),
        invoices.total,
        invoices.paid,
        invoices.pending,
        COALESCE(invoices.note, '')
    FROM invoices
    JOIN customers ON invoices.customer_id = customers.id
    WHERE invoices.id = ?
    """, (invoice_id,))

    data = cursor.fetchone()
    conn.close()
    return data


def get_invoice_items(invoice_id):
    """Get all items in an invoice"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        invoice_items.quantity,
        products.name,
        invoice_items.price,
        products.unit,
        invoice_items.discount,
        COALESCE(invoice_items.discount_base, 'Price'),
        invoice_items.total
    FROM invoice_items
    JOIN products ON invoice_items.product_id = products.id
    WHERE invoice_items.invoice_id = ?
    ORDER BY invoice_items.id
    """, (invoice_id,))

    data = cursor.fetchall()
    conn.close()
    return data


def update_invoice_note(invoice_id, note):
    """Update note for an invoice"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE invoices
    SET note = ?
    WHERE id = ?
    """, (note, invoice_id))

    conn.commit()
    conn.close()
