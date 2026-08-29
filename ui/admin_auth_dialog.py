import tkinter as tk
from tkinter import messagebox
from database import verify_admin_pin, set_admin_pin


def request_admin_pin(parent, action_name="perform this action"):
    """
    Displays a modal dialog asking for the Owner/Admin PIN.
    Returns True if the entered PIN is correct, False otherwise.
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Admin Authorization Required")
    dialog.geometry("450x250")
    dialog.resizable(False, False)
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()

    # Center on screen
    dialog.update_idletasks()
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    w, h = 450, 250
    x = (sw - w) // 2
    y = (sh - h) // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    result = [False]

    # Title / Header
    header_frame = tk.Frame(dialog, bg="#f8f9fa", pady=10)
    header_frame.pack(fill="x")
    
    tk.Label(
        header_frame,
        text="🔒 Admin Authorization Required",
        font=("Arial", 13, "bold"),
        bg="#f8f9fa",
        fg="#d9534f"
    ).pack()

    content_frame = tk.Frame(dialog, padx=20, pady=15)
    content_frame.pack(fill="both", expand=True)

    tk.Label(
        content_frame,
        text=f"Enter Owner PIN to {action_name}:",
        font=("Arial", 11),
        wraplength=400,
        justify="center"
    ).pack(pady=(0, 10))

    pin_entry = tk.Entry(
        content_frame,
        font=("Arial", 14, "bold"),
        show="•",
        justify="center",
        width=15
    )
    pin_entry.pack(pady=5, ipady=4)
    pin_entry.focus_set()

    btn_frame = tk.Frame(content_frame)
    btn_frame.pack(pady=12)

    def on_submit(event=None):
        entered = pin_entry.get().strip()
        if not entered:
            messagebox.showwarning("PIN Required", "Please enter the Admin PIN.", parent=dialog)
            pin_entry.focus_set()
            return

        if verify_admin_pin(entered):
            result[0] = True
            dialog.destroy()
        else:
            messagebox.showerror("Access Denied", "Incorrect Admin PIN.", parent=dialog)
            pin_entry.delete(0, tk.END)
            pin_entry.focus_set()

    def on_cancel():
        result[0] = False
        dialog.destroy()

    tk.Button(
        btn_frame,
        text="Authorize",
        command=on_submit,
        bg="#5634f0",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12,
        padx=4,
        pady=3
    ).pack(side="left", padx=8)

    tk.Button(
        btn_frame,
        text="Cancel",
        command=on_cancel,
        bg="#6c757d",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12,
        padx=4,
        pady=3
    ).pack(side="left", padx=8)

    pin_entry.bind("<Return>", on_submit)
    dialog.bind("<Escape>", lambda e: on_cancel())

    # Footer Branding
    footer = tk.Label(
        dialog,
        text="⚡ Powered by Wokdens",
        font=("Arial", 8, "italic"),
        fg="#888888"
    )
    footer.pack(side="bottom", pady=4)

    dialog.wait_window()
    return result[0]


def change_admin_pin_dialog(parent):
    """
    Dialog for changing the Owner/Admin PIN.
    Requires verifying the current PIN first.
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Change Admin PIN")
    dialog.geometry("450x330")
    dialog.resizable(False, False)
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()

    # Center on screen
    dialog.update_idletasks()
    sw = dialog.winfo_screenwidth()
    sh = dialog.winfo_screenheight()
    w, h = 450, 330
    x = (sw - w) // 2
    y = (sh - h) // 2
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(
        dialog,
        text="Change Admin/Owner PIN",
        font=("Arial", 13, "bold"),
        pady=10
    ).pack()

    form = tk.Frame(dialog, padx=25, pady=10)
    form.pack(fill="both", expand=True)

    tk.Label(form, text="Current PIN:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
    cur_pin_entry = tk.Entry(form, font=("Arial", 11), show="•", width=20)
    cur_pin_entry.grid(row=0, column=1, pady=6, padx=10)
    cur_pin_entry.focus_set()

    tk.Label(form, text="New PIN:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
    new_pin_entry = tk.Entry(form, font=("Arial", 11), show="•", width=20)
    new_pin_entry.grid(row=1, column=1, pady=6, padx=10)

    tk.Label(form, text="Confirm New PIN:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
    confirm_pin_entry = tk.Entry(form, font=("Arial", 11), show="•", width=20)
    confirm_pin_entry.grid(row=2, column=1, pady=6, padx=10)

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=15)

    def on_save():
        cur_pin = cur_pin_entry.get().strip()
        new_pin = new_pin_entry.get().strip()
        conf_pin = confirm_pin_entry.get().strip()

        if not verify_admin_pin(cur_pin):
            messagebox.showerror("Error", "Current PIN is incorrect.", parent=dialog)
            cur_pin_entry.focus_set()
            return

        if len(new_pin) < 4:
            messagebox.showwarning("Weak PIN", "New PIN must be at least 4 digits.", parent=dialog)
            new_pin_entry.focus_set()
            return

        if new_pin != conf_pin:
            messagebox.showerror("Mismatch", "New PIN and Confirm PIN do not match.", parent=dialog)
            confirm_pin_entry.focus_set()
            return

        set_admin_pin(new_pin)
        messagebox.showinfo("Success", "Admin PIN updated successfully!", parent=dialog)
        dialog.destroy()

    tk.Button(
        btn_frame,
        text="Save PIN",
        command=on_save,
        bg="#28a745",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12
    ).pack(side="left", padx=10)

    tk.Button(
        btn_frame,
        text="Cancel",
        command=dialog.destroy,
        bg="#6c757d",
        fg="white",
        font=("Arial", 10, "bold"),
        width=12
    ).pack(side="left", padx=10)

    # Footer Branding
    footer = tk.Label(
        dialog,
        text="⚡ Powered by Wokdens",
        font=("Arial", 8, "italic"),
        fg="#888888"
    )
    footer.pack(side="bottom", pady=4)
