# took inspiration from grinch's script

import glob, os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class IPLIDSorterGUI:
    def __init__(self, master):
        self.master = master
        master.title("IPL ID Sorting Script")
        master.configure(bg="#2E2E2E")

        # Styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#3A3A3A", foreground="white", font=("Arial", 10))
        style.configure("TLabel", background="#2E2E2E", foreground="white", font=("Arial", 12))
        style.configure("Treeview.Heading", background="#3A3A3A", foreground="white", font=("Arial", 10))
        style.configure("Treeview", background="#1E1E1E", foreground="white", fieldbackground="#1E1E1E", font=("Arial", 10))

        self.ide_files_path = ""
        self.ipl_files_path = ""
        self.ide_files_list = []
        self.ipl_files_list = []

        # --- GUI Elements ---
        self.label_ide = ttk.Label(master, text="IDE Files Path:")
        self.label_ide.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.entry_ide = tk.Entry(master, width=50, bg="#1E1E1E", fg="white")
        self.entry_ide.grid(row=0, column=1, padx=5, pady=5)

        self.button_browse_ide = ttk.Button(master, text="Browse", command=self.browse_ide_files)
        self.button_browse_ide.grid(row=0, column=2, padx=5, pady=5)

        self.label_ipl = ttk.Label(master, text="IPL Files Path:")
        self.label_ipl.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        self.entry_ipl = tk.Entry(master, width=50, bg="#1E1E1E", fg="white")
        self.entry_ipl.grid(row=1, column=1, padx=5, pady=5)

        self.button_browse_ipl = ttk.Button(master, text="Browse", command=self.browse_ipl_files)
        self.button_browse_ipl.grid(row=1, column=2, padx=5, pady=5)

        self.process_button = ttk.Button(master, text="Process", command=self.process_files)
        self.process_button.grid(row=2, column=1, pady=10)

        # Treeview for displaying IDE and IPL files
        self.tree = ttk.Treeview(master, columns=('IDE File', 'IPL File'), show='headings')
        self.tree.heading('IDE File', text='IDE File')
        self.tree.heading('IPL File', text='IPL File')
        self.tree.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')

        # --- Configure grid weights to make the Treeview expandable ---
        master.grid_rowconfigure(3, weight=1)
        master.grid_columnconfigure(1, weight=1)

    def browse_ide_files(self):
        self.ide_files_path = filedialog.askdirectory()
        self.entry_ide.delete(0, tk.END)
        self.entry_ide.insert(0, self.ide_files_path)
        self.ide_files_list = self.get_files_with_extension(self.ide_files_path, "ide")
        self.update_treeview()

    def browse_ipl_files(self):
        self.ipl_files_path = filedialog.askdirectory()
        self.entry_ipl.delete(0, tk.END)
        self.entry_ipl.insert(0, self.ipl_files_path)
        self.ipl_files_list = self.get_files_with_extension(self.ipl_files_path, "ipl")
        self.update_treeview()

    def update_treeview(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new items
        max_len = max(len(self.ide_files_list), len(self.ipl_files_list))
        for i in range(max_len):
            ide_file = self.ide_files_list[i] if i < len(self.ide_files_list) else ""
            ipl_file = self.ipl_files_list[i] if i < len(self.ipl_files_list) else ""
            self.tree.insert("", 'end', values=(os.path.basename(ide_file), os.path.basename(ipl_file)))

    def get_files_with_extension(self, path, extention):
        search_path = os.path.join(path, "*." + extention)
        return glob.glob(search_path)

    def process_files(self):
        if not self.ide_files_list or not self.ipl_files_list:
            messagebox.showerror("Error", "Please select folders containing IDE and IPL files.")
            return

        try:
            self.process_ide_files(self.ide_files_list)
            self.process_ipl_files(self.ipl_files_list)
            messagebox.showinfo("Success", "Sorting finished successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def process_ide_files(self, func_ide_list):
        self.ide_models = set()
        for x in func_ide_list:
            with open(x,'r') as ide:
                valid_line : bool = False
                for line in ide:
                    if (line[:4] == "objs" or line[:4] == "tobj"):
                        valid_line = True
                    
                    if valid_line and not (line[0] == '#' or line[0] == '\n' or (line[0] >= 'A' and line[0] <= 'z')):
                        data_line = line.split(',')
                        if len(data_line) > 1:
                            self.ide_models.add(data_line[1].strip())

                    if (line[:3] == "end"):
                        valid_line = False

    def get_id_name(self, func_line):
        if (func_line[0] != '\n'):
            data_line = func_line.split(',')
            return data_line

    def is_inst_line(self, ipl_line):
        if(ipl_line[:3] == "end"):
            return "inst end" 
        elif not (ipl_line[0] == '#' or ipl_line[0] == '\n' or (ipl_line[0] >= 'A' and ipl_line[0] <= 'z')):
            return True
        return False

    def remove_file(self, file):
        if os.path.exists(file):
            os.remove(file)

    def process_ipl_files(self, func_ipl_list):      
        index = 0
        for y in func_ipl_list:
            should_break = False  
            with open(str(y),'r') as ipl:
                lines = ipl.readlines()

            with open(str(y),'w') as ipl:
                for a in lines:
                    if(self.is_inst_line(a) == "inst end"):
                        ipl.write("end\n")
                    elif(self.is_inst_line(a)):
                        ipl_line = self.get_id_name(a)
                        model_name = ipl_line[1].strip()
                        if model_name in self.ide_models:
                            # Find corresponding ID in IDE and update IPL
                            for x in self.ide_files_list:
                                with open(x, 'r') as ide:
                                    ide.seek(0)
                                    valid_line = False
                                    for b in ide:
                                        if (b[:4] == "objs" or b[:4] == "tobj"):
                                            valid_line = True
                                        
                                        if valid_line and not (b[0] == '#' or b[0] == '\n' or (b[0] >= 'A' and b[0] <= 'z')):
                                            ide_line = self.get_id_name(b)
                                            ide_model_name = ide_line[1].strip()
                                            if ide_model_name == model_name:
                                                ipl_line[0] = ide_line[0]
                                                full_ipl_line = ",".join(ipl_line)
                                                ipl.write(full_ipl_line)
                                                should_break = True
                                                break
                                        if (b[:3] == "end"):
                                            valid_line = False
                                    if should_break:
                                        should_break = False
                                        break
                        else:
                            ipl.write(a) # Keep the line as is if model not in IDE
                    else:
                        ipl.write(a)
            index += 1

# ----- Main -----
if __name__ == "__main__":
    root = tk.Tk()
    gui = IPLIDSorterGUI(root)
    root.mainloop()
