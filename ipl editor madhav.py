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
    section_formats = {
        "INST": {
            "coords": [(3, 4, 5)],  # PosX, PosY, PosZ indices
            "min_parts": 11,
            "format": "ID, ModelName, Interior, PosX, PosY, PosZ, RotX, RotY, RotZ, RotW, LOD"
        },
        "CULL": {
            "coords": [(0, 1, 2)],  # CenterX/Y/Z 
            "min_parts": 11,
            "format": "CenterX, CenterY, CenterZ, Unknown1, WidthY, BottomZ, WidthX, Unknown2, TopZ, Flag, Unknown3"
        },
        "PATH": {
            "coords": [(0, 1, 2)],
            "min_parts": 3,
            "format": "X, Y, Z"
        },
        "GRGE": {
            "coords": [(0, 1, 2), (3, 4), (5, 6, 7)],  # Pos, Line, Cube
            "min_parts": 11,
            "format": "PosX, PosY, PosZ, LineX, LineY, CubeX, CubeY, CubeZ, DoorType, GarageType, Name"
        },
        "ENEX": {
            "coords": [(0, 1, 2), (7, 8, 9)],  # Entry and exit points
            "min_parts": 18,
            "format": "X1, Y1, Z1, ROT, W1, W2, C8, X2, Y2, Z2, Rot2, Int, Flag, Name, Sky, I2, TimeOn, TimeOff"
        },
        "PICK": {
            "coords": [(1, 2, 3)],
            "min_parts": 4,
            "format": "ID, PosX, PosY, PosZ"
        },
        "JUMP": {
            "coords": [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10, 11), (12, 13, 14)],
            "min_parts": 16,
            "format": "StartLowerX/Y/Z, StartUpperX/Y/Z, TargetLowerX/Y/Z, TargetUpperX/Y/Z, CameraX/Y/Z, Reward"
        },
        "TCYC": {
            "coords": [(0, 1, 2), (3, 4, 5)],
            "min_parts": 11,
            "format": "X1, Y1, Z1, X2, Y2, Z2, ?, ?, ?, ?, ?"
        },
        "AUZO": {
            "coords": [(3, 4, 5), (6, 7, 8)],  # Format 1
            "alt_coords": [(3, 4, 5)],  # Format 2 (with radius)
            "min_parts": 6,
            "format": "Name, ID, Switch, X1, Y1, Z1, [X2, Y2, Z2 or Radius]"
        },
        "CARS": {
            "coords": [(0, 1, 2)],
            "min_parts": 12,
            "format": "PosX, PosY, PosZ, Angle, CarID, PrimCol, SecCol, ForceSpawn, Alarm, DoorLock, Unknown1, Unknown2"
        },
        "OCCL": {
            "coords": [(0, 1, 2)],  # mid point and dimensions
            "min_parts": 7,
            "format": "midX, midY, bottomZ, widthX, widthY, height, rotation"
        }
    }
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced GTA SA IPL File Editor by Madhav2609")
        self.root.geometry("1200x800")

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
        style.configure("TLabel", background="#1E1E1E", foreground="white", font=("Arial", 12))

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
        tools_menu.add_command(label="Map Mover", command=self.show_map_mover_dialog)  # Add this line
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        # Status Bar
        self.status_bar = ttk.Label(self.root, text="No file loaded", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")
        
        # Add Fastman92 processor path configuration
        self.fastman92_path = self.find_fastman92_processor()
        if not self.fastman92_path:
            messagebox.showwarning("Warning", "Fastman92 Processor not found in the current directory. Some features may be limited.")

        self.text_editor.vbar.bind("<B1-Motion>", self._on_scroll)
        self.text_editor.bind("<MouseWheel>", self._on_scroll)
        self._highlight_after = None

    def find_fastman92_processor(self):
        """Find fastman92_processor.exe in the current directory"""
        search_paths = [
            os.path.dirname(os.path.abspath(__file__)),  # Current directory
            os.getcwd(),  # Working directory
            os.path.dirname(sys.executable),  # Executable directory
            '.'  # Relative path
        ]
        
        for path in search_paths:
            processor_path = os.path.join(path, "fastman92_processor.exe")
            if os.path.exists(processor_path):
                return processor_path
                
        return None

    def run_fastman92_conversion(self, input_file, output_file, input_type, output_type):
        """Run Fastman92 Processor for file conversion"""
        if not self.fastman92_path:
            messagebox.showerror("Error", 
                "Fastman92 Processor not found!\nPlease place fastman92_processor.exe in the same folder as the application.")
            return False

        command = [
            self.fastman92_path,
            "/file_type", "ipl",
            "/input_type", input_type,
            "/input_game", "GAME_EXACT_GTASA_PC",
            "/input_filename", input_file,
            "/output_type", output_type,
            "/output_game", "GAME_EXACT_GTASA_PC", 
            "/output_filename", output_file
        ]

        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Conversion Error", f"Error converting file:\n{e.stderr}")
            return False

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

    def clear_search(self):
        self.text_editor.tag_remove("search_highlight", "1.0", tk.END)
        self.search_results = []
        self.current_search_index = -1

    def show_progress_window(self, title="Loading Files"):
        """Create and return a progress window"""
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.geometry("300x150")
        progress_window.configure(bg="#1E1E1E")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Center the progress window
        window_width = 300
        window_height = 150
        screen_width = progress_window.winfo_screenwidth()
        screen_height = progress_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Progress label
        label = ttk.Label(progress_window, text="Loading files...", style="Dark.TLabel")
        label.pack(pady=20)
        
        # Progress bar
        style = ttk.Style()
        style.configure("Dark.Horizontal.TProgressbar", 
                       background="#4CAF50",
                       troughcolor="#2E2E2E",
                       bordercolor="#1E1E1E")
        
        progress_bar = ttk.Progressbar(progress_window, 
                                     style="Dark.Horizontal.TProgressbar",
                                     length=200, 
                                     mode='determinate')
        progress_bar.pack(pady=10)
        
        return progress_window, progress_bar, label

    def update_progress(self, progress_bar, label, current, total, filename=""):
        """Update progress bar and label"""
        progress = (current / total) * 100
        progress_bar['value'] = progress
        label.config(text=f"Loading files... ({current}/{total})\n{filename}")
        self.root.update()

    def open_and_edit_files(self):
        self.current_directory = filedialog.askdirectory(title="Select GTA SA Directory")
        if not self.current_directory:
            return

        # Find all IPL files first
        ipl_files = []
        for dirpath, _, filenames in os.walk(self.current_directory):
            for file in filenames:
                if file.lower().endswith(".ipl"):
                    ipl_files.append(os.path.join(dirpath, file))

        if not ipl_files:
            messagebox.showinfo("No Files", "No IPL files found in selected directory.")
            return

        # Create progress window
        progress_window, progress_bar, label = self.show_progress_window()

        # Clear existing data
        self.ipl_files = []
        self.file_sections.clear()
        self.original_contents.clear()
        self.file_list.delete(0, tk.END)
        self.text_editor.delete("1.0", tk.END)

        # Load files with progress bar
        total_files = len(ipl_files)
        self.text_editor.config(state='normal')  # Enable editing temporarily
        for i, file_path in enumerate(ipl_files, 1):
            self.update_progress(progress_bar, label, i, total_files, os.path.basename(file_path))
            self.ipl_files.append(file_path)
            self.load_file_into_editor(file_path)

        # Apply syntax highlighting once after all files are loaded
        self.highlight_syntax()
        
        # Destroy progress window
        progress_window.destroy()
        
        self.status_bar.config(text=f"Loaded {len(self.ipl_files)} IPL files")
        self.text_editor.after(100, self.highlight_syntax)

    def open_multiple_files(self):
        file_paths = filedialog.askopenfilenames(title="Select IPL Files", filetypes=[("IPL Files", "*.ipl")])
        if not file_paths:
            return

        # Create progress window
        progress_window, progress_bar, label = self.show_progress_window()

        # Clear existing data
        self.ipl_files = []
        self.file_sections.clear()
        self.original_contents.clear()
        self.file_list.delete(0, tk.END)
        self.text_editor.delete("1.0", tk.END)

        # Load files with progress bar
        total_files = len(file_paths)
        for i, file_path in enumerate(file_paths, 1):
            self.update_progress(progress_bar, label, i, total_files, os.path.basename(file_path))
            self.ipl_files.append(file_path)
            self.load_file_into_editor(file_path)

        # Destroy progress window
        progress_window.destroy()
        
        self.status_bar.config(text=f"Loaded {len(self.ipl_files)} IPL files")
        self.text_editor.after(100, self.highlight_syntax)

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

                # Get current position before inserting
                start_index = self.text_editor.index("end-1c")
                
                # Insert file header and content without triggering syntax highlighting
                self.text_editor.insert("end", f"// --- {os.path.basename(file_path)} --- //\n")
                self.text_editor.insert("end", file_content + "\n\n")
                
                # Get end position after inserting
                end_index = self.text_editor.index("end-1c")

                # Store section boundaries
                self.file_sections[file_path] = (start_index, end_index)
                self.file_list.insert(tk.END, os.path.basename(file_path))
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def read_binary_file(self, file):
        """Modified to use Fastman92 Processor"""
        temp_output = file.name + ".temp"
        try:
            # Convert binary to text using Fastman92 Processor
            success = self.run_fastman92_conversion(
                file.name,
                temp_output,
                "binary",
                "text"
            )

            if not success:
                return ""

            # Read converted text
            with open(temp_output, "r", encoding="utf-8") as f:
                content = f.read()

            # Clean up
            os.remove(temp_output)
            return content

        except Exception as e:
            if os.path.exists(temp_output):
                os.remove(temp_output)
            messagebox.showerror("Error", f"Error reading binary file: {e}")
            return ""

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
        """Modified to use Fastman92 Processor"""
        try:
            selected_file = self.file_list.get(self.file_list.curselection())
            for path, (start, end) in self.file_sections.items():
                if os.path.basename(path) == selected_file:
                    # Create temporary file for conversion
                    temp_dir = os.path.dirname(path)
                    temp_input = os.path.join(temp_dir, "temp_input.ipl")
                    
                    # Get content from editor
                    full_text = self.text_editor.get("1.0", tk.END)
                    start_marker = f"// --- {selected_file} --- //\n"
                    start_index = full_text.find(start_marker) + len(start_marker)
                    next_section_index = full_text.find("// ---", start_index)
                    content = full_text[start_index:next_section_index].strip() if next_section_index != -1 else full_text[start_index:].strip()

                    # Write content to temp file
                    with open(temp_input, "w", encoding="utf-8") as f:
                        f.write(content)

                    # Run conversion
                    input_type = "text"
                    output_type = "binary" if file_type == "binary" else "text"
                    success = self.run_fastman92_conversion(temp_input, path, input_type, output_type)

                    # Clean up
                    os.remove(temp_input)

                    if success:
                        self.original_contents[path] = "bnry" if file_type == "binary" else ""
                        messagebox.showinfo("Success", f"{selected_file} converted to {file_type} successfully!")
                        self.status_bar.config(text=f"{selected_file} converted to {file_type} successfully")
                        return
                    
            messagebox.showerror("Error", "Could not find selected file.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

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
        """Modified to use Fastman92 Processor"""
        temp_file = save_name + ".temp"
        try:
            # Write text content to temporary file
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(text)

            # Convert using Fastman92 Processor
            success = self.run_fastman92_conversion(
                temp_file,
                save_name,
                "text",
                "binary"
            )

            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)

            if not success:
                raise Exception("Conversion failed")

        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            messagebox.showerror("Error", f"An error occurred while writing to file: {e}")

    def highlight_syntax(self, event=None):
        """Efficient syntax highlighting using VS Code-like strategies"""
        try:
            # Get only visible area
            first_visible = self.text_editor.index("@0,0")
            last_visible = self.text_editor.index(f"@0,{self.text_editor.winfo_height()}")
            
            # Convert to line numbers
            start_line = max(1, int(float(first_visible)) - 1)
            end_line = min(int(float(last_visible)) + 1, 
                          int(float(self.text_editor.index("end"))))

            # Clear only visible tags
            for tag in ["section", "id", "modelname", "coordinate", "comment", "file_header"]:
                self.text_editor.tag_remove(tag, f"{start_line}.0", f"{end_line}.end")

            # Cache current section for visible area
            current_section = self._find_current_section(start_line)
            
            # Process only visible lines
            for line_num in range(start_line, end_line + 1):
                line = self.text_editor.get(f"{line_num}.0", f"{line_num}.end").strip()
                if not line:
                    continue

                # Update section context
                if line.upper() in self.section_formats or line.upper() == "END":
                    current_section = line.upper() if line.upper() != "END" else None
                    self.text_editor.tag_add("section", f"{line_num}.0", f"{line_num}.end")
                    continue

                self._highlight_line(line_num, line, current_section)

        except Exception as e:
            print(f"Highlighting error: {e}")

    def _find_current_section(self, start_line):
        """Find the current section context by looking up"""
        line = start_line
        while line > 0:
            content = self.text_editor.get(f"{line}.0", f"{line}.end").strip().upper()
            if content in self.section_formats:
                return content
            if content == "END":
                return None
            line -= 1
        return None

    def _highlight_line(self, line_num, line, current_section):
        """Highlight a single line efficiently"""
        # File headers
        if line.startswith("// --- ") and line.endswith(" --- //"):
            self.text_editor.tag_add("file_header", f"{line_num}.0", f"{line_num}.end")
            return

        # Comments
        if '#' in line:
            comment_start = line.index('#')
            self.text_editor.tag_add("comment", f"{line_num}.{comment_start}", f"{line_num}.end")
            line = line[:comment_start].strip()
            if not line:
                return

        # Process section content
        if current_section and current_section in self.section_formats:
            parts = [p.strip() for p in line.split(',')]
            format_info = self.section_formats[current_section]
            
            if len(parts) >= format_info["min_parts"]:
                pos = 0
                for i, part in enumerate(parts):
                    if not part:
                        continue
                        
                    start_pos = line.find(part, pos)
                    if start_pos == -1:
                        continue
                    end_pos = start_pos + len(part)

                    # Apply appropriate tags based on position and content
                    if i == 0 and part.isdigit():
                        self.text_editor.tag_add("id", f"{line_num}.{start_pos}", f"{line_num}.{end_pos}")
                    elif current_section == "INST" and i == 1:
                        self.text_editor.tag_add("modelname", f"{line_num}.{start_pos}", f"{line_num}.{end_pos}")
                    elif self._is_coordinate_index(i, format_info) and re.match(r'-?\d*\.?\d+', part):
                        self.text_editor.tag_add("coordinate", f"{line_num}.{start_pos}", f"{line_num}.{end_pos}")

                    pos = end_pos + 1

    def _is_coordinate_index(self, index, format_info):
        """Helper to check if index is a coordinate position"""
        if "coords" in format_info:
            if any(index in group for group in format_info["coords"]):
                return True
        if "alt_coords" in format_info:
            if any(index in group for group in format_info["alt_coords"]):
                return True
        return False

    def show_map_mover_dialog(self):
        """Show simplified dialog for map movement settings"""
        if not self.ipl_files:
            messagebox.showwarning("Warning", "No IPL files loaded!")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Map Mover")
        dialog.geometry("500x750")
        dialog.configure(bg="#1E1E1E")
        dialog.resizable(False, False)
        
        # Configure styles for dark theme
        style = ttk.Style()
        style.configure("Dark.TFrame", background="#1E1E1E")
        style.configure("Dark.TLabelframe", background="#1E1E1E", foreground="white")
        style.configure("Dark.TLabelframe.Label", background="#1E1E1E", foreground="white")
        style.configure("Dark.TLabel", background="#1E1E1E", foreground="white")
        style.configure("Dark.TButton", background="#1E1E1E", foreground="white")
        style.configure("Dark.TCheckbutton", background="#1E1E1E", foreground="white")
        style.configure("Dark.TRadiobutton", background="#1E1E1E", foreground="white")
        style.configure("Dark.TEntry", fieldbackground="#1E1E1E", foreground="white")
        
        # Main container
        main_frame = ttk.Frame(dialog, padding="10", style="Dark.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header_label = ttk.Label(main_frame, text="Move Map Coordinates", 
                               style="Dark.TLabel", font=("Arial", 12, "bold"))
        header_label.pack(pady=10)
        
        # Offset frame
        offset_frame = ttk.LabelFrame(main_frame, text="Offset Values", 
                                    padding="10", style="Dark.TLabelframe")
        offset_frame.pack(fill="x", padx=5, pady=10)
        
        # Offset inputs
        x_var = tk.StringVar(value="0.0")
        y_var = tk.StringVar(value="0.0")
        z_var = tk.StringVar(value="0.0")
        
        for axis, var in zip(['X', 'Y', 'Z'], [x_var, y_var, z_var]):
            frame = ttk.Frame(offset_frame, style="Dark.TFrame")
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text=f"{axis}:", width=3, 
                     style="Dark.TLabel").pack(side="left", padx=5)
            entry = ttk.Entry(frame, textvariable=var, width=15, 
                             style="Dark.TEntry")
            entry.pack(side="left", padx=5)
        
        # Sections frame
        sections_frame = ttk.LabelFrame(main_frame, text="Select Sections", 
                                      padding="10", style="Dark.TLabelframe")
        sections_frame.pack(fill="both", expand=True, padx=5, pady=10)
        
        # Scrollable canvas
        canvas = tk.Canvas(sections_frame, bg="#1E1E1E", highlightthickness=0)
        scrollbar = ttk.Scrollbar(sections_frame, orient="vertical", 
                                command=canvas.yview)
        section_list_frame = ttk.Frame(canvas, style="Dark.TFrame")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Section checkboxes
        section_vars = {}
        for section in self.section_formats:
            var = tk.BooleanVar(value=True)
            section_vars[section] = var
            frame = ttk.Frame(section_list_frame, style="Dark.TFrame")
            frame.pack(fill="x", pady=1)
            cb = ttk.Checkbutton(frame, text=section, variable=var, 
                               style="Dark.TCheckbutton")
            cb.pack(side="left")
        
        canvas.create_window((0, 0), window=section_list_frame, anchor="nw", width=350)
        section_list_frame.bind("<Configure>", 
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Mode selection
        mode_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        mode_frame.pack(fill="x", pady=10)
        mode_var = tk.StringVar(value="selected")
        ttk.Radiobutton(mode_frame, text="Selected File", variable=mode_var,
                       value="selected", style="Dark.TRadiobutton").pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="All Files", variable=mode_var,
                       value="all", style="Dark.TRadiobutton").pack(side="left", padx=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        button_frame.pack(fill="x", pady=10)
        
        def apply_movement():
            try:
                offset = [float(x_var.get()), float(y_var.get()), float(z_var.get())]
                selected_sections = [s for s, v in section_vars.items() if v.get()]
                
                if not selected_sections:
                    messagebox.showerror("Error", "Please select at least one section")
                    return
                    
                if mode_var.get() == "selected":
                    self.move_selected_file(offset, selected_sections)
                else:
                    self.move_all_files(offset, selected_sections)
                    
                dialog.destroy()
                messagebox.showinfo("Success", "Coordinates moved successfully!")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers")
        
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy,
                   style="Dark.TButton").pack(side="right", padx=5)
        ttk.Button(button_frame, text="Apply", command=apply_movement,
                   style="Dark.TButton").pack(side="right", padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        dialog.geometry(f"+{dialog.winfo_screenwidth()//2 - dialog.winfo_width()//2}+"
                       f"{dialog.winfo_screenheight()//2 - dialog.winfo_height()//2}")
        
        dialog.transient(self.root)
        dialog.grab_set()

    def move_selected_file(self, offset, sections):
        """Move coordinates in selected file"""
        try:
            selected_file = self.file_list.get(self.file_list.curselection())
            self.move_file_content(selected_file, offset, sections)
        except:
            messagebox.showerror("Error", "Please select a file to move.")

    def move_all_files(self, offset, sections):
        """Move coordinates in all loaded files"""
        for file_path in self.file_sections.keys():
            file_name = os.path.basename(file_path)
            self.move_file_content(file_name, offset, sections)

    def move_file_content(self, file_name, offset, sections):
        """Move coordinates in specified file sections with proper format handling"""
        full_text = self.text_editor.get("1.0", tk.END)
        start_marker = f"// --- {file_name} --- //\n"
        
        start_index = full_text.find(start_marker)
        if start_index == -1:
            return
        
        start_index += len(start_marker)
        next_section_index = full_text.find("// ---", start_index)
        
        content = full_text[start_index:next_section_index].strip() if next_section_index != -1 else full_text[start_index:].strip()
        new_lines = []
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                new_lines.append(line)
                continue
                
            # Check for section header
            lower_line = line.lower()
            if lower_line in (section.lower() for section in sections):
                current_section = lower_line.upper()
                new_lines.append(line)
                continue
            elif lower_line == "end":
                current_section = None
                new_lines.append(line)
                continue
                
            if not current_section or current_section not in sections:
                new_lines.append(line)
                continue
                
            # Process coordinates based on section format
            parts = line.split(',')
            format_info = self.section_formats.get(current_section)  # Use class variable here
            
            if format_info and len(parts) >= format_info["min_parts"]:
                try:
                    # Move all coordinate groups
                    parts = self.move_coordinate_groups(parts, format_info["coords"], offset)
                    
                    # Handle alternative format if exists (like AUZO)
                    if "alt_coords" in format_info and len(parts) == format_info["min_parts"]:
                        parts = self.move_coordinate_groups(parts, format_info["alt_coords"], offset)
                    
                    new_lines.append(','.join(parts))
                except Exception as e:
                    print(f"Error processing line in {current_section}: {line}\nError: {e}")
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Update text editor content
        new_content = '\n'.join(new_lines)
        start = f"{start_marker}{new_content}\n\n"
        if next_section_index != -1:
            rest = full_text[next_section_index:]
            new_text = full_text[:start_index-len(start_marker)] + start + rest
        else:
            new_text = full_text[:start_index-len(start_marker)] + start
            
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", new_text)
        self.highlight_syntax()
        
        self.status_bar.config(text=f"Moved coordinates in {file_name}")

    def move_coordinate_groups(self, parts, coords, offset):
        """Helper function to move multiple coordinate groups correctly"""
        try:
            for coord_group in coords:
                # Handle coordinate groups
                if len(coord_group) >= 3:  # Group of 3 coordinates (X,Y,Z)
                    x, y, z = coord_group
                    if all(i < len(parts) for i in (x, y, z)):
                        parts[x] = f"{float(parts[x].strip()) + offset[0]:.6f}"
                        parts[y] = f"{float(parts[y].strip()) + offset[1]:.6f}"
                        parts[z] = f"{float(parts[z].strip()) + offset[2]:.6f}"
                elif len(coord_group) == 2:  # Group of 2 coordinates (X,Y)
                    x, y = coord_group
                    if all(i < len(parts) for i in (x, y)):
                        parts[x] = f"{float(parts[x].strip()) + offset[0]:.6f}"
                        parts[y] = f"{float(parts[y].strip()) + offset[1]::.6f}"
        except (ValueError, IndexError) as e:
            print(f"Error processing coordinates: {e}")
        return parts

    def _on_scroll(self, event=None):
        """Handle scroll events with debouncing"""
        if self._highlight_after:
            self.root.after_cancel(self._highlight_after)
        self._highlight_after = self.root.after(50, self.highlight_syntax)

if __name__ == "__main__":
    root = tk.Tk()
    app = IPLEditor(root)
    root.mainloop()
