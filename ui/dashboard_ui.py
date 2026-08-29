import os
import shutil

import tkinter as tk

from tkinter import filedialog, messagebox

from database import (
    get_total_products,
    get_total_customers,
    get_total_pending_amount,
    get_today_sales,
    get_low_stock_items,
    backup_database_to_file,
    restore_database_from_file
)

from config import DATABASE_PATH, BACKUPS_DIR



class DashboardUI:

    def __init__(self, parent):

        self.frame = tk.Frame(
            parent,
            bg="#f5f5f5"
        )

        self.frame.pack(
            fill="both",
            expand=True
        )

        # =========================
        # TITLE
        # =========================

        title = tk.Label(
            self.frame,
            text="Business Dashboard",
            font=("Arial", 22, "bold"),
            bg="#f5f5f5"
        )

        title.pack(pady=20)

        # =========================
        # TOP BUTTONS
        # =========================

        top_btn_frame = tk.Frame(
            self.frame,
            bg="#f5f5f5"
        )

        top_btn_frame.pack(pady=10)

        backup_btn = tk.Button(
            top_btn_frame,
            text="Backup Database",
            width=20,
            height=2,
            command=self.backup_database
        )

        backup_btn.pack(
            side="left",
            padx=10
        )

        restore_btn = tk.Button(
            top_btn_frame,
            text="Restore Database",
            width=20,
            height=2,
            command=self.restore_database
        )

        restore_btn.pack(
            side="left",
            padx=10
        )

        # =========================
        # CARDS
        # =========================

        cards_frame = tk.Frame(
            self.frame,
            bg="#f5f5f5"
        )

        cards_frame.pack(pady=10)


        self.create_card(
            cards_frame,
            "Total Pending",
            f"₹ {get_total_pending_amount()}",
            1,
            0
        )

        self.create_card(
            cards_frame,
            "Today's Sales",
            f"₹ {get_today_sales()}",
            1,
            1
        )

        # =========================
        # LOW STOCK
        # =========================

        low_stock_frame = tk.LabelFrame(
            self.frame,
            text="Low Stock Items",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=10
        )

        low_stock_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=20
        )

        low_stock_items = get_low_stock_items()

        if len(low_stock_items) == 0:

            tk.Label(
                low_stock_frame,
                text="No low stock items",
                font=("Arial", 11)
            ).pack(pady=10)

        else:

            for item in low_stock_items:

                product_name = item[0]

                stock = item[1]

                text = (
                    f"{product_name} → Stock: {stock}"
                )

                tk.Label(
                    low_stock_frame,
                    text=text,
                    font=("Arial", 11),
                    anchor="w"
                ).pack(
                    fill="x",
                    pady=5
                )

    # =========================
    # CARD CREATOR
    # =========================

    def create_card(
        self,
        parent,
        title,
        value,
        row,
        column
    ):

        card = tk.Frame(
            parent,
            bg="white",
            width=250,
            height=120,
            relief="solid",
            borderwidth=1
        )

        card.grid(
            row=row,
            column=column,
            padx=20,
            pady=20
        )

        card.grid_propagate(False)

        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", 13, "bold"),
            bg="white"
        )

        title_label.pack(pady=15)

        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 20, "bold"),
            bg="white"
        )

        value_label.pack()

    # =========================
    # BACKUP DATABASE
    # =========================

    def backup_database(self):

        try:

            from datetime import datetime

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            backup_file = os.path.join(
                BACKUPS_DIR,
                f"business_backup_{timestamp}.db"
            )

            backup_database_to_file(backup_file)

            messagebox.showinfo(
                "Success",
                f"Backup created successfully:\n{backup_file}"
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Backup failed: {str(e)}"
            )

    # =========================
    # RESTORE DATABASE
    # =========================

    def restore_database(self):

        try:

            backup_file = filedialog.askopenfilename(
                title="Select Backup File",
                initialdir=BACKUPS_DIR,
                filetypes=[
                    ("Database Files", "*.db")
                ]
            )

            if not backup_file:
                return

            confirm = messagebox.askyesno(
                "Confirm Restore",
                "Current database will be replaced with the selected backup.\nContinue?"
            )

            if not confirm:
                return

            restore_database_from_file(backup_file)

            messagebox.showinfo(
                "Success",
                "Database restored successfully.\nPlease restart the application to reload all views."
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Restore failed: {str(e)}"
            )