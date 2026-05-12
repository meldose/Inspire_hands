from pymodbus.client import ModbusTcpClient
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
    'Action': 1600, 
    'errCode': 1606,
    'statusCode': 1612,
    'temp': 1618,
    'actionSeq': 2320,
    'actionRun': 2322
}

def open_modbus(ip, port):
    client = ModbusTcpClient(ip, port)
    client.connect()
    return client

def write_register(client, address, values):
    # Write values to the given Modbus register address
    client.write_registers(address, values)

def read_register(client, address, count):
    # Read holding registers through Modbus
    response = client.read_holding_registers(address, count)
    return response.registers if response.isError() is False else []

def write6(client, reg_name, val):
    if reg_name in ['angleSet', 'forceSet', 'speedSet']:
        val_reg = []
        for i in range(6):
            val_reg.append(val[i] & 0xFFFF)  # Keep the low 16 bits
        write_register(client, regdict[reg_name], val_reg)
    else:
        print("Function call error. Expected: str = 'angleSet'/'forceSet'/'speedSet', val = list of length 6, values in 0-1000, and -1 may be used as a placeholder")

def read6(client, reg_name):
    # Validate the register name before reading
    if reg_name in ['angleSet', 'forceSet', 'speedSet', 'angleAct', 'forceAct','Action']:
        # Read six registers directly for the selected group
        val = read_register(client, regdict[reg_name], 6)
        if len(val) < 6:
            print('No data was read')
            return
        print('Read values:', end='')
        for v in val:
            print(v, end=' ')
        print()
    
    elif reg_name in ['errCode', 'statusCode', 'temp']:
        # Read error codes, status codes, or temperatures as three registers
        val_act = read_register(client, regdict[reg_name], 3)
        if len(val_act) < 3:
            print('No data was read')
            return
            
        # Collect split low and high bytes
        results = []
        
        # Split each register into low and high bytes
        for i in range(len(val_act)):
            low_byte = val_act[i] & 0xFF            # Low byte
            high_byte = (val_act[i] >> 8) & 0xFF     # High byte
        
            results.append(low_byte)  # Store low byte
            results.append(high_byte)  # Store high byte

        print('Read values:', end='')
        for v in results:
            print(v, end=' ')
        print()
    
    else:
        print("Function call error. Expected: str = 'angleSet'/'forceSet'/'speedSet'/'angleAct'/'forceAct'/'errCode'/'statusCode'/'temp'")

if __name__ == '__main__':
    ip_address = '192.168.11.210'
    port = 6000
    print('Opening Modbus TCP connection')
    client = open_modbus(ip_address, port)
    
    print('Setting dexterous hand motion speed parameters, -1 means keep that speed unchanged')
    write6(client, 'speedSet', [1000, 1000, 1000, 1000, 1000, 1000])
    time.sleep(2)
    
    print('Setting dexterous hand grip force parameters')
    write6(client, 'forceSet', [500, 500, 500, 500, 500, 500])
    time.sleep(1)
    
    print('Setting dexterous hand motion angle parameters to 0, -1 means keep that angle unchanged')
    write6(client, 'angleSet', [0, 0, 0, 0, 400, -1])
    time.sleep(3)
    
    read6(client, 'angleAct')
    time.sleep(1)
    
    print('Setting dexterous hand motion angle parameters to 1000, -1 means keep that angle unchanged')
    write6(client, 'angleSet', [1000, 1000, 1000, 1000, 1000, -1])
    time.sleep(5)
    
    read6(client, 'angleAct')
    time.sleep(1)
    
    print('Error information:')
    read6(client, 'errCode')
    time.sleep(1)
    print('Actuator temperature:')
    read6(client, 'temp')
    time.sleep(1)
    
    print('Setting dexterous hand action library sequence: 2')
    write_register(client, regdict['actionSeq'], [2])
    time.sleep(1)
    
    print('Running the current dexterous hand sequence action')
    write_register(client, regdict['actionRun'], [1])
    
    # Close the Modbus TCP connection
    client.close()

