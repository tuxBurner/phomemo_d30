# phomemo_d30
Python script to print text on a Phomemo D30 label printer

# Acknowledgements
Based on [phomemo_d30](https://github.com/polskafan/phomemo_d30) by polskafan and
Based on [phomemo-tools](https://github.com/vivier/phomemo-tools) by Laurent Vivier and
[phomemo_m02s](https://github.com/theacodes/phomemo_m02s) by theacodes.

# Example
<a href="http://www.youtube.com/watch?feature=player_embedded&v=U1ZqjYgFxjY
" target="_blank"><img src="http://img.youtube.com/vi/U1ZqjYgFxjY/maxresdefault.jpg" 
alt="Video example of the Python script" width="640" /></a>

# Checkout and install

```shell
git clone https://github.com/tuxBurner/phomemo_d30.git
cd phomemo_d30
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

# Usage
Connect to printer with bluetoothctl when not already done.

You can do this either via the bluetooth controll in gnome or via:

```shell
bluetoothctl
scan on
# wait a little bit and check for a line like:
[NEW] Device DA:EE:50:52:DC:30 D30
# get the mac of the printer from the line
pair DA:FF:50:52:DC:30 
```

If you already connected to the D30 printer get the mac like this:

```shell
bluetoothctl devices
# check for a line like:
Device DA:FF:50:52:DC:30 D30
```

You also need the mac address of the adapter of your computer:

```shell
bluetoothctl list
# check for a line like:
Controller D8:B3:2F:BE:C2:26 computer [default]
```


Basic usage
```shell
venv/bin/python print_text.py --adapterMac D8:B3:2F:BE:C2:26 --deviceMac DA:FF:50:52:DC:30 "Hello World!"
```

Print on "fruit" labels
```bash
venv/bin/python print_text.py --adapterMac D8:B3:2F:BE:C2:26 --deviceMac DA:FF:50:52:DC:30 --fruit "This is a fruit label."
```

Change font
```bash
venv/bin/python print_text.py --adapterMac D8:B3:2F:BE:C2:26 --deviceMac DA:FF:50:52:DC:30 --font Arial.ttf "Hello World!"
```

Multiline Labels
```bash
venv/bin/python print_text.py --adapterMac D8:B3:2F:BE:C2:26 --deviceMac DA:FF:50:52:DC:30 "First line\nSecond line"
```

## Reverse engineering steps
We are sniffing the Bluetooth initialization from "Printer Master" with Android bluetooth debugging and Wireshark (see https://www.wireshark.org/docs/man-pages/androiddump.html). tl;dr: If debugging is enabled in developer options and the phone is connected via ADB, Wireshark will display the bluetooth interface to create a capture file.

Looking at the pcap file, the printer seems to use the ESC/POS protocol by Epson. The init string that is sent right before the image data contains the paper size:
```1f1124001b401d7630000c004001```
(see [theacodes/phomemo_m02s/printer.py](https://github.com/theacodes/phomemo_m02s/blob/main/phomemo_m02s/printer.py))

```
Control Code: 1d
Page Init: 7630
Mode: 00
Paper Width: 0c00 =(Little Endian)=> 0xC =(hex2bin)=> 12 (=> 12 byte * 8 bit = 96 pixel)
Paper Height: 4001 =(Little Endian)=> 0x140 =(hex2bin)=> 320 pixel
```

Therefore the picture size is 320x96 (note: The picture is rotated by 90 degrees before printing).
