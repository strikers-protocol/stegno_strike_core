#!/usr/bin/env python3
"""
Strikers' Protocol GUI: Dual-Theme Neon Edition.
Features: Typewriter Boot, Frame Glitch Transitions, Blue/Red Theme Shift.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import threading
import hashlib
import base64
import random

try:
    from cryptography.fernet import Fernet, InvalidToken
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# --- Futuristic Aesthetic Constants ---
BG_COLOR = "#050508"         
PANEL_BG = "#0A0B10"         
CYAN_THEME = "#00E5FF"       # Encode/Protect
DARK_CYAN = "#004455"
CRIMSON_THEME = "#FF003C"    # Decode/Extract
DARK_CRIMSON = "#550011"
SPARK_WHITE = "#FFFFFF"      

FONT_MAIN = ("Consolas", 13)       
FONT_TITLE = ("Consolas", 18, "bold")
FONT_BTN = ("Consolas", 14, "bold")

ctk.set_appearance_mode("dark")

def get_fernet_key(password: str) -> bytes:
    digest = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)

# --- Core LSB functions ---
def to_bits(data: bytes):
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1

def from_bits(bits):
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            yield byte
            byte = 0
            count = 0

def embed_bytes_into_image(cover_path, payload_bytes, out_path):
    img = Image.open(cover_path).convert('RGB')
    w, h = img.size
    pixels = list(img.getdata())

    header = len(payload_bytes).to_bytes(4, 'big')
    bits = list(to_bits(header + payload_bytes))
    capacity = 3 * w * h
    if len(bits) > capacity:
        raise ValueError(f"Payload too large: {len(bits)} bits > capacity {capacity} bits")

    new_pixels = []
    it = iter(bits)
    for (r, g, b) in pixels:
        try: r = (r & ~1) | next(it)
        except StopIteration: new_pixels.append((r, g, b)); continue
        try: g = (g & ~1) | next(it)
        except StopIteration: new_pixels.append((r, g, b)); continue
        try: b = (b & ~1) | next(it)
        except StopIteration: new_pixels.append((r, g, b)); continue
        new_pixels.append((r, g, b))

    if len(new_pixels) < len(pixels):
        new_pixels.extend(pixels[len(new_pixels):])

    img2 = Image.new('RGB', (w, h))
    img2.putdata(new_pixels)
    img2.save(out_path, 'PNG')

def extract_bytes_from_image(stego_path):
    img = Image.open(stego_path).convert('RGB')
    pixels = list(img.getdata())

    bits = []
    for (r, g, b) in pixels:
        bits.extend([r & 1, g & 1, b & 1])

    header_bits = bits[:32]
    length = int(''.join(str(x) for x in header_bits), 2)
    total_bits = 32 + length * 8
    if total_bits > len(bits) or length < 0:
        raise ValueError("Declared length exceeds image capacity or image is corrupted")

    payload_bits = bits[32:total_bits]
    data = bytes(from_bits(payload_bits))
    return data

def choose_file(entry_widget, filetypes=(("PNG images","*.png"),("All files","*.*"))):
    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        entry_widget.delete(0, "end")
        entry_widget.insert(0, path)

def save_file_dialog(default_name="recovered.txt"):
    return filedialog.asksaveasfilename(defaultextension="", initialfile=default_name,
                                        filetypes=(("All files","*.*"),("Text files","*.txt")))

# --- HUD Application ---
class StegoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("STRIKE CORE // STRIKERS'PROTOCOL")
        self.geometry("950x700")
        self.configure(fg_color=BG_COLOR) 

        self.is_encoding = False
        self.is_decoding = False
        self.current_theme = CYAN_THEME

        # Header Strings for Typewriter Animation
        self.target_sys_text = "[ STRIKE_CORE ] :: "
        self.target_brand_text = "STRIKERS'PROTOCOL"

        # Header Title
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(15, 5))
        
        self.sys_label = ctk.CTkLabel(self.header_frame, text="", font=FONT_TITLE, text_color=CYAN_THEME)
        self.sys_label.pack(side="left")
        self.brand_label = ctk.CTkLabel(self.header_frame, text="", font=FONT_TITLE, text_color=CYAN_THEME)
        self.brand_label.pack(side="left")

        # Start Header Animations
        self._typewriter_boot(0)
        self._animate_lightning_spark()

        # Custom Navigation Buttons
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill='x', padx=20, pady=10)
        
        self.btn_nav_encode = ctk.CTkButton(self.nav_frame, text="ENCODE_PAYLOAD", font=FONT_BTN, command=lambda: self.switch_tab("encode"), 
                                            width=200, fg_color=DARK_CYAN, hover_color=DARK_CYAN, border_color=CYAN_THEME, border_width=1, corner_radius=0, text_color=CYAN_THEME)
        self.btn_nav_encode.pack(side='left', padx=(0, 10))

        self.btn_nav_decode = ctk.CTkButton(self.nav_frame, text="DECODE_PAYLOAD", font=FONT_BTN, command=lambda: self.switch_tab("decode"), 
                                            width=200, fg_color="transparent", hover_color=DARK_CRIMSON, border_color=DARK_CRIMSON, border_width=1, corner_radius=0, text_color=DARK_CRIMSON)
        self.btn_nav_decode.pack(side='left')

        # Frame Containers
        self.frame_encode = ctk.CTkFrame(self, fg_color=PANEL_BG, border_width=1, border_color=DARK_CYAN, corner_radius=0)
        self.frame_decode = ctk.CTkFrame(self, fg_color=PANEL_BG, border_width=1, border_color=DARK_CRIMSON, corner_radius=0)

        self._build_encode_tab()
        self._build_decode_tab()

        # Build Footer with Live Copyright Watermark
        copyright_text = "[ LSB-01 // SECURE SECTOR // AES-256 ]\n© 2026 STRIKERS PROTOCOL. ALL RIGHTS RESERVED."
        self.footer = ctk.CTkLabel(self, text=copyright_text, text_color=DARK_CYAN, font=("Consolas", 10))
        self.footer.pack(side='bottom', pady=5)

        # Initial Tab Setup
        self.switch_tab("encode")

    # --- ANIMATIONS ---
    def _typewriter_boot(self, i):
        """Types out the header strings on startup."""
        sys_len = len(self.target_sys_text)
        brand_len = len(self.target_brand_text)
        
        if i < sys_len:
            self.sys_label.configure(text=self.target_sys_text[:i+1])
            self.after(40, self._typewriter_boot, i+1)
        elif i < sys_len + brand_len:
            j = i - sys_len
            self.brand_label.configure(text=self.target_brand_text[:j+1])
            self.after(50, self._typewriter_boot, i+1)

    def _animate_lightning_spark(self):
        """Creates a high-energy lightning spark effect on the brand name."""
        if random.random() < 0.10 and len(self.brand_label.cget("text")) == len(self.target_brand_text):
            self.brand_label.configure(text_color=SPARK_WHITE)
            self.after(random.randint(20, 50), lambda: self.brand_label.configure(text_color=self.current_theme)) 
        
        self.after(random.randint(50, 600), self._animate_lightning_spark)

    def _glitch_box(self, frame, theme_color):
        """Causes the main frame border to rapidly flash like a hologram turning on."""
        delays = [0, 60, 120, 180, 240]
        colors = [SPARK_WHITE, theme_color, SPARK_WHITE, theme_color, theme_color]
        
        for d, c in zip(delays, colors):
            self.after(d, lambda f=frame, col=c: f.configure(border_color=col))

    def switch_tab(self, tab_name):
        if tab_name == "encode":
            self.current_theme = CYAN_THEME
            self.frame_decode.pack_forget()
            self.frame_encode.pack(fill='both', expand=True, padx=20, pady=(0, 15))
            
            # Fire Glitch Animation on the Encode Box
            self._glitch_box(self.frame_encode, CYAN_THEME)
            
            # Switch to Cyan Theme
            self.sys_label.configure(text_color=CYAN_THEME)
            self.brand_label.configure(text_color=CYAN_THEME)
            self.btn_nav_encode.configure(fg_color=DARK_CYAN, border_color=CYAN_THEME, text_color=CYAN_THEME)
            self.btn_nav_decode.configure(fg_color="transparent", border_color=DARK_CRIMSON, text_color=DARK_CRIMSON)
            self.footer.configure(text_color=DARK_CYAN)
        else:
            self.current_theme = CRIMSON_THEME
            self.frame_encode.pack_forget()
            self.frame_decode.pack(fill='both', expand=True, padx=20, pady=(0, 15))
            
            # Fire Glitch Animation on the Decode Box
            self._glitch_box(self.frame_decode, CRIMSON_THEME)

            # Switch to Crimson Theme
            self.sys_label.configure(text_color=CRIMSON_THEME)
            self.brand_label.configure(text_color=CRIMSON_THEME)
            self.btn_nav_decode.configure(fg_color=DARK_CRIMSON, border_color=CRIMSON_THEME, text_color=CRIMSON_THEME)
            self.btn_nav_encode.configure(fg_color="transparent", border_color=DARK_CYAN, text_color=DARK_CYAN)
            self.footer.configure(text_color=DARK_CRIMSON)

    # --- UI Builders ---
    def _build_encode_tab(self):
        self.frame_encode.columnconfigure(1, weight=1)
        self.frame_encode.rowconfigure(2, weight=1)

        self._create_label(self.frame_encode, "TARGET_COVER [PNG]:", 0, 0, CYAN_THEME)
        self.cover_entry = self._create_entry(self.frame_encode, 0, 1, CYAN_THEME, DARK_CYAN, "DIR_PATH...")
        self._create_button(self.frame_encode, "MOUNT", lambda: choose_file(self.cover_entry), 0, 2, CYAN_THEME, DARK_CYAN)

        self._create_label(self.frame_encode, "SECURE_KEY [AES]:", 1, 0, CYAN_THEME)
        self.embed_pass_entry = self._create_entry(self.frame_encode, 1, 1, CYAN_THEME, DARK_CYAN, "NULL/OPTIONAL", is_password=True)

        self._create_label(self.frame_encode, "PAYLOAD_DATA:", 2, 0, CYAN_THEME, sticky='nw')
        self.msg_text = ctk.CTkTextbox(self.frame_encode, font=FONT_MAIN, fg_color=BG_COLOR, text_color=CYAN_THEME, border_width=1, border_color=DARK_CYAN, corner_radius=0, wrap='word')
        self.msg_text.grid(row=2, column=1, columnspan=2, sticky='nsew', padx=10, pady=10)

        self._create_label(self.frame_encode, "OUT_DIRECTORY:", 3, 0, CYAN_THEME)
        self.out_entry = self._create_entry(self.frame_encode, 3, 1, CYAN_THEME, DARK_CYAN)
        self.out_entry.insert(0, "strikers_encoded.png")
        self._create_button(self.frame_encode, "SET_DIR", lambda: self._choose_save(self.out_entry), 3, 2, CYAN_THEME, DARK_CYAN)

        self.embed_loader_lbl = ctk.CTkLabel(self.frame_encode, text="", font=FONT_TITLE, text_color=SPARK_WHITE)
        self.embed_loader_lbl.grid(row=4, column=1, sticky='w', padx=10, pady=5)
        
        self.embed_status = ctk.CTkLabel(self.frame_encode, text="STATUS: STANDBY", font=FONT_MAIN, text_color=DARK_CYAN)
        self.embed_status.grid(row=5, column=1, sticky='w', padx=10, pady=10)

        self.btn_embed = self._create_button(self.frame_encode, "EXECUTE ENCODE", self.start_embed_thread, 5, 2, CYAN_THEME, DARK_CYAN, width=150)

    def _build_decode_tab(self):
        self.frame_decode.columnconfigure(1, weight=1)
        self.frame_decode.rowconfigure(2, weight=1)

        self._create_label(self.frame_decode, "GHOST_IMAGE [PNG]:", 0, 0, CRIMSON_THEME)
        self.stego_entry = self._create_entry(self.frame_decode, 0, 1, CRIMSON_THEME, DARK_CRIMSON, "DIR_PATH...")
        self._create_button(self.frame_decode, "MOUNT", lambda: choose_file(self.stego_entry), 0, 2, CRIMSON_THEME, DARK_CRIMSON)

        self._create_label(self.frame_decode, "SECURE_KEY [AES]:", 1, 0, CRIMSON_THEME)
        self.extract_pass_entry = self._create_entry(self.frame_decode, 1, 1, CRIMSON_THEME, DARK_CRIMSON, "REQUIRED IF ENCRYPTED", is_password=True)

        self._create_label(self.frame_decode, "EXTRACTED_DATA:", 2, 0, CRIMSON_THEME, sticky='nw')
        self.recovered_text = ctk.CTkTextbox(self.frame_decode, font=FONT_MAIN, fg_color=BG_COLOR, text_color=CRIMSON_THEME, border_width=1, border_color=DARK_CRIMSON, corner_radius=0, wrap='word')
        self.recovered_text.grid(row=2, column=1, columnspan=2, sticky='nsew', padx=10, pady=10)

        self.extract_loader_lbl = ctk.CTkLabel(self.frame_decode, text="", font=FONT_TITLE, text_color=SPARK_WHITE)
        self.extract_loader_lbl.grid(row=3, column=1, sticky='w', padx=10, pady=5)

        self.extract_status = ctk.CTkLabel(self.frame_decode, text="STATUS: AWAITING TARGET", font=FONT_MAIN, text_color=DARK_CRIMSON)
        self.extract_status.grid(row=4, column=1, sticky='w', padx=10, pady=10)

        btn_frame = ctk.CTkFrame(self.frame_decode, fg_color="transparent")
        btn_frame.grid(row=4, column=2, padx=10, pady=10, sticky='e')
        self.btn_extract = self._create_button(btn_frame, "EXECUTE DECODE", self.start_extract_thread, 0, 0, CRIMSON_THEME, DARK_CRIMSON, width=150)
        self._create_button(btn_frame, "EXPORT", self.on_save_recovered, 0, 1, CRIMSON_THEME, DARK_CRIMSON)

    # --- UI Factory Methods ---
    def _create_label(self, parent, text, row, col, color, sticky='w'):
        lbl = ctk.CTkLabel(parent, text=text, font=FONT_MAIN, text_color=color)
        lbl.grid(row=row, column=col, sticky=sticky, padx=10, pady=10)
        return lbl

    def _create_entry(self, parent, row, col, text_col, border_col, placeholder="", is_password=False):
        entry = ctk.CTkEntry(parent, font=FONT_MAIN, fg_color=BG_COLOR, text_color=text_col, 
                             border_color=border_col, border_width=1, corner_radius=0, 
                             placeholder_text=placeholder, placeholder_text_color=border_col,
                             show="*" if is_password else "")
        entry.grid(row=row, column=col, sticky='ew', padx=10, pady=10)
        return entry

    def _create_button(self, parent, text, cmd, row, col, main_col, dark_col, width=100):
        btn = ctk.CTkButton(parent, text=text, font=FONT_BTN, command=cmd, width=width,
                            fg_color="transparent", hover_color=dark_col, 
                            border_color=main_col, border_width=1, corner_radius=0, 
                            text_color=main_col)
        btn.grid(row=row, column=col, padx=5, pady=5)
        return btn

    def _choose_save(self, entry_widget):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=(("PNG image","*.png"),("All files","*.*")))
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    # --- Loader Pulsing Text Animation ---
    def _animate_loader(self, label, flag_name, step=0):
        if getattr(self, flag_name):
            frames = [
                "[ ⚡ CORE SYNCING.   ]",
                "[ ⚡ CORE SYNCING..  ]",
                "[ ⚡ CORE SYNCING... ]",
                "[ ❂ CORE SYNCING... ❂ ]",
                "[ ⚡ CORE SYNCING... ]"
            ]
            label.configure(text=frames[step % len(frames)])
            self.after(200, self._animate_loader, label, flag_name, step + 1)
        else:
            label.configure(text="")

    # --- Threading Controllers ---
    def start_embed_thread(self):
        cover = self.cover_entry.get().strip()
        out = self.out_entry.get().strip()
        message = self.msg_text.get("0.0", "end").strip().encode('utf-8')
        password = self.embed_pass_entry.get()

        if not cover or not out or not message:
            messagebox.showwarning("ERR_SYS", "MISSING_PARAMETERS. CHECK INPUTS.")
            return

        if password and HAS_CRYPTO:
            f = Fernet(get_fernet_key(password))
            message = f.encrypt(message)

        self.btn_embed.configure(state='disabled')
        self.is_encoding = True
        self._animate_loader(self.embed_loader_lbl, "is_encoding")
        self.embed_status.configure(text="STATUS: INJECTING PAYLOAD...", text_color=CYAN_THEME)
        
        thread = threading.Thread(target=self._embed_worker, args=(cover, message, out), daemon=True)
        thread.start()

    def _embed_worker(self, cover, message, out):
        try:
            embed_bytes_into_image(cover, message, out)
            self.after(0, self._embed_finished, True, out)
        except Exception as e:
            self.after(0, self._embed_finished, False, str(e))

    def _embed_finished(self, success, result):
        self.is_encoding = False 
        self.btn_embed.configure(state='normal')
        if success:
            self.embed_status.configure(text=f"STATUS: SHIELDED. FILE [{os.path.basename(result)}] SECURED.", text_color=CYAN_THEME)
        else:
            self.embed_status.configure(text="STATUS: SYSTEM FAILURE.", text_color=CRIMSON_THEME)
            messagebox.showerror("ERR_CRITICAL", result)

    def start_extract_thread(self):
        stego = self.stego_entry.get().strip()
        if not stego:
            messagebox.showwarning("ERR_SYS", "NO_TARGET_MOUNTED.")
            return

        self.btn_extract.configure(state='disabled')
        self.is_decoding = True
        self._animate_loader(self.extract_loader_lbl, "is_decoding")
        self.extract_status.configure(text="STATUS: BREACHING MATRIX...", text_color=CRIMSON_THEME)
        self.recovered_text.delete("0.0", "end")

        thread = threading.Thread(target=self._extract_worker, args=(stego,), daemon=True)
        thread.start()

    def _extract_worker(self, stego):
        try:
            data = extract_bytes_from_image(stego)
            self.after(0, self._extract_finished, True, data)
        except Exception as e:
            self.after(0, self._extract_finished, False, str(e))

    def _extract_finished(self, success, result):
        self.is_decoding = False 
        self.btn_extract.configure(state='normal')
        
        if not success:
            self.extract_status.configure(text="STATUS: BREACH FAILED.", text_color=CRIMSON_THEME)
            messagebox.showerror("ERR_CRITICAL", result)
            return

        password = self.extract_pass_entry.get()
        data = result

        if password and HAS_CRYPTO:
            try:
                f = Fernet(get_fernet_key(password))
                data = f.decrypt(data)
            except InvalidToken:
                self.extract_status.configure(text="STATUS: ACCESS DENIED. INVALID KEY.", text_color=CRIMSON_THEME)
                return
            except Exception as e:
                messagebox.showerror("ERR_SYS", str(e))
                return

        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            if not password and HAS_CRYPTO:
                text = ">>> [ENCRYPTED DATA GHOST] <<<\n>>> AES KEY REQUIRED TO DECRYPT <<<"
            else:
                text = data.decode('utf-8', errors='replace')

        self.recovered_text.insert("end", text)
        self.extract_status.configure(text="STATUS: PAYLOAD RECOVERED.", text_color=CRIMSON_THEME)

    def on_save_recovered(self):
        content = self.recovered_text.get("0.0", "end")
        if not content.strip():
            return
        path = save_file_dialog(default_name="ghost_data.txt")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.extract_status.configure(text=f"STATUS: EXPORTED [{os.path.basename(path)}]", text_color=CRIMSON_THEME)
            except Exception as e:
                messagebox.showerror("ERR_WRITE", str(e))

if __name__ == "__main__":
    app = StegoGUI()
    app.mainloop()