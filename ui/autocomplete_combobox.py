import tkinter as tk


class AutocompleteCombobox(tk.Frame):

    def __init__(self, parent, width=30):

        super().__init__(parent)

        self.completion_list = []

        # Entry
        self.entry = tk.Entry(
            self,
            width=width
        )

        self.entry.pack(fill="x", ipady=8)

        # Listbox
        self.listbox = tk.Listbox(
            self,
            height=5
        )

        self.listbox.pack_forget()

        # Events
        self.entry.bind(
            "<KeyRelease>",
            self.check_input
        )

        self.listbox.bind(
            "<<ListboxSelect>>",
            self.select_item
        )

    # =========================
    # SET DATA
    # =========================

    def set_completion_list(self, completion_list):

        self.completion_list = sorted(
            completion_list,
            key=str.lower
        )

    # =========================
    # FILTER
    # =========================

    def check_input(self, event):

        typed = self.entry.get().lower()

        # Clear listbox
        self.listbox.delete(
            0,
            tk.END
        )

        if typed == "":

            self.listbox.pack_forget()

            return

        matches = []

        for item in self.completion_list:

            if typed in item.lower():

                matches.append(item)

        if matches:

            self.listbox.pack(
                fill="x"
            )

            for item in matches:

                self.listbox.insert(
                    tk.END,
                    item
                )

        else:

            self.listbox.pack_forget()

    # =========================
    # SELECT
    # =========================

    def select_item(self, event):

        selected = self.listbox.curselection()

        if not selected:
            return

        value = self.listbox.get(
            selected[0]
        )

        self.entry.delete(
            0,
            tk.END
        )

        self.entry.insert(
            0,
            value
        )

        self.listbox.pack_forget()

    # =========================
    # GET VALUE
    # =========================

    def get(self):

        return self.entry.get()

    # =========================
    # SET VALUE
    # =========================

    def set(self, value):

        self.entry.delete(
            0,
            tk.END
        )

        self.entry.insert(
            0,
            value
        )
