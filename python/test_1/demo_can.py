import serial
import time

# Register map
regdict = {
    'ID': 1000,
    'baudrate': 1001,
    'clearErr': 1004,
    'forceClb': 1009,
    'angleSet': 1486,
    'forceSet': 1498,
    'speedSet': 1522,  
    'angleAct': 1546,
    'forceAct': 1582,
    'errCode': 1606,
    'statusCode': 1612,
    'temp': 1618,
    'actionSeq': 2320,
    'actionRun': 2322
}

def init_serial(port='/dev/ttyUSB0', baudrate=115200):
    """Initialize the serial connection."""
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Serial port {port} opened")
        return ser
    except Exception as e:
        print(f"Failed to open serial port: {e}")
        return None

def convert_address_to_binary_write(address_dec, id_value):
    """Convert a decimal address to the binary format used by write frames."""
    address_bin = bin(address_dec)[2:]  
    id_bin = bin(int(id_value, 2))[2:].zfill(14) 
    formatted_output = f"0000010{address_bin}{id_bin}"  # The sixth prefix bit marks a write request
    return formatted_output

def convert_address_to_binary_read(address_dec, id_value):
    """Convert a decimal address to the binary format used by read frames."""
    address_bin = bin(address_dec)[2:]  
    id_bin = bin(int(id_value, 2))[2:].zfill(14) 
    formatted_output = f"0000000{address_bin}{id_bin}"  # The sixth prefix bit marks a read request
    return formatted_output

def binary_to_hex(binary_string):
    """Convert a binary string to hexadecimal."""
    decimal_value = int(binary_string, 2)
    return hex(decimal_value)[2:].upper()

def convert_number_to_bytes(number):
    """Convert an integer into a byte array."""
    hex_string = hex(number)[2:].upper()  
    if len(hex_string) % 2 != 0:
        hex_string = '0' + hex_string  
    byte_array = [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)][::-1]
    return byte_array

def send_command(ser, reg_name, values, id_value):
    """Send a control command."""
    if reg_name in ['angleSet', 'forceSet', 'speedSet']:
        val_reg = [val & 0xFFFF for val in values]  
        write_register(ser, regdict[reg_name], val_reg, id_value)
    else:
        print("Function call error. Expected: str = 'angleSet'/'forceSet'/'speedSet', val = list of length 6, values in 0-1000, and -1 may be used as a placeholder")

def write_register(ser, address, values, id_value):
    """Build and send a write-register frame."""
    while True:
        chunk = values[:4]  # Use the first four values in the first frame
        values = values[4:]

        # Encode the address using the write-frame format
        ext_id_bin = convert_address_to_binary_write(address, id_value)
        ext_id_hex = binary_to_hex(ext_id_bin)
        print(f"Computed extended identifier: {ext_id_hex}")

        ext_id_number = int(ext_id_hex, 16)
        ext_id_bytes = convert_number_to_bytes(ext_id_number)

        print("Extracted extended identifier bytes:")
        for byte in ext_id_bytes:
            print(f"Byte: {byte:02X}")

        send_buffer = bytearray()
        send_buffer += bytes([0xAA, 0xAA])
        send_buffer.extend(ext_id_bytes)

        # Append register values
        for value in chunk:
            send_buffer.append(value & 0xFF)
            send_buffer.append(value >> 8)

        # Add padding if the payload is shorter than eight bytes
        data_length = len(chunk) * 2
        if data_length < 8:
            padding_length = 8 - data_length
            send_buffer.extend([0xFF] * padding_length)

        # Append the payload length and fixed trailer bytes
        send_buffer.append(len(chunk) * 2 + (padding_length if data_length < 8 else 0))  # Payload length
        send_buffer.append(0x00)
        send_buffer.append(0x01)
        send_buffer.append(0x00)

        # Compute checksum
        check_sum = sum(send_buffer[2:]) & 0xFF
        send_buffer.append(check_sum)
        send_buffer += bytes([0x55, 0x55])

        ser.write(send_buffer)
        print("Sent command:", send_buffer.hex())
        ser.reset_input_buffer()  # Clear the input buffer
        break  # Only send the first chunk once here

    # Send the remaining values in the second frame
    new_address = address + 8
    print(f"New address (second half): {new_address}")

    ext_id_bin = convert_address_to_binary_write(new_address, id_value)
    ext_id_hex = binary_to_hex(ext_id_bin)
    print(f"Computed extended identifier (second half): {ext_id_hex}")

    ext_id_number = int(ext_id_hex, 16)
    ext_id_bytes = convert_number_to_bytes(ext_id_number)

    print("Extracted extended identifier bytes (second half):")
    for byte in ext_id_bytes:
        print(f"Byte: {byte:02X}")

    # Build the second frame with the shifted address bytes
    send_buffer = bytearray()
    send_buffer += bytes([0xAA, 0xAA])
    send_buffer.extend(ext_id_bytes)

    # Append the remaining values
    for value in values:
        send_buffer.append(value & 0xFF)
        send_buffer.append(value >> 8)

    # Add padding if the payload is shorter than eight bytes
    data_length = len(values) * 2
    if data_length < 8:
        padding_length = 8 - data_length
        send_buffer.extend([0xFF] * padding_length)

    # Append the payload length and fixed trailer bytes
    send_buffer.append(0x04)  # Payload length
    send_buffer.append(0x00)
    send_buffer.append(0x01)
    send_buffer.append(0x00)

    # Compute checksum
    check_sum = sum(send_buffer[2:]) & 0xFF
    send_buffer.append(check_sum)
    send_buffer += bytes([0x55, 0x55])

    ser.write(send_buffer)
    print("Sent command (second half):", send_buffer.hex())

def read_register(ser, address, id_value):
    """Build and send a read-register frame."""
    ext_id_bin = convert_address_to_binary_read(address, id_value)
    ext_id_hex = binary_to_hex(ext_id_bin)
    ext_id_number = int(ext_id_hex, 16)
    ext_id_bytes = convert_number_to_bytes(ext_id_number)

    send_buffer = bytearray()
    send_buffer += bytes([0xAA, 0xAA])
    send_buffer.extend(ext_id_bytes)

    # Append the fixed read command payload
    send_buffer.append(0x08)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x01)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    send_buffer.append(0x01)  # Fixed byte
    send_buffer.append(0x00)  # Fixed byte
    # Compute checksum
    check_sum = sum(send_buffer[2:]) & 0xFF
    send_buffer.append(check_sum)
    send_buffer += bytes([0x55, 0x55])

    ser.write(send_buffer)
    print("Sent read command:", send_buffer.hex())
    ser.reset_input_buffer()  # Clear the input buffer
    
    # Wait for the device response
    time.sleep(0.1)  # Give the device time to respond
    response1 = ser.read(23)  # Read the expected response length
    print("Read raw content:", response1.hex())  # Print the raw response in hex

    # Parse the response based on the register being read
    if address == regdict['temp']:
        # Parse the first response frame
        if len(response1) >= 1:
            # Extract bytes 7 through 12 from the first frame
            frame1_data = response1[6:12]  # Bytes 7 through 12

            # Decode the first frame payload
            values1 = []
            for i in range(0, len(frame1_data), 1):
                value = frame1_data[i]
                if value > 60000:
                    value = 0
                values1.append(value)
            print("Read data (temperature):", tuple(values1))  # Print temperature data
    else:
        # Parse the first response frame
        if len(response1) >= 1:
            # Extract bytes 7 through 14 from the first frame
            frame1_data = response1[6:14]  # Bytes 7 through 14

            # Decode the first frame payload
            values1 = []
            for i in range(0, len(frame1_data), 2):
                low_byte = frame1_data[i]      # Low byte
                high_byte = frame1_data[i + 1] # High byte
                value = (high_byte << 8) | low_byte  # Combine into a decimal value
                if value > 60000:
                    value = 0                
                values1.append(value)

        # Send the second read frame
        new_address = address + 8
        ext_id_bin = convert_address_to_binary_read(new_address, id_value)
        ext_id_hex = binary_to_hex(ext_id_bin)

        ext_id_number = int(ext_id_hex, 16)
        ext_id_bytes = convert_number_to_bytes(ext_id_number)

        # Build the second frame with the shifted address bytes
        send_buffer = bytearray()
        send_buffer += bytes([0xAA, 0xAA])
        send_buffer.extend(ext_id_bytes)

        # Append the fixed second-frame read payload
        send_buffer.append(0x04)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x01)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        send_buffer.append(0x01)  # Fixed byte
        send_buffer.append(0x00)  # Fixed byte
        # Compute checksum
        check_sum = sum(send_buffer[2:]) & 0xFF
        send_buffer.append(check_sum)
        send_buffer += bytes([0x55, 0x55])

        ser.write(send_buffer)
        print("Sent read command:", send_buffer.hex())
        ser.reset_input_buffer()  # Clear the input buffer
        
        # Wait for the device response
        time.sleep(0.1)  # Give the device time to respond
        response2 = ser.read(23)  # Read the expected response length
        print("Read raw content:", response2.hex())  # Print the raw response in hex

        # Parse the second response frame
        if len(response2) >= 1:
            # Extract bytes 7 through 10 from the second frame
            frame2_data = response2[6:10]  # Bytes 7 through 10

            # Decode the second frame payload
            values2 = []
            for i in range(0, len(frame2_data), 2):
                low_byte = frame2_data[i]      # Low byte
                high_byte = frame2_data[i + 1] # High byte
                value = (high_byte << 8) | low_byte  # Combine into a decimal value
                if value > 60000:
                    value = 0
                values2.append(value)

        # Merge the final six values
        combined_values = values1[:4] + values2[:2]  # First four values from frame one plus last two from frame two
        print("Read data:", tuple(combined_values))

def write6(ser, reg_name, val, id_value):
    """Write six values through the CAN-style protocol."""
    send_command(ser, reg_name, val, id_value)

if __name__ == "__main__":
    port = '/dev/ttyUSB0'  
    ser = init_serial(port)
    if not ser:
        exit(1)

    print('Setting dexterous hand motion angle parameters to 0, -1 means keep that angle unchanged')  
    # Write demo values
    write6(ser, 'speedSet', [1000, 1000, 1000, 1000, 1000, 1000], '01')
    time.sleep(1)
    write6(ser, 'angleSet', [0, 0, 0, 0, 800, 0], '01')  # Device ID is '01'
    time.sleep(3)
    write6(ser, 'speedSet', [200, 200, 200, 200, 200, 200], '01')
    time.sleep(1)
    write6(ser, 'angleSet', [1000, 1000, 1000, 1000, 1000, 1000], '01') 
    time.sleep(3)

    # Read back several registers
    read_register(ser, regdict['angleSet'], '01')
    read_register(ser, regdict['angleAct'], '01')
    read_register(ser, regdict['speedSet'], '01')
    read_register(ser, regdict['forceSet'], '01')
    read_register(ser, regdict['forceAct'], '01')    
    read_register(ser, regdict['temp'], '01')
    ser.close()
