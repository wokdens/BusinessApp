import tkinter as tk

from tkinter import messagebox

from database import (
    get_connection
)


class CustomerPopup:

    def __init__(
        self,
        parent,
        refresh_callback
    ):

        self.refresh_callback = (
            refresh_callback
        )

        self.window = tk.Toplevel(parent)

        self.window.title(
            "Add Customer"
        )

        self.window.geometry(
            "400x350"
        )

        self.window.grab_set()

        # =========================
        # TITLE
        # =========================

        title = tk.Label(
            self.window,
            text="Add Customer",
            font=("Arial", 16, "bold")
        )

        title.pack(pady=10)

        # =========================
        # FORM FRAME
        # =========================

        form_frame = tk.Frame(
            self.window
        )

        form_frame.pack(
            padx=20,
            pady=10,
            fill="both"
        )

        # NAME

        tk.Label(
            form_frame,
            text="Customer Name"
        ).pack(anchor="w")

        self.name_entry = tk.Entry(
            form_frame,
            width=40
        )

        self.name_entry.pack(
            pady=5
        )

        # PHONE

        tk.Label(
            form_frame,
            text="Phone Number"
        ).pack(anchor="w")

        self.phone_entry = tk.Entry(
            form_frame,
            width=40
        )

        self.phone_entry.pack(
            pady=5
        )

        # ADDRESS

        tk.Label(
            form_frame,
            text="Address"
        ).pack(anchor="w")

        self.address_text = tk.Text(
            form_frame,
            width=40,
            height=5
        )

        self.address_text.pack(
            pady=5
        )

        # =========================
        # BUTTONS
        # =========================

        btn_frame = tk.Frame(
            self.window
        )

        btn_frame.pack(
            pady=20
        )

        add_btn = tk.Button(
            btn_frame,
            text="Add Customer",
            width=15,
            command=self.save_customer
        )

        add_btn.pack(
            side="left",
            padx=10
        )

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            width=15,
            command=self.window.destroy
        )

        cancel_btn.pack(
            side="left",
            padx=10
        )

    # =========================
    # SAVE CUSTOMER
    # =========================

    def save_customer(self):

        name = (
            self.name_entry.get()
            .strip()
        )

        phone = (
            self.phone_entry.get()
            .strip()
        )

        address = (
            self.address_text.get(
                "1.0",
                tk.END
            ).strip()
        )

        if not name:

            messagebox.showerror(
                "Error",
                "Customer name required"
            )

            return

        conn = get_connection()

        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO customers(
                name,
                phone,
                address
            )
            VALUES (?, ?, ?)
            """, (
                name,
                phone,
                address
            ))

            conn.commit()

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e)
            )

            conn.close()

            return

        conn.close()

        messagebox.showinfo(
            "Success",
            "Customer added successfully"
        )

        self.refresh_callback()

        self.window.destroy()