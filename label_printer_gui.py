import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk, Image as PILImage
import os
import socket
import image_helper
from wand.image import Image
from wand.font import Font
import json
from matplotlib import font_manager

# --- Helper functions (adapted from your script) ---
def generate_image(text, font, fontsize, fruit, filename, preview=False):
    font = Font(path=font, size=fontsize, color="black")
    if fruit:
        width, height = 240, 80
    else:
        width, height = 288, 88
    with Image(width=width, height=height, background="white") as img:
        img.caption(text, font=font, gravity="center")
        img.background_color = "white"
        img.gravity = "center"
        if fruit:
            img.extent(width=320, height=96, x=-60)
        else:
            img.extent(width=320, height=96)
        if not preview:
            img.rotate(270)
        img.save(filename=filename)
    return filename

def header(sock):
    packets = [
        '1f1138',
        '1f11121f1113',
        '1f1109',
        '1f1111',
        '1f1119',
        '1f1107',
        '1f110a1f110202'
    ]
    for packet in packets:
        sock.send(bytes.fromhex(packet))

def print_image(sock, filename):
    width = 96
    with PILImage.open(filename) as src:
        image = image_helper.preprocess_image(src, width)
    output = '1f1124001b401d7630000c004001'
    for chunk in image_helper.split_image(image):
        output_bytes = bytearray.fromhex(output)
        bits = image_helper.image_to_bits(chunk)
        for line in bits:
            for byte_num in range(width // 8):
                byte = 0
                for bit in range(8):
                    pixel = line[byte_num * 8 + bit]
                    byte |= (pixel & 0x01) << (7 - bit)
                output_bytes.append(byte)
        sock.send(output_bytes)

CONFIG_FILE = "label_printer_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# --- GUI ---
class LabelPrinterGUI:
    def __init__(self, root):
        config = load_config()
        self.root = root
        root.title("Phomemo D30 Label Printer")
        self.font_path = tk.StringVar(value=config.get("font_path", "Helvetica"))
        self.font_size = tk.IntVar(value=config.get("font_size", 44))
        self.text = tk.StringVar()
        self.device_mac = tk.StringVar(value=config.get("device_mac", ""))
        self.adapter_mac = tk.StringVar(value=config.get("adapter_mac", ""))
        self.fruit = tk.BooleanVar(value=config.get("fruit", False))
        self.preview_img = None
        # Get system fonts, filter out invalid ones
        self.font_files = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
        self.font_names = []
        self.font_map = {}
        for f in self.font_files:
            try:
                name = font_manager.FontProperties(fname=f).get_name()
                self.font_names.append(name)
                self.font_map[name] = f
            except Exception:
                continue
        # Layout
        frm = ttk.Frame(root, padding=10)
        frm.grid()
        ttk.Label(frm, text="Label Text:").grid(row=0, column=0, sticky="e")
        text_entry = ttk.Entry(frm, textvariable=self.text, width=30)
        text_entry.grid(row=0, column=1, columnspan=2, sticky="we")
        text_entry.bind('<Return>', lambda event: self.preview_label())
        text_entry.bind('<KeyRelease>', lambda event: self.preview_label())
        ttk.Label(frm, text="Font Name:").grid(row=1, column=0, sticky="e")
        self.font_combo = ttk.Combobox(frm, values=self.font_names, state="readonly")
        self.font_combo.grid(row=1, column=1, sticky="we")
        self.font_combo.bind('<<ComboboxSelected>>', self.on_font_selected)
        # Set initial font selection if possible
        if self.font_names:
            initial_font = font_manager.FontProperties(fname=self.font_path.get()).get_name() if os.path.exists(self.font_path.get()) else self.font_names[0]
            self.font_combo.set(initial_font)
            self.font_path.set(self.font_map.get(initial_font, self.font_files[0]))
        ttk.Button(frm, text="Browse", command=self.browse_font).grid(row=1, column=2)
        ttk.Label(frm, text="Font Size:").grid(row=2, column=0, sticky="e")
        font_size_spin = tk.Spinbox(frm, from_=1, to=100, textvariable=self.font_size, width=5, command=self.preview_label)
        font_size_spin.grid(row=2, column=1, sticky="w")
        font_size_spin.bind('<KeyRelease>', lambda event: self.preview_label())
        font_size_spin.bind('<FocusOut>', lambda event: self.preview_label())
        ttk.Checkbutton(frm, text="Fruit Label", variable=self.fruit).grid(row=2, column=2, sticky="w")
        ttk.Label(frm, text="Device MAC:").grid(row=3, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.device_mac, width=20).grid(row=3, column=1, sticky="we")
        ttk.Label(frm, text="Adapter MAC:").grid(row=4, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.adapter_mac, width=20).grid(row=4, column=1, sticky="we")
        ttk.Button(frm, text="Print", command=self.print_label).grid(row=5, column=0, pady=10)
        self.preview_label_widget = ttk.Label(frm)
        self.preview_label_widget.grid(row=6, column=0, columnspan=3, pady=10)
        # Save config when settings change
        self.font_path.trace_add('write', lambda *args: self.save_settings())
        self.font_size.trace_add('write', lambda *args: self.save_settings())
        self.device_mac.trace_add('write', lambda *args: self.save_settings())
        self.adapter_mac.trace_add('write', lambda *args: self.save_settings())
        self.fruit.trace_add('write', lambda *args: self.save_settings())
    def browse_font(self):
        path = filedialog.askopenfilename(filetypes=[("Font files", "*.ttf;*.otf"), ("All files", "*")])
        if path:
            self.font_path.set(path)
    def preview_label(self):
        try:
            filename = "temp_preview.png"
            generate_image(self.text.get(), self.font_path.get(), self.font_size.get(), self.fruit.get(), filename, preview=True)
            img = PILImage.open(filename)
            img.thumbnail((320, 320))
            self.preview_img = ImageTk.PhotoImage(img)
            self.preview_label_widget.config(image=self.preview_img)
            os.remove(filename)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))
    def print_label(self):
        try:
            filename = "temp_print.png"
            generate_image(self.text.get(), self.font_path.get(), self.font_size.get(), self.fruit.get(), filename, preview=False)
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.bind((self.adapter_mac.get(), 1))
            sock.connect((self.device_mac.get(), 1))
            header(sock)
            print_image(sock, filename)
            sock.close()
            os.remove(filename)
            messagebox.showinfo("Success", "Label sent to printer!")
        except Exception as e:
            messagebox.showerror("Print Error", str(e))
    def save_settings(self):
        config = {
            "font_path": self.font_path.get(),
            "font_size": self.font_size.get(),
            "device_mac": self.device_mac.get(),
            "adapter_mac": self.adapter_mac.get(),
            "fruit": self.fruit.get()
        }
        save_config(config)
    def on_font_selected(self, event):
        selected_font = self.font_combo.get()
        self.font_path.set(self.font_map[selected_font])
        self.preview_label()

def main():
    root = tk.Tk()
    app = LabelPrinterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
