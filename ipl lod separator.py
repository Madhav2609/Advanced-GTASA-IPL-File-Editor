import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

def process_ipl():
    file_paths = filedialog.askopenfilenames(filetypes=[("IPL Files", "*.ipl")])
    if not file_paths:
        return
    
    for file_path in file_paths:
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
            
            inst_section = False
            lod_entries = []
            modified_lines = []

            for line in lines:
                stripped = line.strip()
                
                if stripped.lower() == "inst":
                    inst_section = True
                    modified_lines.append(line)
                    continue
                
                if inst_section and stripped == "end":
                    inst_section = False
                    modified_lines.append(line)
                    continue
                
                if inst_section:
                    parts = stripped.split(",")
                    if len(parts) > 1:
                        model_name = parts[1].strip()
                        if model_name.lower().startswith("lod"):
                            lod_entries.append(line)
                            continue
                    
                modified_lines.append(line)
            
            if lod_entries:
                save_lod_entries(file_path, lod_entries)
                with open(file_path, "w") as file:
                    file.writelines(modified_lines)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing {file_path}: {e}")
    
    status_label.config(text=f"Processing complete! Processed {len(file_paths)} files.")

def save_lod_entries(file_path, lod_entries):
    directory = os.path.join(os.path.dirname(file_path), "Separated IPLs")
    os.makedirs(directory, exist_ok=True)
    
    new_ipl_path = os.path.join(directory, os.path.basename(file_path))
    with open(new_ipl_path, "w") as new_file:
        new_file.write("inst\n")
        new_file.writelines(lod_entries)
        new_file.write("end\n")

def create_gui():
    global status_label
    
    root = tk.Tk()
    root.title("IPL LOD Separator")
    root.geometry("600x450")
    root.configure(bg="#1e1e1e")
    
    frame = tk.Frame(root, padx=20, pady=20, bg="#1e1e1e")
    frame.pack(expand=True)
    
    description_label = tk.Label(frame, text="This tool processes IPL files by extracting LOD models and saving them separately.\n" \
                                      "The original file is updated to remove LOD models, which is very handy for creating Binary IPLs. Select one or more IPL files to begin.",
                                      font=("Arial", 10, "bold"), wraplength=500, justify="left", fg="white", bg="#1e1e1e")
    description_label.pack(pady=10)
    
    select_btn = tk.Button(frame, text="Select IPL Files", command=process_ipl, font=("Arial", 12, "bold"), padx=10, pady=5, bg="#2d89ef", fg="white", relief="flat", cursor="hand2")
    select_btn.pack(pady=10)
    
    status_label = tk.Label(frame, text="Select IPL files to begin.", font=("Arial", 10), wraplength=500, fg="white", bg="#1e1e1e")
    status_label.pack(pady=10)
    
    
    root.mainloop()

if __name__ == "__main__":
    create_gui()