import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Canvas
from database import (
    get_product_names,
    get_product_complete_details,
    save_complete_invoice,
    get_customer_names_with_phone
)

from ui.autocomplete_combobox import (
    AutocompleteCombobox
)

from ui.customer_popup import (
    CustomerPopup
)

from reportlab.pdfgen import canvas
from datetime import datetime

import os
import textwrap 

from config import INVOICES_DIR

class InvoiceUI:
    _saved_state = None
    

    def __init__(self, parent):

        self.parent = parent
        self.cart_items = []
        self.editing_cart_index = None

        self.frame = tk.Frame(parent)

        self.frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        style = ttk.Style()
        style.configure("TCombobox", font=("Arial", 11, "bold"))
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", font=("Arial", 11), rowheight=28)

        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background="gray",
            darkcolor="gray",
            lightcolor="gray",
            troughcolor="#d9d9d9",
            bordercolor="#d9d9d9",
            arrowcolor="black"
        )

        self.selected_cell_value = ""

        # =========================
        # 1. CUSTOMER SECTION
        # =========================

        customer_frame = tk.Frame(self.frame)
        customer_frame.pack(
            fill="x",
            padx=4,
            pady=(2, 4)
        )

        tk.Label(
            customer_frame,
            text="Customer Name:",
            font=("Arial", 12, "bold")
        ).pack(
            side="left",
            padx=(4, 6)
        )

        self.customer_combo = AutocompleteCombobox(
            customer_frame,
            width=28
        )
        self.customer_combo.entry.config(font=("Arial", 11, "bold"))
        self.customer_combo.listbox.config(font=("Arial", 11))
        self.customer_combo.pack(
            side="left",
            fill="x",
            expand=True,
            padx=4,
            ipady=3
        )

        self.refresh_customers()

        add_customer_btn = tk.Button(
            customer_frame,
            text="+ Add Customer",
            command=self.open_customer_popup,
            bg="#f4a300",
            fg="black",
            activebackground="#d68e00",
            relief="raised",
            bd=2,
            padx=10,
            pady=3,
            font=("Arial", 10, "bold")
        )
        add_customer_btn.pack(side="left", padx=4)

        clear_invoice_btn = tk.Button(
            customer_frame,
            text="🧹 Clear / New Bill",
            bg="#e9ecef",
            fg="#495057",
            activebackground="#dde2e6",
            relief="raised",
            bd=2,
            padx=10,
            pady=3,
            font=("Arial", 10, "bold"),
            command=self.clear_invoice
        )
        clear_invoice_btn.pack(side="left", padx=4)

        # =========================
        # 2. PRODUCT SECTION (Compact & Fast)
        # =========================

        product_frame = tk.LabelFrame(
            self.frame,
            text="Add Product to Bill",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=6
        )
        product_frame.pack(
            fill="x",
            padx=4,
            pady=(2, 4)
        )

        for col in (1, 3, 5, 7):
            product_frame.grid_columnconfigure(col, weight=1)

        # Row 0: Product Search Dropdown & Live Stock Badge
        tk.Label(
            product_frame,
            text="Product (F2):",
            font=("Arial", 11, "bold")
        ).grid(row=0, column=0, padx=6, pady=3, sticky="w")

        self.product_combo = AutocompleteCombobox(
            product_frame,
            width=32
        )
        self.product_combo.entry.config(font=("Arial", 11, "bold"))
        self.product_combo.listbox.config(font=("Arial", 11))
        self.product_combo.grid(
            row=0,
            column=1,
            columnspan=5,
            padx=4,
            pady=3,
            sticky="ew"
        )

        # Live Stock Indicator Badge
        self.stock_badge = tk.Label(
            product_frame,
            text="Stock: --",
            font=("Arial", 10, "bold"),
            fg="#6c757d",
            bg="#e9ecef",
            padx=8,
            pady=2,
            relief="groove"
        )
        self.stock_badge.grid(
            row=0,
            column=6,
            columnspan=2,
            padx=6,
            pady=3,
            sticky="e"
        )

        products = get_product_names()
        self.product_combo.set_completion_list(products)

        self.product_combo.bind("<KeyRelease>", lambda e: self.autofill_product_details(focus_qty=False))
        self.product_combo.bind("<<ComboboxSelected>>", lambda e: self.autofill_product_details(focus_qty=True))
        self.product_combo.bind("<FocusOut>", lambda e: self.autofill_product_details(focus_qty=False))
        self.product_combo.entry.bind("<Return>", self.on_product_enter_pressed)

        # Row 1: Qty, MRP, Price, Unit
        tk.Label(product_frame, text="Qty:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=4, pady=3, sticky="w")
        self.qty_entry = tk.Entry(product_frame, width=6, font=("Arial", 11, "bold"), justify="center")
        self.qty_entry.grid(row=1, column=1, padx=4, pady=3, ipady=2, sticky="ew")

        tk.Label(product_frame, text="MRP:", font=("Arial", 10, "bold")).grid(row=1, column=2, padx=4, pady=3, sticky="w")
        self.mrp_entry = tk.Entry(product_frame, width=8, state="readonly", font=("Arial", 11, "bold"), justify="center")
        self.mrp_entry.grid(row=1, column=3, padx=4, pady=3, ipady=2, sticky="ew")

        tk.Label(product_frame, text="Price:", font=("Arial", 10, "bold")).grid(row=1, column=4, padx=4, pady=3, sticky="w")
        self.price_entry = tk.Entry(product_frame, width=8, font=("Arial", 11, "bold"), justify="center")
        self.price_entry.grid(row=1, column=5, padx=4, pady=3, ipady=2, sticky="ew")

        tk.Label(product_frame, text="Unit:", font=("Arial", 10, "bold")).grid(row=1, column=6, padx=4, pady=3, sticky="w")
        self.unit_entry = tk.Entry(product_frame, width=6, state="readonly", font=("Arial", 11, "bold"), justify="center")
        self.unit_entry.grid(row=1, column=7, padx=4, pady=3, ipady=2, sticky="ew")

        # Row 2: Discount %, Discount Base, Add To Cart Button
        self.discount_base_var = tk.StringVar(value="Price")

        tk.Label(product_frame, text="Disc %:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=4, pady=3, sticky="w")
        self.discount_entry = tk.Entry(product_frame, width=6, font=("Arial", 11, "bold"), justify="center")
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=2, column=1, padx=4, pady=3, ipady=2, sticky="ew")

        tk.Label(product_frame, text="Disc On:", font=("Arial", 10, "bold")).grid(row=2, column=2, padx=4, pady=3, sticky="w")
        self.discount_base_label = tk.Label(
            product_frame,
            textvariable=self.discount_base_var,
            font=("Arial", 10, "bold"),
            fg="#0066cc",
            anchor="w"
        )
        self.discount_base_label.grid(row=2, column=3, padx=4, pady=3, sticky="w")

        self.add_btn = tk.Button(
            product_frame,
            text="➕ Add to Bill (Enter)",
            command=self.add_to_cart,
            bg="#28a745",
            fg="white",
            activebackground="#218838",
            relief="raised",
            bd=2,
            padx=14,
            pady=3,
            font=("Arial", 10, "bold")
        )
        self.add_btn.grid(row=2, column=4, columnspan=4, padx=6, pady=3, sticky="e")

        self.add_btn.bind(
            "<Return>",
            lambda e: self.add_to_cart()
        )

        # =========================
        # TALLY SEAMLESS KEYBOARD NAVIGATION LOOP
        # =========================
        self.customer_combo.entry.bind("<Return>", self.on_customer_enter_pressed)
        self.customer_combo.bind("<<ComboboxSelected>>", self.on_customer_enter_pressed)

        # Auto-Select-All on FocusIn for rapid overwrite
        for entry_w in (self.qty_entry, self.price_entry, self.discount_entry):
            entry_w.bind("<FocusIn>", lambda e, w=entry_w: w.selection_range(0, tk.END))

        # Enter advances to next field seamlessly
        self.qty_entry.bind(
            "<Return>",
            lambda e: (self.price_entry.focus_set(), self.price_entry.selection_range(0, tk.END))
        )
        self.price_entry.bind(
            "<Return>",
            lambda e: (self.discount_entry.focus_set(), self.discount_entry.selection_range(0, tk.END))
        )
        self.discount_entry.bind(
            "<Return>",
            lambda e: self.add_to_cart()
        )



        # =========================
        # 3. CART TABLE WITH INTERNAL SCROLLBAR
        # =========================

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
            padx=4,
            pady=4
        )

        columns = (
            "S.No",
            "Qty",
            "Product",
            "MRP",
            "Price",
            "Unit",
            "Discount",
            "Discount On",
            "Total",
            "Edit",
            "Delete"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            width = 100
            if col == "Product":
                width = 240
            elif col in ("MRP", "Price"):
                width = 90
            elif col in ("Qty", "Unit", "Discount"):
                width = 75
            elif col == "Discount On":
                width = 95
            elif col in ("Edit", "Delete"):
                width = 65

            self.tree.column(col, width=width, anchor="center")

        tree_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.tree.tag_configure("evenrow", background="#ffffff")
        self.tree.tag_configure("oddrow", background="#f8f9fa")

        self.tree.bind(
            "<Button-1>",
            self.handle_table_click
        )
        # Table Keyboard & Mouse Shortcuts (Tally Style)
        self.tree.bind("<Double-1>", lambda e: self._edit_selected_cart_row())
        self.tree.bind("<Delete>", lambda e: self._delete_selected_cart_row())
        self.tree.bind("<BackSpace>", lambda e: self._delete_selected_cart_row())
        self.tree.bind("<Return>", lambda e: self._edit_selected_cart_row())
        self.tree.bind("<F4>", lambda e: self._edit_selected_cart_row())



        # =========================
        # 4. BOTTOM SUMMARY & ACTIONS
        # =========================

        bottom_frame = tk.Frame(
            self.frame,
            bg="#f8f9fa",
            relief="groove",
            borderwidth=1,
            padx=10,
            pady=6
        )
        bottom_frame.pack(
            fill="x",
            padx=4,
            pady=(2, 4),
            side="bottom"
        )

        # Line 1: Items Count, Grand Total, Paid Amount, Pending, Note (ALL in ONE Line)
        line1 = tk.Frame(bottom_frame, bg="#f8f9fa")
        line1.pack(fill="x", pady=2)

        # Wholesale Quantity Counter Badge
        self.items_count_label = tk.Label(
            line1,
            text="Items: 0 | Qty: 0",
            font=("Arial", 10, "bold"),
            fg="#495057",
            bg="#e9ecef",
            padx=6,
            pady=2,
            relief="groove"
        )

        self.items_count_label.pack(side="left", padx=(4, 10))

        self.total_label = tk.Label(
            line1,
            text="Grand Total: ₹ 0",
            font=("Arial", 14, "bold"),
            fg="#5634f0",
            bg="#f8f9fa"
        )
        self.total_label.pack(side="left", padx=(4, 12))

        tk.Label(
            line1,
            text="Paid Amount:",
            font=("Arial", 11, "bold"),
            bg="#f8f9fa"
        ).pack(side="left", padx=(8, 4))

        self.paid_entry = tk.Entry(
            line1,
            width=11,
            font=("Arial", 11, "bold"),
            justify="center"
        )
        self.paid_entry.insert(0, "0")
        self.paid_entry.pack(side="left", padx=4)

        self.paid_entry.bind(
            "<KeyRelease>",
            self.on_paid_changed
        )
        self.paid_entry.bind(
            "<FocusOut>",
            lambda e: self.update_pending()
        )
        self.paid_entry.bind(
            "<FocusIn>",
            lambda e: self.paid_entry.selection_range(0, tk.END)
        )
        self.paid_entry.bind(
            "<Return>",
            lambda e: self.save_invoice()
        )

        self.pending_label = tk.Label(
            line1,
            text="Pending: ₹ 0",
            font=("Arial", 12, "bold"),
            fg="#28a745",
            bg="#f8f9fa"
        )
        self.pending_label.pack(side="left", padx=(12, 12))

        tk.Label(
            line1,
            text="Note:",
            font=("Arial", 11, "bold"),
            bg="#f8f9fa"
        ).pack(side="left", padx=(8, 4))

        self.note_text = tk.Entry(
            line1,
            font=("Arial", 10),
            width=26
        )
        self.note_text.pack(side="left", fill="x", expand=True, padx=4)
        self.note_text.bind(
            "<FocusIn>",
            lambda e: self.note_text.selection_range(0, tk.END)
        )
        self.note_text.bind(
            "<Return>",
            lambda e: self.save_invoice()
        )

        # Line 2: Save Invoice Button, Clear Button & Branding
        line2 = tk.Frame(bottom_frame, bg="#f8f9fa")
        line2.pack(fill="x", pady=(5, 2))

        self.save_btn = tk.Button(
            line2,
            text="💾 Save Invoice + PDF (F9 / Ctrl+S)",
            command=self.save_invoice,
            fg="white",
            bg="#5634f0",
            activebackground="#3f22c2",
            relief="raised",
            bd=3,
            padx=18,
            pady=4,
            font=("Arial", 11, "bold")
        )
        self.save_btn.pack(side="left", padx=(4, 10))

        clear_btn = tk.Button(
            line2,
            text="🧹 Clear / New Bill (Alt+X)",
            command=self.clear_invoice,
            fg="#495057",
            bg="#e9ecef",
            activebackground="#dde2e6",
            relief="raised",
            bd=2,
            padx=12,
            pady=4,
            font=("Arial", 10, "bold")
        )
        clear_btn.pack(side="left", padx=5)

        branding_label = tk.Label(
            line2,
            text="⚡ Powered by wokdens.com",
            font=("Arial", 9, "italic"),
            fg="#888888",
            bg="#f8f9fa"
        )
        branding_label.pack(side="right", padx=10)

        self.auto_fill_paid = True
        self.restore_state()
        self._bind_tally_shortcuts()



    # =========================
    # CUSTOMERS
    # =========================

    
    def refresh_customers(self):

        self.customer_list = (
            get_customer_names_with_phone()
        )

        self.customer_combo.set_completion_list(
            self.customer_list
        )

    def open_customer_popup(self):

        CustomerPopup(
            self.frame,
            self.refresh_customers
        )
        
    def _on_mousewheel(self, event):

        self.canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    # =========================
    # AUTOFILL
    # =========================

    def on_customer_enter_pressed(self, event=None):
        """Move focus seamlessly from customer search to product search."""
        self.product_combo.entry.focus_set()
        self.product_combo.entry.selection_range(0, tk.END)

    def on_product_enter_pressed(self, event=None):
        """Product Enter key: autofill details and advance focus into Qty."""
        self.autofill_product_details(focus_qty=True)

    def autofill_product_details(
        self,
        event=None,
        focus_qty=False
    ):

        selected = (
            self.product_combo.get()
        )

        if not selected or not selected.strip():
            return

        product = get_product_complete_details(selected)
        if not product:
            return

        self.mrp_entry.config(
            state="normal"
        )

        self.mrp_entry.delete(
            0,
            tk.END
        )

        self.mrp_entry.insert(
            0,
            str(product[2] or 0)
        )

        self.mrp_entry.config(
            state="readonly"
        )

        self.price_entry.delete(
            0,
            tk.END
        )

        self.price_entry.insert(
            0,
            str(product[3])
        )

        unit = product[5] if (len(product) > 5 and product[5] and str(product[5]).strip()) else "Pcs"
        self.unit_entry.config(
            state="normal"
        )

        self.unit_entry.delete(
            0,
            tk.END
        )

        self.unit_entry.insert(
            0,
            unit
        )

        self.unit_entry.config(
            state="readonly"
        )


        if len(product) > 6 and product[6]:
            self.discount_base_var.set(product[6])
        else:
            self.discount_base_var.set("Price")

        # Update Live Stock Indicator Badge
        if len(product) > 4:
            stock = product[4]
            unit = product[5] if len(product) > 5 else "Pcs"
            if hasattr(self, "stock_badge"):
                if stock > 10:
                    self.stock_badge.config(
                        text=f"Stock: {stock} {unit}",
                        fg="#155724",
                        bg="#d4edda"
                    )
                elif 1 <= stock <= 10:
                    self.stock_badge.config(
                        text=f"Low Stock: {stock} {unit}",
                        fg="#856404",
                        bg="#fff3cd"
                    )
                else:
                    self.stock_badge.config(
                        text=f"Out of Stock (0 {unit})",
                        fg="#721c24",
                        bg="#f8d7da"
                    )


        # Pre-fill default Qty = 1 if empty
        if not self.qty_entry.get().strip():
            self.qty_entry.delete(0, tk.END)
            self.qty_entry.insert(0, "1")

        # Only focus into Qty if triggered by Enter or dropdown selection
        if focus_qty:
            self.qty_entry.focus_set()
            self.qty_entry.selection_range(0, tk.END)


    # =========================
    # ADD TO CART
    # =========================

    def add_to_cart(self):

        selected_product = (
            self.product_combo.get()
        )

        if not selected_product or not selected_product.strip():

            messagebox.showerror(
                "Error",
                "Please select a product first.",
                parent=self.frame.winfo_toplevel()
            )

            self.product_combo.entry.focus_set()
            return


        product = get_product_complete_details(selected_product)
        if not product:
            messagebox.showerror(
                "Product Not Found",
                "The selected product is not available in inventory."
            )
            return

        product_name = product[1]

        try:
            quantity = int(self.qty_entry.get())
            if quantity <= 0:
                messagebox.showerror(
                    "Invalid Quantity",
                    "Quantity must be a positive whole number greater than 0."
                )
                return
        except ValueError:
            messagebox.showerror(
                "Invalid Quantity",
                "Please enter a valid whole number in Qty."
            )
            return

        try:
            custom_price = float(self.price_entry.get())
            if custom_price < 0:
                messagebox.showerror(
                    "Invalid Price",
                    "Price cannot be negative."
                )
                return
        except ValueError:
            messagebox.showerror(
                "Invalid Price",
                "Please enter a valid numeric value in Price."
            )
            return

        unit = self.unit_entry.get().strip()
        if not unit:
            unit = (product[5] if len(product) > 5 and product[5] else "Pcs")
            self.unit_entry.config(state="normal")
            self.unit_entry.delete(0, tk.END)
            self.unit_entry.insert(0, unit)
            self.unit_entry.config(state="readonly")

        try:
            discount = float(self.discount_entry.get())
            if discount < 0 or discount > 100:
                messagebox.showerror(
                    "Invalid Discount",
                    "Discount must be between 0% and 100%."
                )
                return
        except ValueError:
            messagebox.showerror(
                "Invalid Discount",
                "Please enter a valid numeric value in Discount."
            )
            return


        discount_base = self.discount_base_var.get() or "Price"


        if quantity > product[4]:

            messagebox.showerror(
                "Out of Stock",
                f"Only {product[4]} units of this product are available in inventory."
            )

            return
        mrp = float(self.mrp_entry.get() or 0)

        if discount_base == "MRP":
            # Discount is applied on MRP
            effective_price = mrp - (mrp * discount / 100)
        else:
            # Discount is applied on entered selling price
            effective_price = custom_price - (custom_price * discount / 100)

        total = effective_price * quantity

        # IF CURRENTLY IN EDIT MODE -> UPDATE ROW IN PLACE (SAME ORDER / SERIAL NO)
        if self.editing_cart_index is not None and self.editing_cart_index < len(self.cart_items):
            item = {
                "product_id": product[0],
                "name": product_name,
                "quantity": quantity,
                "mrp": mrp,
                "price": custom_price,
                "unit": unit,
                "discount": discount,
                "discount_base": discount_base,
                "total": total
            }
            self.cart_items[self.editing_cart_index] = item
            self.editing_cart_index = None
            self.add_btn.config(
                text="➕ Add to Bill (Enter)",
                bg="#28a745",
                activebackground="#218838"
            )
            self.refresh_cart_table()
            self.update_total()
            self.clear_inputs()
            self.product_combo.entry.focus_set()
            self.product_combo.entry.icursor(tk.END)
            return

        # Check if identical product is already in cart -> increase count
        existing_item = None
        for itm in self.cart_items:
            if (
                itm["product_id"] == product[0]
                and abs(itm["price"] - custom_price) < 0.001
                and abs(itm["discount"] - discount) < 0.001
                and itm.get("discount_base", "Price") == discount_base
            ):
                existing_item = itm
                break

        if existing_item:
            combined_qty = existing_item["quantity"] + quantity
            if combined_qty > product[4]:
                messagebox.showerror(
                    "Out of Stock",
                    f"Only {product[4]} {unit} available in stock.\nCart already has {existing_item['quantity']} {unit}.",
                    parent=self.frame.winfo_toplevel()
                )
                return

            existing_item["quantity"] = combined_qty
            existing_item["total"] = effective_price * combined_qty
            self.refresh_cart_table()
            self.update_total()
            self.clear_inputs()
            self.product_combo.entry.focus_set()
            self.product_combo.entry.icursor(tk.END)
            return

        item = {
            "product_id": product[0],
            "name": product_name,
            "quantity": quantity,
            "mrp": mrp,
            "price": custom_price,
            "unit": unit,
            "discount": discount,
            "discount_base": discount_base,
            "total": total
        }

        self.cart_items.append(item)
        self.refresh_cart_table()
        self.update_total()
        self.clear_inputs()
        self.product_combo.entry.focus_set()
        self.product_combo.entry.icursor(tk.END)

    # =========================
    # UPDATE TOTAL
    # =========================

    def update_total(self):

        total = sum(
            item["total"]
            for item in self.cart_items
        )

        # Round off paisa values to nearest rupee
        rounded_total = round(total)

        # store for pending calculation
        self.rounded_total = rounded_total

        self.total_label.config(
            text=f"Grand Total: ₹ {rounded_total}"
        )

        # Live Wholesale Counter (Items & Physical Quantity)
        if hasattr(self, "items_count_label"):
            total_items = len(self.cart_items)
            total_qty = sum(int(item.get("quantity", 0)) for item in self.cart_items)
            self.items_count_label.config(
                text=f"Items: {total_items} | Qty: {total_qty}"
            )


        if self.auto_fill_paid:

            self.paid_entry.delete(
                0,
                tk.END
            )

            self.paid_entry.insert(
                0,
                str(rounded_total)
            )

        self.update_pending()

    # =========================
    # CLEAR
    # =========================

    def clear_inputs(self):

        self.editing_cart_index = None
        self.add_btn.config(
            text="➕ Add to Bill (Enter)",
            bg="#28a745",
            activebackground="#218838"
        )

        self.product_combo.set("")

        if hasattr(self, "stock_badge"):
            self.stock_badge.config(
                text="Stock: --",
                fg="#6c757d",
                bg="#e9ecef"
            )

        self.qty_entry.delete(
            0,
            tk.END
        )
        self.qty_entry.insert(0, "1")


        self.price_entry.delete(
            0,
            tk.END
        )

        self.mrp_entry.config(state="normal")
        self.mrp_entry.delete(0, tk.END)
        self.mrp_entry.config(state="readonly")

        self.unit_entry.config(state="normal")
        self.unit_entry.delete(
            0,
            tk.END
        )
        self.unit_entry.config(state="readonly")

        self.discount_entry.delete(
            0,
            tk.END
        )

        self.discount_entry.insert(
            0,
            "0"
        )



    def clear_invoice(self):

        InvoiceUI._saved_state = None

        self.cart_items.clear()

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.customer_combo.set("")

        self.clear_inputs()

        self.paid_entry.delete(0, tk.END)
        self.paid_entry.insert(0, "0")

        self.note_text.delete(0, tk.END)

        self.update_total()

    def save_state(self):
        note_val = self.note_text.get().strip() if hasattr(self.note_text, "get") else ""
        InvoiceUI._saved_state = {
            "cart_items": list(self.cart_items),
            "customer_name": self.customer_combo.get(),
            "product_name": self.product_combo.get(),
            "qty": self.qty_entry.get(),
            "mrp": self.mrp_entry.get(),
            "price": self.price_entry.get(),
            "unit": self.unit_entry.get(),
            "discount": self.discount_entry.get(),
            "discount_base": self.discount_base_var.get(),
            "paid_amount": self.paid_entry.get(),
            "note": note_val,
            "auto_fill_paid": self.auto_fill_paid,
            "rounded_total": getattr(self, "rounded_total", 0)
        }

    def restore_state(self):
        state = InvoiceUI._saved_state
        if not state:
            return

        self.cart_items = list(state["cart_items"])
        self.refresh_cart_table()

        self.customer_combo.set(state["customer_name"])
        self.product_combo.set(state["product_name"])

        self.qty_entry.delete(0, tk.END)
        self.qty_entry.insert(0, state["qty"])

        self.mrp_entry.config(state="normal")
        self.mrp_entry.delete(0, tk.END)
        self.mrp_entry.insert(0, state["mrp"])
        self.mrp_entry.config(state="readonly")

        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, state["price"])

        self.unit_entry.config(state="normal")
        self.unit_entry.delete(0, tk.END)
        self.unit_entry.insert(0, state["unit"])
        self.unit_entry.config(state="readonly")

        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, state["discount"])

        self.discount_base_var.set(state["discount_base"])

        self.auto_fill_paid = state["auto_fill_paid"]
        self.rounded_total = state["rounded_total"]
        self.total_label.config(text=f"Grand Total: ₹ {self.rounded_total}")

        self.paid_entry.delete(0, tk.END)
        self.paid_entry.insert(0, state["paid_amount"])

        self.note_text.delete(0, tk.END)
        self.note_text.insert(0, state.get("note", ""))

    def on_tab_leave(self):
        """Called when user switches tabs away from Invoice page."""
        self.save_state()

    def on_tab_enter(self):
        """Called when user switches tabs back to Invoice page."""
        self.restore_state()


        self.update_pending()

    # =========================
    # SAVE INVOICE
    # =========================

    def save_invoice(self):

        if not self.cart_items:

            messagebox.showerror(
                "Error",
                "Cart is empty",
                parent=self.frame.winfo_toplevel()
            )

            return

        customer_name = (
            self.customer_combo.get()
            .split(" (")[0]
        )

        try:
            paid_amount = float(self.paid_entry.get().strip() or 0)
        except ValueError:
            messagebox.showerror(
                "Invalid Amount",
                "Please enter a valid paid amount.",
                parent=self.frame.winfo_toplevel()
            )
            return

        note = self.note_text.get().strip() if hasattr(self.note_text, "get") else ""

        # compute and round grand total before saving
        grand_total_raw = sum(
            item["total"]
            for item in self.cart_items
        )

        grand_total = round(grand_total_raw)

        raw_customer = self.customer_combo.get().strip()
        customer_name = raw_customer.split(" (")[0].strip() if raw_customer else "Cash / Walk-in Customer"

        invoice_id = save_complete_invoice(
            customer_name,
            self.cart_items,
            grand_total,
            paid_amount,
            note
        )

        self.generate_pdf(
            invoice_id,
            customer_name,
            grand_total,
            paid_amount
        )

        # Clear cart and reset form for the next customer
        self.cart_items = []
        self.refresh_cart_table()
        self.clear_inputs()
        self.customer_combo.set("")
        self.paid_entry.delete(0, tk.END)
        if hasattr(self.note_text, "delete"):
            self.note_text.delete(0, tk.END)
        self.update_total()
        self.customer_combo.entry.focus_set()

        messagebox.showinfo(
            "Success",
            f"Invoice #{invoice_id} saved successfully!\nPDF generated.",
            parent=self.frame.winfo_toplevel()
        )



    # =========================
    # PDF
    # =========================



    def generate_pdf(
        self,
        invoice_number,
        customer_name,
        grand_total,
        paid_amount=0
    ):

        # sanitize customer name for filename
        safe_name = "".join(
            c for c in customer_name if c.isalnum() or c in (" ", "-", "_")
        ).strip().replace(" ", "_")

        if safe_name:
            path = os.path.join(INVOICES_DIR, f"INV-{invoice_number}_{safe_name}.pdf")
        else:
            path = os.path.join(INVOICES_DIR, f"INV-{invoice_number}.pdf")

        pdf = canvas.Canvas(path)
        page_width, page_height = 595.27, 841.89  # Standard A4

        # =====================================
        # HEADER (ESTIMATE ONLY - NO SHOP DETAILS)
        # =====================================
        # Main Heading (ESTIMATE ONLY)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.setFillColorRGB(0.12, 0.14, 0.18)
        pdf.drawString(40, 805, "ESTIMATE ONLY")


        # Date / Time (Right)
        pdf.setFont("Helvetica", 9)
        pdf.setFillColorRGB(0.35, 0.38, 0.42)
        pdf.drawRightString(555, 805, f"Date: {datetime.now().strftime('%d-%m-%Y  %I:%M %p')}")

        # Top Divider Line
        pdf.setStrokeColorRGB(0.8, 0.83, 0.88)
        pdf.setLineWidth(1)
        pdf.line(40, 792, 555, 792)

        # =====================================
        # ESTIMATE & CUSTOMER INFO
        # =====================================
        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.setFillColorRGB(0.2, 0.2, 0.2)
        pdf.drawString(40, 775, f"Estimate No : INV-{invoice_number}")

        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.drawString(280, 775, f"Customer : {customer_name.upper()}")

        # =====================================
        # TABLE HEADER (Modern Slate Header)
        # =====================================
        table_top = 758
        header_height = 20

        # Background fill for header
        pdf.setFillColorRGB(0.93, 0.94, 0.97)
        pdf.rect(40, table_top - header_height, 515, header_height, fill=True, stroke=False)

        # Border for header
        pdf.setStrokeColorRGB(0.75, 0.78, 0.84)
        pdf.setLineWidth(0.8)
        pdf.rect(40, table_top - header_height, 515, header_height, fill=False, stroke=True)

        headers = [
            ("S.No", 55, "center"),
            ("Qty", 82, "center"),
            ("Product Description", 110, "left"),
            ("MRP", 330, "right"),
            ("Price", 380, "right"),
            ("Unit", 415, "center"),
            ("Discount", 465, "center"),
            ("Total (Rs.)", 548, "right")
        ]

        pdf.setFont("Helvetica-Bold", 9)
        pdf.setFillColorRGB(0.15, 0.18, 0.25)

        for title, x_pos, align in headers:
            if align == "center":
                pdf.drawCentredString(x_pos, table_top - 14, title)
            elif align == "right":
                pdf.drawRightString(x_pos, table_top - 14, title)
            else:
                pdf.drawString(x_pos, table_top - 14, title)

        # =====================================
        # TABLE ROWS (Compact Tight Spacing)
        # =====================================
        current_y = table_top - header_height - 13
        serial = 1

        for item in self.cart_items:
            wrapped_product = textwrap.wrap(item["name"], width=32)
            lines_count = len(wrapped_product)
            # Compact row height: 16pt for 1 line, +10pt for extra lines
            row_height = 16 if lines_count <= 1 else (lines_count * 11 + 5)

            # Check for page overflow
            if current_y - row_height < 90:
                pdf.showPage()
                current_y = 800
                pdf.setFont("Helvetica", 8.5)

            # Row background alternating subtle shading
            if serial % 2 == 0:
                pdf.setFillColorRGB(0.98, 0.98, 0.99)
                pdf.rect(40, current_y - row_height + 11, 515, row_height, fill=True, stroke=False)

            pdf.setFont("Helvetica", 8.5)
            pdf.setFillColorRGB(0.15, 0.15, 0.15)

            # 1. S.No
            pdf.drawCentredString(55, current_y, str(serial))

            # 2. Qty
            pdf.setFont("Helvetica-Bold", 8.5)
            pdf.drawCentredString(82, current_y, str(item["quantity"]))
            pdf.setFont("Helvetica", 8.5)

            # 3. Product Description (Multi-line safe)
            yy = current_y
            for line in wrapped_product:
                pdf.drawString(110, yy, line)
                yy -= 11

            # 4. MRP
            mrp_val = float(item.get("mrp", 0))
            pdf.drawRightString(330, current_y, f"{mrp_val:,.1f}" if mrp_val > 0 else "-")

            # 5. Price
            price_val = float(item.get("price", 0))
            pdf.drawRightString(380, current_y, f"{price_val:,.2f}")

            # 6. Unit
            pdf.drawCentredString(415, current_y, str(item["unit"] or "Pcs"))

            # 7. Discount
            discount_value = float(item.get("discount", 0))
            if discount_value > 0:
                disc_base = item.get("discount_base", "Price")
                disc_str = f"{int(discount_value) if discount_value.is_integer() else discount_value}% on {disc_base}"
            else:
                disc_str = "0%"
            pdf.drawCentredString(465, current_y, disc_str)

            # 8. Total
            total_val = float(item.get("total", 0))
            pdf.setFont("Helvetica-Bold", 8.5)
            pdf.drawRightString(548, current_y, f"{total_val:,.2f}")
            pdf.setFont("Helvetica", 8.5)

            # Bottom row divider line
            pdf.setStrokeColorRGB(0.9, 0.91, 0.94)
            pdf.setLineWidth(0.5)
            pdf.line(40, current_y - row_height + 11, 555, current_y - row_height + 11)

            current_y -= row_height
            serial += 1

        # Table outer border
        table_bottom = current_y + 11
        pdf.setStrokeColorRGB(0.75, 0.78, 0.84)
        pdf.setLineWidth(0.8)
        pdf.rect(40, table_bottom, 515, (table_top - table_bottom), fill=False, stroke=True)

        # Vertical Column Divider Lines
        v_dividers = [70, 95, 290, 340, 395, 435, 495]
        pdf.setStrokeColorRGB(0.88, 0.89, 0.92)
        pdf.setLineWidth(0.5)
        for vx in v_dividers:
            pdf.line(vx, table_top, vx, table_bottom)

        # =====================================
        # SUMMARY SECTION (TOTAL ONLY - NO PENDING/PAID)
        # =====================================
        summary_y = table_bottom - 16

        # Left Remarks / Note
        note_str = getattr(self, "note_text", None)
        note_val = note_str.get().strip() if (note_str and hasattr(note_str, "get")) else ""
        if note_val:
            pdf.setFont("Helvetica-Bold", 8.5)
            pdf.setFillColorRGB(0.2, 0.2, 0.2)
            pdf.drawString(45, summary_y - 2, f"Note / Remarks: {note_val}")

        # Grand Total Box (Right Aligned Accent Box)
        total_box_width = 190
        total_box_height = 30
        total_box_x = 365
        total_box_y = summary_y - total_box_height + 10

        pdf.setFillColorRGB(0.94, 0.96, 1.0)
        pdf.rect(total_box_x, total_box_y, total_box_width, total_box_height, fill=True, stroke=False)
        pdf.setStrokeColorRGB(0.2, 0.35, 0.65)
        pdf.setLineWidth(1)
        pdf.rect(total_box_x, total_box_y, total_box_width, total_box_height, fill=False, stroke=True)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColorRGB(0.1, 0.2, 0.5)
        pdf.drawRightString(total_box_x + total_box_width - 10, total_box_y + 9, f"Grand Total:  Rs. {grand_total:,.2f}")

        # =====================================
        # MANDATORY FOOTER & BRANDING (IMMEDIATELY AFTER GRAND TOTAL)
        # =====================================
        footer_line_y = total_box_y - 12
        footer_text_y = footer_line_y - 12

        # Bottom Divider Line directly below Total box
        pdf.setStrokeColorRGB(0.85, 0.88, 0.92)
        pdf.setLineWidth(0.5)
        pdf.line(40, footer_line_y, 555, footer_line_y)

        # Left: Mandatory PO / GST line
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.35, 0.35, 0.35)
        pdf.drawString(40, footer_text_y, "GST as per applicable. Order against PO.")

        # Right: Powered by wokdens.com
        pdf.setFont("Helvetica-Bold", 8)
        pdf.setFillColorRGB(0.35, 0.35, 0.35)
        pdf.drawRightString(555, footer_text_y, "⚡ Powered by wokdens.com")

        pdf.save()






        # Attempt to open the generated PDF automatically (Windows)
        try:
            abs_path = os.path.abspath(path)
            if os.name == "nt":
                os.startfile(abs_path)
            else:
                # For other OSes, try the default opener
                import subprocess

                opener = "open" if os.name == "darwin" else "xdg-open"
                subprocess.Popen([opener, abs_path])
        except Exception:
            pass

    def on_paid_changed(self, event=None):

        self.auto_fill_paid = False

        self.update_pending()

    def update_pending(self):

        try:
            paid = float(self.paid_entry.get())
        except Exception:
            paid = 0.0

        rounded_total = getattr(self, "rounded_total", round(sum(item["total"] for item in self.cart_items) if self.cart_items else 0))

        pending_amount = rounded_total - paid

        # display as integer if whole rupee, else keep float
        if float(pending_amount).is_integer():
            pending_display = int(pending_amount)
        else:
            pending_display = pending_amount

        if pending_amount > 0:
            self.pending_label.config(
                text=f"Pending: ₹ {pending_display}",
                fg="#d9534f"
            )
        else:
            self.pending_label.config(
                text=f"Pending: ₹ {pending_display}",
                fg="#28a745"
            )

        
    def handle_table_click(self, event):

        region = self.tree.identify(
            "region",
            event.x,
            event.y
        )

        if region != "cell":
            return

        column = self.tree.identify_column(
            event.x
        )

        item = self.tree.identify_row(
            event.y
        )

        if not item:
            return

        column_number = int(
            column.replace("#", "")
        )

        # EDIT COLUMN
        if column_number == 10:

            self.edit_cart_item(item)

        # DELETE COLUMN
        elif column_number == 11:

            self.delete_cart_item(item)


    def delete_cart_item(self, item):

        index = self.tree.index(item)

        self.tree.delete(item)

        if index < len(self.cart_items):

            del self.cart_items[index]

        if self.editing_cart_index == index:
            self.clear_inputs()
        elif self.editing_cart_index is not None and self.editing_cart_index > index:
            self.editing_cart_index -= 1

        self.refresh_cart_table()

        self.update_total()


    def edit_cart_item(self, item):

        index = self.tree.index(item)

        if index >= len(self.cart_items):
            return

        self.editing_cart_index = index
        cart_item = self.cart_items[index]

        self.product_combo.set(
            cart_item["name"]
        )

        self.qty_entry.delete(0, tk.END)

        self.qty_entry.insert(
            0,
            cart_item["quantity"]
        )

        self.price_entry.delete(
            0,
            tk.END
        )

        self.price_entry.insert(
            0,
            cart_item["price"]
        )

        self.mrp_entry.config(
            state="normal"
        )

        self.mrp_entry.delete(
            0,
            tk.END
        )

        self.mrp_entry.insert(
            0,
            cart_item.get("mrp", 0)
        )

        self.mrp_entry.config(
            state="readonly"
        )

        self.unit_entry.config(
            state="normal"
        )

        self.unit_entry.delete(
            0,
            tk.END
        )

        self.unit_entry.insert(
            0,
            cart_item.get("unit", "Pcs") or "Pcs"
        )


        self.unit_entry.config(
            state="readonly"
        )

        self.discount_entry.delete(
            0,
            tk.END
        )

        self.discount_entry.insert(
            0,
            cart_item["discount"]
        )

        self.discount_base_var.set(cart_item.get("discount_base", "Price"))

        self.add_btn.config(
            text=f"💾 Update Row #{index + 1} (Enter)",
            bg="#0066cc",
            activebackground="#0052a3"
        )

        self.qty_entry.focus_set()
        self.qty_entry.selection_range(0, tk.END)



    def refresh_cart_table(self):

        for row in self.tree.get_children():

            self.tree.delete(row)

        serial = 1

        for idx, item in enumerate(self.cart_items):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=(
                    serial,
                    item["quantity"],
                    item["name"],
                    item["mrp"],
                    item["price"],
                    item["unit"],
                    item["discount"],
                    item.get("discount_base", "Price"),
                    item["total"],
                    "✏",
                    "❌"
                ),
                tags=(tag,)
            )

            serial += 1




    # =========================
    # TALLY GLOBAL KEYBOARD SHORTCUTS
    # =========================

    def _delete_selected_cart_row(self):
        """Delete currently selected row in table via Delete / BackSpace key."""
        selected = self.tree.selection()
        if selected:
            self.delete_cart_item(selected[0])

    def _edit_selected_cart_row(self):
        """Edit currently selected row in table via Enter / F4 key."""
        selected = self.tree.selection()
        if selected:
            self.edit_cart_item(selected[0])

    def _bind_tally_shortcuts(self):
        """Bind global Tally / POS keyboard shortcuts to toplevel window."""
        top = self.frame.winfo_toplevel()
        # F1: Focus Customer Search
        top.bind("<F1>", lambda e: self.customer_combo.focus_set())
        # F2: Focus Product Search
        top.bind("<F2>", lambda e: self.product_combo.focus_set())
        # F3: Quick Add Customer Popup
        top.bind("<F3>", lambda e: self.open_customer_popup())
        top.bind("<Alt-c>", lambda e: self.open_customer_popup())
        top.bind("<Alt-C>", lambda e: self.open_customer_popup())
        # F4: Edit Selected Item in Table
        top.bind("<F4>", lambda e: self._edit_selected_cart_row())
        # F9 / Ctrl+S: Save Invoice + PDF
        top.bind("<F9>", lambda e: self.save_invoice())
        top.bind("<Control-s>", lambda e: self.save_invoice())
        top.bind("<Control-S>", lambda e: self.save_invoice())
        # F12: Jump to Paid Amount
        top.bind("<F12>", lambda e: (self.paid_entry.focus_set(), self.paid_entry.selection_range(0, tk.END)))
        # Alt+X: Clear / New Bill
        top.bind("<Alt-x>", lambda e: self.clear_invoice())
        top.bind("<Alt-X>", lambda e: self.clear_invoice())

