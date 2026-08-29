import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
from database import (
    get_customers_with_pending,
    get_customer_invoices,
    get_invoice_details_by_id,
    get_invoice_items,
    update_invoice_payment,
    get_total_pending,
    update_invoice_note
)
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

        # =========================
        # TABLE
        # =========================

        columns = ("Customer Name", "Total Pending", "Invoices Count")

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", font=("Arial", 10), rowheight=28)

        self.customer_tree = ttk.Treeview(
            self.frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            self.customer_tree.heading(col, text=col, anchor="w")
            self.customer_tree.column(col, width=250, anchor="w")

        self.customer_tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.customer_tree.bind("<Double-1>", self.on_customer_select)

        # Load data
        self.all_customers = []
        self.load_customers()

    def load_customers(self):
        """Load customers with pending amounts"""
        self.customer_tree.delete(*self.customer_tree.get_children())
        self.all_customers = get_customers_with_pending()

        for row in self.all_customers:
            values = (row[0], f"₹ {row[1]}", row[2])
            self.customer_tree.insert("", "end", values=values)

    def search_customers(self, event):
        """Search customers by name"""
        keyword = self.search_entry.get().lower()
        self.customer_tree.delete(*self.customer_tree.get_children())

        for row in self.all_customers:
            if keyword in row[0].lower():
                values = (row[0], f"₹ {row[1]}", row[2])
                self.customer_tree.insert("", "end", values=values)

    def on_customer_select(self, event):
        """Handle customer selection"""
        selected = self.customer_tree.selection()
        if not selected:
            return

        values = self.customer_tree.item(selected)["values"]
        customer_name = values[0]
        self.selected_customer = customer_name
        self.show_invoice_list(customer_name)

    # =========================
    # INVOICE LIST VIEW
    # =========================

    def show_invoice_list(self, customer_name):
        """Display invoices for selected customer"""
        
        # Clear frame
        for widget in self.frame.winfo_children():
            widget.destroy()

        # =========================
        # HEADER
        # =========================

        header_frame = tk.Frame(self.frame)
        header_frame.pack(fill="x", padx=20, pady=10)

        back_btn = tk.Button(
            header_frame,
            text="← Back to Customers",
            command=self.show_customer_list,
            bg="#ffcc66",
            font=("Arial", 10, "bold")
        )
        back_btn.pack(side="left")

        title = tk.Label(
            header_frame,
            text=f"Invoices - {customer_name}",
            font=("Arial", 18, "bold")
        )
        title.pack(side="left", padx=20)

        total_dues = get_total_pending(customer_name) or 0

        dues_label = tk.Label(
            header_frame,
            text=f"Total Dues: ₹ {total_dues}",
            font=("Arial", 13, "bold"),
            fg="red"
        )
        dues_label.pack(side="left", padx=10)

        pay_all_btn = tk.Button(
            header_frame,
            text="Pay All Pending Bills",
            command=self.pay_all_pending_bills,
            bg="#5634f0",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=4
        )
        pay_all_btn.pack(side="left", padx=10)

        # Filter button
        self.filter_pending_only = False
        self.filter_btn = tk.Button(
            header_frame,
            text="Show Pending Invoices Only",
            command=self.toggle_invoice_filter,
            bg="#66ccff",
            font=("Arial", 10, "bold")
        )
        self.filter_btn.pack(side="right")

        # =========================
        # TABLE
        # =========================

        columns = ("Invoice No", "Date", "Total", "Paid", "Pending", "Status", "Note")

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", font=("Arial", 10), rowheight=28)

        self.invoice_tree = ttk.Treeview(
            self.frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            self.invoice_tree.heading(col, text=col, anchor="w")
            self.invoice_tree.column(col, width=180, anchor="w")

        self.invoice_tree.pack(fill="both", expand=True, padx=20, pady=20)
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

    def toggle_invoice_filter(self):
        """Toggle between showing all invoices and pending only"""
        self.filter_pending_only = not self.filter_pending_only
        
        if self.filter_pending_only:
            self.filter_btn.config(text="Show All Invoices")
        else:
            self.filter_btn.config(text="Show Pending Invoices Only")
        
        self.refresh_invoice_display()

    def refresh_invoice_display(self):
        """Refresh invoice tree with current filter"""
        self.invoice_tree.delete(*self.invoice_tree.get_children())

        for row in self.all_invoices:
            invoice_id, invoice_number, date_str, total, paid, pending, note = row
            
            # Apply filter
            if self.filter_pending_only and pending == 0:
                continue
            
            status = "Pending" if pending > 0 else "Paid"
            values = (
                f"INV-{invoice_number}",
                date_str,
                f"₹ {total}",
                f"₹ {paid}",
                f"₹ {pending}",
                status,
                note
            )
            self.invoice_tree.insert("", "end", values=values, iid=invoice_id)

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

        items_table_frame = tk.Frame(items_frame)
        items_table_frame.pack(fill="both", expand=True)

        columns = ("Qty", "Product", "Price", "Unit", "Discount", "Discount On", "Total")
        items_tree = ttk.Treeview(items_table_frame, columns=columns, show="headings", height=6)
        items_scrollbar = ttk.Scrollbar(items_table_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=items_scrollbar.set)

        for col in columns:
            items_tree.heading(col, text=col, anchor="w")
            items_tree.column(col, width=100, anchor="w")

        items_tree.pack(side="left", fill="both", expand=True)
        items_scrollbar.pack(side="right", fill="y")

        # Load items
        invoice_items = get_invoice_items(invoice_id)
        for item in invoice_items:
            qty, product, price, unit, discount, discount_base, item_total = item
            values = (qty, product, f"₹{price}", unit, f"{discount}%", discount_base, f"₹{item_total}")
            items_tree.insert("", "end", values=values)

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

