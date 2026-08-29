import tkinter as tk
from tkinter import ttk

from database import (
    get_customer_history,
    get_total_pending
)


class CustomerHistoryUI:

    def __init__(self, parent, customer_name):

        self.frame = tk.Frame(parent)

        self.frame.pack(fill="both", expand=True)

        title = tk.Label(
            self.frame,
            text=f"{customer_name} Purchase History",
            font=("Arial", 18, "bold")
        )

        title.pack(pady=10)

        # Pending Amount
        pending_amount = get_total_pending(
            customer_name
        )

        pending_label = tk.Label(
            self.frame,
            text=f"Total Pending Balance: ₹ {pending_amount}",
            font=("Arial", 12, "bold"),
            fg="red"
        )

        pending_label.pack(pady=5)

        columns = (
            "Invoice ID",
            "Timestamp",
            "Product",
            "Qty",
            "Total",
            "Paid",
            "Pending"
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
                width=130,
                anchor="w"
            )

        self.tree.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        history = get_customer_history(
            customer_name
        )

        for row in history:

            self.tree.insert(
                "",
                "end",
                values=row
            )