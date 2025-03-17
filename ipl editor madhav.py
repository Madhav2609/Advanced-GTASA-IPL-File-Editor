import struct, re, sys, webbrowser
import tkinter as tk
import subprocess
from tkinter import filedialog, messagebox, simpledialog, scrolledtext, ttk
import os
####################################################### Insipired by grinch's ipl file editor ####################################
###############################################
# Format
header_format = "4s18i"
inst_format = "7f3i"
cars_format = "4f8i"
header_size = struct.calcsize(header_format)
inst_size = struct.calcsize(inst_format)
cars_size = struct.calcsize(cars_format)
###############################################

program_name = "IPL Editor"
filename: str = None
filetype: str = " "
# string variables to shorten loop and menu code
file_new: str = 'New'
file_open: str = 'Open'
file_save: str = 'Save'

doc_links = ['Auzo', 'Cars', 'Cull', 'Enex', 'Grge', 'Inst', 'Jump', 'Mult', 'Occl', 'Path', 'Pick', 'Tcyc', 'Zone']


class IPLEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced GTA SA IPL File Editor by Madhav2609")
        self.root.geometry("1000x600")

        # Variables
        self.ipl_files = []
        self.current_directory = None
        self.file_sections = {}
        self.original_contents = {}
        self.search_results = []
        self.current_search_index = -1

        # Styling
        self.root.configure(bg="#2E2E2E")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#3A3A3A", foreground="white", font=("Arial", 10))
        style.configure("TLabel", background="#2E2E2E", foreground="white", font=("Arial", 12))

        # Sidebar Panel (File Explorer)
        self.sidebar = tk.Frame(self.root, bg="#252525", width=250)
        self.sidebar.pack(side="left", fill="y", padx=5, pady=5)

        tk.Label(self.sidebar, text="IPL Files", bg="#252525", fg="white", font=("Arial", 12, "bold")).pack(pady=5)
        self.file_list = tk.Listbox(self.sidebar, bg="#1E1E1E", fg="white", font=("Arial", 11),
                                     selectbackground="#555555")
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_list.bind("<<ListboxSelect>>", self.navigate_to_file)

        # Search Bar
        self.search_frame = tk.Frame(self.root, bg="#2E2E2E")
        self.search_frame.pack(fill="x", padx=10, pady=5)

        self.search_entry = tk.Entry(self.search_frame, font=("Arial", 12), width=40)
        self.search_entry.pack(side="left", padx=5)

        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.search_text)
        self.search_button.pack(side="left", padx=5)

        self.next_button = ttk.Button(self.search_frame, text="Next", command=self.next_search_result)
        self.next_button.pack(side="left", padx=5)

        self.prev_button = ttk.Button(self.search_frame, text="Previous", command=self.previous_search_result)
        self.prev_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(self.search_frame, text="Clear", command=self.clear_search)
        self.clear_button.pack(side="left", padx=5)

        # Text Editor with syntax highlighting configuration
        self.text_editor = scrolledtext.ScrolledText(self.root, wrap="word", undo=True,
                                                      font=("Consolas", 12), bg="#1E1E1E", fg="white",
                                                      insertbackground="white")
        self.text_editor.pack(expand=True, fill="both", padx=10, pady=10)

        # Configure syntax highlighting tags
        self.text_editor.tag_configure("section", foreground="#00FF00")  # Section headers
        self.text_editor.tag_configure("id", foreground="#FFA500")  # ID numbers
        self.text_editor.tag_configure("modelname", foreground="#ADD8E6")  # Model names
        self.text_editor.tag_configure("coordinate", foreground="#FF69B4")  # Coordinates
        self.text_editor.tag_configure("comment", foreground="#808080")  # Comments
        self.text_editor.tag_configure("keyword", foreground="#FF00FF")  # Special keywords

        # Bind syntax highlighting to text changes
        self.text_editor.bind("<KeyRelease>", self.highlight_syntax)

        # Menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open IPL Files(Scans Whole Folders)", command=self.open_and_edit_files)
        file_menu.add_command(label="Open IPL Files (Multiple)", command=self.open_multiple_files)
        file_menu.add_command(label="Save Changes", command=self.save_edits)
        file_menu.add_command(label="Save Selected File", command=self.save_selected_file)
        file_menu.add_separator()
        file_menu.add_command(label="Convert Selected to Text", command=self.convert_selected_to_text)
        file_menu.add_command(label="Convert Selected to Binary", command=self.convert_selected_to_binary)
        file_menu.add_separator()
        file_menu.add_command(label="Convert All to Text", command=self.convert_all_to_text)
        file_menu.add_command(label="Convert All to Binary", command=self.convert_all_to_binary)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="IPL Lod Separator", command=self.launch_IPL_LOD_Separator_Tool)
        tools_menu.add_command(label="IPL ID Sorting", command=self.launch_IPL_ID_Sorting_Tool)

        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        # Status Bar
        self.status_bar = ttk.Label(self.root, text="No file loaded", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")
        
    def launch_IPL_ID_Sorting_Tool(self):
            tool_path = os.path.join(os.path.dirname(__file__), "IPL ID Sorting Script.py")
            if os.path.exists(tool_path):
               subprocess.Popen(["python", tool_path], shell=True)
            else:
               messagebox.showerror("Error", "Tool script not found!")
    
    def launch_IPL_LOD_Separator_Tool(self):
        tool_path = os.path.join(os.path.dirname(__file__), "ipl lod separator.py")
        if os.path.exists(tool_path):
           subprocess.Popen(["python", tool_path], shell=True)
        else:
           messagebox.showerror("Error", "Tool script not found!")
    def search_text(self):
        self.text_editor.tag_remove("search_highlight", "1.0", tk.END)
        search_query = self.search_entry.get().strip()
        if not search_query:
            return

        self.search_results = []
        self.current_search_index = -1
        start_pos = "1.0"

        while True:
            start_pos = self.text_editor.search(search_query, start_pos, stopindex=tk.END, nocase=True)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(search_query)}c"
            self.text_editor.tag_add("search_highlight", start_pos, end_pos)
            self.search_results.append(start_pos)
            start_pos = end_pos  # Move forward

        self.text_editor.tag_config("search_highlight", background="yellow", foreground="black")
        self.next_search_result()  # Move to first match

    def next_search_result(self):
        if self.search_results:
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
            self.text_editor.see(self.search_results[self.current_search_index])

    def previous_search_result(self):
        if self.search_results:
            self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
            self.text_editor.see(self.search_results[self.current_search_index])

    def clear_search(self):
        self.text_editor.tag_remove("search_highlight", "1.0", tk.END)
        self.search_results = []
        self.current_search_index = -1

    def open_and_edit_files(self):
        self.current_directory = filedialog.askdirectory(title="Select GTA SA Directory")
        if not self.current_directory:
            return

        self.ipl_files = []
        self.file_sections.clear()
        self.original_contents.clear()
        self.file_list.delete(0, tk.END)
        self.text_editor.delete("1.0", tk.END)

        for dirpath, _, filenames in os.walk(self.current_directory):
            for file in filenames:
                if file.lower().endswith(".ipl"):
                    file_path = os.path.join(dirpath, file)
                    self.ipl_files.append(file_path)
                    self.load_file_into_editor(file_path)

        self.status_bar.config(text=f"Loaded {len(self.ipl_files)} IPL files")
        self.highlight_syntax()

    def open_multiple_files(self):
        file_paths = filedialog.askopenfilenames(title="Select IPL Files", filetypes=[("IPL Files", "*.ipl")])
        if not file_paths:
            return

        self.ipl_files = []
        self.file_sections.clear()
        self.original_contents.clear()
        self.file_list.delete(0, tk.END)
        self.text_editor.delete("1.0", tk.END)

        for file_path in file_paths:
            self.ipl_files.append(file_path)
            self.load_file_into_editor(file_path)

        self.status_bar.config(text=f"Loaded {len(self.ipl_files)} IPL files")
        self.highlight_syntax()

    def load_file_into_editor(self, file_path):
        try:
            with open(file_path, "rb") as f:
                # Attempt to read as binary first
                try:
                    data = struct.unpack(header_format, f.read()[:header_size])
                    if str(data[0])[2:-1] == "bnry":
                        filetype = " (binary)"
                        f.seek(0)  # Reset file pointer
                        file_content = self.read_binary_file(f)
                    else:
                        filetype = " (text)"
                        f.seek(0)
                        file_content = f.read().decode('utf-8')
                except struct.error:
                    # If binary read fails, try reading as text
                    filetype = " (text)"
                    f.seek(0)
                    file_content = f.read().decode('utf-8')

                self.original_contents[file_path] = file_content

                start_index = self.text_editor.index(tk.END)
                self.text_editor.insert(tk.END, f"// --- {os.path.basename(file_path)} --- //\n",
                                        "file_header")
                self.text_editor.insert(tk.END, file_content + "\n\n")
                end_index = self.text_editor.index(tk.END)

                self.file_sections[file_path] = (start_index, end_index)
                self.file_list.insert(tk.END, os.path.basename(file_path))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def read_binary_file(self, file):
        global header_size, inst_size, cars_size, inst_format, cars_format
        try:
            data = struct.unpack(header_format, file.read()[:header_size])
        except:
            messagebox.showerror("Error", "The binary file format is not recognized")
            return ""

        inst_instances = data[1]
        car_instances = data[5]
        text = "# Binary file converted to text using " + program_name + "\ninst\n"

        size = header_size

        for x in range(inst_instances):
            file.seek(0, 0)
            try:
                data = struct.unpack(inst_format, file.read()[size:(size + inst_size)])
                size += inst_size
            except:
                messagebox.showerror("Error", "Error reading the IPL file (inst)")
                return ""
            text += "{}, dummy, {}, {:.4f}, {:.4f}, {:.4f}, {:.4f}, {:.4f}, {:.4f}, {:.4f}, {}\n".format(data[7],
                                                                                                          data[8],
                                                                                                          data[0],
                                                                                                          data[1],
                                                                                                          data[2],
                                                                                                          data[3],
                                                                                                          data[4],
                                                                                                          data[5],
                                                                                                          data[6],
                                                                                                          data[9])

        text += "end\ncars\n"

        for x in range(car_instances):
            file.seek(0, 0)
            try:
                data = struct.unpack(cars_format, file.read()[size:(size + cars_size)])
                size += cars_size
            except:
                messagebox.showerror("Error", "Error reading file (cars)")
                return ""
            text += "{:.4f}, {:.4f}, {:.4f}, {:.4f}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(data[0], data[1],
                                                                                                  data[2], data[3],
                                                                                                  data[4], data[5],
                                                                                                  data[6], data[7],
                                                                                                  data[8], data[9],
                                                                                                  data[10], data[11])
        text += "end"
        return text

    def navigate_to_file(self, event):
        try:
            self.text_editor.tag_remove("highlight", "1.0", tk.END)

            selected_file = self.file_list.get(self.file_list.curselection())
            for path, (start, end) in self.file_sections.items():
                if os.path.basename(path) == selected_file:
                    self.text_editor.see(start)
                    self.text_editor.tag_add("highlight", start, end)
                    self.text_editor.tag_config("highlight", background="#444444")
                    return
        except Exception:
            pass

    def save_edits(self):
        if not self.ipl_files:
            messagebox.showwarning("No Files Loaded", "Please open IPL files first.")
            return

        full_text = self.text_editor.get("1.0", tk.END)

        try:
            for ipl_file in self.ipl_files:
                file_basename = os.path.basename(ipl_file)
                start_marker = f"// --- {file_basename} --- //\n"

                start_index = full_text.find(start_marker)
                if (start_index == -1):
                    continue

                start_index += len(start_marker)
                next_section_index = full_text.find("// ---", start_index)

                new_content = full_text[start_index:next_section_index].strip() if next_section_index != -1 else full_text[start_index:].strip()

                # Determine if the file should be saved as binary or text
                if ipl_file in self.original_contents and "bnry" in self.original_contents[ipl_file]:
                    self.write_binary_file(ipl_file, new_content)
                else:
                    with open(ipl_file, "w", encoding="utf-8", errors="ignore") as file:
                        file.write(new_content)

            messagebox.showinfo("Success", "Changes saved successfully!")
            self.status_bar.config(text="Changes saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving changes: {e}")

    def save_selected_file(self):
        try:
            selected_file = self.file_list.get(self.file_list.curselection())
            for path, (start, end) in self.file_sections.items():
                if os.path.basename(path) == selected_file:
                    full_text = self.text_editor.get("1.0", tk.END)
                    start_marker = f"// --- {selected_file} --- //\n"

                    start_index = full_text.find(start_marker)
                    if (start_index == -1):
                        messagebox.showerror("Error", "Could not find selected file in editor.")
                        return

                    start_index += len(start_marker)
                    next_section_index = full_text.find("// ---", start_index)

                    new_content = full_text[start_index:next_section_index].strip() if next_section_index != -1 else full_text[start_index:].strip()

                    # Determine if the file should be saved as binary or text
                    if path in self.original_contents and "bnry" in self.original_contents[path]:
                        self.write_binary_file(path, new_content)
                    else:
                        with open(path, "w", encoding="utf-8", errors="ignore") as file:
                            file.write(new_content)

                    messagebox.showinfo("Success", f"{selected_file} saved successfully!")
                    self.status_bar.config(text=f"{selected_file} saved successfully")
                    return
            messagebox.showerror("Error", "Could not find selected file.")
        except Exception:
            messagebox.showerror("Error", "No file selected.")

    def convert_selected_to_text(self):
        self.convert_selected_file("text")

    def convert_selected_to_binary(self):
        self.convert_selected_file("binary")

    def convert_all_to_text(self):
        self.convert_all_files("text")

    def convert_all_to_binary(self):
        self.convert_all_files("binary")

    def convert_selected_file(self, file_type):
        try:
            selected_file = self.file_list.get(self.file_list.curselection())
            for path, (start, end) in self.file_sections.items():
                if os.path.basename(path) == selected_file:
                    full_text = self.text_editor.get("1.0", tk.END)
                    start_marker = f"// --- {selected_file} --- //\n"

                    start_index = full_text.find(start_marker)
                    if (start_index == -1):
                        messagebox.showerror("Error", "Could not find selected file in editor.")
                        return

                    start_index += len(start_marker)
                    next_section_index = full_text.find("// ---", start_index)

                    new_content = full_text[start_index:next_section_index].strip() if next_section_index != -1 else full_text[start_index:].strip()

                    if file_type == "binary":
                        self.write_binary_file(path, new_content)
                        self.original_contents[path] = "bnry"  # Mark as binary
                    else:
                        with open(path, "w", encoding="utf-8", errors="ignore") as file:
                            file.write(new_content)
                        self.original_contents[path] = ""  # Mark as text

                    messagebox.showinfo("Success", f"{selected_file} converted to {file_type} successfully!")
                    self.status_bar.config(text=f"{selected_file} converted to {file_type} successfully")
                    self.highlight_syntax()
                    return

            messagebox.showerror("Error", "Could not find selected file.")
        except Exception:
            messagebox.showerror("Error", "No file selected.")

    def convert_all_files(self, file_type):
        for path, (start, end) in self.file_sections.items():
            full_text = self.text_editor.get("1.0", tk.END)
            file_basename = os.path.basename(path)
            start_marker = f"// --- {file_basename} --- //\n"

            start_index = full_text.find(start_marker)
            if (start_index == -1):
                print(f"Could not find {file_basename} in editor.")
                continue

            start_index += len(start_marker)
            next_section_index = full_text.find("// ---", start_index)

            new_content = full_text[start_index:next_section_index].strip() if next_section_index != -1 else full_text[start_index:].strip()

            if file_type == "binary":
                self.write_binary_file(path, new_content)
                self.original_contents[path] = "bnry"  # Mark as binary
            else:
                with open(path, "w", encoding="utf-8", errors="ignore") as file:
                    file.write(new_content)
                self.original_contents[path] = ""  # Mark as text

        messagebox.showinfo("Success", f"All files converted to {file_type} successfully!")
        self.status_bar.config(text=f"All files converted to {file_type} successfully")
        self.highlight_syntax()

    def write_binary_file(self, save_name, text):
        try:
            # Separate the 'inst' and 'cars' sections
            inst_section = ""
            cars_section = ""
            current_section = None

            for line in text.splitlines():
                line = line.strip()
                if line == "inst":
                    current_section = "inst"
                    continue
                elif line == "cars":
                    current_section = "cars"
                    continue
                elif line == "end":
                    current_section = None
                    continue

                if current_section == "inst":
                    inst_section += line + "\n"
                elif current_section == "cars":
                    cars_section += line + "\n"

            # Process instance data
            inst_data = []
            inst_count = 0
            for line in inst_section.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                temp = re.findall(r'[-,+]?\b\d[\d,.]*\b', line)
                if len(temp) == 10:
                    inst_data.append(temp)
                    inst_count += 1

            # Process cars data
            cars_data = []
            for line in cars_section.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                temp = re.findall(r'[-,+]?\b\d[\d,.]*\b', line)
                if len(temp) == 12:
                    cars_data.append(temp)

            # Write binary file
            with open(save_name, 'wb') as f:
                write_data = b""
                cars_offset = inst_count * inst_size

                # Write instance data
                for data in inst_data:
                    write_data += struct.pack(inst_format, 
                        float(data[2]), float(data[3]), float(data[4]),
                        float(data[5]), float(data[6]), float(data[7]),
                        float(data[8]), int(data[0]), int(data[1]), int(data[9]))

                # Write cars data
                for data in cars_data:
                    write_data += struct.pack(cars_format,
                        float(data[0]), float(data[1]), float(data[2]), float(data[3]),
                        int(data[4]), int(data[5]), int(data[6]), int(data[7]),
                        int(data[8]), int(data[9]), int(data[10]), int(data[11]))

                # Write header and data
                header = struct.pack(header_format, b'bnry', inst_count, 0, 0, 0, 
                                   len(cars_data), 0, 76, 0, 0, 0, 0, 0, 0, 0, 
                                   cars_offset, 0, 0, 0)
                f.write(header + write_data)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while writing to file: {e}")

    def highlight_syntax(self, event=None):
        # Clear existing tags
        for tag in ["section", "id", "modelname", "coordinate", "comment", "keyword"]:
            self.text_editor.tag_remove(tag, "1.0", "end")

        # Get all text content
        content = self.text_editor.get("1.0", "end")

        # Process line by line
        for line_num, line in enumerate(content.split('\n'), 1):
            # Skip empty lines
            if not line.strip():
                continue

            # Highlight comments
            if '#' in line:
                comment_start = line.index('#')
                start_index = f"{line_num}.{comment_start}"
                self.text_editor.tag_add("comment", start_index, f"{line_num}.end")
                continue

            # Highlight section headers
            if line.strip().lower() in {"inst", "cars", "end"}:
                self.text_editor.tag_add("section", f"{line_num}.0", f"{line_num}.end")
                continue

            # Process data lines
            parts = line.strip().split(',')
            if len(parts) > 1:
                # Highlight ID (first number)
                if parts[0].strip().isdigit():
                    self.text_editor.tag_add("id", f"{line_num}.0", f"{line_num}.{len(parts[0])}")

                # Highlight model name (second part)
                if len(parts) > 1:
                    start_pos = len(parts[0]) + 1
                    end_pos = start_pos + len(parts[1])
                    self.text_editor.tag_add("modelname", f"{line_num}.{start_pos}", f"{line_num}.{end_pos}")

                # Highlight coordinates (floating point numbers)
                for i, part in enumerate(parts[2:], 2):
                    if re.match(r'-?\d*\.?\d+', part.strip()):
                        start_pos = sum(len(p) + 1 for p in parts[:i])
                        end_pos = start_pos + len(part)
                        self.text_editor.tag_add("coordinate", f"{line_num}.{start_pos}", f"{line_num}.{end_pos}")


if __name__ == "__main__":
    root = tk.Tk()
    app = IPLEditor(root)
    root.mainloop()
