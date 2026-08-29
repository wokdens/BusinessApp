import tkinter as tk
from tkinter import filedialog
import csv


from tkinter import ttk, messagebox, simpledialog

from database import (
    get_connection,
    get_all_categories,
    add_category
)

from ui.autocomplete_combobox import AutocompleteCombobox
from ui.admin_auth_dialog import request_admin_pin



class InventoryUI:

    def __init__(self, parent):

        self.parent = parent

        self.selected_product_id = None

        self.frame = tk.Frame(parent)

        self.frame.pack(
            fill="both",
            expand=True
        )

        # =========================
        # TITLE
        # =========================

        title = tk.Label(
            self.frame,
            text="Inventory Management",
            font=("Arial", 18, "bold")
        )
        
        # scroll_y = ttk.Scrollbar(
        #     table_frame,
        #     orient="vertical",
        #     command=self.tree.yview
        # )

        # scroll_x = ttk.Scrollbar(
        #     table_frame,
        #     orient="horizontal",
        #     command=self.tree.xview
        # )

        # self.tree.configure(
        #     yscrollcommand=scroll_y.set,
        #     xscrollcommand=scroll_x.set
        # )

        title.pack(pady=10)

        # =========================
        # SEARCH
        # =========================

        search_frame = tk.Frame(self.frame)

        search_frame.pack(
            fill="x",
            padx=20
        )

        tk.Label(
            search_frame,
            text="Search Product:",
            font=("Arial", 11, "bold")
        ).pack(side="left")

        self.search_entry = tk.Entry(
            search_frame,
            width=30
        )

        self.search_entry.pack(
            side="left",
            padx=10
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.search_products
        )

        # =========================
        # FORM
        # =========================

        form_frame = tk.LabelFrame(
            self.frame,
            text="Product Details",
            padx=15,
            pady=15
        )

        form_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        # CATEGORY
        tk.Label(
            form_frame,
            text="Category"
        ).grid(
            row=0,
            column=0,
            padx=10,
            pady=5
        )

        self.category_combo = AutocompleteCombobox(
            form_frame,
            width=27
        )

        self.category_combo.grid(
            row=0,
            column=1
        )

        self.refresh_categories()

        add_category_btn = tk.Button(
            form_frame,
            text="+ Add Category",
            command=self.create_category,
            bg="#ffcc66",
            font=("Arial", 10, "bold")
        )

        add_category_btn.grid(
            row=0,
            column=2,
            padx=10
        )   
        
        self.import_btn = tk.Button(
            form_frame,
            text="Import CSV",
            width=15,
            command=self.import_products_csv,
            bg="#ffcc66",
            font=("Arial", 10, "bold")
        )
        
        self.export_btn = tk.Button(
            form_frame,
            text="Export CSV",
            width=15,
            command=self.export_products_csv,
            bg="#90EE90",
            font=("Arial", 10, "bold")
        )

        self.export_btn.grid(
            row=0,
            column=4,
            padx=10,
            pady=5
        )

        self.import_btn.grid(
            row=0,
            column=3,
            padx=10,
            pady=5
        )

        # PRODUCT NAME
        tk.Label(
            form_frame,
            text="Product Name"
        ).grid(
            row=1,
            column=0,
            padx=10,
            pady=5
        )

        self.name_entry = tk.Entry(
            form_frame,
            width=30
        )

        self.name_entry.grid(
            row=1,
            column=1
        )

        # MRP
        tk.Label(
            form_frame,
            text="MRP"
        ).grid(
            row=2,
            column=0,
            padx=10,
            pady=5
        )

        self.mrp_entry = tk.Entry(
            form_frame,
            width=30
        )

        self.mrp_entry.grid(
            row=2,
            column=1
        )

        # PURCHASE PRICE
        tk.Label(
            form_frame,
            text="Purchase Price"
        ).grid(
            row=3,
            column=0,
            padx=10,
            pady=5
        )

        self.purchase_entry = tk.Entry(
            form_frame,
            width=30
        )

        self.purchase_entry.grid(
            row=3,
            column=1
        )

        # SELLING PRICE
        tk.Label(
            form_frame,
            text="Selling Price"
        ).grid(
            row=4,
            column=0,
            padx=10,
            pady=5
        )

        self.selling_entry = tk.Entry(
            form_frame,
            width=30
        )

        self.selling_entry.grid(
            row=4,
            column=1
        )
        
        tk.Label(
            form_frame,
            text="Unit"
        ).grid(
            row=5,
            column=0,
            padx=10,
            pady=5
        )

        self.unit_entry = tk.Entry(
            form_frame,
            width=30
        )

        self.unit_entry.grid(
            row=5,
            column=1
        )
        # STOCK
        tk.Label(
            form_frame,
            text="Stock Quantity"
        ).grid(
            row=6,
            column=0,
            padx=10,
            pady=5
        )

        self.stock_entry = tk.Entry(
            form_frame,
            width=30
        )

        self.stock_entry.grid(
            row=6,
            column=1
        )

        tk.Label(
            form_frame,
            text="Discount On"
        ).grid(
            row=7,
            column=0,
            padx=10,
            pady=5
        )

        self.discount_base_combo = ttk.Combobox(
            form_frame,
            values=("Price", "MRP"),
            state="readonly",
            width=27
        )
        self.discount_base_combo.set("Price")
        self.discount_base_combo.grid(
            row=7,
            column=1
        )

        # =========================
        # BUTTONS
        # =========================

        btn_frame = tk.Frame(form_frame)

        btn_frame.grid(
            row=8,
            column=0,
            columnspan=3,
            pady=15
        )

        tk.Button(
            btn_frame,
            text="Add Product",
            width=15,
            command=self.save_product,
            fg="white",
            bg="#5634f0",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Update Product",
            width=15,
            command=self.update_product,
            fg="white",
            bg="#5634f0",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Delete Product",
            width=15,
            command=self.delete_product,
            fg="white",
            bg="#ea1b1b",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Clear",
            width=15,
            command=self.clear_form,
            fg="white",
            bg="#ea1b1b",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)

        # =========================
        # TABLE
        # =========================

        columns = (
            "ID",
            "Category",
            "Name",
            "MRP",
            "Purchase",
            "Selling",
            "Unit",
            "Stock",
            "Discount On"
        )

        style = ttk.Style()

        style.configure(
            "Treeview.Heading",
            font=("Arial", 11, "bold")
        )

        style.configure(
            "Treeview",
            font=("Arial", 10),
            rowheight=28
        )
        
        table_frame = tk.Frame(
            self.frame
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )
        
        scroll_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        # scroll_x = ttk.Scrollbar(
        #     table_frame,
        #     orient="horizontal",
        #     command=self.tree.xview
        # )

        self.tree.configure(
            yscrollcommand=scroll_y.set,
            # xscrollcommand=scroll_x.set
        )

        for col in columns:

            self.tree.heading(
                col,
                text=col,
                anchor="w"
            )

            self.tree.column(
                col,
                width=140,
                anchor="w"
            )

            # self.tree.pack(
            #     side="left",
            #     fill="both",
            #     expand=True
            # )

            # scroll_y.pack(
            #     side="right",
            #     fill="y"
            # )

            # scroll_x.pack(
            #     side="bottom",
            #     fill="x"
            # )
            
        self.tree.pack(
                side="left",
                fill="both",
                expand=True
        )

        scroll_y.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_product
        )

        self.all_products = []

        self.load_products()

    # =========================
    # REFRESH CATEGORIES
    # =========================

    def refresh_categories(self):

        categories = get_all_categories()

        self.category_combo.set_completion_list(
            categories
        )

    # =========================
    # CREATE CATEGORY
    # =========================

    def create_category(self):

        category_name = simpledialog.askstring(
            "Category",
            "Enter category name"
        )

        if not category_name:
            return

        add_category(category_name)

        self.refresh_categories()

        self.category_combo.set(category_name)

    # =========================
    # LOAD PRODUCTS
    # =========================

    def load_products(self):

        self.tree.delete(
            *self.tree.get_children()
        )

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
            unit,
            stock,
            COALESCE(discount_base, 'Price')
        FROM products
        ORDER BY id DESC
        """)

        products = cursor.fetchall()

        conn.close()

        self.all_products = products

        for product in products:

            self.tree.insert(
                "",
                "end",
                iid=str(product[0]),
                values=product
            )

    # =========================
    # SEARCH PRODUCTS
    # =========================

    def search_products(self, event):

        keyword = (
            self.search_entry.get()
            .lower()
        )

        self.tree.delete(
            *self.tree.get_children()
        )

        for product in self.all_products:

            category = str(product[1]).lower()

            name = str(product[2]).lower()

            if (
                keyword in category
                or keyword in name
            ):

                self.tree.insert(
                    "",
                    "end",
                    iid=str(product[0]),
                    values=product
                )

    # =========================
    # SAVE PRODUCT
    # =========================

    def save_product(self):

        conn = get_connection()

        cursor = conn.cursor()

        # Product Name validation
        if not self.name_entry.get().strip():
            messagebox.showerror(
                "Missing Information",
                "Please enter Product Name."
            )
            self.name_entry.focus()
            return

        # Unit validation
        if not self.unit_entry.get().strip():
            messagebox.showerror(
                "Missing Information",
                "Please enter Unit."
            )
            self.unit_entry.focus()
            return

        cursor.execute("""
        INSERT INTO products(
            category,
            name,
            mrp,
            purchase_price,
            selling_price,
            unit,
            stock,
            discount_base
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.category_combo.get().strip(),
            self.name_entry.get(),
            float(self.mrp_entry.get().strip() or 0),
            float(self.purchase_entry.get().strip() or 0),
            float(self.selling_entry.get().strip() or 0),
            self.unit_entry.get(),
            int(self.stock_entry.get() or 0),
            self.discount_base_combo.get() or "Price"
        ))
        
       

        conn.commit()

        conn.close()

        messagebox.showinfo(
            "Success",
            "Product added successfully"
        )

        self.load_products()

        self.clear_form()

    # =========================
    # SELECT PRODUCT
    # =========================

    def select_product(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        item_id = selected[0]

        values = self.tree.item(
            item_id
        )["values"]

        self.selected_product_id = values[0]

        self.clear_form_fields()

        self.category_combo.set(values[1])

        self.name_entry.insert(0, values[2])

        self.mrp_entry.insert(0, values[3])

        self.purchase_entry.insert(0, values[4])

        self.selling_entry.insert(0, values[5])
        
        self.unit_entry.insert(0, values[6])
        
        self.stock_entry.insert(0, values[7])

        self.discount_base_combo.set(values[8] if len(values) > 8 else "Price")

    # =========================
    # UPDATE PRODUCT
    # =========================

    def update_product(self):

        if self.selected_product_id is None:

            messagebox.showerror(
                "Error",
                "Select product first"
            )

            return

        # Security: Require Admin PIN to modify existing pricing / product info
        if not request_admin_pin(self.frame, "modify product pricing and details"):
            return

        try:
            mrp_val = float(self.mrp_entry.get().strip() or 0)
            purchase_val = float(self.purchase_entry.get().strip() or 0)
            selling_val = float(self.selling_entry.get().strip() or 0)
            stock_val = int(self.stock_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for MRP, Purchase Price, Selling Price, and Stock.")
            return

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
        UPDATE products
        SET
            category = ?,
            name = ?,
            mrp = ?,
            purchase_price = ?,
            selling_price = ?,
            unit = ?,
            stock = ?,
            discount_base = ?
        WHERE id = ?
        """, (
            self.category_combo.get().strip() or "General",
            self.name_entry.get().strip(),
            mrp_val,
            purchase_val,
            selling_val,
            self.unit_entry.get().strip() or "Pcs",
            stock_val,
            self.discount_base_combo.get() or "Price",
            self.selected_product_id
        ))

        conn.commit()

        conn.close()

        messagebox.showinfo(
            "Success",
            "Product updated successfully"
        )

        self.load_products()

        self.clear_form()

    # =========================
    # DELETE PRODUCT
    # =========================

    def delete_product(self):

        if self.selected_product_id is None:

            messagebox.showerror(
                "Error",
                "Select product first"
            )

            return

        # Security: Require Admin PIN to delete product
        if not request_admin_pin(self.frame, "delete this product from inventory"):
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Delete this product?"
        )

        if not confirm:
            return

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
        DELETE FROM products
        WHERE id = ?
        """, (
            self.selected_product_id,
        ))

        conn.commit()

        conn.close()

        messagebox.showinfo(
            "Success",
            "Product deleted successfully"
        )

        self.load_products()

        self.clear_form()


    # =========================
    # CLEAR FORM FIELDS
    # =========================

    def clear_form_fields(self):

        self.category_combo.set("")

        self.name_entry.delete(0, tk.END)

        self.mrp_entry.delete(0, tk.END)

        self.purchase_entry.delete(0, tk.END)

        self.selling_entry.delete(0, tk.END)
        
        self.unit_entry.delete(0, tk.END)

        self.stock_entry.delete(0, tk.END)

        self.discount_base_combo.set("Price")

    # =========================
    # CLEAR FORM
    # =========================

    def clear_form(self):

        self.selected_product_id = None

        self.clear_form_fields()
        
    def export_products_csv(self):
        # Security: Require Admin PIN to export products & pricing data
        if not request_admin_pin(self.frame, "export full product and pricing catalog to CSV"):
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Inventory",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="inventory_backup.csv"
        )

        if not file_path:
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    category,
                    name,
                    mrp,
                    purchase_price,
                    selling_price,
                    unit,
                    stock,
                    COALESCE(discount_base, 'Price')
                FROM products
                ORDER BY category, name
            """)

            products = cursor.fetchall()
            conn.close()

            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                # Header with Powered by Wokdens metadata
                writer.writerow([
                    "Category",
                    "Product Name",
                    "MRP",
                    "Purchase Price",
                    "Selling Price",
                    "Unit",
                    "Stock",
                    "Discount On"
                ])

                writer.writerows(products)

            messagebox.showinfo(
                "Success",
                f"Inventory exported successfully!\n\nLocation:\n{file_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                str(e)
            )  
        
    def import_products_csv(self):
        # Security: Require Admin PIN to import bulk inventory
        if not request_admin_pin(self.frame, "import bulk inventory from CSV"):
            return

        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )


        if not file_path:
            return

        try:

            with open(file_path, newline='', encoding='utf-8') as csvfile:

                reader = csv.DictReader(csvfile)

                conn = get_connection()

                cursor = conn.cursor()

                for row in reader:

                    category = row["Category"].strip()

                    product_name = row["Product Name"].strip()

                    mrp = float(row["MRP"])

                    purchase_price = row["Purchase Price"]

                    selling_price = float(row["Selling Price"])

                    stock = int(row["Stock"])
                    
                    unit = row["Unit"]
                    
                    discount_base = row.get("Discount On", "Price") or "Price"


                    # INSERT PRODUCT

                    cursor.execute(
                        """
                        INSERT INTO products(
                            category,
                            name,
                            mrp,
                            purchase_price,
                            selling_price,
                            unit,
                            stock,
                            discount_base
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            category,
                            product_name,
                            mrp,
                            purchase_price,
                            selling_price,
                            unit,
                            stock,
                            discount_base
                        )
                    )

                conn.commit()

                conn.close()

            self.load_products()

            messagebox.showinfo(
                "Success",
                "Products imported successfully"
            )

        except Exception as e:

            messagebox.showerror(
                "Import Error",
                str(e)
            )
