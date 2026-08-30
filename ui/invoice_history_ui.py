import os

import tkinter as tk

from tkinter import ttk, messagebox

from database import get_connection, update_invoice_note
from config import INVOICES_DIR
from ui.admin_auth_dialog import request_admin_pin




class InvoiceHistoryUI:

    def __init__(self, parent):

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
            text="Invoice History",
            font=("Arial", 18, "bold")
        )

        title.pack(pady=10)

        # =========================
        # SEARCH
        # =========================

        search_frame = tk.Frame(self.frame)

        search_frame.pack(
            fill="x",
            padx=20,
            pady=10
        )

        tk.Label(
            search_frame,
            text="Search:"
        ).pack(side="left")

        self.search_entry = tk.Entry(
            search_frame,
            width=40,
            font=("Arial", 11)
        )

        self.search_entry.pack(
            side="left",
            padx=10
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.search_invoices
        )

        # =========================
        # TABLE
        # =========================

        columns = (
            "Invoice No",
            "Date",
            "Customer",
            "Total",
            "Paid",
            "Pending",
            "Note"
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
            padx=20,
            pady=(0, 20)
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
        self.tree.configure(yscrollcommand=scroll_y.set)

        for col in columns:
            self.tree.heading(
                col,
                text=col,
                anchor="center" if col in ("Date", "Total", "Paid", "Pending") else "w"
            )

            width = 150
            if col == "Invoice No":
                width = 220
            elif col == "Customer":
                width = 200
            elif col in ("Date", "Total", "Paid", "Pending"):
                width = 110
            elif col == "Note":
                width = 180

            self.tree.column(
                col,
                width=width,
                anchor="center" if col in ("Date", "Total", "Paid", "Pending") else "w"
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

        # Double Click
        self.tree.bind(
            "<Double-1>",
            self.handle_double_click
        )

        self.all_invoices = []

        self.load_invoices()

    # =========================
    # LOAD INVOICES
    # =========================

    def load_invoices(self):

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            invoices.id,
            invoices.invoice_number,
            COALESCE(strftime('%d-%m-%Y', invoices.invoice_date), 'N/A'),
            customers.name,
            invoices.total,
            invoices.paid,
            invoices.pending,
            COALESCE(invoices.note, '')

        FROM invoices

        JOIN customers
        ON invoices.customer_id = customers.id

        ORDER BY invoices.id DESC
        """)

        data = cursor.fetchall()

        conn.close()

        self.all_invoices = data

        self.render_table(data)

    # =========================
    # RENDER TABLE
    # =========================

    def render_table(self, data):

        self.tree.delete(
            *self.tree.get_children()
        )

        for idx, row in enumerate(data):

            invoice_no = row[1]  # invoice_number column
            customer_name = row[3]

            # Format: INV-DDMMYY_01_customername
            if invoice_no:
                safe_name = "".join(
                    c for c in customer_name if c.isalnum() or c in (" ", "-", "_")
                ).strip().replace(" ", "_")
                display_invoice = f"INV-{invoice_no}_{safe_name}"
            else:
                display_invoice = f"INV-{row[0]}"

            new_row = (
                display_invoice,
                row[2],
                row[3],
                f"₹ {row[4]}",
                f"₹ {row[5]}",
                f"₹ {row[6]}",
                row[7]
            )

            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                values=new_row,
                iid=row[0],
                tags=(tag,)
            )


    # =========================
    # SEARCH (SMART MULTI-TERM TOKEN SEARCH)
    # =========================

    def search_invoices(self, event=None):

        keyword = (
            self.search_entry.get()
            .strip()
            .lower()
        )

        search_terms = keyword.split()
        if not search_terms:
            self.render_table(self.all_invoices)
            return

        filtered = []

        for row in self.all_invoices:
            # Format: row = (id, invoice_number, date, customer_name, total, paid, pending, note)
            invoice_no = str(row[1] or row[0]).lower()
            date_str = str(row[2] or "").lower()
            customer = str(row[3] or "").lower()
            total = str(row[4] or "")
            paid = str(row[5] or "")
            pending = str(row[6] or "")
            note = str(row[7] or "").lower()

            searchable_text = f"inv-{invoice_no} {date_str} {customer} {total} {paid} {pending} {note}".lower()

            if all(term in searchable_text for term in search_terms):
                filtered.append(row)

        self.render_table(filtered)


    # =========================
    # OPEN PDF
    # =========================

    def handle_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item:
            return

        if column == "#7":
            self.edit_note(item)
        else:
            self.open_invoice_pdf()

    def edit_note(self, invoice_id):
        # Security: Require Admin PIN to edit note
        if not request_admin_pin(self.frame, "modify invoice note"):
            return

        current_values = self.tree.item(invoice_id)["values"]

        current_note = current_values[6] if len(current_values) > 6 else ""

        dialog = tk.Toplevel(self.frame)
        dialog.title("Edit Note")
        dialog.geometry("520x260")
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Update invoice note",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        note_text = tk.Text(dialog, width=50, height=7, font=("Arial", 11))
        note_text.pack(padx=20, pady=10, fill="both", expand=True)
        note_text.insert("1.0", current_note)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        def save_note():
            new_note = note_text.get("1.0", tk.END).strip()
            update_invoice_note(invoice_id, new_note)
            dialog.destroy()
            self.load_invoices()

        tk.Button(
            btn_frame,
            text="Save",
            command=save_note,
            bg="#66cc66",
            fg="white",
            font=("Arial", 11, "bold"),
            width=12
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bg="#cccccc",
            font=("Arial", 11, "bold"),
            width=12
        ).pack(side="left", padx=10)

    def open_invoice_pdf(self):

        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(
            selected
        )["values"]

        invoice_display = values[0]  # Display format: INV-DDMMYY_01_customername

        abs_path = os.path.join(
            INVOICES_DIR,
            f"{invoice_display}.pdf"
        )

        if not os.path.exists(abs_path):


            messagebox.showerror(
                "Error",
                f"PDF not found at {abs_path}"
            )

            return

        try:
            if os.name == "nt":
                os.startfile(abs_path)
            else:
                import subprocess
                opener = "open" if os.name == "darwin" else "xdg-open"
                subprocess.Popen([opener, abs_path])
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not open PDF: {str(e)}"
            )
