import time
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ExceptionResponse
import struct

# Modbus TCP connection settings
MODBUS_IP = "192.168.11.210"
MODBUS_PORT = 6000

# Base register address for each finger sensor block
TOUCH_SENSOR_BASE_ADDR_PINKY = 3000   # Pinky
TOUCH_SENSOR_BASE_ADDR_RING = 3058     # Ring finger
TOUCH_SENSOR_BASE_ADDR_MIDDLE = 3116   # Middle finger
TOUCH_SENSOR_BASE_ADDR_INDEX = 3174    # Index finger
TOUCH_SENSOR_BASE_ADDR_THUMB = 3232    # Thumb

def read_register_range(client, start_addr, count):
    register_values = []
    response = client.read_holding_registers(address=start_addr, count=count)

    if isinstance(response, ExceptionResponse) or response.isError():
        print(f"Failed to read register {start_addr}: {response}")
        return None
    else:
        register_values = response.registers

    return register_values

def read_float_from_bytes(registers, index):
    """
    Read a floating-point value from two consecutive registers.
    """
    # Extract the four raw bytes
    byte0 = registers[index] & 0xFF       # Low byte
    byte1 = (registers[index] >> 8) & 0xFF # High byte
    byte2 = registers[index + 1] & 0xFF   # Low byte
    byte3 = (registers[index + 1] >> 8) & 0xFF # High byte

    # Rebuild the float bit pattern
    combined = (byte3 << 24) | (byte2 << 16) | (byte1 << 8) | byte0

    result = struct.unpack('!f', struct.pack('!I', combined))[0]
    
    return result

def read_finger_data(client, base_addr):
    """
    Read normal and tangential force data for one finger.
    Normal force starts at base_addr + 32 and tangential force at base_addr + 40.
    """
    # Read the raw registers
    register_values = read_register_range(client, base_addr, 25)  

    if register_values is None:
        return None
    
    # Decode normal force and tangential force
    normal_force = read_float_from_bytes(register_values, 16)  # Normal force
    tangential_force = read_float_from_bytes(register_values, 20)  # Tangential force

    return normal_force, tangential_force

def read_multiple_registers():
    client = ModbusTcpClient(MODBUS_IP, port=MODBUS_PORT)
    client.connect()

    try:
        while True:
            start_time = time.time()

            # Read all finger force blocks
            pinky_force = read_finger_data(client, TOUCH_SENSOR_BASE_ADDR_PINKY)
            ring_force = read_finger_data(client, TOUCH_SENSOR_BASE_ADDR_RING)
            middle_force = read_finger_data(client, TOUCH_SENSOR_BASE_ADDR_MIDDLE)
            index_force = read_finger_data(client, TOUCH_SENSOR_BASE_ADDR_INDEX)
            thumb_force = read_finger_data(client, TOUCH_SENSOR_BASE_ADDR_THUMB)

            end_time = time.time()
            frequency = 1 / (end_time - start_time)

            # Print the current values
            print(f"Pinky normal force: {pinky_force[0]}, tangential force: {pinky_force[1]}")
            print(f"Ring finger normal force: {ring_force[0]}, tangential force: {ring_force[1]}")
            print(f"Middle finger normal force: {middle_force[0]}, tangential force: {middle_force[1]}")
            print(f"Index finger normal force: {index_force[0]}, tangential force: {index_force[1]}")
            print(f"Thumb normal force: {thumb_force[0]}, tangential force: {thumb_force[1]}")
            print(f"Read frequency: {frequency:.2f} Hz")

            time.sleep(0.02)

    finally:
        client.close()

if __name__ == "__main__":
    read_multiple_registers()

