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

        # self.frame = tk.Frame(parent)

        # self.frame.pack(
        #     fill="both",
        #     expand=True
        # )
        
        canvas = Canvas(parent)

        style = ttk.Style()
        style.configure("TCombobox", font=("Arial", 12, "bold"))
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 12, "bold"), rowheight=36)

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

        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=canvas.yview
        )

        self.frame = tk.Frame(canvas)

        self.frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window(
            (0, 0),
            window=self.frame,
            anchor="nw"
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )
        
        self.canvas = canvas

        # self.frame.bind_all(
        #     "<MouseWheel>",
        #     self._on_mousewheel
        # )
        
        canvas.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5)
        )

        scrollbar.pack(
            side="right",
            fill="y",
            padx=2,
            pady=2
        )

        self.selected_cell_value = ""

        # =========================
        # CUSTOMER SECTION
        # =========================

        customer_frame = tk.Frame(
            self.frame
        )

        customer_frame.pack(
            fill="x",
            padx=12,
            pady=6
        )

        tk.Label(
            customer_frame,
            text="Customer Name",
            font=("Arial", 14, "bold")
        ).pack(
            side="left",
            padx=(6, 8)
        )

        self.customer_combo = (
            AutocompleteCombobox(
                customer_frame,
                width=26
            )
        )

        self.customer_combo.entry.config(
            font=("Arial", 12, "bold")
        )
        self.customer_combo.listbox.config(font=("Arial", 11, "bold"))

        self.customer_combo.pack(
            side="left",
            fill="x",
            expand=True,
            padx=6,
            ipady=4
        )
        
        self.refresh_customers()
        
        # def _on_mousewheel(self, event):

        #     self.canvas.yview_scroll(
        #         int(-1 * (event.delta / 120)),
        #         "units"
        #     )

        #     self.refresh_customers()

        add_customer_btn = tk.Button(
            customer_frame,
            text="+ Add Customer",
            command=self.open_customer_popup,
            bg="#f4a300",
            fg="black",
            activebackground="#d68e00",
            relief="raised",
            bd=3,
            padx=8,
            pady=4,
            font=("Arial", 11, "bold"),
        )

        add_customer_btn.pack(
            side="left",
            padx=5
        )
        
        clear_invoice_btn = tk.Button(
            customer_frame,
            text="Clear & New Invoice",
            bg="#f4a300",
            fg="black",
            activebackground="#d68e00",
            relief="raised",
            bd=3,
            padx=8,
            pady=4,
            font=("Arial", 11, "bold"),
            command=self.clear_invoice
        )

        clear_invoice_btn.pack(
            side="left",
            padx=5
        )

        # =========================
        # PRODUCT SECTION
        # =========================

        product_frame = tk.LabelFrame(
            self.frame,
            text="Add Product",
            padx=15,
            pady=15
        )

        product_frame.pack(
            fill="x",
            padx=12,
            pady=6
        )

        for col in (1, 3, 5, 7):
            product_frame.grid_columnconfigure(col, weight=1)

        # PRODUCT

        tk.Label(
            product_frame,
            text="Product",
            font=("Arial", 13, "bold")
        ).grid(
            row=0,
            column=0,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.product_combo = (
            AutocompleteCombobox(
                product_frame,
                width=28
            )
        )

        self.product_combo.entry.config(
            font=("Arial", 12, "bold")
        )
        self.product_combo.listbox.config(font=("Arial", 11, "bold"))

        self.product_combo.grid(
            row=0,
            column=1,
            columnspan=5,
            padx=5,
            pady=4,
            sticky="ew"
        )

        products = get_product_names()

        self.product_combo.set_completion_list(
            products
        )

        # AUTOFILL EVENTS

        self.product_combo.bind(
            "<KeyRelease>",
            self.autofill_product_details
        )

        self.product_combo.bind(
            "<<ComboboxSelected>>",
            self.autofill_product_details
        )

        self.product_combo.bind(
            "<FocusOut>",
            self.autofill_product_details
        )

        # QTY

        tk.Label(
            product_frame,
            text="Qty",
            font=("Arial", 13, "bold")
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.qty_entry = tk.Entry(
            product_frame,
            width=8,
            font=("Arial", 12, "bold")
        )

        self.qty_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=4,
            ipady=4,
            sticky="ew"
        )


        # MRP

        tk.Label(
            product_frame,
            text="MRP",
            font=("Arial", 13, "bold")
        ).grid(
            row=1,
            column=2,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.mrp_entry = tk.Entry(
            product_frame,
            width=10,
            state="readonly",
            font=("Arial", 12, "bold")
        )

        self.mrp_entry.grid(
            row=1,
            column=3,
            padx=5,
            pady=4,
            ipady=4,
            sticky="ew"
        )

        # PRICE

        tk.Label(
            product_frame,
            text="Price",
            font=("Arial", 13, "bold")
        ).grid(
            row=1,
            column=4,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.price_entry = tk.Entry(
            product_frame,
            width=10,
            font=("Arial", 12, "bold")
        )

        self.price_entry.grid(
            row=1,
            column=5,
            padx=5,
            pady=4,
            ipady=4,
            sticky="ew"
        )

        # UNIT

        tk.Label(
            product_frame,
            text="Unit",
            font=("Arial", 13, "bold")
        ).grid(
            row=1,
            column=6,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.unit_entry = tk.Entry(
            product_frame,
            width=8,
            state="readonly",
            font=("Arial", 12, "bold")
        )

        self.unit_entry.grid(
            row=1,
            column=7,
            padx=5,
            pady=4,
            ipady=4,
            sticky="ew"
        )

        # DISCOUNT

        self.discount_base_var = tk.StringVar(value="Price")

        tk.Label(
            product_frame,
            text="Discount %",
            font=("Arial", 13, "bold")
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.discount_entry = tk.Entry(
            product_frame,
            width=8,
            font=("Arial", 12, "bold")
        )

        self.discount_entry.insert(
            0,
            "0"
        )

        self.discount_entry.grid(
            row=2,
            column=1,
            padx=5,
            pady=4,
            ipady=4,
            sticky="ew"
        )

        tk.Label(
            product_frame,
            text="Discount On",
            font=("Arial", 13, "bold")
        ).grid(
            row=2,
            column=2,
            padx=8,
            pady=6,
            sticky="w"
        )

        self.discount_base_label = tk.Label(
            product_frame,
            textvariable=self.discount_base_var,
            font=("Arial", 12, "bold"),
            fg="#0066cc",
            anchor="w",
            width=10
        )
        self.discount_base_label.grid(
            row=2,
            column=3,
            padx=5,
            pady=4,
            sticky="ew"
        )

        # BUTTON

        self.add_btn = tk.Button(
            product_frame,
            text="Add To Cart",
            width=16,
            command=self.add_to_cart,
            bg="#f4a300",
            fg="black",
            activebackground="#d68e00",
            relief="raised",
            bd=3,
            padx=8,
            pady=4,
            font=("Arial", 11, "bold"),
        )

        self.add_btn.grid(
            row=2,
            column=4,
            columnspan=2,
            padx=10,
            pady=4,
            sticky="e"
        )
        
        self.canvas = canvas

        self.canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

        self.add_btn.bind(
            "<Return>",
            lambda e: self.add_to_cart()
        )

        # =========================
        # TABLE
        # =========================

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
            self.frame,
            columns=columns,
            show="headings"
        )

        for col in columns:

            self.tree.heading(
                col,
                text=col
            )

            width = 120

            if col == "Product":
                width = 220
            elif col in ("MRP", "Price"):
                width = 95
            elif col == "Discount On":
                width = 110
            elif col in ("Edit", "Delete"):
                width = 80

            self.tree.column(
                col,
                width=width,
                anchor="center"
            )

        # SMALLER ACTION COLUMNS

        self.tree.column(
            "Edit",
            width=85,
            anchor="center"
        )

        self.tree.column(
            "Delete",
            width=85,
            anchor="center"
        )

        self.tree.pack(
            fill="x",
            padx=12,
            pady=10
        )

        self.tree.bind(
            "<Button-1>",
            self.handle_table_click
        )

        # =========================
        # BOTTOM
        # =========================

        bottom_frame = tk.Frame(
            self.frame
        )

        bottom_frame.pack(
            fill="x",
            padx=12,
            pady=8
        )

        self.total_label = tk.Label(
            bottom_frame,
            text="Grand Total: ₹ 0",
            font=("Arial", 16, "bold")
        )

        self.total_label.grid(
            row=0,
            column=0,
            columnspan=2,
            pady=6
        )

        tk.Label(
            bottom_frame,
            text="Paid Amount",
            font=("Arial", 12, "bold")
        ).grid(
            row=1,
            column=0,
            pady=6
        )

        self.paid_entry = tk.Entry(
            bottom_frame,
            width=20,
            font=("Arial", 11, "bold")
        )

        self.paid_entry.insert(
            0,
            "0"
        )

        self.paid_entry.grid(
            row=1,
            column=1,
            pady=6
        )
        self.auto_fill_paid = True

        # Update pending when paid amount changes
        self.paid_entry.bind(
            "<KeyRelease>",
            self.on_paid_changed
        )

        self.paid_entry.bind(
            "<FocusOut>",
            lambda e: self.update_pending()
        )

        # Pending amount label (calculated from grand total - paid)
        self.pending_label = tk.Label(
            bottom_frame,
            text="Pending: ₹ 0",
            font=("Arial", 12, "bold")
        )

        self.pending_label.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=5
        )

        tk.Label(
            bottom_frame,
            text="Note",
            font=("Arial", 12, "bold")
        ).grid(
            row=3,
            column=0,
            sticky="nw",
            pady=6
        )

        self.note_text = tk.Text(
            bottom_frame,
            width=40,
            height=3,
            font=("Arial", 11)
        )
        self.note_text.grid(
            row=3,
            column=1,
            pady=6,
            padx=5
        )

        self.save_btn = tk.Button(
            bottom_frame,
            text="Save Invoice + PDF",
            width=25,
            height=2,
            command=self.save_invoice,
            fg="white",
            bg="#5634f0",
            activebackground="#3f22c2",
            relief="raised",
            bd=3,
            padx=10,
            pady=6,
            font=("Arial", 11, "bold"),
        )

        self.save_btn.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=10
        )
        
        self.canvas = canvas

        self.canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )
        
        self.auto_fill_paid = True

        self.restore_state()

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

    def autofill_product_details(
        self,
        event=None
    ):

        selected = (
            self.product_combo.get()
        )

        if not selected:
            return

        if " - " in selected:
            product_name = selected.split(
                " - ",
                1
            )[1]
        else:
            product_name = selected

        product = (
            get_product_complete_details(
                product_name
            )
        )

        if not product:
            return

        # self.price_entry.config(
        #     state="normal"
        # )
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

        # self.price_entry.config(
        #     state="readonly"
        # )

        self.unit_entry.config(
            state="normal"
        )

        self.unit_entry.delete(
            0,
            tk.END
        )

        if len(product) > 5:

            self.unit_entry.insert(
                0,
                str(product[5])
            )

        self.unit_entry.config(
            state="readonly"
        )

        if len(product) > 6 and product[6]:
            self.discount_base_var.set(product[6])
        else:
            self.discount_base_var.set("Price")

    # =========================
    # ADD TO CART
    # =========================

    def add_to_cart(self):

        selected_customer = (
            self.customer_combo.get()
        )

        if selected_customer not in self.customer_list:

            messagebox.showerror(
                "Error",
                "Please select existing customer"
            )

            return

        selected_product = (
            self.product_combo.get()
        )

        if not selected_product:

            messagebox.showerror(
                "Error",
                "Please select product"
            )

            return

        if " - " in selected_product:
            product_name = selected_product.split(
                " - ",
                1
            )[1]
        else:
            product_name = selected_product

        try:
            quantity = int(self.qty_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Quantity",
                "Please enter a valid whole number in Qty."
            )
            return

        try:
            custom_price = float(self.price_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Price",
                "Please enter a valid numeric value in Price."
            )
            return

        unit = self.unit_entry.get()
        if not unit:
            messagebox.showerror(
                "Missing Unit",
                "Unit is missing for the selected product."
            )
            return

        try:
            discount = float(self.discount_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Discount",
                "Please enter a valid numeric value in Discount."
            )
            return

        discount_base = self.discount_base_var.get() or "Price"

        product = (
            get_product_complete_details(
                product_name
            )
        )

        if not product:

            messagebox.showerror(
                "Product Not Found",
                "The selected product is not available in inventory."
            )

            return

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

        item = {

            "product_id": product[0],
            "name": product_name,
            "quantity": quantity,
            "mrp": mrp,
            "price":custom_price,
            "unit": unit,
            "discount": discount,
            "discount_base": discount_base,
            "total": total

        }

        self.cart_items.append(item)

        serial_no = len(
            self.cart_items
        )

        self.tree.insert(
            "",
            "end",
            values=(
                serial_no,
                quantity,
                product_name,
                item["mrp"],
                custom_price,
                unit,
                discount,
                discount_base,
                total,
                "✏",
                "❌"
            )
        )

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

        self.product_combo.set("")

        self.qty_entry.delete(
            0,
            tk.END
        )

        # self.price_entry.config(
        #     state="normal"
        # )

        self.price_entry.delete(
            0,
            tk.END
        )

        # self.price_entry.config(
        #     state="readonly"
        # )

        self.unit_entry.delete(
            0,
            tk.END
        )

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

        self.note_text.delete("1.0", tk.END)

        self.update_total()

    def save_state(self):
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
            "note": self.note_text.get("1.0", "end-1c"),
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

        self.note_text.delete("1.0", tk.END)
        self.note_text.insert("1.0", state["note"])

        self.update_pending()

    # =========================
    # SAVE INVOICE
    # =========================

    def save_invoice(self):

        if not self.cart_items:

            messagebox.showerror(
                "Error",
                "Cart is empty"
            )

            return

        customer_name = (
            self.customer_combo.get()
            .split(" (")[0]
        )

        paid_amount = float(
            self.paid_entry.get()
        )

        note = self.note_text.get("1.0", tk.END).strip()

        # compute and round grand total before saving
        grand_total_raw = sum(
            item["total"]
            for item in self.cart_items
        )

        grand_total = round(grand_total_raw)

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

        messagebox.showinfo(
            "Success",
            "Invoice saved successfully"
        )

    # =========================
    # PDF
    # =========================



    def generate_pdf(
        self,
        invoice_number,
        customer_name,
        grand_total,
        paid_amount
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


        # =====================================
        # TITLE
        # =====================================

        pdf.setFont(
            "Helvetica-Bold",
            22
            
        )
        pdf.setFillColorRGB(0, 0, 1)

        pdf.drawString(
            220,
            800,
            "ESTIMATE ONLY"
        )

        # =====================================
        # HEADER
        # =====================================

        pdf.setFont(
            "Helvetica",
            11
        )
        
        pdf.setFillColorRGB(0, 0, 0)

        pdf.drawString(
            50,
            770,
            f"Invoice: INV-{invoice_number}-{customer_name.split(' ')[0].upper()}"
        )

        pdf.drawString(
            50,
            750,
            f"Customer: {customer_name.upper()}"
        )

        pdf.drawString(
            450,
            770,
            f"Date: {datetime.now().strftime('%d-%m-%Y')}"
        )

        # =====================================
        # TABLE HEADER
        # =====================================

        headers = [
            "S.No",
            "Qty",
            "Product",
            "MRP",
            "Price",
            "Unit",
            "Discount",
            "Total"
        ]

        # x_positions = [
        #     40,
        #     80,
        #     130,
        #     320,
        #     390,
        #     450,
        #     520,
        #     590
        # ]
        x_positions = [
            40,   # S.No
            80,   # Qty
            125,  # Product
            300,  # MRP
            360,  # Price
            420,  # Unit
            475,  # Discount
            540,  # Total
        ]

        table_top = 690

        # Top line
        pdf.line(
            40,
            table_top,
            590,
            table_top
        )

        # Header bottom line
        pdf.line(
            40,
            table_top - 25,
            590,
            table_top - 25
        )

        pdf.setFont(
            "Helvetica-Bold",
            11
        )
        

        for i, header in enumerate(headers):

            pdf.drawString(
                x_positions[i] + 5,
                table_top - 17,
                header
            )
            
        

        # =====================================
        # TABLE ROWS
        # =====================================

        current_y = table_top - 45

        pdf.setFont(
            "Helvetica",
            10
        )

        serial = 1

        for item in self.cart_items:

            wrapped_product = textwrap.wrap(
                item["name"],
                width=24
            )

            row_height = max(
                25,
                len(wrapped_product) * 12
            )

            # S.No
            pdf.drawString(
                x_positions[0] + 5,
                current_y,
                str(serial)
            )

            # Qty
            pdf.drawString(
                x_positions[1] + 5,
                current_y,
                str(item["quantity"])
            )

            # Product
            yy = current_y

            for line in wrapped_product:

                pdf.drawString(
                    x_positions[2] + 5,
                    yy,
                    line
                )

                yy -= 12

            # # Price
            # pdf.drawString(
            #     x_positions[3] + 5,
            #     current_y,
            #     str(item["price"])
            # )

            # # Unit
            # pdf.drawString(
            #     x_positions[4] + 5,
            #     current_y,
            #     str(item["unit"])
            # )

            # # Discount
            # pdf.drawString(
            #     x_positions[5] + 5,
            #     current_y,
            #     str(item["discount"])
            # )

            # # Total
            # pdf.drawString(
            #     x_positions[6] + 5,
            #     current_y,
            #     str(item["total"])
            # )
            
                        # MRP
            pdf.drawString(
                x_positions[3] + 5,
                current_y,
                str(item["mrp"])
            )

            # Price
            pdf.drawString(
                x_positions[4] + 5,
                current_y,
                str(item["price"])
            )

            # Unit
            pdf.drawString(
                x_positions[5] + 5,
                current_y,
                str(item["unit"] or "")
            )

            # Discount
            discount_value = float(item["discount"])

            if discount_value.is_integer():
                discount_text = f'{int(discount_value)}% on {item.get("discount_base", "Price")}'
            else:
                discount_text = f'{discount_value}% on {item.get("discount_base", "Price")}'

            pdf.drawString(
                x_positions[6] + 5,
                current_y,
                discount_text
            )

            # Total
            pdf.drawString(
                x_positions[7] + 5,
                current_y,
                str(round(item["total"], 2))
            )

            current_y -= row_height

            serial += 1

        # =====================================
        # TABLE BOTTOM
        # =====================================

        table_bottom = current_y + 10

        pdf.line(
            40,
            table_bottom,
            590,
            table_bottom
        )

        # =====================================
        # VERTICAL LINES
        # =====================================

        for x in x_positions:

            pdf.line(
                x,
                table_top,
                x,
                table_bottom
            )

        # =====================================
        # TOTALS
        # =====================================

        totals_y = table_bottom - 50

        pending_amount = (
            grand_total - paid_amount
        )

        pdf.setFont(
            "Helvetica-Bold",
            10
        )

        pdf.drawString(
            430,
            totals_y,
            f"Grand Total : Rs. {grand_total}"
        )

        pdf.drawString(
            430,
            totals_y - 25,
            f"Paid Amount : Rs. {paid_amount}"
        )

        pdf.drawString(
            430,
            totals_y - 50,
            f"Pending Amount : Rs. {pending_amount}"
        )
        
        pdf.setFont(
            "Helvetica",
            8
        )
        
        pdf.drawString(
            230,
            totals_y - 200,
            f"GST as per applicable. Order against PO"
        )

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

        self.pending_label.config(
            text=f"Pending: ₹ {pending_display}"
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

        self.refresh_cart_table()

        self.update_total()


    def edit_cart_item(self, item):

        index = self.tree.index(item)

        if index >= len(self.cart_items):
            return

        cart_item = self.cart_items[index]

        self.product_combo.set(
            cart_item["name"]
        )

        self.qty_entry.delete(0, tk.END)

        self.qty_entry.insert(
            0,
            cart_item["quantity"]
        )

        # self.price_entry.config(
        #     state="normal"
        # )

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

        # self.price_entry.config(
        #     state="readonly"
        # )

        self.unit_entry.config(
            state="normal"
        )

        self.unit_entry.delete(
            0,
            tk.END
        )

        self.unit_entry.insert(
            0,
            cart_item["unit"]
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

        del self.cart_items[index]

        self.refresh_cart_table()

        self.update_total()


    def refresh_cart_table(self):

        for row in self.tree.get_children():

            self.tree.delete(row)

        serial = 1

        for item in self.cart_items:

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
                )
            )

            serial += 1
