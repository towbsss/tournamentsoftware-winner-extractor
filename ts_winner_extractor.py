import os
import re
import urllib.parse
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd

# Disable Insecure Request Warning from urllib3 when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CORE LOGIC ---

def clean_player_name(name):
    """Strip trailing seeding info like [1] or [3/4] or [5/8]."""
    cleaned = re.sub(r'\s*\[\s*\d+(?:/\d+)?\s*\]\s*$', '', name)
    cleaned = ' '.join(cleaned.split())
    return cleaned

def extract_players_from_cell(cell):
    """Extract and clean player names from a cell (tries <a> first, falls back to text splits)."""
    links = cell.find_all('a')
    if links:
        names = [a.get_text().strip() for a in links]
    else:
        names = [name.strip() for name in cell.get_text(separator='\n').split('\n') if name.strip()]
    
    return [clean_player_name(name) for name in names if name.strip()]

def map_place(place_str):
    """Map place string (1, 2, 3/4) to standard text."""
    place_str = place_str.strip()
    if place_str == '1':
        return 'Champion'
    elif place_str == '2':
        return 'Finalist'
    elif place_str in ('3', '4', '3/4'):
        return 'Semi-finalist'
    else:
        return f"Placed {place_str}"

def extract_winners(html_content, target_names):
    """Parse winners page HTML and match against target names (case-insensitive)."""
    target_names_lower = {name.lower().strip(): name for name in target_names}
    matched_results = {}  # name -> list of result strings
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        current_event = "Unknown Event"
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 1:
                # Event category header (e.g. MS, WD, S SH6)
                current_event = cells[0].get_text().strip()
            elif len(cells) == 2:
                # Placement row
                place = cells[0].get_text().strip()
                players = extract_players_from_cell(cells[1])
                
                for player in players:
                    player_lower = player.lower()
                    if player_lower in target_names_lower:
                        original_target_name = target_names_lower[player_lower]
                        placement_str = map_place(place)
                        result_entry = f"{current_event} {placement_str}"
                        
                        if original_target_name not in matched_results:
                            matched_results[original_target_name] = []
                        matched_results[original_target_name].append(result_entry)
                        
    return matched_results


# --- GUI APPLICATION ---

class WinnerExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TournamentSoftware Winner Extractor")
        self.root.geometry("750x850")
        self.root.configure(bg="#121214")
        
        # Style configurations
        self.bg_color = "#121214"
        self.card_bg = "#1e1e24"
        self.accent_color = "#7c4dff"
        self.accent_hover = "#651fff"
        self.text_primary = "#ffffff"
        self.text_secondary = "#a0a0b0"
        self.input_bg = "#2e2e38"
        self.border_color = "#3a3a4a"
        
        # Load custom fonts
        self.font_title = ("Segoe UI", 16, "bold")
        self.font_header = ("Segoe UI", 12, "bold")
        self.font_body = ("Segoe UI", 10)
        self.font_body_bold = ("Segoe UI", 10, "bold")
        self.font_console = ("Consolas", 10)
        
        # Build UI components
        self.create_widgets()
        
    def create_widgets(self):
        # 1. Header Frame
        header_frame = tk.Frame(self.root, bg=self.card_bg, pady=15, padx=20)
        header_frame.pack(fill="x", side="top")
        
        title_label = tk.Label(
            header_frame, 
            text="🏆 TournamentSoftware Winner Extractor", 
            font=self.font_title, 
            fg=self.text_primary, 
            bg=self.card_bg
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Extract placements of your athletes from any tournament winners page.", 
            font=self.font_body, 
            fg=self.text_secondary, 
            bg=self.card_bg
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Main scrollable/padded container
        container = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        # 2. Tournament URL / ID Section
        url_frame = tk.LabelFrame(
            container, 
            text=" 1. Tournament Link or ID ", 
            font=self.font_header, 
            fg=self.accent_color, 
            bg=self.bg_color, 
            bd=1, 
            relief="solid",
            padx=15,
            pady=15
        )
        url_frame.pack(fill="x", pady=(0, 15))
        
        url_desc = tk.Label(
            url_frame, 
            text="Paste the full TournamentSoftware tournament URL or the 36-character ID (GUID):",
            font=self.font_body, 
            fg=self.text_secondary, 
            bg=self.bg_color,
            justify="left",
            anchor="w"
        )
        url_desc.pack(fill="x", pady=(0, 8))
        
        self.url_entry = tk.Entry(
            url_frame, 
            font=self.font_body, 
            bg=self.input_bg, 
            fg=self.text_primary, 
            insertbackground=self.text_primary,
            bd=1, 
            relief="solid",
            highlightthickness=0
        )
        self.url_entry.pack(fill="x", ipady=8)
        self.url_entry.insert(0, "https://badmintoncanada.tournamentsoftware.com/tournament/7A817C4F-7EDD-493C-918B-8DC6C2EDFA67")

        # 3. Athletes / Names Input Section
        names_frame = tk.LabelFrame(
            container, 
            text=" 2. Athlete Names ", 
            font=self.font_header, 
            fg=self.accent_color, 
            bg=self.bg_color, 
            bd=1, 
            relief="solid",
            padx=15,
            pady=15
        )
        names_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        names_desc = tk.Label(
            names_frame, 
            text="Enter player names (one per line). Case-insensitive matching is used.",
            font=self.font_body, 
            fg=self.text_secondary, 
            bg=self.bg_color,
            anchor="w"
        )
        names_desc.pack(fill="x", pady=(0, 8))
        
        # Text area with scrollbar
        txt_container = tk.Frame(names_frame, bg=self.bg_color)
        txt_container.pack(fill="both", expand=True)
        
        self.names_text = tk.Text(
            txt_container, 
            font=self.font_body, 
            bg=self.input_bg, 
            fg=self.text_primary, 
            insertbackground=self.text_primary,
            bd=1, 
            relief="solid",
            height=8,
            wrap="word",
            undo=True
        )
        self.names_text.pack(fill="both", expand=True, side="left")
        
        names_scroll = ttk.Scrollbar(txt_container, orient="vertical", command=self.names_text.yview)
        names_scroll.pack(fill="y", side="right")
        self.names_text.config(yscrollcommand=names_scroll.set)
        
        # Preset test names
        self.names_text.insert("1.0", "John DOE\nJane SMITH\nAlex JONES")
        
        # Buttons to load names
        buttons_frame = tk.Frame(names_frame, bg=self.bg_color, pady=10)
        buttons_frame.pack(fill="x")
        
        self.btn_load_txt = self.create_button(
            buttons_frame, "Load from Text File...", self.load_txt_file, bg="#3a3a4a"
        )
        self.btn_load_txt.pack(side="left", padx=(0, 10))
        
        self.btn_load_excel = self.create_button(
            buttons_frame, "Load from Excel...", self.load_excel_file, bg="#3a3a4a"
        )
        self.btn_load_excel.pack(side="left", padx=10)
        
        self.btn_clear_names = self.create_button(
            buttons_frame, "Clear Names", self.clear_names, bg="#d32f2f"
        )
        self.btn_clear_names.pack(side="right")

        # 4. Action Section
        action_frame = tk.Frame(container, bg=self.bg_color, pady=5)
        action_frame.pack(fill="x", pady=(0, 15))
        
        self.extract_btn = self.create_button(
            action_frame, 
            "⚡ Extract & Match Winners", 
            self.start_extraction, 
            bg=self.accent_color,
            fg=self.text_primary,
            active_bg=self.accent_hover
        )
        self.extract_btn.pack(fill="x", ipady=5)
        
        self.status_label = tk.Label(
            action_frame, 
            text="Ready to search.", 
            font=self.font_body_bold, 
            fg=self.text_secondary, 
            bg=self.bg_color,
            pady=5
        )
        self.status_label.pack()

        # 5. Output / Results Section
        results_frame = tk.LabelFrame(
            container, 
            text=" 3. Results ", 
            font=self.font_header, 
            fg=self.accent_color, 
            bg=self.bg_color, 
            bd=1, 
            relief="solid",
            padx=15,
            pady=15
        )
        results_frame.pack(fill="both", expand=True)
        
        res_container = tk.Frame(results_frame, bg=self.bg_color)
        res_container.pack(fill="both", expand=True)
        
        self.results_text = tk.Text(
            res_container, 
            font=self.font_console, 
            bg=self.input_bg, 
            fg="#a8ffb2",  # light green console text
            bd=1, 
            relief="solid",
            height=10,
            wrap="word"
        )
        self.results_text.pack(fill="both", expand=True, side="left")
        self.results_text.insert("1.0", "Results will appear here...")
        self.results_text.config(state="disabled")
        
        results_scroll = ttk.Scrollbar(res_container, orient="vertical", command=self.results_text.yview)
        results_scroll.pack(fill="y", side="right")
        self.results_text.config(yscrollcommand=results_scroll.set)
        
        # Result output actions
        res_buttons_frame = tk.Frame(results_frame, bg=self.bg_color, pady=10)
        res_buttons_frame.pack(fill="x")
        
        self.btn_copy = self.create_button(
            res_buttons_frame, "Copy to Clipboard", self.copy_to_clipboard, bg="#3a3a4a"
        )
        self.btn_copy.pack(side="left")
        
        self.btn_save_txt = self.create_button(
            res_buttons_frame, "Save Results to File...", self.save_results_file, bg="#3a3a4a"
        )
        self.btn_save_txt.pack(side="left", padx=10)

    # --- UI HELPERS ---
    
    def create_button(self, parent, text, command, bg="#3a3a4a", fg="#ffffff", active_bg=None):
        """Helper to create flat modern styled buttons with hover transitions."""
        if not active_bg:
            # slightly lighter/darker color for hover
            active_bg = "#4c4c5e" if bg == "#3a3a4a" else "#e53935" if bg == "#d32f2f" else self.accent_hover
            
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            font=self.font_body_bold,
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=active_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    # --- EVENT HANDLERS ---

    def clear_names(self):
        self.names_text.delete("1.0", "end")
        self.status_label.config(text="Player names cleared.", fg=self.text_secondary)

    def load_txt_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Names Text File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                
                # Append or insert content into names text box
                self.names_text.delete("1.0", "end")
                self.names_text.insert("1.0", content)
                self.status_label.config(text=f"Loaded names from: {os.path.basename(file_path)}", fg="#4caf50")
            except Exception as e:
                messagebox.showerror("Error Reading File", f"Could not read text file:\n{str(e)}")

    def load_excel_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel Player List",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                df = pd.read_excel(file_path, header=None)
                if df.empty:
                    raise ValueError("The Excel file is empty.")
                
                # Read first column
                raw_names = df.iloc[:, 0].dropna().tolist()
                names = [str(n).strip() for n in raw_names if str(n).strip()]
                
                # Insert list into names box
                self.names_text.delete("1.0", "end")
                self.names_text.insert("1.0", "\n".join(names))
                self.status_label.config(text=f"Loaded {len(names)} names from Excel: {os.path.basename(file_path)}", fg="#4caf50")
            except Exception as e:
                messagebox.showerror("Error Reading Excel", f"Could not read Excel file:\n{str(e)}")

    def copy_to_clipboard(self):
        content = self.results_text.get("1.0", "end-1c").strip()
        if content and content != "Results will appear here...":
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.status_label.config(text="Copied results to clipboard!", fg="#4caf50")
        else:
            messagebox.showwarning("Clipboard Empty", "No results available to copy.")

    def save_results_file(self):
        content = self.results_text.get("1.0", "end-1c").strip()
        if not content or content == "Results will appear here...":
            messagebox.showwarning("Empty Results", "No results available to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Results File",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.status_label.config(text=f"Results saved to: {os.path.basename(file_path)}", fg="#4caf50")
            except Exception as e:
                messagebox.showerror("Error Saving File", f"Could not save results to file:\n{str(e)}")

    def start_extraction(self):
        url_input = self.url_entry.get().strip()
        names_text_val = self.names_text.get("1.0", "end-1c").strip()
        
        if not url_input:
            messagebox.showerror("Missing Information", "Please enter a tournament URL or ID.")
            return
        
        names_list = [n.strip() for n in names_text_val.split('\n') if n.strip()]
        if not names_list:
            messagebox.showerror("Missing Information", "Please enter or load at least one athlete name.")
            return
            
        # Configure UI for active extraction state
        self.status_label.config(text="🔄 Scraping and matching... Please wait.", fg=self.accent_color)
        self.extract_btn.config(state="disabled")
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "Fetching results, please wait...")
        self.results_text.config(state="disabled")
        
        # Start thread
        def worker_thread():
            try:
                # 1. Normalize ID and domain
                subdomain = "badmintoncanada" # default fallback
                tournament_id = ""
                
                guid_pattern = r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
                guid_match = re.search(guid_pattern, url_input, re.IGNORECASE)
                
                if guid_match:
                    tournament_id = guid_match.group(0)
                else:
                    raise ValueError("Could not find a valid 36-character tournament ID (GUID) in your input.")
                
                if "tournamentsoftware.com" in url_input:
                    parsed_url = urllib.parse.urlparse(url_input)
                    netloc = parsed_url.netloc
                    if netloc:
                        parts = netloc.split('.')
                        if len(parts) >= 3:
                            subdomain = parts[0]
                
                # 2. Build final url
                winners_url = f"https://{subdomain}.tournamentsoftware.com/sport/winners.aspx?id={tournament_id}"
                
                # 3. Fetch webpage
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                response = requests.get(winners_url, headers=headers, verify=False, timeout=15)
                
                if response.status_code != 200:
                    raise Exception(f"Unable to access winners page. Server returned status code: {response.status_code}")
                
                # 4. Extract winners
                matched_results = extract_winners(response.text, names_list)
                
                # 5. Format results exactly as requested
                output_lines = []
                has_matches = False
                
                for name in names_list:
                    # Find case-insensitive match key in dictionary
                    matched_key = None
                    for key in matched_results:
                        if key.lower() == name.lower():
                            matched_key = key
                            break
                    
                    if matched_key:
                        has_matches = True
                        output_lines.append(name)
                        for placement in matched_results[matched_key]:
                            output_lines.append(placement)
                        output_lines.append("") # blank line between players
                
                output_text = "\n".join(output_lines).strip()
                
                if not has_matches:
                    output_text = "No matches found in the tournament winners list."
                
                # 6. Update GUI safely on main thread
                self.root.after(0, lambda: self.finish_extraction(output_text, True))
                
            except Exception as e:
                self.root.after(0, lambda: self.finish_extraction(str(e), False))
                
        threading.Thread(target=worker_thread, daemon=True).start()

    def finish_extraction(self, output_text, success):
        self.extract_btn.config(state="normal")
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        
        if success:
            self.results_text.insert("1.0", output_text)
            self.results_text.config(fg="#a8ffb2") # green text for success
            self.status_label.config(text="✅ Matches extracted successfully!", fg="#4caf50")
        else:
            self.results_text.insert("1.0", f"Error encountered:\n\n{output_text}")
            self.results_text.config(fg="#ff7272") # red text for error
            self.status_label.config(text="❌ Failed to extract results.", fg="#ff7272")
            messagebox.showerror("Extraction Error", f"An error occurred while fetching/parsing:\n{output_text}")
            
        self.results_text.config(state="disabled")


# --- RUN APPLICATION ---

if __name__ == "__main__":
    root = tk.Tk()
    app = WinnerExtractorApp(root)
    root.mainloop()
