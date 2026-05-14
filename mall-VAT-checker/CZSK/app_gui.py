import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, Toplevel
from tkinter.ttk import Progressbar
import pandas as pd
import os
import datetime
from kontrola_api import kontrola_dph

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kontrola DPH a Bankovních Účtů")
        self.root.geometry("800x550")
        
        # Sekce pro ruční zadání údajů
        input_frame = tk.LabelFrame(root, text="Vložení údajů", padx=10, pady=10)
        input_frame.place(x=20, y=20, width=760, height=120)

        tk.Label(input_frame, text="IČO").grid(row=0, column=0)
        self.ico_entry = tk.Entry(input_frame, width=30)
        self.ico_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(input_frame, text="Bankovní účet").grid(row=1, column=0)
        self.bank_entry = tk.Entry(input_frame, width=30)
        self.bank_entry.grid(row=1, column=1, padx=10, pady=5)

        self.manual_add_button = tk.Button(input_frame, text="Přidat", command=self.add_manual_entry)
        self.manual_add_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)

        # Hromadné vložení
        bulk_frame = tk.LabelFrame(root, text="Hromadné vložení", padx=10, pady=10)
        bulk_frame.place(x=20, y=150, width=760, height=180)
        
        self.upload_bulk_button = tk.Button(bulk_frame, text="Otevřít hromadné vložení", command=self.open_bulk_entry)
        self.upload_bulk_button.pack()
        
        self.upload_status = tk.Label(bulk_frame, text="Data nenahrána", fg="red")
        self.upload_status.pack()
        
        # Tlačítko pro spuštění kontroly
        self.check_button = tk.Button(root, text="Spustit kontrolu", command=self.start_check, state=tk.DISABLED)
        self.check_button.place(x=350, y=340)
        
        # Progress bar
        self.progress = Progressbar(root, orient="horizontal", length=200, mode="determinate")
        self.progress.place(x=300, y=380)

        # Výstup výsledků
        output_frame = tk.LabelFrame(root, text="Výsledky kontroly", padx=10, pady=10)
        output_frame.place(x=20, y=410, width=760, height=120)
        
        self.result_text = scrolledtext.ScrolledText(output_frame, width=90, height=5)
        self.result_text.pack(pady=5)

        self.data = []
    
    def add_manual_entry(self):
        ico = self.ico_entry.get().strip()
        bank = self.bank_entry.get().strip()
        if ico or bank:
            self.data.append({"IČO": ico, "Bankovní účet": bank})
            self.upload_status.config(text="Data nahrána", fg="green")
            self.check_button.config(state=tk.NORMAL)
            self.ico_entry.delete(0, tk.END)
            self.bank_entry.delete(0, tk.END)
    
    def open_bulk_entry(self):
        bulk_window = Toplevel(self.root)
        bulk_window.title("Hromadné vložení")
        bulk_window.geometry("500x300")

        tk.Label(bulk_window, text="IČO").grid(row=0, column=0)
        tk.Label(bulk_window, text="Bankovní účet").grid(row=0, column=1)

        self.bulk_ico_text = scrolledtext.ScrolledText(bulk_window, width=20, height=10)
        self.bulk_ico_text.grid(row=1, column=0, padx=10, pady=5)

        self.bulk_bank_text = scrolledtext.ScrolledText(bulk_window, width=20, height=10)
        self.bulk_bank_text.grid(row=1, column=1, padx=10, pady=5)

        save_button = tk.Button(bulk_window, text="Uložit", command=self.save_bulk_data)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)
    
    def save_bulk_data(self):
        ico_data = self.bulk_ico_text.get("1.0", tk.END).strip().split("\n")
        bank_data = self.bulk_bank_text.get("1.0", tk.END).strip().split("\n")
        
        if len(ico_data) != len(bank_data):
            messagebox.showerror("Chyba", "Počet IČO a bankovních účtů se neshoduje!")
            return
        
        for ico, bank in zip(ico_data, bank_data):
            self.data.append({"IČO": ico.strip(), "Bankovní účet": bank.strip()})
        
        self.upload_status.config(text="Data nahrána", fg="green")
        self.check_button.config(state=tk.NORMAL)
        messagebox.showinfo("Info", "Hromadná data byla uložena.")
    
    def start_check(self):
        if not self.data:
            messagebox.showerror("Chyba", "Žádná data k ověření.")
            return
        
        self.progress['value'] = 0
        self.root.update_idletasks()
        
        try:
            df = pd.DataFrame(self.data)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filepath = f"kontrola_vystup_{timestamp}.xlsx"
            df.to_excel(output_filepath, index=False, engine='openpyxl')
            kontrola_dph(output_filepath, output_filepath)
            
            self.progress['value'] = 100
            messagebox.showinfo("Hotovo", f"Kontrola dokončena! Výsledky uloženy do souboru {output_filepath}.")
            self.display_results(output_filepath)
        except Exception as e:
            messagebox.showerror("Chyba", f"Nastala chyba: {str(e)}")
    
    def display_results(self, filepath):
        try:
            df = pd.read_excel(filepath, engine='openpyxl')
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, df.to_string(index=False))
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se načíst výsledky: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()




