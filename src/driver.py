# driver.py
# 硬件设备驱动代码，硬件包含室内外的温湿度传感器，雨雪感应器，两个执行动作的电机，补光灯
# 温湿度传感器和雨雪感应器挂载在 RS485 总线上，通讯协议为 modbus

from threading import Event, Thread
from time import sleep
from random import randint

import minimalmodbus
import wiringpi

__auth__ = "yingbing"

__debug_ = False
__simulate__ = False

__addr_rain_detector_1__ = 0x11
__addr_rain_detector_2__ = 0x12
__addr_rain_detector_3__ = 0x13

__addr_THL_sensor_outdoor__ = 0x01  # THL:温度、湿度、照度
__addr_THL_sensor_indoor__  = 0x02

__serial_baudrate__ = 9600
__serial_timeout__ = 0.5
__serial_port__ = "/dev/ttyUSB0"

if __simulate__ == False:
    dev_THL_indoor  = minimalmodbus.Instrument(__serial_port__, __addr_THL_sensor_indoor__, debug=__debug_)
    dev_THL_outdoor = minimalmodbus.Instrument(__serial_port__, __addr_THL_sensor_outdoor__, debug=__debug_)
    dev_rain_detector_1 = minimalmodbus.Instrument(__serial_port__, __addr_rain_detector_1__, debug=__debug_)
    dev_rain_detector_2 = minimalmodbus.Instrument(__serial_port__, __addr_rain_detector_2__, debug=__debug_)
    dev_rain_detector_3 = minimalmodbus.Instrument(__serial_port__, __addr_rain_detector_3__, debug=__debug_)

    common_serial_port = dev_THL_indoor.serial
    common_serial_port.baudrate = __serial_baudrate__
    common_serial_port.timeout = __serial_timeout__

if __debug_:
    print(dev_THL_indoor.serial.get_settings()) 

OUTPUT = 1
HIGH = 1
LOW = 0

pin_led = 25
pin_juanlian_1 = 30
pin_juanlian_2 = 21
pin_fengkou_1 = 23
pin_fengkou_2 = 24
pin_forbidden = 22

STOP = 0
FORWARD = 1
BACKWARD = -1

def setGPIO(pin, val):
        wiringpi.pinMode(pin,OUTPUT)
        wiringpi.digitalWrite(pin, val)

wiringpi.wiringPiSetup()
for pin in [pin_juanlian_1, pin_juanlian_2, pin_fengkou_1, pin_fengkou_2, pin_led]:
    setGPIO(pin, 0)

if __simulate__:
    def get_humid_indoor():
        return 33.258

    def get_humid_outdoor():
        return randint(1, 100)

    def get_temp_indoor():
        return 100

    def get_temp_outdoor():
        return randint(-40, 50)

    def get_light_indoor():
        return randint(0, 65535)

    def get_light_outdoor():
        return 100

    def get_rain_state():
        return True
        if randint(0,1) == 1:
            return True
        else:
            return False
    
    def turn_led(cmd:str=None):
        wiringpi.pinMode(pin_led,OUTPUT)
        if cmd in ["on", "ON"]:
            wiringpi.digitalWrite(pin_led, HIGH)
        elif cmd in ["off", "OFF"]:
            wiringpi.digitalWrite(pin_led, LOW)
        state =  wiringpi.digitalRead(pin_led)
        return ("on" if state else "off")

else:
    def get_rain_state():
        sleep(1)
        rain_state = 0
        valid_devices = 0
        try:
            rain_state += dev_rain_detector_1.read_register(registeraddress=0x00)
            valid_devices += 1
        except:
            pass
        try:
            rain_state += dev_rain_detector_2.read_register(registeraddress=0x00)
            valid_devices += 1
        except:
            pass
        try:
            rain_state += dev_rain_detector_3.read_register(registeraddress=0x00)
            valid_devices += 1
        except:
            pass

        if valid_devices > 1:
            return True if rain_state >= valid_devices-1 else False
        elif valid_devices == 1:
            return True if rain_state >= 1 else False
        else:
            return False

    def get_temp_indoor():
        sleep(1)
        x = None
        try:
            x = dev_THL_indoor.read_register(registeraddress=0x00, number_of_decimals=1, signed=True)
        except:
            pass
        return x
    def get_humid_indoor():
        sleep(1)
        x = None
        try:
            x =  dev_THL_indoor.read_register(registeraddress=0x01, number_of_decimals=1, signed=True)
        except:
            pass
        return x
    def get_light_indoor():
        sleep(1)
        x = None
        try:
            data1, data2 = dev_THL_indoor.read_registers(registeraddress=0x03, number_of_registers=2)
            x = data2*10 + data1
        except:
            pass
        return x

    def get_temp_outdoor():
        sleep(1)
        try:
            return dev_THL_outdoor.read_register(registeraddress=0x00, number_of_decimals=1, signed=True)
        except:
            return None
    def get_humid_outdoor():
        sleep(1)
        try:
            return dev_THL_outdoor.read_register(registeraddress=0x01, number_of_decimals=1, signed=True)
        except:
            return None
    def get_light_outdoor():
        sleep(1)
        try:
            data1, data2 = dev_THL_outdoor.read_registers(registeraddress=0x02, number_of_registers=2)
            return data1*10 + data2
        except:
            return None

    def turn_led(cmd:str=None):
        wiringpi.pinMode(pin_led,OUTPUT)
        if cmd in ["on", "ON"]:
            wiringpi.digitalWrite(pin_led, HIGH)
        elif cmd in ["off", "OFF"]:
            wiringpi.digitalWrite(pin_led, LOW)
        state =  wiringpi.digitalRead(pin_led)
        return ("on" if state else "off")


class Motor:
    _speed:float = None
    _state:int = 0   #0停止，1正转， 2反转
    _path:str = None
    speed_file_able:bool = True
    chengdu_file_able:bool = True
    state_file_able:bool = True
    _chengdu:float = 0
    _exit_last_motor_threading_now:bool = False
    _motor_threading_running:bool = False

    def __init__(self, dev_path:str):
        self._path = dev_path
        self.load()
    
    def power_func(self, mode):
        pass

    def safety_stop(self):
        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self._exit_last_motor_threading_now = False


    def stop(self):
        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self.power_func(STOP)
        self._exit_last_motor_threading_now = False

    def forward(self):
        self.stop()
        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self.power_func(FORWARD)
        self._exit_last_motor_threading_now = False

    def backward(self):
        self.stop()
        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self.power_func(BACKWARD)
        self._exit_last_motor_threading_now = False
    
    
    def _save_config(self, speed:float=None, chengdu:float=None, state:int=None):
        if (self.speed_file_able and self.chengdu_file_able and self.state_file_able) == False:
            return -1
        
        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self._exit_last_motor_threading_now = False
        
        if speed != None:
            self.speed_file_able = False
            with open(self._path+"speed", "w") as fp:
                fp.write(str(speed))
                fp.close()
            self.speed_file_able = True

        if chengdu != None:
            self.chengdu_file_able = False
            with open(self._path+"chengdu", "w") as fp:
                fp.write(str(chengdu))
                fp.close()
            self.chengdu_file_able = True

        if state != None:
            self.state_file_able = False
            with open(self._path+"state", "w") as fp:
                fp.write(str(state))
                fp.close()
            self.state_file_able = True
    
    def set_speed(self, speed:float):
        while self.speed_file_able == False:
            pass
        self.speed_file_able = False

        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self._exit_last_motor_threading_now = False
        
        self._speed = speed
        with open(self._path+"speed", "w") as fp:
            fp.write(str(self._speed))
            fp.close()
        self.speed_file_able = True
        return 0
    
    def get_speed(self, flush:bool = False):
        if flush:
            if self.speed_file_able == False:
                return None
            with open(self._path+"speed", "r") as fp:
                self._speed = float(fp.read())
                fp.close()
        return self._speed
    
    def get_chengdu(self, flush:bool = False):
        if flush:
            if self.chengdu_file_able == False:
                return None
            with open(self._path+"chengdu", "r") as fp:
                self._chengdu = float(fp.read())
                fp.close()
        return self._chengdu
    
    def get_state(self, flush:bool = False):
        if flush:
            if self.state_file_able == False:
                return None
            with open(self._path+"state", "r") as fp:
                self._state = int(fp.read())
                fp.close()
        return self._state

    def set_state(self, mode):
        while self.state_file_able == False:
            pass
        
        self.state_file_able = False
        self._state = mode
        with open(self._path+"state", "w") as fp:
            fp.write(str(mode))
            fp.close()
        self.state_file_able = True
    
    def load(self):
        with open(self._path+"speed", "r") as fp:
            self._speed = float(fp.read())
            fp.close()

        with open(self._path+"chengdu", "r") as fp:
            self._chengdu = float(fp.read())
            fp.close()

        with open(self._path+"state", "r") as fp:
            self._state = int(fp.read())
            fp.close()
    
    def set_chengdu(self, val, run_event:Event=None):
        
        if run_event != None:
            run_event.wait()
            run_event.clear()
        self._exit_last_motor_threading_now = True
        while self._motor_threading_running:
            pass
        self._exit_last_motor_threading_now = False
            
        if self.power_func == None:
            if run_event != None:
                run_event.set()
            return -3
        
        speed = self._speed
        chengdu = self._chengdu
        if chengdu <= val-speed:
            self.set_state(1) #正转
        elif chengdu >= val+speed:
            self.set_state(-1) #反转
        else:
            if self._state != 0:
                self.set_state(0) #停止
            if run_event != None:
                run_event.set()
            return -2

        def task():
            speed = self._speed
            self._motor_threading_running = True
            self.chengdu_file_able = False
            with open(self._path+"chengdu", "w") as fp_chengdu:
                sleep(1.5)  # 等待继电器恢复为未吸合状态
                self.power_func(self._state)    #here let the GPIO ouput evaluate
                tmp = 0
                while (self._state>0 and val-self._chengdu>=speed) or (self._state<0 and self._chengdu-val>=speed):
                    if self._exit_last_motor_threading_now == True:
                        break
                    self._chengdu += self._state * speed
                    if tmp%5 == 0:
                        fp_chengdu.seek(0)
                        fp_chengdu.write(str(self._chengdu))
                        tmp = 0
                    tmp += 1
                    sleep(1)
                self.power_func(STOP)    #here let the GPIO ouput disevaluate
                fp_chengdu.seek(0)
                fp_chengdu.write(str(self._chengdu))
                fp_chengdu.close()
            
            self.set_state(0)
            self.chengdu_file_able = True
            self._motor_threading_running = False
            if run_event != None:
                run_event.set()
        
        t_task = Thread(target=task)
        t_task.start()
        return 0

class Juanlian(Motor):
    def __init__(self, dev_path:str):
        super().__init__(dev_path)
        self.stop()

    def power_func(self, mode):
        if __simulate__ == True:
            return
        wiringpi.pinMode(pin_juanlian_1, OUTPUT)
        wiringpi.pinMode(pin_juanlian_2, OUTPUT)
        wiringpi.digitalWrite(pin_juanlian_1, LOW)
        wiringpi.digitalWrite(pin_juanlian_2, LOW)
        if mode == FORWARD:
            wiringpi.digitalWrite(pin_juanlian_1, HIGH)
        elif mode == BACKWARD:
            wiringpi.digitalWrite(pin_juanlian_2, HIGH)


class Fengkou(Motor):
    def __init__(self, dev_path:str):
        super().__init__(dev_path)
        self.stop()

    def power_func(self, mode):
        if __simulate__ == True:
            return
        wiringpi.pinMode(pin_fengkou_1, OUTPUT)
        wiringpi.pinMode(pin_fengkou_2, OUTPUT)
        wiringpi.digitalWrite(pin_fengkou_1, LOW)
        wiringpi.digitalWrite(pin_fengkou_2, LOW)
        if mode == FORWARD:
            wiringpi.digitalWrite(pin_fengkou_2, HIGH)
        elif mode == BACKWARD:
            wiringpi.digitalWrite(pin_fengkou_1, HIGH)
    

if __name__ == "__main__":
    # print(get_rain_state())
    # while True:
    #     print(f"temp_indoor: {get_temp_indoor()} ,temp_outdoor: {get_temp_outdoor()}")
    #     print(f"humid_indoor: {get_humid_indoor()}, humid_outdoor: {get_humid_outdoor()}")
    #     print(f"light_indoor: {get_light_indoor()}, light_outdoor: {get_light_outdoor()}")
    # sleep(1)

    # print(f"temp_indoor: {get_temp_indoor()} ,temp_outdoor: {get_temp_outdoor()}")

    fengdou_dev = Fengkou("/home/pi/smart-dapeng/src/dev/fengkou/")
    fengdou_dev.stop()
    # fengdou_dev.forward()
    fengdou_dev.backward()

    # juanlian_dev = Juanlian("/home/pi/smart-dapeng/src/dev/juanlian/")
    # juanlian_dev.stop()
    # juanlian_dev.forward()
    # juanlian_dev.backward()

