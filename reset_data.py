import os
import sqlite3
from pathlib import Path
import database

root = Path(__file__).resolve().parent
os.chdir(root)

for path in [
    root / 'database' / 'business.db',
    root / 'database' / 'business.db-shm',
    root / 'database' / 'business.db-wal',
]:
    if path.exists():
        path.unlink()

database.create_tables()
database.run_migrations()

conn = sqlite3.connect(root / 'database' / 'business.db')
cur = conn.cursor()
print('products', cur.execute('select count(*) from products').fetchone()[0])
print('customers', cur.execute('select count(*) from customers').fetchone()[0])
print('invoices', cur.execute('select count(*) from invoices').fetchone()[0])
print('invoice_items', cur.execute('select count(*) from invoice_items').fetchone()[0])
print('categories', cur.execute('select count(*) from categories').fetchone()[0])
conn.close()
