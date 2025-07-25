import click
import serial
from wand.image import Image
from wand.font import Font
import PIL.Image
import image_helper
import os
import socket


@click.command()
@click.argument('text')
@click.option('--deviceMac',  help='Printer Bluetooth device MAC address get it with: bluetoothctl devices')
@click.option('--adapterMac', help='Bluetooth adapter MAC address get it with: bluetoothctl list')
@click.option('--font', default="Helvetica", help='Path to TTF font file')
@click.option('--fontSize', default=44, help='Size of the font in pixels')
@click.option('--print', is_flag=True, show_default=True, default=False, help='Print the label on the printer')
@click.option('--fruit', is_flag=True, show_default=True, default=False, help='Enable offsets to print on a fruit label')
def main(text, devicemac, adaptermac, font, fontsize, print, fruit):

    if(devicemac is None and print):
        raise click.UsageError('You must specify --deviceMac')

    if(adaptermac is None and print):
        raise click.UsageError('You must specify --adapterMac')        

    filename = generate_image(text, font, fontsize, fruit, "temp.png")

    if(print):
        # connect to printer via Bluetooth
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.bind((adaptermac, 1))
        sock.connect((devicemac, 1))
        header(sock)
        print_image(sock, filename)
        os.remove(filename)
        sock.close()
    #else:
    #    print(f"Image saved to {filename}")    

def header(sock):
    # printer initialization sniffed from Android app "Print Master"
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


def generate_image(text, font, fontsize, fruit, filename):
    font = Font(path=font, size=fontsize, color="black")
    
    if fruit:
        width, height = 240, 80
    else:
        width, height = 288, 88

    with Image(width=width, height=height, background="white") as img:
        # center text, fill canvas
        img.caption(text, font=font, gravity="center")

        # extent and rotate image
        img.background_color = "white"
        img.gravity = "center"
        if fruit:
            img.extent(width=320, height=96, x=-60)
        else:
            img.extent(width=320, height=96)
        img.rotate(270)
        img.save(filename=filename)

    return filename


def print_image(sock, filename):
    width = 96

    with PIL.Image.open(filename) as src:
        image = image_helper.preprocess_image(src, width)

    # printer initialization sniffed from Android app "Print Master"
    output = '1f1124001b401d7630000c004001'

    # adapted from https://github.com/theacodes/phomemo_m02s/blob/main/phomemo_m02s/printer.py
    for chunk in image_helper.split_image(image):
        output = bytearray.fromhex(output)

        bits = image_helper.image_to_bits(chunk)
        for line in bits:
            for byte_num in range(width // 8):
                byte = 0
                for bit in range(8):
                    pixel = line[byte_num * 8 + bit]
                    byte |= (pixel & 0x01) << (7 - bit)
                output.append(byte)

        sock.send(output)
        
        output = ''


if __name__ == '__main__':
    main()
