#!/usr/bin/python3
#Filename : backend.py
# 程序后端业务代码

# -*- coding: utf-8 -*-

__auth__ = "yinbing"
__DEBUG__ = False
__auth_key__ = '3a66eca2c941'
__yike_appid__ = '75246564'
__yike_appsecret__ = 'Ga0ty4WS'
__local_city__ = '五寨'

import asyncio
import datetime
import json
import threading

from time import sleep, time
from aiohttp.client_exceptions import \
    ClientConnectorError as aiohttp_ClientConnectorError
from blinker import ButtonWidget, Device, NumberWidget, RangeWidget, TextWidget
from blinker.device import logger
from requests import get as sync_get
from requests.exceptions import ConnectionError as requests_ConnectionError

# driver.py模块内封装了各类传感器的读写函数
import driver

# 各种天气对应的手机APP上的天气状态图标
__weather_icon_app__ = {"qing":"fas fa-sun",        "yin":"fas fa-cloud",          "yun":"fas fa-sun-cloud", 
                        "yu":"fas fa-cloud-rain",   "lei":"fas fa-thunderstorm",   "bingbao":"fas fa-cloud-hail",
                        "xue":"fas fa-snowflake",   "wu":"fas fa-fog",             "shachen":"fas fa-smog"}

workig_path = "/home/pi/smart-dapeng/"


# 继承并客制化一个blinker IoT设备
class IotDevice(Device):
    """
    :param auth_key
    :param yike_appid
    :param yike_appsecret
    :param city
    :param websocket
    :param send_pipe_conn
    """
    # 从天气API获取的数据
    weather:str     = None
    weather_img:str = None
    wind:str        = None
    wind_level:str  = None
    sunrise_web     = None
    sunset_web      = None
    sunrise:datetime.time = None
    sunset:datetime.time  = None

    # sunrise sunset是否发生改变
    sunrise_sunset_changed:bool = False

    # 如果日期发生变更，则True
    date_change:bool = False

    # 手机APP上的天气状态图标
    weather_icon_app:str = None

    # 天气API以及所需要的key
    yike_api:str = 'https://www.yiketianqi.com/free/day'
    moji_api:str = 'https://devapi.qweather.com/v7/weather/3d'
    yike_appid:str = None
    yike_appsecret:str = None

    # 所在城市
    city:str = None

    # 温度   web后缀表示该数据从天气API获取
    temperature_web:float     = None
    temperature_indoor:float  = None
    temperature_outdoor:float = None

    # 湿度   web后缀表示该数据从天气API获取
    humidity_web:float     = None
    humidity_indoor:float  = None
    humidity_outdoor:float = None

    # 照度
    light_indoor:float  = None
    light_outdoor:float = None

    # 雨雪状态
    is_rain:bool = False

    # 高低温阈值
    threshold_temp:dict = None

    # 一些状态量，用于控制程序运行状态
    auto_run:bool = True
    RS485_busy:bool = False
    internet_ok:bool = False
    pipe_update_realtime_able:bool = True
    phone_control_able:bool = True
    local_control_able:bool = False
    safety_stop:bool = False

    # 业务逻辑（非联网部分）中的规划运行任务
    scheduler_daily_tasks:dict = {}

    # 需要在driver.py导入并实例化的卷帘、风口设备类
    juanlian_dev = None
    fengkou_dev  = None

    # 卷帘、风口电机的运行结束标志事件
    # 如果电机处于运行状态（即电机正在转动），对应设备的运行结束标志事件被clear()，调用该事件的wait()时会阻塞
    # 如果电机结束运行状态（即电机停止转动），对应设备的运行结束标志事件被set()，该事件的wait()的阻塞结束
    juanlian_run_finished = threading.Event()
    juanlian_run_finished.clear()
    fengkou_run_finished  = threading.Event()
    fengkou_run_finished.clear()

    send_pipe_conn = None
    recv_pipe_conn = None



    def __init__(self, auth_key, yike_appid, yike_appsecret, city, send_pipe_conn, recv_pipe_conn, websocket:bool = False):
        super().__init__(auth_key, websocket=websocket)

        self.yike_appid = yike_appid
        self.yike_appsecret = yike_appsecret
        self.city = city

        self.send_pipe_conn = send_pipe_conn
        self.recv_pipe_conn = recv_pipe_conn

        self.num_temp_indoor = self.addWidget(NumberWidget("num-tid"))
        self.num_temp_outdoor = self.addWidget(NumberWidget("num-tod"))

        self.num_humid_indoor = self.addWidget(NumberWidget("num-hid"))
        self.num_humid_outdoor = self.addWidget(NumberWidget("num-hod"))

        self.num_light_indoor = self.addWidget(NumberWidget("num-lid"))
        self.num_light_outdoor = self.addWidget(NumberWidget("num-lod"))

        self.tex_weather = self.addWidget(TextWidget("tex-wea"))

        self.tex_rain = self.addWidget(TextWidget("tex-rain"))

        self.btn_manual = self.addWidget(ButtonWidget("btn-man"))

        self.num_juanlian = self.addWidget(NumberWidget("num-jua"))
        self.num_fengkou = self.addWidget(NumberWidget("num-fen"))

        self.ran_juanlian = self.addWidget(RangeWidget("ran-jua"))

        self.ran_fengkou = self.addWidget(RangeWidget("ran-fen"))

        self.btn_led = self.addWidget(ButtonWidget("btn-led"))  # 补光灯的开关

        self.btn_juanlian_safety_stop = self.addWidget(ButtonWidget("btn-jst"))
        self.btn_fengkou_safety_stop = self.addWidget(ButtonWidget("btn-fst"))
        self.btn_clean_safety_stop   = self.addWidget(ButtonWidget("btn-cst"))

        self.tex_notice = self.addWidget(TextWidget("tex-not"))

        self.juanlian_dev = driver.Juanlian(workig_path + "src/dev/juanlian/")
        self.fengkou_dev  = driver.Fengkou(workig_path + "src/dev/fengkou/")
        
        # self._realtime_callable = self.realtime_callable

        self.btn_manual.func = self.btn_manual_callable

        self.ran_juanlian.func = self.ran_juanlian_callable
        self.ran_fengkou.func  = self.ran_fengkou_callable

        self.btn_led.func = self.btn_led_callable

        self.btn_juanlian_safety_stop.func = self.btn_juanlian_safety_stop_callable
        self.btn_fengkou_safety_stop.func  = self.btn_fengkou_safety_stop_callable
        self.btn_clean_safety_stop.func    = self.btn_clean_safety_stop_callable

        cfg = self.load_config()
        self.threshold_temp = cfg["temperature"]

        self.sunrise = datetime.time.fromisoformat("07:30:59")
        self.sunset  = datetime.time.fromisoformat("18:30:59")

        self.count_send_tempthreshlod = 0


    def update_weather(self):   # HTTP
        yike_url = '{0}?appid={1}&appsecret={2}&cityid={3}&unescape=1'.format(self.yike_api, self.yike_appid, self.yike_appsecret, '101101014')
        #yike_url = '{0}?appid={1}&appsecret={2}&unescape=1'.format(self.yike_api, self.yike_appid, self.yike_appsecret)
        try:
            weather_text = sync_get(yike_url).text
        except requests_ConnectionError:
            logger.error("requests.exceptions.ConnectionError")
            return 1
        weather_json = json.loads(weather_text)
        #print(weather_json)
        self.weather = weather_json['wea']
        self.weather_img = weather_json['wea_img']
        self.wind = weather_json['win']
        self.wind_level = weather_json['win_speed']
        self.temperature_web = eval(weather_json['tem'])
        self.humidity_web = eval(weather_json['humidity'].split('%')[0])

        moji_url = '{0}?location=101101014&key=5916031d30bc4c038e8327ff45579ee4'.format(self.moji_api)
        moji_text = sync_get(moji_url).text
        moji_json = json.loads(moji_text)

        #print(moji_json)
        

        sunrise_str = moji_json['daily'][0]['sunrise']+":59"
        sunset_str  = moji_json['daily'][0]['sunset']+":59"

        #print(sunrise_str,sunset_str)
        #print(self.sunrise, self.sunset)

        if any([self.sunrise != datetime.datetime.strptime(sunrise_str, "%H:%M:%S").time(), 
                self.sunset != datetime.datetime.strptime(sunset_str, "%H:%M:%S").time()]):
            self.sunrise = datetime.datetime.strptime(sunrise_str, "%H:%M:%S").time()
            self.sunset = datetime.datetime.strptime(sunset_str, "%H:%M:%S").time()
            self.sunrise_sunset_changed = True

        #print(self.sunrise, self.sunset)
        
        # self.send_pipe_conn.send({'wea': self.weather, 'sr': self.sunrise, 'ss': self.sunset})
        self.send_pipe_conn.send({'wea': self.weather})
            
        logger.success("weather update")
        logger.info("weather_text: {}".format(weather_text))
        logger.info("sunrise: {}, sunset: {}".format(self.sunrise, self.sunset))
        # logger.info("sunset: {}".format(self.sunset))
        return 0

    def update_environment_data(self):  # RS485
        if self.RS485_busy == True:
            return
        
        self.RS485_busy = True
        temperature_indoor  = driver.get_temp_indoor()
        temperature_outdoor = driver.get_temp_outdoor()
        humidity_indoor  = driver.get_humid_indoor()
        humidity_outdoor = driver.get_humid_outdoor()
        light_indoor  = driver.get_light_indoor()
        light_outdoor = driver.get_light_outdoor()
        is_rain = driver.get_rain_state()

        self.temperature_indoor  = temperature_indoor if temperature_indoor!=None else self.temperature_indoor
        self.temperature_outdoor = temperature_outdoor if temperature_outdoor!=None else self.temperature_outdoor
        self.humidity_indoor  = humidity_indoor if humidity_indoor!=None else self.humidity_indoor
        self.humidity_outdoor = humidity_outdoor if humidity_outdoor!=None else self.humidity_outdoor
        self.light_indoor  = light_indoor if light_indoor!=None else self.light_indoor
        self.light_outdoor = light_outdoor if light_outdoor!=None else self.light_outdoor
        self.is_rain = is_rain

        juanlian = round(self.get_juanlian_chengdu(), 2)  # 上报的数据精确到2位小数
        fengkou = round(self.get_fengkou_chengdu(), 2)

        pipe_msg = {'ti': self.temperature_indoor,
                    'to': self.temperature_outdoor,
                    'hi': self.humidity_indoor,
                    'ho': self.humidity_outdoor,
                    'li': self.light_indoor,
                    'lo': self.light_outdoor,
                    'rs': self.is_rain,
                    'jua': juanlian,
                    'fen': fengkou}
        if self.count_send_tempthreshlod < 1:
            pipe_msg["t_ack"] = self.threshold_temp
            self.count_send_tempthreshlod += 1
        
        if self.pipe_update_realtime_able:
            self.send_pipe_conn.send(pipe_msg)

        logger.success("environment element update")
        self.RS485_busy = False
    
    def turn_led(self, cmd:str = None): # GPIO
        return driver.turn_led(cmd)

    # FILE
    def get_juanlian_chengdu(self):
        return self.juanlian_dev.get_chengdu()
    def set_juanlian_chengdu(self, val, run_event=None):
        if run_event != None:
            if self.fengkou_run_finished.isSet() and self.juanlian_run_finished.isSet():
                self.juanlian_dev.set_chengdu(val, run_event)
        else:
            self.juanlian_dev.set_chengdu(val)
    def get_juanlian_state(self):
        return self.juanlian_dev.get_state()

    # FILE
    def get_fengkou_chengdu(self):
        return self.fengkou_dev.get_chengdu()
    def set_fengkou_chengdu(self, val, run_event=None):
        if run_event != None:
            if self.fengkou_run_finished.isSet() and self.juanlian_run_finished.isSet():
                self.fengkou_dev.set_chengdu(val, run_event)
        else:
            self.fengkou_dev.set_chengdu(val)
    def get_fengkou_state(self):
        return self.fengkou_dev.get_state()

    def load_config(self):
        # 这里用来从文件载入一些设置，这个文件应是json的
        # 文件内容应该包括：
        with open("/home/pi/smart-dapeng/src/config.cfg") as f:
            return json.load(f)
       
    def save_config(self, cfg):
        # 这里用来向文保存一些设置，这个文件应是json的
        with open("/home/pi/smart-dapeng/src/config.cfg", "w") as f:
            json.dump(cfg, f)

    # 设备的自动运行逻辑函数
    def auto_control(self):
        self.logic_init()
        logger.info("auto_control running...")
        run_mode_old = self.auto_run
        state = -1  # 用于记录当前系统运行于什么状态 
                    # -2 安全制动态
                    # -1 非自动运行态
                    # 0 自动运行态
                    # 1 日间有雨态
                    # 2 日间无雨态
                    # 3 夜间态
        while True:
            if self.safety_stop == True:
                if state != -2:
                    logger.info("系统状态：安全制动状态")
                    state = -2
                sleep(1)
                continue
            if self.auto_run == True:
                if state < 0:
                    logger.info("系统状态：自动运行态")
                    state = 0

                now_time = datetime.datetime.now().time()      # 获取当前时间
                if now_time >= self.sunrise and now_time <= self.sunset:    # 如果在日间
                    if self.is_rain == True:    # 如果有雨
                        if self.get_fengkou_chengdu() >= self.fengkou_dev.get_speed():  # 如果风口没到 0%
                            self.set_juanlian_chengdu(100, self.juanlian_run_finished)  # 先设置卷帘至 100%
                            self.set_fengkou_chengdu(0, self.fengkou_run_finished)      # 再设置风口至 0%
                        self.set_juanlian_chengdu(95, self.juanlian_run_finished)       # 设置卷帘至 95%
                        if state != 1:
                            logger.info("系统状态：日间有雨态")
                            state = 1

                    else:   # 如果无雨
                        self.set_juanlian_chengdu(100, self.juanlian_run_finished)      # 设置卷帘至 100%
                        if self.temperature_indoor > self.threshold_temp["high"]:       # 如果温度高于高温阈值
                            self.set_fengkou_chengdu(100, self.fengkou_run_finished)    # 设置风口至 100%
                        elif self.temperature_indoor < self.threshold_temp["low"]:      # 如果温度低于低温阈值
                            self.set_fengkou_chengdu(0, self.fengkou_run_finished)      # 设置风口至 0%
                        if state != 2:
                            logger.info("系统状态：日间无雨态")
                            state = 2
                        
                else:   # 如果在夜间
                    if self.get_fengkou_chengdu() >= self.fengkou_dev.get_speed():  # 如果风口没到 0%
                        self.set_juanlian_chengdu(100, self.juanlian_run_finished)  # 先设置卷帘至 100%
                        self.set_fengkou_chengdu(0, self.fengkou_run_finished)      # 再设置风口至 0%
                    self.set_juanlian_chengdu(0, self.juanlian_run_finished)        # 设置卷帘至 0%
                    if state != 3:
                        logger.info("系统状态：夜间态")
                        state = 3
            else:
                if state >= 0:
                    logger.info("系统状态：非自动运行态")
                    state = -1
            sleep(1)
                


    # 设备逻辑初始化函数 与网络客户端初始化有别
    def logic_init(self):
        self.juanlian_run_finished.set()
        self.fengkou_run_finished.set()

        self.update_environment_data()
        
        self.scheduler_daily_tasks["update_env"] = self.scheduler.add_job(self.update_environment_data,
                                                                    'interval', 
                                                                    minutes=1, 
                                                                    max_instances=10,
                                                                    jitter=10, 
                                                                    id="update_env")
        logger.info("scheduler task for <update_env> has started")


    # 接收从设备端输入的信号
    def pipe_receiver(self):

        logger.success("Pipe receiver ready...")

        while True:
            # print(1,self.auto_run, self.pipe_update_realtime_able, self.phone_control_able)
            recv_data = self.recv_pipe_conn.recv() # 阻塞函数
            # print(2,self.auto_run, self.pipe_update_realtime_able, self.phone_control_able)

            for key in recv_data:
                if key == "set":
                    # 设备端开始设置电机运行速度 True or False
                    val = recv_data[key]
                    self.auto_run = not val
                    self.pipe_update_realtime_able = not val
                    self.phone_control_able = not val

                    juanlian_chengdu = round(self.get_juanlian_chengdu(), 2)
                    fengkou_chengdu = round(self.get_fengkou_chengdu(), 2)
                    self.send_pipe_conn.send({'set': val, 'jua': juanlian_chengdu, 'fen': fengkou_chengdu})
                 
                    # print("backend send: {}".format({'set': val}))
                    # print(3,self.auto_run, self.pipe_update_realtime_able, self.phone_control_able)

                elif key == "fsp":
                    # 设置风口电机运行速度
                    # self.fengkou_dev.set_speed(recv_data[key])
                    self.fengkou_dev._save_config(speed=recv_data[key], chengdu=100.0, state=0)
                    self.fengkou_dev.load()
                    logger.info(f"设置风口电机运行速度：{recv_data[key]}")
                elif key == "fs":
                    # 风口电机停转
                    self.fengkou_dev.stop()
                elif key == "fst":
                    # 风口电机安全制动
                    self.safety_stop = True
                    self.fengkou_dev.safety_stop()
                elif key == "ff":
                    # 风口电机正转
                    self.fengkou_dev.forward()
                elif key == "fb":
                    # 风口电机反转
                    self.fengkou_dev.backward()
                elif key == "fsc":
                    # 设置风口打开程度
                    # set fengkou chengdu
                    if self.auto_run == False and self.local_control_able == True and self.safety_stop == False:
                        self.set_fengkou_chengdu(recv_data[key])
                        # print("frontstage: {}".format({'fsc': recv_data[key]}))

                elif key == "jsp":
                    # 设置卷帘电机运行速度
                    self.juanlian_dev._save_config(speed=recv_data[key], chengdu=100.0, state=0)
                    self.juanlian_dev.load()
                    logger.info(f"设置卷帘电机运行速度：{recv_data[key]}")
                elif key == "js":
                    self.juanlian_dev.stop()
                elif key == "jst":
                    self.safety_stop = True
                    self.juanlian_dev.safety_stop()
                elif key == "jf":
                    self.juanlian_dev.forward()
                elif key == "jb":
                    self.juanlian_dev.backward()
                elif key == "jsc":
                    if self.auto_run == False and self.local_control_able == True and self.safety_stop == False:
                        self.set_juanlian_chengdu(recv_data[key])
                        # print("frontstage: {}".format({'jsc': recv_data[key]}))
                
                elif key == "cst":
                    # 清除制动状态
                    self.safety_stop = False

                elif key == "lc":
                    val = recv_data[key]
                    self.local_control_able = val
                    self.auto_run = not val
                    self.phone_control_able = not val
                    juanlian_chengdu = round(self.get_juanlian_chengdu(), 2)
                    fengkou_chengdu = round(self.get_fengkou_chengdu(), 2)
                    self.send_pipe_conn.send({'lc': val, 'jua': juanlian_chengdu, 'fen': fengkou_chengdu})
                    # print("backend send: {}".format({'lc': val, 'jua': juanlian_chengdu, 'fen': fengkou_chengdu}))
                    # print("auto_run = {}".format(self.auto_run))
                
                elif key == "led":
                    # 切换补光灯状态
                    state_led = self.turn_led()
                    if state_led == "on":
                        self.turn_led("off")
                    else:
                        self.turn_led("on")
                
                elif key == "thres":
                    # 设置高温阈值
                    self.threshold_temp["high"] = recv_data[key]["h"]
                    self.threshold_temp["low"] = recv_data[key]["l"]
                    self.save_config({"temperature":self.threshold_temp})
                    self.send_pipe_conn.send({"t_ack":self.threshold_temp})
                    # print(self.threshold_temp, recv_data)


    # 连上服务器后 ready
    def ready_callable(self):
        self.internet_ok = True
        logger.success('iot device ready')

    def get_weather(self):
        s = self.update_weather()
        if s == 0:
            self.internet_ok = True
        # 每10分钟get一次天气，动作的上下浮动时间在60秒内  被scheduler运行的函数不能是协程,因为executor选的background
        self.scheduler_daily_tasks["update_wea"] = self.scheduler.add_job(self.update_weather, 
                                                                            'interval', 
                                                                            minutes=10, 
                                                                            max_instances=10,
                                                                            jitter=60, 
                                                                            id="update_wea")

    # 响应APP发送的{"get":"state"}信号 大约40s一次
    async def heartbeat_callable(self, msg):
        await self.num_temp_indoor.value(self.temperature_indoor).update()
        await self.num_temp_outdoor.value(self.temperature_outdoor).update()

        await self.num_humid_indoor.value(self.humidity_indoor).update()
        await self.num_humid_outdoor.value(self.humidity_outdoor).update()

        await self.num_light_indoor.value(self.light_indoor).update()
        await self.num_light_outdoor.value(self.light_outdoor).update()

        await self.btn_led.turn(self.turn_led()).update()

        if self.weather != None and self.weather_img!= None:
            self.weather_icon_app = __weather_icon_app__[self.weather_img]
            await self.tex_weather.text(self.weather).icon(self.weather_icon_app).update()

        await self.tex_rain.text("有雨" if self.is_rain else "无雨").icon("fad fa-raindrops" if self.is_rain else "fas fa-sun").update()

        juanlian = round(self.get_juanlian_chengdu(), 2)
        fengkou = round(self.get_fengkou_chengdu(), 2)

        await self.num_juanlian.value(juanlian).update()
        await self.num_fengkou.value(fengkou).update()

        if self.auto_run == True:
            await self.ran_juanlian.value(juanlian).update()
            await self.ran_fengkou.value(fengkou).update()

        await self.btn_manual.turn("off" if self.auto_run else "on").update()

    # 独立线程 电机动则发送实时电机程度 包括向服务器和向设备面板 每秒1次
    def realtime_motor_chengdu(self):
        while True:
            if self.pipe_update_realtime_able == False:
                sleep(1)
                continue
            if self.get_juanlian_state() != 0:
                val = round(self.get_juanlian_chengdu(), 2) # 上报的数据精确到2位小数
                self.send_pipe_conn.send({"jua": val})
                message = {"num-jua": {"val": val, "date": int(time())}}
                if self.mqtt_client != None:
                    if self.mqtt_client.client.is_connected():
                        self.mqtt_client.send_to_device(message, to_device=self.config.uuid)
                if self.auto_run:
                    message = {"ran-jua": {"val": val, "date": int(time())}}
                    if self.mqtt_client != None:
                        if self.mqtt_client.client.is_connected():
                            self.mqtt_client.send_to_device(message, to_device=self.config.uuid)
            if self.get_fengkou_state() != 0:
                val = round(self.get_fengkou_chengdu(), 2) # 上报的数据精确到2位小数
                self.send_pipe_conn.send({"fen": val})
                message = {"num-fen": {"val": val, "date": int(time())}}
                if self.mqtt_client != None:
                    if self.mqtt_client.client.is_connected():
                        self.mqtt_client.send_to_device(message, to_device=self.config.uuid)
                if self.auto_run:
                    message = {"ran-fen": {"val": val, "date": int(time())}}
                    if self.mqtt_client != None:
                        if self.mqtt_client.client.is_connected():
                            self.mqtt_client.send_to_device(message, to_device=self.config.uuid)
            sleep(1)

    # APP【手动调节】按钮的响应函数
    async def btn_manual_callable(self, received_data):
        if self.phone_control_able == False or self.safety_stop == True:
            await self.tex_notice.text("设备端已禁止手机控制。").update()
            return
        if received_data[self.btn_manual.key] == "on" and self.auto_run:
            self.auto_run = False
            juanlian = round(self.get_juanlian_chengdu(), 2)
            fengkou  = round(self.get_fengkou_chengdu(), 2)
            await self.ran_juanlian.value(juanlian).update()
            await self.ran_fengkou.value(fengkou).update()

        elif received_data[self.btn_manual.key] == "off" and not self.auto_run:
            self.auto_run = True
            
        await self.btn_manual.turn("off" if self.auto_run else "on").update()
        await self.tex_notice.text("").update()
    
    # APP 卷帘滑动条的响应函数
    async def ran_juanlian_callable(self, received_data):
        if self.auto_run == False:
            if self.phone_control_able == False or self.safety_stop == True:
                await self.tex_notice.text("设备端已禁止手机控制。").update()
                val = round(self.get_juanlian_chengdu(), 2)
                await self.ran_juanlian.value(val).update()
                return
            if self.get_fengkou_state() == 0:
                self.set_juanlian_chengdu(received_data[self.ran_juanlian.key])
                await self.tex_notice.text("").update()
                return
            else:
                await self.tex_notice.text("风口停止运行后，才能控制卷帘").update()
        else:
            await self.tex_notice.text("需要先启用手动调节模式。").update()
        await asyncio.sleep(0.5)
        val = round(self.get_juanlian_chengdu(), 2)
        await self.ran_juanlian.value(val).update()

    # APP 风口滑动条的响应函数
    async def ran_fengkou_callable(self, received_data):
        if self.auto_run == False:
            if self.phone_control_able == False or self.safety_stop == True:
                await self.tex_notice.text("设备端已禁止手机控制。").update()
                val = round(self.get_fengkou_chengdu(), 2)
                await self.ran_fengkou.value(val).update()
                return
            if self.get_juanlian_state() == 0:
                if 100-self.get_juanlian_chengdu() < self.juanlian_dev.get_speed():
                    self.set_fengkou_chengdu(received_data[self.ran_fengkou.key])
                    await self.tex_notice.text("").update()
                    return
                else:
                    await self.tex_notice.text("卷帘完全打开后，才能控制风口。").update()
            else:
                await self.tex_notice.text("卷帘停止运行后，才能控制风口。").update()
        else:
            await self.tex_notice.text("需要先启用手动调节模式。").update()
        await asyncio.sleep(0.5)
        val = round(self.get_fengkou_chengdu(), 2)
        await self.ran_fengkou.value(val).update()

    # APP【补光灯】的响应函数
    async def btn_led_callable(self, received_data):
        if received_data[self.btn_led.key] == "on":
            await self.btn_led.turn(self.turn_led("on")).update()
        if received_data[self.btn_led.key] == "off":
            await self.btn_led.turn(self.turn_led("off")).update()
    
    async def btn_juanlian_safety_stop_callable(self, received_data):
        self.safety_stop = True
        self.juanlian_dev.safety_stop()
        await self.tex_notice.text("卷帘电机已安全制动").update()
    
    async def btn_fengkou_safety_stop_callable(self, received_data):
        self.safety_stop = True
        self.fengkou_dev.safety_stop()
        await self.tex_notice.text("风口电机已安全制动").update()
    
    async def btn_clean_safety_stop_callable(self, received_data):
        self.safety_stop = False
        await self.tex_notice.text("制动状态已清除").update()

    # 使得在网络不通时，设备可以进行重连
    async def my_device_init(self):
        while True:
            try:
                await self.device_init()
                break
            except aiohttp_ClientConnectorError:
                # print("aiohttp.client_exceptions.ClientConnectorError")
                logger.error("aiohttp.client_exceptions.ClientConnectorError")
                logger.info("trying to reconnect...")
                await asyncio.sleep(5)

    # 每600s 向blinker broker发送http心跳包
    async def my_cloud_heartbeat(self):
        try:
            await self._cloud_heartbeat()
        except aiohttp_ClientConnectorError:
            logger.error("aiohttp.client_exceptions.ClientConnectorError")
            await asyncio.sleep(5)
    
    async def my_upload_data(self):
        while True:
            upload_data = {"temp_indoor" : self.temperature_indoor, "humid_indoor": self.humidity_indoor, "light_indoor": self.light_indoor,
                        "temp_outdoor": self.temperature_outdoor, "humid_outdoor": self.humidity_outdoor, "light_outdoor": self.light_outdoor,
                        "temp_web": self.temperature_web, "is_rain": (1 if self.is_rain else 0),
                        "juanlian_chengdu": self.get_juanlian_chengdu(), "fengkou_chengdu": self.get_fengkou_chengdu()}
            try:
                await self.saveTsData(upload_data)
            except aiohttp_ClientConnectorError:
                logger.error("my_upload_data: aiohttp.client_exceptions")
                await asyncio.sleep(300)
            
    async def main(self):
        tasks = [
            threading.Thread(target=self.auto_control, daemon=True, name="auto_control"),
            threading.Thread(target=self.realtime_motor_chengdu, daemon=True, name="realtime_motor_chengdu"),
            threading.Thread(target=self.pipe_receiver, daemon=True, name="pipe_receiver"),
            threading.Thread(target=self.get_weather, daemon=True, name="get_weather"),
            threading.Thread(target=asyncio.run, args=(self.my_device_init(),), daemon=True, name="my_device_init"),
            threading.Thread(target=asyncio.run, args=(self.mqttclient_init(),), daemon=True, name="mqttclient_init"),
            threading.Thread(target=asyncio.run, args=(self.my_cloud_heartbeat(),), daemon=True, name="cloud_heartbeat"),
            threading.Thread(target=asyncio.run, args=(self._receiver(),), daemon=True, name="_receiver"),
            threading.Thread(target=asyncio.run, args=(self.my_upload_data(),), daemon=True, name="my_upload_data"),
            threading.Thread(target=self.scheduler_run, daemon=True, name="blinker scheduler")
        ]

        if self.websocket:
            tasks.append(threading.Thread(target=asyncio.run, args=(self.init_local_service(),), name="websocket"))

        if self.ready_callable:
            tasks.append(threading.Thread(target=asyncio.run, args=(self._custom_runner(self.ready_callable),), name="blinker ready"))

        if self.voice_assistant:
            tasks.append(threading.Thread(target=asyncio.run, args=(self.voice_assistant.listen(),), name="voice_assistant"))

        # start
        for task in tasks:
            task.start()
            await asyncio.sleep(1.5)
        
        for task in tasks:
            task.join()

def backend_run(auth_key, yike_appid, yike_appsecret, city, debug, send_pipe_conn, recv_pipe_conn):
    if debug == False:
        logger.remove(handler_id=None)
        logger.add(workig_path + "log/LOG_{time:YYYY-MM-DD}.log",level="INFO", rotation="00:00", encoding="utf-8", retention="7 day", compression="zip", enqueue=True)
    
    dapeng = IotDevice (auth_key       = auth_key, 
                        yike_appid     = yike_appid, 
                        yike_appsecret = yike_appsecret, 
                        city           = city,
                        send_pipe_conn = send_pipe_conn,
                        recv_pipe_conn = recv_pipe_conn)
    dapeng.run()


if __name__ == '__main__':
    # 设置本进程名为 smart-dapeng-backend，可在bash用 [ps aux] 命令查看
    import setproctitle
    setproctitle.setproctitle("smart-dapeng-backend")
    backend_run(auth_key       = __auth_key__, 
                yike_appid     = __yike_appid__, 
                yike_appsecret = __yike_appsecret__, 
                city           = __local_city__,
                debug          = __DEBUG__,
                send_pipe_conn = None,
                recv_pipe_conn = None)
    