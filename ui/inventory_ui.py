import tkinter as tk
from tkinter import filedialog
import csv


from tkinter import ttk, messagebox, simpledialog

from database import (
    get_connection,
    get_all_categories,
    add_category,
    record_stock_adjustment,
    record_audit_log,
    trigger_auto_backup,
    is_product_duplicate
)



from ui.autocomplete_combobox import AutocompleteCombobox
from ui.admin_auth_dialog import request_admin_pin, is_admin_mode






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
            text="Unit (Preset)"
        ).grid(
            row=5,
            column=0,
            padx=10,
            pady=5
        )

        self.unit_entry = ttk.Combobox(
            form_frame,
            values=(
                "Pcs",
                "Coil",
                "Mtr",
                "Box",
                "Nos",
                "Bundle",
                "Length",
                "Set",
                "Pkt",
                "Roll"
            ),
            width=27
        )
        self.unit_entry.set("Pcs")

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
        # KEYBOARD NAVIGATION LOOP (TALLY SPEED)
        # =========================
        self.category_combo.entry.bind("<Return>", lambda e: (self.name_entry.focus_set(), self.name_entry.selection_range(0, tk.END)))
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: (self.name_entry.focus_set(), self.name_entry.selection_range(0, tk.END)))

        self.name_entry.bind("<Return>", lambda e: (self.mrp_entry.focus_set(), self.mrp_entry.selection_range(0, tk.END)))
        self.mrp_entry.bind(
            "<Return>",
            lambda e: (
                self.purchase_entry.focus_set()
                if str(self.purchase_entry.cget("state")) != "disabled"
                else self.selling_entry.focus_set()
            )
        )
        self.purchase_entry.bind("<Return>", lambda e: (self.selling_entry.focus_set(), self.selling_entry.selection_range(0, tk.END)))
        self.selling_entry.bind("<Return>", lambda e: self.unit_entry.focus_set())
        self.unit_entry.bind("<Return>", lambda e: (self.stock_entry.focus_set(), self.stock_entry.selection_range(0, tk.END)))
        self.stock_entry.bind("<Return>", lambda e: self.save_product())

        for entry_w in (self.name_entry, self.mrp_entry, self.purchase_entry, self.selling_entry, self.stock_entry):
            entry_w.bind("<FocusIn>", lambda e, w=entry_w: w.selection_range(0, tk.END) if hasattr(w, "selection_range") else None)

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
            width=13,
            command=self.save_product,
            fg="white",
            bg="#5634f0",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame,
            text="Update Product",
            width=14,
            command=self.update_product,
            fg="white",
            bg="#5634f0",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame,
            text="Delete Product",
            width=13,
            command=self.delete_product,
            fg="white",
            bg="#ea1b1b",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame,
            text="⚠️ Stock Adjust",
            width=14,
            command=self.open_stock_adjustment_dialog,
            fg="white",
            bg="#fd7e14",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame,
            text="Clear Form",
            width=11,
            command=self.clear_form,
            fg="white",
            bg="#6c757d",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame,
            text="🗑️ Clear Inventory",
            width=16,
            command=self.clear_entire_inventory,
            fg="white",
            bg="#c82333",
            activebackground="#a71d2a",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=4)



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
            self.frame,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#ced4da"
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
            show="headings",
            selectmode="browse"
        )
        
        scroll_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scroll_y.set
        )

        for col in columns:

            self.tree.heading(
                col,
                text=col,
                anchor="center" if col in ("MRP", "Purchase", "Selling", "Unit", "Stock", "Discount On") else "w"
            )

            width = 140
            if col == "ID":
                width = 60
            elif col in ("Name", "Category"):
                width = 200
            elif col in ("MRP", "Purchase", "Selling", "Stock"):
                width = 100
            elif col in ("Unit", "Discount On"):
                width = 85

            self.tree.column(
                col,
                width=width,
                anchor="center" if col in ("MRP", "Purchase", "Selling", "Unit", "Stock", "Discount On") else "w"
            )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scroll_y.pack(
            side="right",
            fill="y"
        )

        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8f9fa")

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_product
        )
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Return>", self._on_tree_double_click)
        self.tree.bind("<Delete>", lambda e: self.delete_product())

        self.search_entry.bind("<Down>", self._focus_first_table_row)
        self.search_entry.bind("<Return>", self._focus_first_table_row)

        self.all_products = []

        self.load_products()

    def _focus_first_table_row(self, event=None):
        """Move focus from search bar to first product row in table."""
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])
            self.tree.focus_set()
            self.select_product(None)
        return "break"

    def _on_tree_double_click(self, event=None):
        """Double click or Enter on table row: load into form and focus selling price."""
        self.select_product(None)
        self.selling_entry.focus_set()
        self.selling_entry.selection_range(0, tk.END)
        return "break"


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
        self.product_map = {p[0]: p for p in products}
        admin_active = is_admin_mode()

        for idx, product in enumerate(products):
            display_val = list(product)
            if not admin_active:
                display_val[4] = "***"

            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(product[0]),
                values=display_val,
                tags=(tag,)
            )

    # =========================
    # SEARCH PRODUCTS (SMART MULTI-TERM TOKEN SEARCH)
    # =========================

    def search_products(self, event=None):

        keyword = (
            self.search_entry.get()
            .strip()
            .lower()
        )

        self.tree.delete(
            *self.tree.get_children()
        )

        admin_active = is_admin_mode()
        search_terms = keyword.split()

        match_count = 0
        for product in self.all_products:
            prod_id = str(product[0])
            category = str(product[1] or "").lower()
            name = str(product[2] or "").lower()
            mrp = str(product[3] or "")
            purchase = str(product[4] or "") if admin_active else ""
            selling = str(product[5] or "")
            unit = str(product[6] or "").lower()
            stock = str(product[7] or "")

            searchable_text = f"{prod_id} {category} {name} {mrp} {purchase} {selling} {unit} {stock}".lower()

            if not search_terms or all(term in searchable_text for term in search_terms):
                display_val = list(product)
                if not admin_active:
                    display_val[4] = "***"

                tag = "evenrow" if match_count % 2 == 0 else "oddrow"
                self.tree.insert(
                    "",
                    "end",
                    iid=str(product[0]),
                    values=display_val,
                    tags=(tag,)
                )
                match_count += 1


    # =========================
    # SAVE PRODUCT
    # =========================

    def save_product(self):

        category = self.category_combo.get().strip() or "General"
        name = self.name_entry.get().strip()

        # Product Name validation
        if not name:
            messagebox.showerror(
                "Missing Information",
                "Please enter Product Name.",
                parent=self.frame.winfo_toplevel()
            )
            self.name_entry.focus()
            return

        # Unit validation
        unit = self.unit_entry.get().strip() or "Pcs"

        # Duplicate Check
        existing = is_product_duplicate(name, category)
        if existing:
            messagebox.showerror(
                "Duplicate Product",
                f"Product '{name}' already exists in Category '{category}' (ID: {existing[0]}).\n\n"
                f"Duplicate products are not allowed.\n"
                f"Please select the existing product in the table and use 'Update Product' to modify its details or stock.",
                parent=self.frame.winfo_toplevel()
            )
            self.name_entry.focus()
            return

        try:
            mrp_val = float(self.mrp_entry.get().strip() or 0)
            purchase_val = float(self.purchase_entry.get().strip() or 0)
            selling_val = float(self.selling_entry.get().strip() or 0)
            stock_val = int(self.stock_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid numeric values for MRP, Purchase Price, Selling Price, and Stock.",
                parent=self.frame.winfo_toplevel()
            )
            return

        conn = get_connection()
        cursor = conn.cursor()

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
            category,
            name,
            mrp_val,
            purchase_val,
            selling_val,
            unit,
            stock_val,
            self.discount_base_combo.get() or "Price"
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            f"Product '{name}' added successfully",
            parent=self.frame.winfo_toplevel()
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

        prod_id = int(values[0])
        self.selected_product_id = prod_id

        self.clear_form_fields()

        orig_prod = getattr(self, "product_map", {}).get(prod_id)

        self.category_combo.set(values[1])

        self.name_entry.insert(0, values[2])

        self.mrp_entry.insert(0, values[3])

        # Purchase price masking logic
        self.purchase_entry.config(state="normal")
        if is_admin_mode():
            real_purchase = orig_prod[4] if orig_prod else values[4]
            self.purchase_entry.insert(0, str(real_purchase))
        else:
            self.purchase_entry.insert(0, "***")
            self.purchase_entry.config(state="disabled")

        self.selling_entry.insert(0, values[5])
        
        self.unit_entry.set(values[6] if len(values) > 6 else "Pcs")
        
        self.stock_entry.insert(0, values[7])

        self.discount_base_combo.set(values[8] if len(values) > 8 else "Price")

    # =========================
    # UPDATE PRODUCT
    # =========================

    def update_product(self):

        # Fallback to current tree selection if selected_product_id wasn't set
        if self.selected_product_id is None:
            selected = self.tree.selection()
            if selected:
                values = self.tree.item(selected[0])["values"]
                self.selected_product_id = int(values[0])

        if self.selected_product_id is None:

            messagebox.showerror(
                "Error",
                "Please select a product from the table first.",
                parent=self.frame.winfo_toplevel()
            )

            return

        # Security: Require Admin PIN to modify existing pricing / product info
        if not request_admin_pin(self.frame, "modify product pricing and details"):
            return

        category = self.category_combo.get().strip() or "General"
        name = self.name_entry.get().strip()

        if not name:
            messagebox.showerror("Missing Information", "Please enter Product Name.", parent=self.frame.winfo_toplevel())
            self.name_entry.focus()
            return

        # Check duplicate against other products
        existing = is_product_duplicate(name, category, exclude_id=self.selected_product_id)
        if existing:
            messagebox.showerror(
                "Duplicate Product",
                f"Cannot update: Another product '{name}' already exists in Category '{category}' (ID: {existing[0]}).\n\n"
                f"Duplicate names within the same category are not permitted.",
                parent=self.frame.winfo_toplevel()
            )
            return

        try:
            mrp_val = float(self.mrp_entry.get().strip() or 0)
            selling_val = float(self.selling_entry.get().strip() or 0)
            stock_val = int(self.stock_entry.get().strip() or 0)
            
            # If purchase price was masked, keep original purchase price from DB
            purchase_str = self.purchase_entry.get().strip()
            if purchase_str == "***":
                orig_prod = getattr(self, "product_map", {}).get(self.selected_product_id)
                purchase_val = float(orig_prod[4] if (orig_prod and orig_prod[4]) else 0)
            else:
                purchase_val = float(purchase_str or 0)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for MRP, Purchase Price, Selling Price, and Stock.", parent=self.frame.winfo_toplevel())
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

        record_audit_log(
            "PRICE_OVERRIDE",
            f"Updated product ID {self.selected_product_id} '{self.name_entry.get().strip()}' - MRP: Rs.{mrp_val}, Selling: Rs.{selling_val}, Cost: Rs.{purchase_val}, Stock: {stock_val} {self.unit_entry.get().strip()}"
        )

        messagebox.showinfo(
            "Success",
            "Product updated successfully",
            parent=self.frame.winfo_toplevel()
        )


        self.load_products()

        # Preserve active search filter if any
        if self.search_entry.get().strip():
            self.search_products(None)

        self.clear_form()


    # =========================
    # DELETE PRODUCT
    # =========================

    def delete_product(self):

        # Fallback to current tree selection if selected_product_id wasn't captured
        if self.selected_product_id is None:
            selected = self.tree.selection()
            if selected:
                values = self.tree.item(selected[0])["values"]
                self.selected_product_id = int(values[0])

        if self.selected_product_id is None:

            messagebox.showerror(
                "Error",
                "Please select a product from the table first.",
                parent=self.frame.winfo_toplevel()
            )

            return

        p_name = self.name_entry.get().strip() or f"Product #{self.selected_product_id}"
        p_id = self.selected_product_id

        # Security: Require Admin PIN to delete product
        if not request_admin_pin(self.frame, f"delete '{p_name}' from inventory"):
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n\n'{p_name}' (ID: {p_id})?",
            parent=self.frame.winfo_toplevel()
        )

        if not confirm:
            return

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
        DELETE FROM products
        WHERE id = ?
        """, (
            p_id,
        ))

        conn.commit()

        conn.close()

        record_audit_log(
            "PRODUCT_DELETE",
            f"Deleted product '{p_name}' (ID: {p_id}) from inventory"
        )

        messagebox.showinfo(
            "Success",
            f"Product '{p_name}' deleted successfully",
            parent=self.frame.winfo_toplevel()
        )

        self.load_products()

        if self.search_entry.get().strip():
            self.search_products(None)

        self.clear_form()

    # =========================
    # CLEAR ENTIRE INVENTORY (ADMIN ONLY)
    # =========================

    def clear_entire_inventory(self):
        """Clear all products from inventory (Admin PIN Protected with auto-backup & double confirmation)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        total_count = cursor.fetchone()[0]
        conn.close()

        if total_count == 0:
            messagebox.showinfo(
                "Inventory Empty",
                "The inventory is already empty. There are no products to clear.",
                parent=self.frame.winfo_toplevel()
            )
            return

        # Security: Require Admin PIN
        if not request_admin_pin(self.frame, f"CLEAR & DELETE ALL {total_count} products from inventory"):
            return

        # Confirmation Dialog 1
        confirm1 = messagebox.askyesno(
            "⚠️ DANGER: Clear Entire Inventory",
            f"Are you sure you want to permanently delete ALL {total_count} products from the inventory?\n\n"
            f"• All product records, rates, MRPs, and stock counts will be erased.\n"
            f"• An automatic safety backup will be created before deletion.\n\n"
            f"Do you want to proceed?",
            parent=self.frame.winfo_toplevel(),
            icon="warning"
        )
        if not confirm1:
            return

        # Final Confirmation Dialog 2
        confirm2 = messagebox.askyesno(
            "Final Confirmation - Clear Inventory",
            f"FINAL WARNING:\n\nThis will permanently delete {total_count} products!\n\n"
            f"Are you 100% certain you want to proceed?",
            parent=self.frame.winfo_toplevel(),
            icon="warning"
        )
        if not confirm2:
            return

        try:
            # 1. Trigger automatic safety backup
            backup_file = trigger_auto_backup(reason="pre_clear_inventory")

            # 2. Delete all products
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products")
            conn.commit()
            conn.close()

            # 3. Record Audit Log
            record_audit_log(
                "CLEAR_INVENTORY",
                f"Admin cleared entire inventory ({total_count} products deleted). Pre-clear backup saved at {backup_file}"
            )

            # 4. Refresh UI
            self.clear_form()
            self.load_products()

            messagebox.showinfo(
                "Inventory Cleared",
                f"All {total_count} products have been cleared from the inventory.\n\n"
                f"Safety backup created successfully.",
                parent=self.frame.winfo_toplevel()
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to clear inventory: {e}",
                parent=self.frame.winfo_toplevel()
            )

    # =========================
    # CLEAR FORM FIELDS
    # =========================


    def clear_form_fields(self):

        self.category_combo.set("")

        self.name_entry.delete(0, tk.END)

        self.mrp_entry.delete(0, tk.END)

        self.purchase_entry.config(state="normal")
        self.purchase_entry.delete(0, tk.END)

        self.selling_entry.delete(0, tk.END)
        
        self.unit_entry.set("Pcs")

        self.stock_entry.delete(0, tk.END)

        self.discount_base_combo.set("Price")


    # =========================
    # CLEAR FORM
    # =========================

    def clear_form(self):

        self.selected_product_id = None

        self.clear_form_fields()

    def on_role_changed(self, admin_active):
        """Called automatically when switching between Staff and Admin modes."""
        self.load_products()
        self.clear_form()

        
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

            record_audit_log("CSV_EXPORT", f"Exported product inventory catalog ({len(products)} products) to {file_path}")

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

                added_count = 0
                updated_count = 0
                skipped_count = 0

                for row in reader:
                    category = (row.get("Category") or row.get("category") or "General").strip() or "General"
                    product_name = (row.get("Product Name") or row.get("name") or row.get("Product") or "").strip()

                    if not product_name:
                        skipped_count += 1
                        continue

                    try:
                        mrp = float(row.get("MRP") or row.get("mrp") or 0)
                    except (ValueError, TypeError):
                        mrp = 0.0

                    try:
                        purchase_price = float(row.get("Purchase Price") or row.get("purchase_price") or 0)
                    except (ValueError, TypeError):
                        purchase_price = 0.0

                    try:
                        selling_price = float(row.get("Selling Price") or row.get("selling_price") or 0)
                    except (ValueError, TypeError):
                        selling_price = 0.0

                    try:
                        stock = int(row.get("Stock") or row.get("stock") or 0)
                    except (ValueError, TypeError):
                        stock = 0

                    unit = (row.get("Unit") or row.get("unit") or "Pcs").strip() or "Pcs"
                    discount_base = (row.get("Discount On") or row.get("discount_base") or "Price").strip() or "Price"

                    # Check if already exists in DB (case-insensitive)
                    cursor.execute("""
                        SELECT id FROM products
                        WHERE LOWER(TRIM(COALESCE(category, 'General'))) = LOWER(TRIM(?))
                          AND LOWER(TRIM(name)) = LOWER(TRIM(?))
                        LIMIT 1
                    """, (category, product_name))
                    existing_prod = cursor.fetchone()

                    if existing_prod:
                        # Update existing product without creating duplicate row
                        cursor.execute("""
                            UPDATE products
                            SET mrp = ?, purchase_price = ?, selling_price = ?, unit = ?, stock = ?, discount_base = ?
                            WHERE id = ?
                        """, (mrp, purchase_price, selling_price, unit, stock, discount_base, existing_prod[0]))
                        updated_count += 1
                    else:
                        # Insert new unique product
                        cursor.execute("""
                            INSERT INTO products(category, name, mrp, purchase_price, selling_price, unit, stock, discount_base)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (category, product_name, mrp, purchase_price, selling_price, unit, stock, discount_base))
                        added_count += 1

                conn.commit()
                conn.close()

            self.load_products()

            record_audit_log(
                "CSV_IMPORT",
                f"Admin imported CSV: {added_count} new products added, {updated_count} existing updated, {skipped_count} skipped. 0 duplicates."
            )

            messagebox.showinfo(
                "Import Complete",
                f"✅ CSV Import Completed Successfully!\n\n"
                f"• New products added: {added_count}\n"
                f"• Existing products updated: {updated_count}\n"
                f"• Empty/invalid rows skipped: {skipped_count}\n\n"
                f"All inventory entries remain strictly unique with zero duplicates.",
                parent=self.frame.winfo_toplevel()
            )

        except Exception as e:
            messagebox.showerror(
                "Import Error",
                f"Failed to import products from CSV:\n{e}",
                parent=self.frame.winfo_toplevel()
            )


    # =====================================
    # STOCK ADJUSTMENT (RETURNS & DAMAGES)
    # =====================================

    def open_stock_adjustment_dialog(self):
        """Allows recording stock adjustments (Damaged, Return, Expired, Count Correction)."""
        if self.selected_product_id is None:
            messagebox.showinfo("Select Product", "Please select a product from the inventory list first.")
            return

        # Security: Require Admin PIN for stock adjustments
        if not request_admin_pin(self.frame, "record stock adjustment (Damage/Return/Audit)"):
            return

        # Fetch latest product info
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, stock, unit FROM products WHERE id = ?", (self.selected_product_id,))
        prod = cursor.fetchone()
        conn.close()

        if not prod:
            messagebox.showerror("Error", "Product not found.")
            return

        p_id, p_name, p_cat, p_stock, p_unit = prod

        dialog = tk.Toplevel(self.frame)
        dialog.title("Stock Adjustment (Audit)")
        dialog.geometry("520x400")
        dialog.resizable(False, False)
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()

        # Center on screen
        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        w, h = 520, 400
        x = (sw - w) // 2
        y = (sh - h) // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        # Title
        header = tk.Frame(dialog, bg="#1e222d", pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text="⚠️ Stock Adjustment (Returns & Damages)",
            font=("Arial", 13, "bold"),
            bg="#1e222d",
            fg="#ffcc00"
        ).pack()

        form = tk.Frame(dialog, padx=25, pady=15)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Product:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        tk.Label(form, text=f"{p_name} ({p_cat})", font=("Arial", 10)).grid(row=0, column=1, sticky="w", pady=6, padx=10)

        tk.Label(form, text="Current Stock:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        tk.Label(form, text=f"{p_stock} {p_unit}", font=("Arial", 10, "bold"), fg="#007bff").grid(row=1, column=1, sticky="w", pady=6, padx=10)

        tk.Label(form, text="Adjustment Type:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        adj_type_combo = ttk.Combobox(
            form,
            values=[
                "Damaged / Broken (-)",
                "Customer Return (+)",
                "Supplier Return (-)",
                "Expired / Dead Stock (-)",
                "Inventory Count Correction (+)",
                "Inventory Count Correction (-)"
            ],
            state="readonly",
            width=28,
            font=("Arial", 10)
        )
        adj_type_combo.set("Damaged / Broken (-)")
        adj_type_combo.grid(row=2, column=1, sticky="w", pady=6, padx=10)

        tk.Label(form, text="Quantity:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        qty_entry = tk.Entry(form, font=("Arial", 11), width=15)
        qty_entry.grid(row=3, column=1, sticky="w", pady=6, padx=10)
        qty_entry.focus_set()

        tk.Label(form, text="Audit Reason / Note:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="nw", pady=6)
        reason_entry = tk.Text(form, font=("Arial", 10), width=28, height=3)
        reason_entry.grid(row=4, column=1, sticky="w", pady=6, padx=10)

        def save_adjustment():
            qty_str = qty_entry.get().strip()
            if not qty_str:
                messagebox.showwarning("Missing Quantity", "Please enter adjustment quantity.", parent=dialog)
                qty_entry.focus_set()
                return

            try:
                adj_qty = int(qty_str)
                if adj_qty <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be greater than 0.", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid whole number for quantity.", parent=dialog)
                return

            adj_type = adj_type_combo.get()
            # Calculate signed quantity
            if "(-)" in adj_type:
                signed_qty = -adj_qty
            else:
                signed_qty = adj_qty

            reason = reason_entry.get("1.0", tk.END).strip()

            try:
                new_stock = record_stock_adjustment(p_id, adj_type, signed_qty, reason)
                record_audit_log(
                    "STOCK_ADJUSTMENT",
                    f"Product '{p_name}' (ID: {p_id}): {adj_type} {adj_qty} {p_unit}. Reason: {reason or 'None'}"
                )
                messagebox.showinfo(
                    "Stock Adjusted",
                    f"Stock updated successfully!\n\nProduct: {p_name}\nAdjustment: {adj_type} {adj_qty}\nNew Stock: {new_stock} {p_unit}",
                    parent=dialog
                )

                dialog.destroy()
                self.load_products()
                self.clear_form()
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=dialog)

        btn_box = tk.Frame(dialog, pady=10)
        btn_box.pack(fill="x", padx=25)

        tk.Button(
            btn_box,
            text="Save Adjustment",
            command=save_adjustment,
            bg="#28a745",
            fg="white",
            font=("Arial", 10, "bold"),
            width=16
        ).pack(side="left", padx=10)

        tk.Button(
            btn_box,
            text="Cancel",
            command=dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        ).pack(side="right", padx=10)

        tk.Label(
            dialog,
            text="⚡ Powered by wokdens.com",
            font=("Arial", 8, "italic"),
            fg="#888888"
        ).pack(side="bottom", pady=4)


