import tkinter as tk
import subprocess
import sys

def continue_action():
    subprocess.Popen([sys.executable, "checkaddslow.py"])
    root.destroy()

root = tk.Tk()
root.title("README PLEASE")
root.geometry("500x300")

message = """README PLEASE:)
Instructions to use:
1. Verify you have specific ico_list.xslx file
2. If not, write administrator to obtain
3. Paste company IDs to Column A in ico_list.xslx
4. Do not change any settings in ico_list.xslx
5. Upload your current ico_list.xslx (should be placed in the app folder)
6. Wait, the average speed is 20-30 minutes per 1000 records
"""

lbl_message = tk.Label(root, text=message, justify="left")
lbl_message.pack(padx=10, pady=10)

btn_continue = tk.Button(root, text="Continue", command=continue_action)
btn_continue.pack(pady=10)

root.mainloop()

