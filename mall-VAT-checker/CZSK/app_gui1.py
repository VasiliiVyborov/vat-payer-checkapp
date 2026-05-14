import tkinter as tk
from tkinter import messagebox, scrolledtext, Toplevel
from tkinter.ttk import Progressbar
import pandas as pd
import os
from kontrola_dph_sk import kontrola_dph_sk

def zapis_vysledky_do_excelu(data, output_file="vat_check_results.xlsx"):
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    print(f"📁 Výsledky uloženy do {output_file}")

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VAT and Bank Account Check (SK)")
        self.root.geometry("1280x800")
        self.data = []  # Uložiště dat
        self.create_ui()
    
    def create_ui(self):
        # Vždy se vytvoří pouze SK rozhraní
        tk.Label(self.root, text="Current Mode: SK", font=("Arial", 12)).pack()
        self.create_sk_ui()

    def create_sk_ui(self):
        self.create_common_ui("VAT ID (IČ DPH)", "Bank Account")
    
    def create_common_ui(self, id_label, bank_label):
        input_frame = tk.LabelFrame(self.root, text="Enter Information", padx=10, pady=10)
        input_frame.place(x=20, y=20, width=760, height=120)

        tk.Label(input_frame, text=id_label).grid(row=0, column=0)
        self.id_entry = tk.Entry(input_frame, width=30)
        self.id_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(input_frame, text=bank_label).grid(row=1, column=0)
        self.bank_entry = tk.Entry(input_frame, width=30)
        self.bank_entry.grid(row=1, column=1, padx=10, pady=5)

        self.manual_add_button = tk.Button(input_frame, text="Add", command=self.add_manual_entry)
        self.manual_add_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)

        self.create_bulk_ui()

    def create_bulk_ui(self):
        bulk_frame = tk.LabelFrame(self.root, text="Upload Bulk Data", padx=10, pady=10)
        bulk_frame.place(x=20, y=150, width=760, height=180)
        
        self.upload_bulk_button = tk.Button(bulk_frame, text="Open Upload Bulk Data", command=self.open_bulk_entry)
        self.upload_bulk_button.pack()
        
        self.upload_status = tk.Label(bulk_frame, text="No Data Uploaded", fg="red")
        self.upload_status.pack()
        
        self.check_button = tk.Button(self.root, text="Begin Verification", command=self.start_check, state=tk.DISABLED)
        self.check_button.place(x=350, y=340)
        
        self.progress = Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
        self.progress.place(x=300, y=380)

        output_frame = tk.LabelFrame(self.root, text="Verification Results", padx=10, pady=10)
        output_frame.place(x=20, y=410, width=760, height=120)
        
        self.result_text = scrolledtext.ScrolledText(output_frame, width=90, height=5)
        self.result_text.pack(pady=5)

    def open_bulk_entry(self):
        bulk_window = Toplevel(self.root)
        bulk_window.title("Bulk Upload")
        bulk_window.geometry("500x300")

        tk.Label(bulk_window, text="VAT ID").grid(row=0, column=0)
        self.bulk_ico_text = tk.Text(bulk_window, width=25, height=10)
        self.bulk_ico_text.grid(row=1, column=0, padx=5, pady=5)

        tk.Label(bulk_window, text="Bank Account").grid(row=0, column=1)
        self.bulk_bank_text = tk.Text(bulk_window, width=25, height=10)
        self.bulk_bank_text.grid(row=1, column=1, padx=5, pady=5)

        save_button = tk.Button(bulk_window, text="Save", command=self.save_bulk_data)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)

    def save_bulk_data(self):
        ico_data = self.bulk_ico_text.get("1.0", tk.END).strip().split("\n")
        bank_data = self.bulk_bank_text.get("1.0", tk.END).strip().split("\n")

        if len(ico_data) != len(bank_data):
            messagebox.showerror("Error", "Number of VAT IDs and Bank Accounts do not match.")
            return

        for ico, bank in zip(ico_data, bank_data):
            self.data.append({
                "ID": ico.strip(),
                "Bank Account": bank.strip(),
                "Checked Bank Account": bank.strip()
            })

        self.upload_status.config(text="Data uploaded", fg="green")
        self.check_button.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "Bulk data saved!")

    def start_check(self):
        if not self.data:
            messagebox.showerror("Error", "No data to check.")
            return

        self.progress['value'] = 0
        self.root.update_idletasks()

        try:
            results = []
            for entry in self.data:
                vat_id = entry.get("ID", "").strip()
                bank_account = entry.get("Bank Account", "").strip()
                if vat_id and bank_account:
                    result = kontrola_dph_sk(vat_id, bank_account)
                    result["Checked Bank Account"] = bank_account
                    results.append(result)
            
            output_filepath = "vat_check_results.xlsx"
            zapis_vysledky_do_excelu(results, output_filepath)
            
            self.progress['value'] = 100
            messagebox.showinfo("Completed", f"Check completed! Results saved in {output_filepath}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def add_manual_entry(self):
        vat_id = self.id_entry.get().strip()
        bank = self.bank_entry.get().strip()
        if vat_id or bank:
            self.data.append({
                "ID": vat_id,
                "Bank Account": bank,
                "Checked Bank Account": bank
            })
            self.upload_status.config(text="Data uploaded", fg="green")
            self.check_button.config(state=tk.NORMAL)
            
            self.id_entry.delete(0, tk.END)
            self.bank_entry.delete(0, tk.END)

if __name__ == '__main__':
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()

