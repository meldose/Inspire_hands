from pymodbus.client import ModbusTcpClient  # pip3 install pymodbus==2.5.3
import time
import threading
import random

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

def open_modbus(ip, port, timeout=10):
    start_time = time.time()
    client = ModbusTcpClient(ip, port)
    
    while (time.time() - start_time) < timeout:
        if client.connect():
            print(f"Connected successfully to {ip}:{port}")
            return client
        else:
            print(f"Connection failed: {ip}:{port}, retrying...")
            time.sleep(1)  # Wait 1 second before retrying
            
    print(f"Connection failed, timed out: {ip}:{port}")
    return None

def write_register(client, address, values):
    client.write_registers(address, values)

def read_register(client, address, count):
    response = client.read_holding_registers(address, count)
    return response.registers if response.isError() is False else []

def write6(client, reg_name, val):
    if reg_name in ['angleSet', 'forceSet', 'speedSet']:
        val_reg = []
        for i in range(6):
            val_reg.append(val[i] & 0xFFFF)  # Keep the low 16 bits
        write_register(client, regdict[reg_name], val_reg)
    else:
        print('Function call error')

def read6(client, reg_name):
    if reg_name in ['angleSet', 'forceSet', 'speedSet', 'angleAct', 'forceAct']:
        val = read_register(client, regdict[reg_name], 6)
        if len(val) < 6:
            print('No data was read')
            return
        print('Read values:', end='')
        for v in val:
            print(v, end=' ')
        print()
    elif reg_name in ['errCode', 'statusCode', 'temp']:
        val_act = read_register(client, regdict[reg_name], 3)
        if len(val_act) < 3:
            print('No data was read')
            return
        results = []
        for i in range(len(val_act)):
            low_byte = val_act[i] & 0xFF
            high_byte = (val_act[i] >> 8) & 0xFF
            results.append(low_byte)
            results.append(high_byte)
        print('Read values:', end='')
        for v in results:
            print(v, end=' ')
        print()

def control_device(ip):
    client = open_modbus(ip, 6000, timeout=10)
    if client is None:
        return

    # Run the command sequence for one device
    print(f'{ip} - Setting dexterous hand motion speed parameters')
    write6(client, 'speedSet', [1000, 1000, 1000, 1000, 1000, 1000])
    time.sleep(2)

    print(f'{ip} - Setting dexterous hand grip force parameters')
    write6(client, 'forceSet', [500, 500, 500, 500, 500, 500])
    time.sleep(1)

    print(f'{ip} - Setting dexterous hand motion angle parameters to 0')
    write6(client, 'angleSet', [0, 0, 0, 0, 500, 500])
    time.sleep(3)

    read6(client, 'angleAct')
    time.sleep(1)

    print(f'{ip} - Setting dexterous hand motion angle parameters to 1000')
    write6(client, 'angleSet', [1000, 1000, 1000, 1000, 1000, 1000])
    time.sleep(5)

    read6(client, 'angleAct')
    time.sleep(1)

    print(f'{ip} - Error information:')
    read6(client, 'errCode')
    time.sleep(1)

    print(f'{ip} - Actuator temperature:')
    read6(client, 'temp')
    time.sleep(1)

    print(f'{ip} - Setting dexterous hand action library sequence: 2')
    write_register(client, regdict['actionSeq'], [2])
    time.sleep(1)

    print(f'{ip} - Running the current dexterous hand sequence action')
    write_register(client, regdict['actionRun'], [1])

    client.close()
    print(f'{ip} - Connection closed')

if __name__ == '__main__':
    ip_addresses = ['192.168.11.210', '192.168.11.220']  # Add the IP addresses of all devices
    threads = []
    clients = []

    # Try to connect to all devices
    for ip in ip_addresses:
        client = open_modbus(ip, 6000, timeout=10)
        if client:
            clients.append(client)
        else:
            print(f"Unable to connect to device: {ip}")

    # Run the control sequence only if every device connects successfully
    if len(clients) == len(ip_addresses):
        print("All devices connected successfully, starting device control...")
        for ip, client in zip(ip_addresses, clients):
            thread = threading.Thread(target=control_device, args=(ip,))
            threads.append(thread)
            thread.start()  # Start the worker thread

        # Wait for all worker threads to finish
        for thread in threads:
            thread.join()

        print("All device control tasks completed.")
    else:
        print("Failed to connect to all devices, control program was not executed.")

