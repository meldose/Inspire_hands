import time
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ExceptionResponse

# Modbus TCP connection settings
MODBUS_IP = "192.168.11.210"
MODBUS_PORT = 6000

# Register ranges for each touch sensor area
TOUCH_SENSOR_BASE_ADDR_PINKY = 3000  # Pinky
TOUCH_SENSOR_END_ADDR_PINKY = 3369

TOUCH_SENSOR_BASE_ADDR_RING = 3370  # Ring finger
TOUCH_SENSOR_END_ADDR_RING = 3739

TOUCH_SENSOR_BASE_ADDR_MIDDLE = 3740  # Middle finger
TOUCH_SENSOR_END_ADDR_MIDDLE = 4109

TOUCH_SENSOR_BASE_ADDR_INDEX = 4110  # Index finger
TOUCH_SENSOR_END_ADDR_INDEX = 4479

TOUCH_SENSOR_BASE_ADDR_THUMB = 4480  # Thumb
TOUCH_SENSOR_END_ADDR_THUMB = 4899

TOUCH_SENSOR_BASE_ADDR_PALM = 4900  # Palm
TOUCH_SENSOR_END_ADDR_PALM = 5123

# Maximum number of registers to read per Modbus request
MAX_REGISTERS_PER_READ = 125


def read_register_range(client, start_addr, end_addr):
    """
    Read a continuous register range in batches.
    """
    register_values = []
    # Read the range in chunks
    for addr in range(start_addr, end_addr + 1, MAX_REGISTERS_PER_READ * 2):
        current_count = min(MAX_REGISTERS_PER_READ, (end_addr - addr) // 2 + 1)
        response = client.read_holding_registers(address=addr, count=current_count)

        if isinstance(response, ExceptionResponse) or response.isError():
            print(f"Failed to read register {addr}: {response}")
            register_values.extend([0] * current_count)
        else:
            register_values.extend(response.registers)

    return register_values

def format_finger_data(finger_name, data):
    """
    Format tactile data for a finger into structured matrices.
    """
    result = {}

    if finger_name != "Thumb":
        # Layout used by the four non-thumb fingers
        if len(data) < 185:
            print(f"{finger_name} data length is insufficient, expected at least 185 values, actual: {len(data)}")
            return None

        idx = 0
        # Fingertip end data, 3x3
        result['tip_end'] = [data[idx + i*3: idx + (i+1)*3] for i in range(3)]
        idx += 9

        # Fingertip tactile data, 12x8
        result['tip_touch'] = [data[idx + i*8: idx + (i+1)*8] for i in range(12)]
        idx += 96

        # Finger pad tactile data
        result['finger_pad'] = [data[idx + i*8: idx + (i+1)*8] for i in range(12)]
        idx += 80
    else:
        # Layout used by the thumb
        if len(data) < 210:
            print(f"{finger_name} data length is insufficient, expected at least 210 values, actual: {len(data)}")
            return None

        idx = 0
        # Fingertip end data, 3x3
        result['tip_end'] = [data[idx + i*3: idx + (i+1)*3] for i in range(3)]
        idx += 9

        # Fingertip tactile data, 12x8
        result['tip_touch'] = [data[idx + i*8: idx + (i+1)*8] for i in range(12)]
        idx += 96

        # Mid-finger tactile data, 3x3
        result['middle_touch'] = [data[idx + i*3: idx + (i+1)*3] for i in range(3)]
        idx += 9

        # Finger pad tactile data, 12x8
        finger_pad = [data[idx + i*8: idx + (i+1)*8] for i in range(12)]
        idx += 96

        # Reverse elements within each finger-pad row
        finger_pad = [row[::-1] for row in finger_pad]
        # Reverse the order of the finger-pad rows
        finger_pad.reverse()

        result['finger_pad'] = finger_pad

    return result

def format_palm_data(data):
    """
    Format palm data as a 14x8 matrix and transpose it to 8x14.
    """
    expected_len = 14 * 8
    if len(data) < expected_len:
        print(f"Palm data length is insufficient, expected at least {expected_len} values, actual: {len(data)}")
        return None

    # Build the original 14x8 matrix
    palm_matrix = [data[i*8:(i+1)*8] for i in range(14)]

    # Transpose the matrix
    transposed = list(map(list, zip(*palm_matrix)))

    return transposed


def print_formatted_finger_data(finger_name, formatted_data):
    if formatted_data is None:
        print(f"{finger_name} data formatting failed")
        return

    print(f"--- {finger_name} fingertip end data (3x3) ---")
    for row in formatted_data.get('tip_end', []):
        print(row)

    print(f"--- {finger_name} fingertip tactile data (12x8) ---")
    for row in formatted_data.get('tip_touch', []):
        print(row)

    if finger_name == "Thumb":
        if 'middle_touch' in formatted_data:
            print(f"--- {finger_name} middle tactile data (3x3) ---")
            for row in formatted_data['middle_touch']:
                print(row)
        else:
            print(f"{finger_name} middle tactile data is missing")

    print(f"--- {finger_name} finger pad tactile data ({'12x8' if finger_name == 'Thumb' else '10x8'}) ---")
    for row in formatted_data.get('finger_pad', []):
        print(row)

def print_formatted_palm_data(palm_data):
    if palm_data is None:
        print("Palm data formatting failed")
        return

    print("--- Palm data (8x14) ---")
    for row in palm_data:
        print(row)


def read_multiple_registers():
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)
    client.connect()

    try:
        while True:
            start_time = time.time()

            # Read each touch-sensor region
            pinky_register_values = read_register_range(
                client,
                TOUCH_SENSOR_BASE_ADDR_PINKY,
                TOUCH_SENSOR_END_ADDR_PINKY
            )
            ring_register_values = read_register_range(
                client,
                TOUCH_SENSOR_BASE_ADDR_RING,
                TOUCH_SENSOR_END_ADDR_RING
            )
            middle_register_values = read_register_range(
                client,
                TOUCH_SENSOR_BASE_ADDR_MIDDLE,
                TOUCH_SENSOR_END_ADDR_MIDDLE
            )
            index_register_values = read_register_range(
                client,
                TOUCH_SENSOR_BASE_ADDR_INDEX,
                TOUCH_SENSOR_END_ADDR_INDEX
            )
            thumb_register_values = read_register_range(
                client,
                TOUCH_SENSOR_BASE_ADDR_THUMB,
                TOUCH_SENSOR_END_ADDR_THUMB
            )
            palm_register_values = read_register_range(
                client,
                TOUCH_SENSOR_BASE_ADDR_PALM,
                TOUCH_SENSOR_END_ADDR_PALM
            )

            end_time = time.time()
            frequency = 1 / (end_time - start_time) if end_time > start_time else float('inf')

            # Format the raw register values
            pinky_formatted = format_finger_data("Pinky", pinky_register_values)
            ring_formatted = format_finger_data("Ring", ring_register_values)
            middle_formatted = format_finger_data("Middle", middle_register_values)
            index_formatted = format_finger_data("Index", index_register_values)
            thumb_formatted = format_finger_data("Thumb", thumb_register_values)
            palm_formatted = format_palm_data(palm_register_values)

            # Print the formatted data
            print_formatted_finger_data("Pinky", pinky_formatted)
            print_formatted_finger_data("Ring", ring_formatted)
            print_formatted_finger_data("Middle", middle_formatted)
            print_formatted_finger_data("Index", index_formatted)
            print_formatted_finger_data("Thumb", thumb_formatted)
            print_formatted_palm_data(palm_formatted)

            print(f"Read frequency: {frequency:.2f} Hz")
            print("\n" + "="*40 + "\n")

    finally:
        client.close()


if __name__ == "__main__":
    read_multiple_registers()
