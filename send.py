import os
import time
import argparse
from typing import List

import can


def parse_can_message(line: str) -> can.Message:
    """
    Parses a single line from a file representing a CAN message.

    Args:
        line: A string representing a CAN message in the format "ID DATA".

    Returns:
        A `can.Message` object with the parsed arbitration ID and data bytes.

    Note:
        The arbitration ID is assumed to be the first two characters of the ID,
        converted from hexadecimal. The data is assumed to be hexadecimal bytes,
        where the first part of the data is directly following the ID in the
        same string, and additional data parts are separated by spaces.
    """
    parts = line.split(" ")
    arbitration_id = int(parts[0][:2], 16)
    data = [int(parts[0][i : i + 2], 16) for i in range(2, len(parts[0]), 2)] + [
        int(byte, 16) for byte in parts[1:]
    ]
    return can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)


def calculate_crc(arbitration_id: int, status: int) -> int:
    """
    Calculates a simple CRC value based on the arbitration ID and status.

    Args:
        arbitration_id: The arbitration ID of the CAN message.
        status: An arbitrary status value.

    Returns:
        An integer representing the calculated CRC value.
    """
    return (arbitration_id + 0xF4 + status) & 0xFF


def adjust_speeds_within_packet(messages: List[can.Message]) -> None:
    """
    Adjusts the speeds within a packet of CAN messages based on the average speed.

    Args:
        messages: A list of `can.Message` objects, each representing a CAN message.

    Note:
        This function directly modifies the `data` attribute of each `can.Message`
        object in the list to adjust the speed values.
    """
    speeds = [(msg.data[3] << 8) + msg.data[4] for msg in messages]
    reference_speed = sum(speeds) // len(speeds)
    if reference_speed == 0:
        return
    for msg in messages:
        speed = (msg.data[3] << 8) + msg.data[4]
        adjusted_speed = int((speed / reference_speed) * reference_speed)
        msg.data[3] = (adjusted_speed >> 8) & 0xFF
        msg.data[4] = adjusted_speed & 0xFF


def can_send_messages(bus: can.interface.Bus, messages: List[can.Message], recv_timeout: int = 3) -> None:
    """
    Sends a list of CAN messages through a specified CAN bus and waits for responses.

    Args:
        bus: The `can.interface.Bus` instance representing the CAN bus to send messages on.
        messages: A list of `can.Message` objects to be sent.

    Note:
        This function waits for responses from expected motors after sending messages
        and prints out the status of the sent and received messages.
    """
    expected_responses = {1, 2}
    received_responses = set()
    for msg in messages:
        bus.send(msg)
        data_bytes = ", ".join([f"0x{byte:02X}" for byte in msg.data])
        print(
            f"Sent: arbitration_id=0x{msg.arbitration_id:X}, data=[{data_bytes}], is_extended_id=False"
        )
    timeout = recv_timeout
    start_time = time.time()
    while True:
        received_msg = bus.recv(timeout=recv_timeout)
        if received_msg is not None:
            received_data_bytes = ", ".join(
                [f"0x{byte:02X}" for byte in received_msg.data]
            )
            print(
                f"Received: arbitration_id=0x{received_msg.arbitration_id:X}, data=[{received_data_bytes}], is_extended_id=False"
            )
            if received_msg.data[1] in expected_responses:
                received_responses.add(received_msg.arbitration_id)
        if received_responses == expected_responses:
            if all(
                received_msg.data[1] == 2 if received_msg is not None else False
                for received_msg in [bus.recv(timeout=recv_timeout)] * len(expected_responses)
            ):
                print(
                    "Responses received for all expected motors with status 2. Moving to the next set of messages."
                )
                break
        if time.time() - start_time > timeout:
            print("Timeout waiting for responses from expected motors with status 2.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send CAN messages from a .can file through a CAN bus.")
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="The .can file containing CAN messages to send.",
    )
    parser.add_argument(
        "-d",
        "--device",
        type=str,
        default="/dev/ttyACM0",
        help="The CAN bus device to send messages through.",
    )
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        default="slcan",
        help="The type of CAN bus to use for sending messages.",
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=500000,
        help="The bitrate of the CAN bus in bits per second.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="The timeout value in seconds for waiting for responses.",
    )
    parser.add_argument(
        "--virtual",
        action="store_true",
        help="Use a virtual CAN interface instead of a physical one."
    )
    args = parser.parse_args()
    if args.file:
        if args.virtual:
            args.interface = "virtual"
        with can.interface.Bus(interface=args.interface, channel=args.device, bitrate=args.bitrate) as bus:
            with open(args.file, "r") as file:
                lines = file.readlines()
            # Split the lines into sets of 6 lines each representing a message
            message_sets = [lines[i : i + 6] for i in range(0, len(lines), 6)]
            # Parse each message set and send the messages
            for message in message_sets:
                messages = [parse_can_message(line.strip()) for line in message]
                adjust_speeds_within_packet(messages)
                can_send_messages(bus, messages, recv_timeout=args.timeout)
    else:
        print("Please specify a .can file to send messages from.")