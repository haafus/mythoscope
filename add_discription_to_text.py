import tkinter as tk
from tkinter import ttk, messagebox
import csv
import sys
from pathlib import Path


CSV_FILE = "corpus/corpus_catalog.csv"


class DescriptionEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор описания")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self.data = []
        self.ids = []
        self.id_to_row = {}

        self.load_csv()
        self.create_widgets()

    def load_csv(self):
        if not Path(CSV_FILE).exists():
            messagebox.showerror("Ошибка", f"Файл {CSV_FILE} не найден")
            sys.exit(1)

        with open(CSV_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self.data = list(reader)

        if not self.data:
            messagebox.showerror("Ошибка", "CSV файл пуст")
            sys.exit(1)

        self.ids = [row["id"] for row in self.data if "id" in row]
        self.id_to_row = {row["id"]: i for i, row in enumerate(self.data)}

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Наименование (ID):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.id_var = tk.StringVar()
        self.id_combo = ttk.Combobox(frame, textvariable=self.id_var, values=self.ids, width=40)
        self.id_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        self.id_combo.bind("<<ComboboxSelected>>", self.on_id_selected)
        self.id_combo.bind("<KeyRelease>", self.on_id_typed)

        ttk.Label(frame, text="Описание:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        self.desc_text = tk.Text(frame, width=50, height=8, wrap=tk.WORD, undo=True)
        self.desc_text.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))

        self.desc_text.bind("<Control-c>", self.on_copy)
        self.desc_text.bind("<Control-v>", self.on_paste)
        self.desc_text.bind("<Control-x>", self.on_cut)
        self.desc_text.bind("<Control-a>", self.on_select_all)
        self.desc_text.bind("<Command-c>", self.on_copy)
        self.desc_text.bind("<Command-v>", self.on_paste)
        self.desc_text.bind("<Command-x>", self.on_cut)
        self.desc_text.bind("<Command-a>", self.on_select_all)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))

        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Отмена", command=self.cancel).pack(side=tk.LEFT)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def on_copy(self, event):
        try:
            selected = self.desc_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except tk.TclError:
            pass
        return "break"

    def on_paste(self, event):
        try:
            text = self.root.clipboard_get()
            self.desc_text.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return "break"

    def on_cut(self, event):
        try:
            selected = self.desc_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
            self.desc_text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return "break"

    def on_select_all(self, event):
        self.desc_text.tag_add(tk.SEL, "1.0", tk.END)
        self.desc_text.mark_set(tk.INSERT, "1.0")
        self.desc_text.see(tk.INSERT)
        return "break"

    def on_id_selected(self, event=None):
        selected_id = self.id_var.get()
        if selected_id in self.id_to_row:
            row_idx = self.id_to_row[selected_id]
            current_desc = self.data[row_idx].get("description", "")
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", current_desc)

    def on_id_typed(self, event=None):
        typed = self.id_var.get().lower()
        filtered = [id_val for id_val in self.ids if typed in id_val.lower()]
        self.id_combo["values"] = filtered

    def save(self):
        selected_id = self.id_var.get()
        if not selected_id:
            messagebox.showwarning("Предупреждение", "Выберите ID")
            return

        if selected_id not in self.id_to_row:
            messagebox.showwarning("Предупреждение", "Неверный ID")
            return

        description = self.desc_text.get("1.0", tk.END).strip()
        row_idx = self.id_to_row[selected_id]
        self.data[row_idx]["description"] = description

        fieldnames = list(self.data[0].keys())
        if "description" not in fieldnames:
            fieldnames.append("description")

        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)

        messagebox.showinfo("Успех", "Описание сохранено")
        self.root.destroy()

    def cancel(self):
        self.root.destroy()
        sys.exit(0)


def main():
    root = tk.Tk()
    app = DescriptionEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()