# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET
import csv
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(script_dir, ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from database import get_connection

ods_path = os.path.join(project_dir, "INVENTORY SARTAJ 0786 (1).ods")
if not os.path.exists(ods_path):
    print("Error: ODS file not found")
    sys.exit(1)

print("Reading ODS file: " + ods_path)
with zipfile.ZipFile(ods_path, 'r') as z:
    with z.open('content.xml') as f:
        tree = ET.parse(f)
        root = tree.getroot()

ns = {
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
}

all_rows = []
for table in root.findall('.//table:table', ns):
    for row in table.findall('.//table:table-row', ns):
        row_cells = []
        for cell in row.findall('.//table:table-cell', ns):
            rep = int(cell.attrib.get('{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated', 1))
            texts = [t.text for t in cell.findall('.//text:p', ns) if t.text]
            val = ' '.join(texts) if texts else ''
            for _ in range(min(rep, 30)):
                row_cells.append(val)
        while row_cells and not row_cells[-1]:
            row_cells.pop()
        if any(row_cells):
            all_rows.append(row_cells)

print("Successfully extracted rows: " + str(len(all_rows)))

# Write standard UTF-8 CSV
csv_dest = os.path.join(project_dir, "INVENTORY_SARTAJ_0786.csv")
desktop_csv = os.path.join(os.path.expanduser("~"), "Desktop", "INVENTORY_SARTAJ_0786.csv")

for p in [csv_dest, desktop_csv]:
    try:
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            for r in all_rows:
                writer.writerow(r)
        print("Saved CSV to: " + p)
    except Exception as e:
        print("Could not write to " + str(p) + ": " + str(e))

# Parse rows
headers = [str(h).strip().lstrip('\ufeff').lower() for h in all_rows[0]]
print("Headers detected: " + str(headers))

conn = get_connection()
cursor = conn.cursor()

added_count = 0
updated_count = 0
skipped_count = 0

for raw_cells in all_rows[1:]:
    row = {}
    for idx, h in enumerate(headers):
        val = raw_cells[idx] if idx < len(raw_cells) else ''
        row[h] = val

    category = (row.get('category') or row.get('cat') or row.get('group') or 'General').strip() or 'General'
    product_name = (row.get('name') or row.get('product name') or row.get('product') or row.get('item name') or row.get('item') or '').strip()

    if not product_name:
        skipped_count += 1
        continue

    try:
        mrp = float(str(row.get('mrp') or 0).replace(',', '').strip() or 0)
    except Exception:
        mrp = 0.0

    try:
        pp_val = str(row.get('purchase') or row.get('purchase price') or row.get('purchase_price') or row.get('cost') or 0).replace(',', '').strip()
        purchase_price = float(pp_val or 0)
    except Exception:
        purchase_price = 0.0

    try:
        sp_val = str(row.get('selling') or row.get('selling price') or row.get('selling_price') or row.get('price') or row.get('rate') or 0).replace(',', '').strip()
        selling_price = float(sp_val or 0)
    except Exception:
        selling_price = 0.0

    try:
        st_val = str(row.get('stock') or row.get('qty') or row.get('quantity') or 0).replace(',', '').strip()
        stock = int(float(st_val or 0))
    except Exception:
        stock = 0

    unit = str(row.get('unit') or row.get('uom') or 'Pcs').strip() or 'Pcs'
    discount_base = str(row.get('discount on') or row.get('discount_base') or 'Price').strip()
    if discount_base.lower() in ('mrp', 'on mrp'):
        discount_base = 'MRP'
    else:
        discount_base = 'Price'

    try:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,))
    except Exception:
        pass

    cursor.execute("""
        SELECT id FROM products
        WHERE LOWER(TRIM(COALESCE(category, 'General'))) = LOWER(TRIM(?))
          AND LOWER(TRIM(name)) = LOWER(TRIM(?))
        LIMIT 1
    """, (category, product_name))
    existing_prod = cursor.fetchone()

    if existing_prod:
        cursor.execute("""
            UPDATE products
            SET mrp = ?, purchase_price = ?, selling_price = ?, unit = ?, stock = ?, discount_base = ?
            WHERE id = ?
        """, (mrp, purchase_price, selling_price, unit, stock, discount_base, existing_prod[0]))
        updated_count += 1
    else:
        cursor.execute("""
            INSERT INTO products(category, name, mrp, purchase_price, selling_price, unit, stock, discount_base)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (category, product_name, mrp, purchase_price, selling_price, unit, stock, discount_base))
        added_count += 1

conn.commit()

cursor.execute("SELECT COUNT(*) FROM products")
total_prods = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM categories")
total_cats = cursor.fetchone()[0]

conn.close()

print("--------------------------------------------------")
print("IMPORT SUMMARY:")
print("  - New Products Added:   " + str(added_count))
print("  - Existing Updated:     " + str(updated_count))
print("  - Skipped (blank):      " + str(skipped_count))
print("  - Total Products in DB: " + str(total_prods))
print("  - Total Categories:     " + str(total_cats))
print("--------------------------------------------------")
