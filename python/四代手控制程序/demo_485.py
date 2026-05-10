import serial  # Serial communication library
import time    # Time utilities

# Register map, referenced from the RH56 user manual section 2.4
regdict = {
    'ID'         : 1000,  # ID
    'baudrate'   : 1001,  # Baud rate setting
    'clearErr'   : 1004,  # Clear error flag
    'forceClb'   : 1009,  # Force sensor calibration
    'angleSet'   : 1486,  # Target angle for each degree of freedom
    'forceSet'   : 1498,  # Force threshold for each degree of freedom
    'speedSet'   : 1522,  # Speed setting for each degree of freedom
    'angleAct'   : 1546,  # Actual angle for each degree of freedom
    'forceAct'   : 1582,  # Actual force for each finger
    'errCode'    : 1606,  # Actuator error information
    'statusCode' : 1612,  # Actuator status information
    'temp'       : 1618,  # Actuator temperature
    'actionSeq'  : 2320,  # Current action sequence index
    'actionRun'  : 2322   # Run the current action sequence
}

# Open the serial port with the selected port name and baud rate.
def openSerial(port, baudrate):
    ser = serial.Serial() # Create the serial connection object
    ser.port = port
    ser.baudrate = baudrate
    ser.open()            # Open the serial port
    return ser

# Write data to the hand starting at the given register address.
def writeRegister(ser, id, add, num, val):
    bytes = [0xEB, 0x90]            # Frame header
    bytes.append(id)                # id
    bytes.append(num + 3)           # len
    bytes.append(0x12)              # Write-register command
    bytes.append(add & 0xFF)        # Register start address low byte
    bytes.append((add >> 8) & 0xFF) # Register start address high byte
    for i in range(num):
        bytes.append(val[i])
    checksum = 0x00                 # Initialize checksum
    for i in range(2, len(bytes)):
        checksum += bytes[i]        # Sum payload bytes
    checksum &= 0xFF                # Keep only the low byte
    bytes.append(checksum)          # Append checksum
    
    print("发送到串口的指令:", [hex(b) for b in bytes])
    
    ser.write(bytes)                # Write the frame to the serial port
    time.sleep(0.01)                # Delay 10 ms
    ser.read_all()                  # Discard the response frame

# Read register data from the hand.
def readRegister(ser, id, add, num, mute=False):
    bytes = [0xEB, 0x90]            # Frame header
    bytes.append(id)                # id
    bytes.append(0x04)              # Frame payload length
    bytes.append(0x11)              # Read-register command
    bytes.append(add & 0xFF)        # Register start address low byte
    bytes.append((add >> 8) & 0xFF) # Register start address high byte
    bytes.append(num)
    checksum = 0x00                 # Initialize checksum
    for i in range(2, len(bytes)):
        checksum += bytes[i]        # Sum payload bytes
    checksum &= 0xFF                # Keep only the low byte
    bytes.append(checksum)          # Append checksum
    
    print("发送到串口的指令:", [hex(b) for b in bytes])
    
    ser.write(bytes)                # Write the frame to the serial port
    time.sleep(0.01)                # Delay 10 ms
    recv = ser.read_all()           # Read bytes from the port
    print(recv)
    if len(recv) == 0:              # Return immediately if no response arrives
        return []
    num = (recv[3] & 0xFF) - 3      # Number of returned register bytes
    val = []
    for i in range(num):
        val.append(recv[7 + i])
    if not mute:
        print('读到的寄存器值依次为：', end='')
        for i in range(num):
            print(val[i], end=' ')
        print()
    return val

# Write six actuator values for angle, force, or speed.
def write6(ser, id, str, val):
    if str == 'angleSet' or str == 'forceSet' or str == 'speedSet':
        val_reg = []
        for i in range(6):
            val_reg.append(val[i] & 0xFF)
            val_reg.append((val[i] >> 8) & 0xFF)
        writeRegister(ser, id, regdict[str], 12, val_reg)
    else:
        print('函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'，val为长度为6的list，值为0~1000，允许使用-1作为占位符')

# Read six actuator values for command or feedback registers.
def read6(ser, id, str):
    if str == 'angleSet' or str == 'forceSet' or str == 'speedSet' or str == 'angleAct' or str == 'forceAct':
        val = readRegister(ser, id, regdict[str], 12, True) # Read 12 bytes
        if len(val) < 12:         # Ignore incomplete responses
            print('没有读到数据')
            return
        val_act = []
        for i in range(6):
            val_act.append((val[2*i] & 0xFF) + (val[1 + 2*i] << 8)) #
        print('读到的值依次为：', end='')
        for i in range(6):
            print(val_act[i], end=' ')
        print()
    elif str == 'errCode' or str == 'statusCode' or str == 'temp':
        val_act = readRegister(ser, id, regdict[str], 6, True)
        if len(val_act) < 6:      # Ignore incomplete responses
            print('没有读到数据')
            return
        print('读到的值依次为：', end='')
        for i in range(6):
            print(val_act[i], end=' ')
        print()
    else:
        print('函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'/\'angleAct\'/\'forceAct\'/\'errCode\'/\'statusCode\'/\'temp\'')

# Open the port and run a simple speed, force, and angle demo.
if __name__ == '__main__':
    print('打开串口！') # Startup message for opening the serial port
    ser = openSerial('/dev/ttyUSB0', 115200) # Change to the correct port and baud rate
    print('设置灵巧手运动速度参数，-1为不设置该运动速度！')
    write6(ser, 1, 'speedSet', [1000, 1000, 1000, 1000, 1000, 1000]) # Update the device ID as needed; valid values are 0-1000 and -1 means no change
    time.sleep(1)                   # Delay 1 s
    print('设置灵巧手抓握力度参数！')
    write6(ser, 1, 'forceSet', [500, 500, 500, 500, 500, 500])# Update the device ID as needed; valid values are 0-1000 and -1 means no change
    time.sleep(1)                   # Delay 1 s
    print('设置灵巧手运动角度参数0，-1为不设置该运动角度！')
    write6(ser, 1, 'angleSet', [0, 0, 0, 0, 0, 0])# Update the device ID as needed; valid values are 0-1000 and -1 means no change
    time.sleep(1)                   # Delay 1 s
    print('设置灵巧手运动角度参数1000，-1为不设置该运动角度！')
    write6(ser, 1, 'angleSet', [1000, 1000, 1000, 1000, 1000, 1000])
    
    time.sleep(1) 
    # Read temperature
    print('读取温度...')
    read6(ser, 1, 'temp')
        
    # Read actual angle values
    print('读取实际角度值...')
    read6(ser, 1, 'angleAct')  
    
    print('设置灵巧手动作库序列：3！')
    writeRegister(ser, 1, regdict['actionSeq'], 1, [3])
    time.sleep(1)                   # Delay 1 s
    print('运行灵巧手当前序列动作！')
    writeRegister(ser, 1, regdict['actionRun'], 1, [1])  

    print("关闭串口")
    ser.close()
