
# G-code to CAN BUS Converter

Watch the demo: https://www.youtube.com/watch?v=CeugYSGpj0s

These two files convert G-code to CAN BUS messages, supporting 6 axis style G-code for: X, Y, Z, A, B, and C axes.

## Prerequisites
Before using these scripts, ensure you have the following dependencies installed:
- Python 3
- python-can library (`pip install python-can[serial]`)
- ttkthemes library (`pip install ttkthemes`)

G-code is converted to follow Makerbase CAN bus message format:

### CAN Message Structure

```
ID + Mode + Speed + Acceleration + Position + CRC
```

- **ID:** Configured from ID 01 to ID 06
- **Mode:** F5 for absolute axis
- **Speed:** Taken from Feedrate in G-code
- **Acceleration:** Configured as 02 (default)
- **Position:** Converted from G-code
- **CRC:** Cyclic Redundancy Check calculated by the formula: CRC = (ID + Mode + Speed + Acceleration + Position) & 0xFF

To change the gear ratio on each axis, modify the following line in `convert.py` script:

```python
gear_ratios = [0.5, 0.5, 1, 1, 1, 1]
```

## Usage

### Convert G-code to CAN messages

`convert.py` converts a G-code file in `.gcode` format and creates a corresponding `.can` file containing CAN messages.

You can convert all gcode files in a folder by running the following command:

```bash
$ python convert.py -h
usage: convert.py [-h] [-d DIRECTORY] [-f FILE] [-o OUTPUT]

Convert gcode files to CAN messages.

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        Directory containing the gcode files to convert.
  -f FILE, --file FILE  Single gcode file to convert.
  -o OUTPUT, --output OUTPUT
                        Output directory for the converted files.
```

#### Convert all files in a directory

```bash
python convert.py -d examples/ -o examples/can
```

#### Convert a single file

```bash
python convert.py -f examples/move_a.gcode -o examples/can
```

### Send CAN messages

`send.py` streams CAN messages to the Canable adapter.

```bash
$ python send.py -h
usage: send.py [-h] [-f FILE] [-d DEVICE] [-i INTERFACE] [--bitrate BITRATE] [--timeout TIMEOUT] [--virtual]

Send CAN messages from a .can file through a CAN bus.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  The .can file containing CAN messages to send.
  -d DEVICE, --device DEVICE
                        The CAN bus device to send messages through.
  -i INTERFACE, --interface INTERFACE
                        The type of CAN bus to use for sending messages.
  --bitrate BITRATE     The bitrate of the CAN bus in bits per second.
  --timeout TIMEOUT     The timeout value in seconds for waiting for responses.
  --virtual             Use a virtual CAN interface instead of a physical one.
```

#### Send CAN messages

You can send CAN messages to a physical or virtual CAN bus by running the following command:

```python
python send.py -f examples/can/move_b.can -d /dev/tty.usbmodem --timeout 5
```

## GUI Application
A GUI application is provided for easier control and interaction with the scripts. It includes features such as selecting ports, connecting/disconnecting, sending files, and displaying messages.

### Features
- Refresh Ports: Updates the list of available serial ports.
- Connect: Connects to the selected port for communication.
- Disconnect: Disconnects from the currently connected port.
- Send: Initiates sending of CAN messages.
- Convert: Converts a G-code file to CAN messages.
- Stop: Placeholder button for stopping logic.
- Browse: Opens a file dialog to select files for conversion or sending.
- Clear Messages: Clears the message display area.
- Messages Display: Shows status messages and sent/received messages.
- Field Displays: Shows converted values for each axis (X, Y, Z, A, B, C).
Feel free to adapt and use these scripts for your robotic arm!


