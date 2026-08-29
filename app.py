import sys
import tkinter as tk
from tkinter import ttk

from database import (
    create_tables,
    reset_application_data,
    run_migrations
)

from ui.main_window import MainWindow


# =========================
# CREATE DATABASE TABLES
# =========================

if "--reset" in sys.argv:
    reset_application_data()
    print("Application data cleared successfully.")
    sys.exit(0)

create_tables()

run_migrations()


# =========================
# START APPLICATION
# =========================

root = tk.Tk()

# Make buttons easier to read and tap across the app.
root.option_add("*Button.Font", "Arial 13 bold")
root.option_add("*Button.padX", 10)
root.option_add("*Button.padY", 6)

style = ttk.Style()
style.configure("TButton", font=("Arial", 13, "bold"), padding=(12, 8))

app = MainWindow(root)

root.mainloop()
