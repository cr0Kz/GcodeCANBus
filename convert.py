import os
import re
from typing import List
import argparse

# Parameters Section
# -------------------

# Gearbox ratios for each motor
gear_ratios: List[float] = [
    13.5,
    150,
    150,
    48,
    67.82,
    67.82
]  # Replace with your actual gearbox ratios

# Direction inversion for each motor (True/False)
invert_direction: List[bool] = [
    True,
    True,
    False,
    False,
    False,
    False,
]  # Set True for motors where direction should be inverted

# Initialize zero positions and last positions
initial_positions: List[int] = [0] * 6
last_positions: List[float] = [0] * 6

# -------------------


def calculate_crc(data: List[int]) -> int:
    """
    Calculates a simple CRC (Cyclic Redundancy Check) value for a list of integers.

    Args:
        data: A list of integers representing the data to calculate the CRC for.

    Returns:
        An integer representing the calculated CRC value.
    """
    crc = sum(data) & 0xFF
    return crc


def convert_to_can_message(
    axis_id: int,
    speed: int,
    position: float,
    gear_ratio: float,
    invert_direction: bool = False,
) -> str:
    """
    Converts motion parameters into a CAN message string.

    TODO: #1 invert_direction is not used in this function. Implement the logic to invert the direction of the motor axis.

    Args:
        axis_id: The ID of the motor axis.
        speed: The speed for the motor axis.
        position: The target position for the motor axis.
        gear_ratio: The gear ratio for the motor axis.
        invert_direction: If True, the direction of the motor axis is inverted.

    Returns:
        A string representing the CAN message.
    """
    can_id = format(axis_id, "02X")
    speed_hex = format(speed, "04X")

    # Calculate relative position based on the initial position
    rel_position = int((position * gear_ratio - initial_positions[axis_id - 1]) * 100)

    # Handle signed 24-bit integer using two's complement representation
    rel_position_hex = format(rel_position & 0xFFFFFF, "06X")

    # Update last_position for the axis
    last_positions[axis_id - 1] = position * gear_ratio

    return can_id + "F5" + speed_hex + "02" + rel_position_hex

def process_gcode_file(file: str, output_directory: str = None) -> None:
    """
    Processes a single .gcode file, converting it into a .can file containing CAN messages.

    Args:
        file: The .gcode file to process.
        output_directory: The directory to save the converted .can file. If None, the .can file is saved in the same directory as the input file.

    Note:
        The function reads each line from the .gcode file, extracts the motion parameters,
        and converts them into CAN messages. The CAN messages are then written to a .can file.
    """
    input_filename = file
    output_filename = os.path.splitext(file)[0] + ".can"

    if output_directory:
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_filename = os.path.join(output_directory, os.path.basename(output_filename))

    with open(input_filename, "r") as input_file, open(
        output_filename, "w"
    ) as output_file:
        speed = 0

        try: 
            for line in input_file:
                speed_match = re.search(r"F(\d+)", line)
                if speed_match:
                    try:
                        speed = int(speed_match.group(1))
                    except ValueError:
                        continue

                if line.startswith("G90"):
                    values = [
                        float(value) if "." in value else int(value)
                        for value in re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)
                    ]

                    if len(values) >= 7:
                        for axis_id, position in enumerate(values[1:7], start=1):
                            # Use the corresponding gear ratio for each motor
                            gear_ratio = gear_ratios[axis_id - 1]
                            invert_dir = invert_direction[axis_id - 1]
                            can_message = convert_to_can_message(
                                axis_id, speed, position, gear_ratio, invert_dir
                            )
                            crc = calculate_crc(
                                [
                                    int(can_message[i : i + 2], 16)
                                    for i in range(0, len(can_message), 2)
                                ]
                            )
                            can_message_with_crc = can_message + format(crc, "02X")
                            output_file.write(can_message_with_crc + "\n")
            
            print(f"Successfully converted {input_filename} to {output_filename}.")
        except Exception as e:
            print(f"An error occurred while processing {input_filename}: {e}")
            return

def process_gcode_directory(directory: str, output_directory: str = None) -> None:
    """
    Processes all .gcode files in the script directory, converting them into .can files containing CAN messages.

    Args:
        directory: The directory containing the .gcode files to process.
        output_directory: The directory to save the converted .can files. If None, the .can files are saved in the same directory as the input files.

    Note:
        The function reads each line from the .gcode file, extracts the motion parameters,
        and converts them into CAN messages. The CAN messages are then written to a .can file.
    """
    
    try:
        for filename in os.listdir(directory):
            if filename.endswith(".gcode"):
                process_gcode_file(os.path.join(directory, filename), output_directory)
    except FileNotFoundError:
        print(f"Directory {directory} not found.")
        return
    
    print("Conversion completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert gcode files to CAN messages.')
    parser.add_argument('-d', '--directory' ,type=str, help='Directory containing the gcode files to convert.')
    parser.add_argument('-f', '--file' ,type=str, help='Single gcode file to convert.')
    parser.add_argument('-o', '--output', type=str, help='Output directory for the converted files.')
    args = parser.parse_args()

    if args.file:
        process_gcode_file(args.file, args.output)
    elif args.directory:
        process_gcode_directory(args.directory, args.output)