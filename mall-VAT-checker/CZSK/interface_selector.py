import tkinter as tk
import subprocess
import sys

def launch_vat_cz():
    subprocess.Popen([sys.executable, "app_gui.py"])
    
def launch_vat_sk():
    subprocess.Popen([sys.executable, "app_gui1.py"])
    
def launch_name_address():
    # Spustí okno s upozorněním (naczmessage.py)
    subprocess.Popen([sys.executable, "naczmessage.py"])

root = tk.Tk()
root.title("Select Interface and Tools")
root.geometry("400x300")

# Sekce pro VAT-Bank Account Check
vat_frame = tk.LabelFrame(root, text="VAT-Bank Account Check", padx=10, pady=10)
vat_frame.pack(padx=10, pady=10, fill="x")

btn_vat_cz = tk.Button(vat_frame, text="Czech (CZ)", width=15, command=launch_vat_cz)
btn_vat_cz.pack(side="left", padx=10, pady=5)

btn_vat_sk = tk.Button(vat_frame, text="Slovak (SK)", width=15, command=launch_vat_sk)
btn_vat_sk.pack(side="left", padx=10, pady=5)

# Sekce pro Name-Address Check
na_frame = tk.LabelFrame(root, text="Name-Address Check", padx=10, pady=10)
na_frame.pack(padx=10, pady=10, fill="x")

btn_na_cz = tk.Button(na_frame, text="NA CZ", width=15, command=launch_name_address)
btn_na_cz.pack(padx=10, pady=5)

root.mainloop()

