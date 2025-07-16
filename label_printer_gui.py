import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import ImageTk, Image as PILImage
import os
import socket
import image_helper
from wand.image import Image
from wand.font import Font

# --- Helper functions (adapted from your script) ---
def generate_image(text, font, fontsize, fruit, filename):
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

# --- GUI ---
class LabelPrinterGUI:
    def __init__(self, root):
        self.root = root
        root.title("Phomemo D30 Label Printer")
        self.font_path = tk.StringVar(value="Helvetica")
        self.font_size = tk.IntVar(value=44)
        self.text = tk.StringVar()
        self.device_mac = tk.StringVar()
        self.adapter_mac = tk.StringVar()
        self.fruit = tk.BooleanVar()
        self.preview_img = None
        # Layout
        frm = ttk.Frame(root, padding=10)
        frm.grid()
        ttk.Label(frm, text="Label Text:").grid(row=0, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.text, width=30).grid(row=0, column=1, columnspan=2, sticky="we")
        ttk.Label(frm, text="Font Path:").grid(row=1, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.font_path, width=20).grid(row=1, column=1, sticky="we")
        ttk.Button(frm, text="Browse", command=self.browse_font).grid(row=1, column=2)
        ttk.Label(frm, text="Font Size:").grid(row=2, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.font_size, width=5).grid(row=2, column=1, sticky="w")
        ttk.Checkbutton(frm, text="Fruit Label", variable=self.fruit).grid(row=2, column=2, sticky="w")
        ttk.Label(frm, text="Device MAC:").grid(row=3, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.device_mac, width=20).grid(row=3, column=1, sticky="we")
        ttk.Label(frm, text="Adapter MAC:").grid(row=4, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.adapter_mac, width=20).grid(row=4, column=1, sticky="we")
        ttk.Button(frm, text="Preview", command=self.preview_label).grid(row=5, column=0, pady=10)
        ttk.Button(frm, text="Print", command=self.print_label).grid(row=5, column=1, pady=10)
        self.preview_label_widget = ttk.Label(frm)
        self.preview_label_widget.grid(row=6, column=0, columnspan=3, pady=10)
    def browse_font(self):
        path = filedialog.askopenfilename(filetypes=[("Font files", "*.ttf;*.otf"), ("All files", "*")])
        if path:
            self.font_path.set(path)
    def preview_label(self):
        try:
            filename = "temp_preview.png"
            generate_image(self.text.get(), self.font_path.get(), self.font_size.get(), self.fruit.get(), filename)
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
            generate_image(self.text.get(), self.font_path.get(), self.font_size.get(), self.fruit.get(), filename)
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

def main():
    root = tk.Tk()
    app = LabelPrinterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
