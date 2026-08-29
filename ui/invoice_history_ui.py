import os

import tkinter as tk

from tkinter import ttk, messagebox

from database import get_connection, update_invoice_note
from config import INVOICES_DIR



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

        self.tree = ttk.Treeview(
            self.frame,
            columns=columns,
            show="headings"
        )

        for col in columns:

            self.tree.heading(
                col,
                text=col,
                anchor="w"
            )

            self.tree.column(
                col,
                width=160,
                anchor="w"
            )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

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

        for row in data:

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
                row[4],
                row[5],
                row[6],
                row[7]
            )

            self.tree.insert(
                "",
                "end",
                values=new_row,
                iid=row[0]
            )

    # =========================
    # SEARCH
    # =========================

    def search_invoices(self, event):

        keyword = (
            self.search_entry.get()
            .lower()
        )

        filtered = []

        for row in self.all_invoices:

            invoice_no = row[1]  # invoice_number

            customer = str(row[3]).lower()  # customer name is now at index 3
            note = str(row[7]).lower()

            if (
                keyword in invoice_no.lower()
                or keyword in customer
                or keyword in note
            ):

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
