import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
from datetime import datetime
from database import (
    get_customers_with_pending,
    get_customer_invoices,
    get_invoice_details_by_id,
    get_invoice_items,
    update_invoice_payment,
    get_total_pending,
    update_invoice_note,
    get_customer_statement_data,
    record_audit_log
)

from config import INVOICES_DIR
from ui.admin_auth_dialog import request_admin_pin




class LedgerUI:

    def __init__(self, parent):

        self.parent = parent
        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        
        self.current_view = "customers"  # Track current view
        self.selected_customer = None
        self.selected_invoice = None

        # Show customer list initially
        self.show_customer_list()

    # =========================
    # CUSTOMER LIST VIEW
    # =========================

    def show_customer_list(self):
        """Display customers with pending amounts"""
        
        # Clear frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # =========================
        # TITLE
        # =========================

        title = tk.Label(
            self.frame,
            text="Customer Ledger - Pending Amounts",
            font=("Arial", 18, "bold")
        )

        title.pack(pady=10)

        # =========================
        # SEARCH
        # =========================

        search_frame = tk.Frame(self.frame)
        search_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(
            search_frame,
            text="Search Customer:",
            font=("Arial", 11, "bold")
        ).pack(side="left")

        self.search_entry = tk.Entry(
            search_frame,
            width=30,
            font=("Arial", 11)
        )

        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<KeyRelease>", self.search_customers)

        open_ledger_btn = tk.Button(
            search_frame,
            text="📂 View Invoices (Enter)",
            command=self.on_customer_select,
            bg="#0066cc",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=3
        )
        open_ledger_btn.pack(side="right", padx=5)

        export_ledger_btn = tk.Button(
            search_frame,
            text="📊 Export Ledger CSV",
            command=self.export_ledger_csv,
            bg="#28a745",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=3
        )
        export_ledger_btn.pack(side="right", padx=5)


        # =========================
        # TABLE
        # =========================

        columns = ("Customer Name", "Total Pending", "Invoices Count")

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

        self.customer_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        scroll_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.customer_tree.yview
        )
        self.customer_tree.configure(yscrollcommand=scroll_y.set)

        for col in columns:
            self.customer_tree.heading(
                col,
                text=col,
                anchor="center" if col in ("Total Pending", "Invoices Count") else "w"
            )
            width = 300 if col == "Customer Name" else 160
            self.customer_tree.column(
                col,
                width=width,
                anchor="center" if col in ("Total Pending", "Invoices Count") else "w"
            )

        self.customer_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.customer_tree.tag_configure("evenrow", background="#ffffff")
        self.customer_tree.tag_configure("oddrow", background="#f8f9fa")

        self.customer_tree.bind("<Double-1>", self.on_customer_select)
        self.customer_tree.bind("<Return>", self.on_customer_select)
        self.customer_tree.bind("<ButtonRelease-1>", self.on_customer_select)

        # Load data
        self.all_customers = []
        self.load_customers()

    def load_customers(self):
        """Load customers with pending amounts"""
        self.customer_tree.delete(*self.customer_tree.get_children())
        self.all_customers = get_customers_with_pending()

        for idx, row in enumerate(self.all_customers):
            values = (row[0], f"₹ {row[1]}", row[2])
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.customer_tree.insert("", "end", values=values, tags=(tag,))

    def search_customers(self, event):
        """Search customers by name"""
        keyword = self.search_entry.get().lower()
        self.customer_tree.delete(*self.customer_tree.get_children())

        match_count = 0
        for row in self.all_customers:
            if keyword in row[0].lower():
                values = (row[0], f"₹ {row[1]}", row[2])
                tag = "evenrow" if match_count % 2 == 0 else "oddrow"
                self.customer_tree.insert("", "end", values=values, tags=(tag,))
                match_count += 1

    def on_customer_select(self, event=None):
        """Handle customer selection on click, double-click, or Enter key"""
        if event and hasattr(event, "y"):
            region = self.customer_tree.identify("region", event.x, event.y)
            if region not in ("cell", "tree"):
                return
            row_id = self.customer_tree.identify_row(event.y)
            if row_id:
                self.customer_tree.selection_set(row_id)

        selected = self.customer_tree.selection()
        if not selected:
            return

        item_data = self.customer_tree.item(selected[0])
        values = item_data.get("values", [])
        if not values or len(values) == 0:
            return

        customer_name = str(values[0])
        self.selected_customer = customer_name
        self.show_invoice_list(customer_name)


    def export_ledger_csv(self):
        """Exports the customer dues ledger to CSV (Admin PIN Protected)."""
        if not request_admin_pin(self.frame, "export customer ledger data to CSV"):
            return

        from tkinter import filedialog
        import csv

        file_path = filedialog.asksaveasfilename(
            title="Export Customer Ledger",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="customer_ledger.csv"
        )

        if not file_path:
            return

        try:
            customers = get_customers_with_pending()
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Customer Name", "Total Pending Dues (Rs)", "Invoices Count"])
                for row in customers:
                    writer.writerow([row[0], row[1], row[2]])

            record_audit_log("CSV_EXPORT", f"Exported customer ledger dues ({len(customers)} customers) to {file_path}")

            messagebox.showinfo("Export Successful", f"Customer ledger exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))


    # =========================
    # INVOICE LIST VIEW
    # =========================

    def show_invoice_list(self, customer_name):
        """Display invoices for selected customer"""
        
        # Clear frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Header Frame
        header_frame = tk.Frame(self.frame)
        header_frame.pack(fill="x", padx=20, pady=10)

        # Back Button
        back_btn = tk.Button(
            header_frame,
            text="← Back to Customers",
            command=self.show_customer_list,
            bg="#f0f0f0",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5
        )
        back_btn.pack(side="left")

        # Customer Info
        info_frame = tk.Frame(header_frame)
        info_frame.pack(side="left", padx=20)

        name_label = tk.Label(
            info_frame,
            text=f"Customer: {customer_name}",
            font=("Arial", 13, "bold"),
            fg="#333333"
        )
        name_label.pack(anchor="w")

        # Calculate Total Pending for this customer
        invoices = get_customer_invoices(customer_name)
        total_dues = sum(inv[5] for inv in invoices)

        dues_label = tk.Label(
            info_frame,
            text=f"Total Dues: ₹ {total_dues}",
            font=("Arial", 12, "bold"),
            fg="#d9534f" if total_dues > 0 else "#5cb85c"
        )
        dues_label.pack(anchor="w")

        # Action Buttons on Right
        action_btn_frame = tk.Frame(header_frame)
        action_btn_frame.pack(side="right")

        # Export Statement PDF Button
        statement_btn = tk.Button(
            action_btn_frame,
            text="📄 Statement PDF",
            command=self.export_statement_pdf,
            bg="#17a2b8",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=5
        )
        statement_btn.pack(side="left", padx=5)

        # Pay All Bills Button
        pay_all_btn = tk.Button(
            action_btn_frame,
            text="Pay All Bills",
            command=self.pay_all_pending_bills,
            bg="#5634f0",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=12,
            pady=5
        )
        pay_all_btn.pack(side="left", padx=5)

        # Search / Filter by Date
        filter_frame = tk.Frame(self.frame)
        filter_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(
            filter_frame,
            text="Filter Invoices:",
            font=("Arial", 10, "bold")
        ).pack(side="left")

        self.invoice_search_entry = tk.Entry(
            filter_frame,
            width=25,
            font=("Arial", 10)
        )
        self.invoice_search_entry.pack(side="left", padx=10)
        self.invoice_search_entry.bind("<KeyRelease>", self.filter_invoices)

        # Status filter buttons
        self.status_filter_var = tk.StringVar(value="All")

        all_radio = tk.Radiobutton(
            filter_frame,
            text="All",
            variable=self.status_filter_var,
            value="All",
            command=self.filter_invoices
        )
        all_radio.pack(side="left", padx=5)

        pending_radio = tk.Radiobutton(
            filter_frame,
            text="Pending Only",
            variable=self.status_filter_var,
            value="Pending",
            command=self.filter_invoices
        )
        pending_radio.pack(side="left", padx=5)

        paid_radio = tk.Radiobutton(
            filter_frame,
            text="Paid Only",
            variable=self.status_filter_var,
            value="Paid",
            command=self.filter_invoices
        )
        paid_radio.pack(side="left", padx=5)

        # Invoices Table
        columns = ("Invoice ID", "Invoice Number", "Date", "Total", "Paid", "Pending", "Note")

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

        self.invoice_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        scroll_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.invoice_tree.yview
        )
        self.invoice_tree.configure(yscrollcommand=scroll_y.set)

        for col in columns:
            self.invoice_tree.heading(
                col,
                text=col,
                anchor="center" if col in ("Date", "Total", "Paid", "Pending") else "w"
            )
            width = 160
            if col == "Invoice Number":
                width = 220
            elif col in ("Date", "Total", "Paid", "Pending"):
                width = 110
            elif col == "Note":
                width = 180

            self.invoice_tree.column(
                col,
                width=width,
                anchor="center" if col in ("Date", "Total", "Paid", "Pending") else "w"
            )

        self.invoice_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.invoice_tree.tag_configure("evenrow", background="#ffffff")
        self.invoice_tree.tag_configure("oddrow", background="#f8f9fa")

        self.invoice_tree.bind("<Double-1>", self.on_invoice_double_click)

        # Store all invoices for filtering
        self.all_invoices = get_customer_invoices(customer_name)
        self.current_customer_name = customer_name
        self.current_total_dues = total_dues
        
        # Display invoices
        self.refresh_invoice_display()


    def pay_all_pending_bills(self):
        """Clear all pending invoices for the selected customer (Admin PIN Required)"""
        customer_name = getattr(self, "current_customer_name", None)
        total_dues = getattr(self, "current_total_dues", 0)

        if not customer_name:
            return

        if total_dues <= 0:
            messagebox.showinfo("No Pending Bills", f"{customer_name} has no pending bills")
            return

        # Security: Require Admin PIN
        if not request_admin_pin(self.frame, f"clear all pending bills (₹ {total_dues}) of {customer_name}"):
            return

        pending_invoices = [invoice for invoice in self.all_invoices if invoice[5] > 0]
        pending_invoice_count = len(pending_invoices)

        confirm_dialog = tk.Toplevel(self.frame)
        confirm_dialog.title("Confirm Clear All Bills")
        confirm_dialog.geometry("620x280")
        confirm_dialog.resizable(False, False)
        confirm_dialog.transient(self.frame.winfo_toplevel())
        confirm_dialog.grab_set()
        confirm_dialog.update_idletasks()

        screen_width = confirm_dialog.winfo_screenwidth()
        screen_height = confirm_dialog.winfo_screenheight()
        dialog_width = 620
        dialog_height = 280
        pos_x = (screen_width - dialog_width) // 2
        pos_y = (screen_height - dialog_height) // 2
        confirm_dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")

        msg = tk.Label(
            confirm_dialog,
            text=(
                f"Are you sure you want to clear total "
                f"{pending_invoice_count} pending invoices of ₹ {total_dues}\n"
                f"of {customer_name}?"
            ),
            font=("Arial", 17, "bold"),
            fg="#333333",
            pady=36,
            padx=20,
            justify="center",
            wraplength=540,
            anchor="center"
        )
        msg.pack(fill="x", padx=20)

        btn_frame = tk.Frame(confirm_dialog)
        btn_frame.pack(pady=20)

        def confirm_yes():
            for invoice in pending_invoices:
                invoice_id, invoice_number, date_str, total, paid, pending, note = invoice
                update_invoice_payment(invoice_id, total)

            record_audit_log(
                "BILL_CLEAR_ALL",
                f"Cleared all {pending_invoice_count} pending bills (Total dues: Rs.{total_dues}) for customer '{customer_name}'"
            )

            confirm_dialog.destroy()
            messagebox.showinfo("Success", f"All pending bills of {customer_name} cleared successfully")
            self.show_invoice_list(customer_name)

        def confirm_no():
            confirm_dialog.destroy()

        yes_btn = tk.Button(
            btn_frame,
            text="Yes",
            command=confirm_yes,
            bg="#66cc66",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=2
        )
        yes_btn.pack(side="left", padx=20)

        no_btn = tk.Button(
            btn_frame,
            text="No",
            command=confirm_no,
            bg="#ff6666",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=2
        )
        no_btn.pack(side="left", padx=20)

    def export_statement_pdf(self):
        """Generates a formal Statement of Account PDF for the selected customer."""
        customer_name = getattr(self, "current_customer_name", None)
        if not customer_name:
            return

        cust_info, transactions = get_customer_statement_data(customer_name)
        if not cust_info or not transactions:
            messagebox.showinfo("No Transactions", f"No transactions found for {customer_name}")
            return

        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', customer_name)
        today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.join(INVOICES_DIR, f"Statement_{safe_name}_{today_str}.pdf")

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from database import get_shop_details

            shop = get_shop_details()

            pdf = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter

            # Header Title
            pdf.setFont("Helvetica-Bold", 18)
            pdf.setFillColorRGB(0.12, 0.14, 0.18)
            pdf.drawString(40, height - 50, "STATEMENT OF ACCOUNT")

            pdf.setFont("Helvetica", 9)
            pdf.setFillColorRGB(0.35, 0.35, 0.35)
            pdf.drawString(40, height - 68, f"Generated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}")

            # Business Details (Right aligned)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColorRGB(0.1, 0.1, 0.1)
            pdf.drawRightString(width - 40, height - 50, str(shop["name"]))
            pdf.setFont("Helvetica", 9)
            pdf.setFillColorRGB(0.4, 0.4, 0.4)
            pdf.drawRightString(width - 40, height - 65, str(shop["address"]))
            pdf.drawRightString(width - 40, height - 78, f"Phone: {shop['phone']}")


            # Divider line
            pdf.setStrokeColorRGB(0.8, 0.8, 0.8)
            pdf.setLineWidth(1)
            pdf.line(40, height - 90, width - 40, height - 90)

            # Customer Details & Balance Box
            pdf.setFillColorRGB(0.96, 0.97, 0.98)
            pdf.roundRect(40, height - 165, width - 80, 65, 4, fill=1, stroke=0)

            pdf.setFont("Helvetica-Bold", 11)
            pdf.setFillColorRGB(0.2, 0.2, 0.2)
            pdf.drawString(55, height - 112, f"Customer: {cust_info['name']}")
            pdf.setFont("Helvetica", 9)
            pdf.drawString(55, height - 128, f"Phone: {cust_info['phone'] or 'N/A'}")
            pdf.drawString(55, height - 144, f"Address: {cust_info['address'] or 'N/A'}")

            # Balance Summary (Right Box)
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(width - 230, height - 112, f"Total Invoiced: Rs. {cust_info['total_invoiced']:.2f}")
            pdf.drawString(width - 230, height - 128, f"Total Paid: Rs. {cust_info['total_paid']:.2f}")
            pdf.setFillColorRGB(0.85, 0.1, 0.1)
            pdf.drawString(width - 230, height - 144, f"Net Balance: Rs. {cust_info['net_dues']:.2f}")

            # Table Header Bar
            table_top = height - 190
            pdf.setFillColorRGB(0.12, 0.14, 0.18)
            pdf.rect(40, table_top - 18, width - 80, 20, fill=1, stroke=0)

            pdf.setFont("Helvetica-Bold", 9)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.drawString(50, table_top - 14, "Date")
            pdf.drawString(130, table_top - 14, "Invoice No")
            pdf.drawRightString(280, table_top - 14, "Billed (Debit)")
            pdf.drawRightString(370, table_top - 14, "Paid (Credit)")
            pdf.drawRightString(460, table_top - 14, "Pending")
            pdf.drawRightString(width - 50, table_top - 14, "Balance Due")

            # Table Rows
            y = table_top - 36
            for i, tx in enumerate(transactions):
                if y < 70:
                    # Draw page footer on current page
                    pdf.setStrokeColorRGB(0.85, 0.85, 0.85)
                    pdf.line(40, 45, width - 40, 45)
                    pdf.setFont("Helvetica-Bold", 8)
                    pdf.setFillColorRGB(0.5, 0.5, 0.5)
                    pdf.drawRightString(width - 40, 32, "⚡ Powered by wokdens.com")

                    pdf.showPage()
                    y = height - 60

                    # Table Header on new page
                    pdf.setFillColorRGB(0.12, 0.14, 0.18)
                    pdf.rect(40, y - 18, width - 80, 20, fill=1, stroke=0)
                    pdf.setFont("Helvetica-Bold", 9)
                    pdf.setFillColorRGB(1, 1, 1)
                    pdf.drawString(50, y - 14, "Date")
                    pdf.drawString(130, y - 14, "Invoice No")
                    pdf.drawRightString(280, y - 14, "Billed (Debit)")
                    pdf.drawRightString(370, y - 14, "Paid (Credit)")
                    pdf.drawRightString(460, y - 14, "Pending")
                    pdf.drawRightString(width - 50, y - 14, "Balance Due")
                    y -= 36

                # Alternate row shading
                if i % 2 == 1:
                    pdf.setFillColorRGB(0.97, 0.97, 0.97)
                    pdf.rect(40, y - 4, width - 80, 16, fill=1, stroke=0)

                pdf.setFont("Helvetica", 9)
                pdf.setFillColorRGB(0.2, 0.2, 0.2)
                pdf.drawString(50, y, str(tx["date"]))
                pdf.drawString(130, y, f"INV-{tx['invoice_number']}")
                pdf.drawRightString(280, y, f"Rs. {tx['total']:.2f}")
                pdf.drawRightString(370, y, f"Rs. {tx['paid']:.2f}")
                pdf.drawRightString(460, y, f"Rs. {tx['pending']:.2f}")
                pdf.drawRightString(width - 50, y, f"Rs. {tx['running_balance']:.2f}")
                y -= 18

            # Footer
            pdf.setStrokeColorRGB(0.8, 0.8, 0.8)
            pdf.line(40, 45, width - 40, 45)
            pdf.setFont("Helvetica", 8)
            pdf.setFillColorRGB(0.4, 0.4, 0.4)
            pdf.drawString(40, 32, "Please verify all transactions and clear outstanding dues promptly.")
            pdf.setFont("Helvetica-Bold", 8)
            pdf.drawRightString(width - 40, 32, "⚡ Powered by wokdens.com")


            pdf.save()

            # Open PDF automatically
            if os.name == "nt":
                os.startfile(os.path.abspath(pdf_path))
            else:
                subprocess.Popen(["xdg-open", os.path.abspath(pdf_path)])

            messagebox.showinfo("Statement Generated", f"Statement of Account saved successfully:\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Error Generating Statement", str(e))


    def filter_invoices(self, event=None):
        """Filter invoices based on search text and status filter (All, Pending, Paid)."""
        search_kw = getattr(self, "invoice_search_entry", None)
        keyword = search_kw.get().strip().lower() if search_kw else ""
        status_filter = getattr(self, "status_filter_var", None)
        status_val = status_filter.get() if status_filter else "All"

        self.invoice_tree.delete(*self.invoice_tree.get_children())

        display_count = 0
        for row in getattr(self, "all_invoices", []):
            invoice_id, invoice_number, date_str, total, paid, pending, note = row

            # Status filter
            if status_val == "Pending" and pending <= 0:
                continue
            elif status_val == "Paid" and pending > 0:
                continue

            # Keyword filter (invoice number, date, note, amounts)
            if keyword:
                searchable_text = f"inv-{invoice_number} {date_str} {note or ''} {total} {paid} {pending}".lower()
                if keyword not in searchable_text:
                    continue

            status = "Pending" if pending > 0 else "Paid"
            values = (
                f"INV-{invoice_number}",
                date_str,
                f"₹ {total}",
                f"₹ {paid}",
                f"₹ {pending}",
                status,
                note or ""
            )
            tag = "evenrow" if display_count % 2 == 0 else "oddrow"
            self.invoice_tree.insert("", "end", values=values, iid=invoice_id, tags=(tag,))
            display_count += 1

    def refresh_invoice_display(self):
        """Refresh invoice tree with current filter"""
        self.filter_invoices()



    def on_invoice_double_click(self, event):
        """Open payment dialog or edit note depending on clicked column"""
        region = self.invoice_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        invoice_id = self.invoice_tree.identify_row(event.y)
        column = self.invoice_tree.identify_column(event.x)

        if not invoice_id:
            return

        self.selected_invoice = invoice_id
        if column == "#7":
            self.edit_invoice_note(invoice_id)
        else:
            self.show_payment_dialog(invoice_id)

    def edit_invoice_note(self, invoice_id):
        # Security: Require Admin PIN to edit note
        if not request_admin_pin(self.frame, "modify invoice note"):
            return

        current_values = self.invoice_tree.item(invoice_id)["values"]
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
            self.show_invoice_list(self.current_customer_name)

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


    # =========================
    # PAYMENT DIALOG
    # =========================

    def show_payment_dialog(self, invoice_id):
        """Show payment update dialog for invoice"""
        
        invoice_data = get_invoice_details_by_id(invoice_id)
        
        if not invoice_data:
            messagebox.showerror("Error", "Invoice not found")
            return

        inv_id, inv_number, customer_name, date_str, total, paid, pending, note = invoice_data

        # Create dialog with scrollbar - optimized height
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Update Payment - INV-{inv_number}")
        dialog.geometry("900x650")

        # Main canvas for scrolling
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # =========================
        # INVOICE DETAILS - OPTIMIZED LAYOUT
        # =========================

        details_frame = tk.LabelFrame(scrollable_frame, text="Invoice Details", padx=15, pady=10)
        details_frame.pack(fill="x", padx=20, pady=10)

        # Left column (Date and Customer)
        left_column = tk.Frame(details_frame)
        left_column.pack(side="left", fill="x", expand=True)

        date_row = tk.Frame(left_column)
        date_row.pack(anchor="w", pady=2)
        tk.Label(date_row, text="Date:", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(date_row, text=date_str, font=("Arial", 10)).pack(side="left", padx=10)

        customer_row = tk.Frame(left_column)
        customer_row.pack(anchor="w", pady=2)
        tk.Label(customer_row, text="Customer:", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(customer_row, text=customer_name, font=("Arial", 10)).pack(side="left", padx=10)

        # Right column (Invoice Number and Total Pending)
        right_column = tk.Frame(details_frame)
        right_column.pack(side="right", fill="x", expand=True)

        inv_row = tk.Frame(right_column)
        inv_row.pack(anchor="w", pady=2)
        tk.Label(
            inv_row,
            text=f"Invoice Number: INV-{inv_number}",
            font=("Arial", 10, "bold"),
            fg="#0066ff"
        ).pack(side="left")

        pending_row = tk.Frame(right_column)
        pending_row.pack(anchor="w", pady=2)
        tk.Label(pending_row, text="Total Pending:", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(pending_row, text=f"₹ {pending}", font=("Arial", 11, "bold"), fg="red").pack(side="left", padx=10)

        # =========================
        # INVOICE ITEMS TABLE
        # =========================

        items_frame = tk.LabelFrame(scrollable_frame, text="Invoice Items", padx=15, pady=15)
        items_frame.pack(fill="x", padx=20, pady=10)

        items_table_frame = tk.Frame(
            items_frame,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground="#ced4da"
        )
        items_table_frame.pack(fill="both", expand=True)

        columns = ("Qty", "Product", "Price", "Unit", "Discount", "Discount On", "Total")
        items_tree = ttk.Treeview(items_table_frame, columns=columns, show="headings", height=6)
        items_scrollbar = ttk.Scrollbar(items_table_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=items_scrollbar.set)

        for col in columns:
            items_tree.heading(
                col,
                text=col,
                anchor="center" if col in ("Qty", "Price", "Unit", "Discount", "Discount On", "Total") else "w"
            )
            items_tree.column(
                col,
                width=100,
                anchor="center" if col in ("Qty", "Price", "Unit", "Discount", "Discount On", "Total") else "w"
            )

        items_tree.pack(side="left", fill="both", expand=True)
        items_scrollbar.pack(side="right", fill="y")

        items_tree.tag_configure("evenrow", background="#ffffff")
        items_tree.tag_configure("oddrow", background="#f8f9fa")

        # Load items
        invoice_items = get_invoice_items(invoice_id)
        for idx, item in enumerate(invoice_items):
            qty, product, price, unit, discount, discount_base, item_total = item
            values = (qty, product, f"₹{price}", unit, f"{discount}%", discount_base, f"₹{item_total}")
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            items_tree.insert("", "end", values=values, tags=(tag,))


        # =========================
        # PAYMENT UPDATE
        # =========================

        payment_frame = tk.LabelFrame(scrollable_frame, text="Payment Update", padx=15, pady=15)
        payment_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(payment_frame, text="Current Paid:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(payment_frame, text=f"₹ {paid}", font=("Arial", 10)).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        tk.Label(payment_frame, text="Current Pending:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(payment_frame, text=f"₹ {pending}", font=("Arial", 10)).grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Option: Pay Partially (incremental)
        tk.Label(payment_frame, text="Pay Partially:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=10)

        pay_partial_entry = tk.Entry(payment_frame, font=("Arial", 10), width=20)
        pay_partial_entry.insert(0, "0")
        pay_partial_entry.grid(row=2, column=1, sticky="w", padx=10, pady=10)

        # Real-time pending calculation
        pending_label = tk.Label(payment_frame, text=f"New Pending: ₹ {pending}", font=("Arial", 10, "bold"), fg="red")
        pending_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

        def update_pending_display(event=None):
            try:
                pay_partial = float(pay_partial_entry.get()) if pay_partial_entry.get() else 0
                new_pending = max(0, pending - pay_partial)
                pending_label.config(text=f"New Pending: ₹ {new_pending}")
            except:
                pending_label.config(text=f"New Pending: ₹ {pending}")

        pay_partial_entry.bind("<KeyRelease>", update_pending_display)

        # =========================
        # BUTTONS
        # =========================

        button_frame = tk.Frame(scrollable_frame)
        button_frame.pack(fill="x", padx=20, pady=20)

        def clear_bill():
            """Mark the entire bill as paid with confirmation (Admin PIN Required)"""
            if not request_admin_pin(dialog, f"clear bill INV-{inv_number} (₹ {pending})"):
                return

            # Confirmation popup - larger and bolder
            confirm_dialog = tk.Toplevel(dialog)
            confirm_dialog.title("Confirm Payment")
            confirm_dialog.geometry("560x260")
            confirm_dialog.resizable(False, False)
            
            # Center the dialog
            confirm_dialog.transient(dialog)
            confirm_dialog.grab_set()
            
            # Message label - bold and large
            msg = tk.Label(
                confirm_dialog,
                text=f"Are you sure {customer_name}\nhas paid ₹ {pending}?",
                font=("Arial", 17, "bold"),
                fg="#333333",
                pady=38,
                padx=20,
                justify="center"
            )
            msg.pack()
            
            # Button frame
            btn_frame = tk.Frame(confirm_dialog)
            btn_frame.pack(pady=20)
            
            response_var = [None]
            
            def confirm_yes():
                response_var[0] = True
                confirm_dialog.destroy()
            
            def confirm_no():
                response_var[0] = False
                confirm_dialog.destroy()
            
            yes_btn = tk.Button(
                btn_frame,
                text="Yes",
                command=confirm_yes,
                bg="#66cc66",
                fg="white",
                font=("Arial", 13, "bold"),
                width=12,
                height=2
            )
            yes_btn.pack(side="left", padx=20)
            
            no_btn = tk.Button(
                btn_frame,
                text="No",
                command=confirm_no,
                bg="#ff6666",
                fg="white",
                font=("Arial", 13, "bold"),
                width=12,
                height=2
            )
            no_btn.pack(side="left", padx=20)
            
            confirm_dialog.wait_window()
            response = response_var[0]
            
            if response:
                # Update database - set paid to total
                update_invoice_payment(invoice_id, total)
                record_audit_log(
                    "BILL_CLEAR",
                    f"Cleared full bill INV-{inv_number} (Paid: Rs.{pending}) for customer '{customer_name}'"
                )
                messagebox.showinfo("Success", "Bill marked as paid successfully")
                
                # Refresh invoice list
                dialog.destroy()
                self.show_invoice_list(self.current_customer_name)
            else:
                messagebox.showinfo("Cancelled", "Payment not confirmed")

        def pay_partially():
            try:
                pay_partial_amount = float(pay_partial_entry.get())
                if pay_partial_amount <= 0:
                    messagebox.showerror("Error", "Please enter a valid amount to pay")
                    return

                if pay_partial_amount > pending:
                    messagebox.showerror("Error", f"Payment amount (₹ {pay_partial_amount}) cannot exceed pending (₹ {pending})")
                    return

                if not request_admin_pin(dialog, f"record partial payment of ₹ {pay_partial_amount} for INV-{inv_number}"):
                    return

                new_paid = paid + pay_partial_amount
                
                # Update database
                update_invoice_payment(invoice_id, new_paid)
                record_audit_log(
                    "PARTIAL_PAYMENT",
                    f"Paid partial amount Rs.{pay_partial_amount} on bill INV-{inv_number} for customer '{customer_name}' (New Paid: Rs.{new_paid})"
                )

                messagebox.showinfo("Success", f"Payment of ₹ {pay_partial_amount} recorded successfully")

                # Refresh invoice list
                dialog.destroy()
                self.show_invoice_list(self.current_customer_name)

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")


        clear_bill_btn = tk.Button(
            button_frame,
            text="Clear Bill",
            command=clear_bill,
            bg="#5634f0",
            fg="white",
            font=("Arial", 10, "bold"),
            width=18
        )
        clear_bill_btn.pack(side="left", padx=5)

        pay_partial_btn = tk.Button(
            button_frame,
            text="Pay Partially",
            command=pay_partially,
            bg="#66cc66",
            fg="white",
            font=("Arial", 10, "bold"),
            width=18
        )
        pay_partial_btn.pack(side="left", padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            bg="#cccccc",
            font=("Arial", 10, "bold"),
            width=18
        )
        cancel_btn.pack(side="left", padx=5)

