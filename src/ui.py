#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 设备上GUI界面代码

"""
Created on 2018年5月29日
@author: Irony
@site: https://pyqt.site , https://github.com/PyQt5
@email: 892768447@qq.com
@file: LeftTabWidget
@description:
"""

from tabnanny import check
from threading import Thread
from time import sleep

from PyQt5.QtCore import Qt, QSize, QTimer, QDateTime
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QStackedWidget, QHBoxLayout, \
    QListWidgetItem, QLabel, QVBoxLayout, QPushButton, QRadioButton, QTextBrowser, QSlider, QCheckBox, \
    QMessageBox, QSpinBox

class RealDataWidget(QWidget):
    def __init__(self):
        super(RealDataWidget, self).__init__()
        self.v_layout = QVBoxLayout(self)
        # self.layout.setSpacing(0)
        self.initUI()
    def initUI(self):
        self.labels0 = []
        self.labels1 = []
        self.labels2 = []
        self.labels3 = []
        self.labels4 = []
        self.labelss = []
        
        self.labels0.append(QLabel("{}        天气：{}".format(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss  ddd"), "未知")))
        self.labels1.append(QLabel("棚内温度：{}℃".format(0)))
        self.labels1.append(QLabel("棚外温度：{}℃".format(0)))
        self.labels2.append(QLabel("棚内湿度：{}%RH".format(0)))
        self.labels2.append(QLabel("棚外湿度：{}%RH".format(0)))
        self.labels3.append(QLabel("棚内照度：{}Lux".format(0)))
        self.labels3.append(QLabel("棚外照度：{}Lux".format(0)))
        self.labels4.append(QLabel("卷帘打开：{}%".format(0)))
        self.labels4.append(QLabel("风口打开：{}%".format(0)))

        self.labelss.append(self.labels0)
        self.labelss.append(self.labels1)
        self.labelss.append(self.labels2)
        self.labelss.append(self.labels3)
        self.labelss.append(self.labels4)

        # self.v_layout.setSpacing(20)
        for labels in self.labelss:
            layout = QHBoxLayout()
            for label in labels:
                label.setTextFormat(Qt.AutoText)
                label.setAlignment(Qt.AlignCenter)
                # label.setStyleSheet( '''color: black;
                #                         background: white;
                #                         margin-top: 10px;
                #                         margin-left: 5px;
                #                         margin-right: 5px;
                #                         padding:15px;
                #                         font-size: 25px;''')
                # label.setMaximumWidth(300)
                label.setMinimumHeight(80)
                layout.addWidget(label)
            self.v_layout.addLayout(layout)

        layout = QHBoxLayout()
        hidden_label = QLabel("")
        hidden_label.setStyleSheet('''background: rgba(240, 240, 240, 0);''')
        hidden_label.setMinimumHeight(40)
        layout.addWidget(hidden_label)
        self.v_layout.addLayout(layout)

    
class ParamSetWidget(QWidget):
    def __init__(self, pipe_send_conn, page_control, *args, **kwargs):
        super(ParamSetWidget, self).__init__(*args, **kwargs)
        self.pipe_send_conn = pipe_send_conn
        self.setting_able = False
        self.recved_ack = False
        self.page_control = page_control
        self.initUI()
        self.initLogic()
        
    def initUI(self):
        self.v_layout = QVBoxLayout(self)
        self.h_layout_0 = QHBoxLayout()
        self.h_layout_1 = QHBoxLayout()
        
        self.textBrowser_title = QTextBrowser()
        self.textBrowser_title.setText('''<p>本软件通过控制电机的通电时长，间接控制卷帘（风口）的打开程度。因此，测量电机在卷帘（风口）在关闭和打开过程中的运行时间是必要的。</p>
                                        <p><b>操作方法：</b></p>
                                        <p>
                                        1.勾选【开始设置】，设备退出自动模式，进入设置模式；<br>
                                        2.选择【卷帘机】或【放风机】；<br>
                                        3.点击【正转】或【反转】按钮，当使得卷帘（风口）完全关闭时，点击【停转】按钮，使电机停转；<br>
                                        4.点击【开始计时】按钮，当使得卷帘（风口）完全打开时，点击【停止计时】按钮；<br>
                                        5.点击【保存计时】按钮，保存电机在运行过程中所需时间；<br>
                                        6.取消勾选【开始设置】，设备退出设置模式，恢复自动模式。</p>
                                        <p><b>注意事项：</b></p>
                                        <p>在测量放风机运行时间前，一定要确保卷帘完全打开，否则放风机会被<b style="color: red;">卡住</b>！！！</p>''')
        self.textBrowser_title.setEnabled(False)
        # self.textBrowser_title.setAlignment(Qt.AlignCenter)
        self.textBrowser_title.setFontPointSize(500)
        # self.textBrowser_title.setMaximumHeight(200)

        self.checkbox_setAble = QCheckBox()
        self.checkbox_setAble.setText("开始设置")
        self.checkbox_setAble.setChecked(False)
        self.radio_button_juanlian = QRadioButton("卷帘机")
        self.radio_button_juanlian.setChecked(True)
        self.radio_button_fengkou  = QRadioButton("放风机")
        # self.radio_button_fengkou.setCheckable(False)

        self.label_text = QLabel("已运行")
        self.label_time_counter = QLabel("{}".format(0))
        self.label_unit = QLabel("秒")
        self.label_unit.setMaximumWidth(50)
        self.label_text.setAlignment(Qt.AlignCenter)
        self.label_time_counter.setAlignment(Qt.AlignCenter)
        self.label_unit.setAlignment(Qt.AlignCenter)

        self.button_start = QPushButton("开始计时")
        self.button_stop  = QPushButton("停止计时")
        self.button_confirm = QPushButton("保存计时")

        self.button_motor_forward = QPushButton("正转")
        self.button_motor_backward = QPushButton("反转")
        self.button_motor_stop = QPushButton("停转")

        state = False
        self.button_start.setEnabled(state)
        self.button_stop.setEnabled(state)
        self.button_confirm.setEnabled(state)
        self.button_motor_forward.setEnabled(state)
        self.button_motor_backward.setEnabled(state)
        self.button_motor_stop.setEnabled(state)


        self.v_layout.addLayout(self.h_layout_0)
        self.v_layout.addLayout(self.h_layout_1)
        
        layout = QVBoxLayout()
        self.h_layout_1.addLayout(layout)
        layout.addWidget(self.checkbox_setAble)
        layout.addWidget(self.radio_button_juanlian)
        layout.addWidget(self.radio_button_fengkou)

        self.h_layout_1.addWidget(self.label_text)
        self.h_layout_1.addWidget(self.label_time_counter)
        self.h_layout_1.addWidget(self.label_unit)

        layout = QVBoxLayout()
        self.h_layout_1.addLayout(layout)
        layout.addWidget(self.button_start)
        layout.addWidget(self.button_stop)
        layout.addWidget(self.button_confirm)

        layout = QVBoxLayout()
        self.h_layout_1.addLayout(layout)
        layout.addWidget(self.button_motor_forward)
        layout.addWidget(self.button_motor_backward)
        layout.addWidget(self.button_motor_stop)

        self.h_layout_0.addWidget(self.textBrowser_title)

    def initLogic(self):

        self.time_count_num = 0
        def time_increase(dt):
            self.time_count_num += dt
            self.label_time_counter.setText("%.1f"%(self.time_count_num/1000))

        self.dt = 100 # 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(lambda:time_increase(self.dt))

        self.checkbox_setAble.clicked.connect(self.on_clicked_checkbox_setAble)

        self.button_start.clicked.connect(self.on_clicked_button_start)
        self.button_stop.clicked.connect(self.on_clicked_button_stop)
        self.button_confirm.clicked.connect(self.on_clicked_button_confirm)

        self.button_motor_backward.clicked.connect(lambda: self.on_clicked_button_motor('b'))
        self.button_motor_forward.clicked.connect(lambda: self.on_clicked_button_motor('f'))
        self.button_motor_stop.clicked.connect(lambda: self.on_clicked_button_motor('s'))

        def task():
            while True:
                if self.recved_ack == True:
                    if self.setting_able == self.checkbox_setAble_state:
                        self.button_start.setEnabled(self.checkbox_setAble_state)
                        self.button_stop.setEnabled(self.checkbox_setAble_state)
                        self.button_confirm.setEnabled(self.checkbox_setAble_state)

                        self.button_motor_forward.setEnabled(self.checkbox_setAble_state)
                        self.button_motor_backward.setEnabled(self.checkbox_setAble_state)
                        self.button_motor_stop.setEnabled(self.checkbox_setAble_state)
                    self.recved_ack = False
                sleep(0.5)

        thread_task = Thread(target=task, daemon=True)
        thread_task.start()

    def on_clicked_checkbox_setAble(self):
        self.checkbox_setAble_state = self.checkbox_setAble.isChecked()
        
        if self.checkbox_setAble_state == True:
            self.sendSignal({'set':True}) # 关闭本地手动控制
            self.page_control.checkbox_local_control.setEnabled(False)
            self.page_control.slider_jualian.setEnabled(False)
            self.page_control.slider_fengkou.setEnabled(False)
            self.radio_button_juanlian.setEnabled(True)
            self.radio_button_fengkou.setEnabled(True)
        else:
            self.sendSignal({'set':False})
            self.page_control.checkbox_local_control.setEnabled(True)
            self.page_control.slider_jualian.setEnabled(self.page_control.local_control_able)
            self.page_control.slider_fengkou.setEnabled(self.page_control.local_control_able)
            self.radio_button_juanlian.setEnabled(False)
            self.radio_button_fengkou.setEnabled(False)

    def on_clicked_button_start(self):
        self.time_count_num = 0
        self.label_time_counter.setText("0")
    
        self.button_motor_forward.setEnabled(False)
        self.button_motor_backward.setEnabled(False)
        self.button_motor_stop.setEnabled(False)
        self.button_start.setEnabled(False)
        self.button_confirm.setEnabled(False)
        self.checkbox_setAble.setEnabled(False)
        self.radio_button_juanlian.setEnabled(False)
        self.radio_button_fengkou.setEnabled(False)

        if self.radio_button_juanlian.isChecked():
            self.sendSignal({'jf': ''})
        if self.radio_button_fengkou.isChecked():
            self.sendSignal({'ff': ''})
        
        self.timer.start(self.dt)

        
    
    def on_clicked_button_stop(self):
        self.button_start.setEnabled(True)
        self.button_motor_forward.setEnabled(True)
        self.button_motor_backward.setEnabled(True)
        self.button_motor_stop.setEnabled(True)
        self.button_start.setEnabled(True)
        self.button_confirm.setEnabled(True)
        self.checkbox_setAble.setEnabled(True)
        self.radio_button_juanlian.setEnabled(False)
        self.radio_button_fengkou.setEnabled(False)

        if self.radio_button_juanlian.isChecked():
            self.sendSignal({'js': ''})
        if self.radio_button_fengkou.isChecked():
            self.sendSignal({'fs': ''})

        self.timer.stop()

    def on_clicked_button_confirm(self):
        if self.time_count_num == 0:
            return
        speed = round(100000/self.time_count_num, 6) # 100(%)/x/1000ms 精确到6位小数
        if self.radio_button_juanlian.isChecked():
            self.sendSignal({'jsp': speed})
        if self.radio_button_fengkou.isChecked():
            self.sendSignal({'fsp': speed})
        self.radio_button_juanlian.setEnabled(True)
        self.radio_button_fengkou.setEnabled(True)
    
    def on_clicked_button_motor(self, mode):
        # mode = 's','f','b' means stop,forward,back
        cmd = None
        if self.radio_button_juanlian.isChecked():
            cmd = 'j'
        elif self.radio_button_fengkou.isChecked():
            cmd = 'f'
        cmd += mode
        self.sendSignal({cmd:''})
        if mode != 's':
            self.button_motor_forward.setEnabled(False)
            self.button_motor_backward.setEnabled(False)
            self.button_start.setEnabled(False)
            self.button_stop.setEnabled(False)
            self.button_confirm.setEnabled(False)
            self.checkbox_setAble.setEnabled(False)
            self.radio_button_juanlian.setEnabled(False)
            self.radio_button_fengkou.setEnabled(False)
        else:
            self.button_motor_forward.setEnabled(True)
            self.button_motor_backward.setEnabled(True)
            self.button_start.setEnabled(True)
            self.button_stop.setEnabled(True)
            self.button_confirm.setEnabled(True)
            self.checkbox_setAble.setEnabled(True)
            self.radio_button_juanlian.setEnabled(True)
            self.radio_button_fengkou.setEnabled(True)
    
    def sendSignal(self, data):
        self.pipe_send_conn.send(data)


class ParamSetWidget2(QWidget):
    def __init__(self, pipe_send_conn, *args, **kwargs):
        super(ParamSetWidget2, self).__init__(*args, **kwargs)
        self.pipe_send_conn = pipe_send_conn
        self.recved_ack = False
        self.temp_threshold = {"high": 31, "low": 28}
        self.initUI()
        self.initLogic()
    def initUI(self):
        self.label_tempHigh = QLabel("高温阈值（℃）")
        self.label_tempLow  = QLabel("低温阈值（℃）")
        self.label_tempHigh.setMinimumHeight(60)
        self.label_tempLow.setMinimumHeight(60)
        self.spinBox_tempHigh = QSpinBox()
        self.spinBox_tempLow  = QSpinBox()
        self.spinBox_tempHigh.setValue(31)
        self.spinBox_tempLow.setValue(28)
        self.spinBox_tempHigh.setMinimumHeight(60)
        self.spinBox_tempLow.setMinimumHeight(60)
        self.button_confirm = QPushButton()
        self.button_confirm.setText("确认")
        self.label_notice = QLabel("高温阈值")
        self.label_notice.setMaximumHeight(60)

        self.v_layout = QVBoxLayout(self)
        self.h_layout_0 = QHBoxLayout()
        self.h_layout_1 = QHBoxLayout()
        self.h_layout_2 = QHBoxLayout()
        self.h_layout_3 = QHBoxLayout()

        self.h_layout_0.addWidget(self.label_notice)
        self.h_layout_1.addWidget(self.label_tempHigh)
        self.h_layout_1.addWidget(self.spinBox_tempHigh)
        self.h_layout_2.addWidget(self.label_tempLow)
        self.h_layout_2.addWidget(self.spinBox_tempLow)
        self.h_layout_3.addWidget(self.button_confirm)

        self.v_layout.addLayout(self.h_layout_0)
        self.v_layout.addLayout(self.h_layout_1)
        self.v_layout.addLayout(self.h_layout_2)
        self.v_layout.addLayout(self.h_layout_3)

    def initLogic(self):
        self.button_confirm.clicked.connect(self.onclick_button_confirm)
        def task():
            while True:
                if self.recved_ack == True:
                    self.spinBox_tempHigh.setValue(self.temp_threshold["high"])
                    self.spinBox_tempLow.setValue(self.temp_threshold["low"])
                    self.label_notice.setText(f"已更新高温阈值{self.temp_threshold['high']}℃，低温阈值{self.temp_threshold['low']}℃")
                    self.recved_ack = False
                sleep(0.1)
        thread_task = Thread(target=task, daemon=True)
        thread_task.start()
    
    def onclick_button_confirm(self):
        th = self.spinBox_tempHigh.value()
        tl = self.spinBox_tempLow.value()
        if th <= tl:
            self.label_notice.setText("高温阈值需要高于低温阈值")
            return
        self.pipe_send_conn.send({"thres": {"h":th,"l":tl}})


        

class ControlPanelWidget(QWidget):
    def __init__(self, pipe_send_conn, *args, **kwargs):
        super(ControlPanelWidget, self).__init__(*args, **kwargs)

        self.local_control_able = False
        self.recved_ack = False
        self.checkbox_local_control_state = False

        self.pipe_send_conn = pipe_send_conn
        self.initUI()
        self.initLogic()

    def initUI(self):
        self.v_layout = QVBoxLayout(self)
        self.h_layout_0 = QHBoxLayout()
        self.h_layout_1 = QHBoxLayout()
        self.h_layout_2 = QHBoxLayout()
        self.h_layout_3 = QHBoxLayout()
        self.h_layout_4 = QHBoxLayout()

        self.checkbox_local_control = QCheckBox()
        self.checkbox_local_control.setChecked(False)
        self.checkbox_local_control.setText("本地手动控制（同时手机控制被禁用）")

        self.label_text_juanlian = QLabel("卷帘")
        self.label_text_fengkou  = QLabel("风口")
        self.label_text_juanlian.setMaximumHeight(60)
        self.label_text_fengkou.setMaximumHeight(60)

        self.slider_jualian = QSlider()
        self.slider_jualian.setOrientation(Qt.Horizontal)
        self.slider_fengkou = QSlider()
        self.slider_fengkou.setOrientation(Qt.Horizontal)

        self.label_target_juanlian = QLabel("0")
        self.label_target_fengkou  = QLabel("0")
        self.label_target_juanlian.setMaximumHeight(60)
        self.label_target_fengkou.setMaximumHeight(60)
        self.label_target_juanlian.setMinimumWidth(70)
        self.label_target_fengkou.setMinimumWidth(70)
        self.label_target_juanlian.setAlignment(Qt.AlignCenter)
        self.label_target_fengkou.setAlignment(Qt.AlignCenter)

        self.button_led = QPushButton()
        self.button_led.setText("补光灯开关")
        self.button_juanlian_safety_stop = QPushButton()
        self.button_fengkou_safety_stop  = QPushButton()
        self.button_clean_safety_stop    = QPushButton()
        self.button_juanlian_safety_stop.setText("卷帘电机制动")
        self.button_fengkou_safety_stop.setText("风口电机制动")
        self.button_clean_safety_stop.setText("清除制动状态")
        
        self.v_layout.addLayout(self.h_layout_0)
        self.h_layout_0.addStretch(1)
        self.h_layout_0.addWidget(self.checkbox_local_control)
        self.h_layout_0.addStretch(1)
        
        self.v_layout.addLayout(self.h_layout_1)
        self.h_layout_1.addWidget(self.label_text_juanlian)
        self.h_layout_1.addWidget(self.slider_jualian)
        self.h_layout_1.addWidget(self.label_target_juanlian)

        self.v_layout.addLayout(self.h_layout_2)

        self.v_layout.addLayout(self.h_layout_3)
        self.h_layout_3.addWidget(self.label_text_fengkou)
        self.h_layout_3.addWidget(self.slider_fengkou)
        self.h_layout_3.addWidget(self.label_target_fengkou)

        self.v_layout.addLayout(self.h_layout_4)
        self.h_layout_4.addWidget(self.button_juanlian_safety_stop)
        self.h_layout_4.addWidget(self.button_fengkou_safety_stop)
        self.h_layout_4.addWidget(self.button_clean_safety_stop)
        self.h_layout_4.addWidget(self.button_led)
    
    def initLogic(self):
        self.checkbox_local_control.setChecked(self.local_control_able)
        self.slider_jualian.setEnabled(self.local_control_able)
        self.slider_fengkou.setEnabled(self.local_control_able)

        self.checkbox_local_control.clicked.connect(self.onclick_checkbox_local_control)
        self.slider_jualian.setTracking(False)
        self.slider_jualian.setMaximum(100)
        self.slider_jualian.valueChanged.connect(self.valueChange_juanlian)
        self.slider_fengkou.setTracking(False)
        self.slider_fengkou.setMaximum(100)
        self.slider_fengkou.valueChanged.connect(self.valueChange_fengkou)
        self.button_led.clicked.connect(lambda: self.pipe_send_conn.send({'led':''}))
        self.button_juanlian_safety_stop.clicked.connect(lambda: self.pipe_send_conn.send({'jst':''}))
        self.button_fengkou_safety_stop.clicked.connect(lambda: self.pipe_send_conn.send({'fst':''}))
        self.button_clean_safety_stop.clicked.connect(lambda: self.pipe_send_conn.send({'cst':''}))

        def task():
            while True:
                if self.recved_ack == True:
                    if self.local_control_able == self.checkbox_local_control_state:
                        self.slider_jualian.setEnabled(self.local_control_able)
                        self.slider_fengkou.setEnabled(self.local_control_able)
                    self.recved_ack = False
                sleep(0.5)
        thread_task = Thread(target=task, daemon=True)
        thread_task.start()


    def onclick_checkbox_local_control(self):
        self.checkbox_local_control_state = self.checkbox_local_control.isChecked()
        self.pipe_send_conn.send({"lc": self.checkbox_local_control_state})

        # self.slider_jualian.setEnabled(self.local_control_able)
        # self.slider_fengkou.setEnabled(self.local_control_able)
    
    def valueChange_juanlian(self):
        val = self.slider_jualian.value()
        # print("juanlian: {}".format(val))
        self.label_target_juanlian.setText(str(val))
        self.pipe_send_conn.send({"jsc": val})
    def valueChange_fengkou(self):
        val = self.slider_fengkou.value()
        # print("fengkou: {}".format(val))
        self.label_target_fengkou.setText(str(val))
        self.pipe_send_conn.send({"fsc": val})

    




class LeftTabWidget(QWidget):

    def __init__(self, pipe_conn_recv, pipe_conn_send, *args, **kwargs):
        super(LeftTabWidget, self).__init__(*args, **kwargs)
        # self.setMaximumSize(800,480)
        # self.resize(800, 480)
        # 左右布局(左边一个QListWidget + 右边QStackedWidget)
        self.pipe_conn_recv = pipe_conn_recv
        self.pipe_recv_data = None
        self.recv_data_empty = True

        self.pipe_conn_send = pipe_conn_send

        layout = QHBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        # 左侧列表
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)
        # 右侧层叠窗口
        self.stackedWidget = QStackedWidget(self)
        layout.addWidget(self.stackedWidget)
        self.initUi()

    def initUi(self):
        # 隐藏鼠标光标
        self.setCursor(Qt.BlankCursor)
        # 通过QListWidget的当前item变化来切换QStackedWidget中的序号
        self.listWidget.currentRowChanged.connect(self.stackedWidget.setCurrentIndex)
        # 去掉边框
        self.listWidget.setFrameShape(QListWidget.NoFrame)
        # 隐藏滚动条
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.listWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # self.setStyleSheet("background-image:url(./img/plant.jpg)")
        
        items = []
        items.append(QListWidgetItem(str('实时数据'), self.listWidget))
        items.append(QListWidgetItem(str('运行控制'), self.listWidget))
        items.append(QListWidgetItem(str('参数设置'), self.listWidget))
        items.append(QListWidgetItem(str('参数设置2'), self.listWidget))
        items.append(QListWidgetItem(str('使用说明'), self.listWidget))
        items.append(QListWidgetItem(str(' 关  于 '), self.listWidget))
        for item in items:
            item.setSizeHint(QSize(0, 70))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Arial", 15))
        items[0].setSelected(True)

        # 再模拟20个右侧的页面(就不和上面一起循环放了)
        # for i in range(8):
        #     label = QLabel('我是页 %d' % i, self)
        #     label.setAlignment(Qt.AlignCenter)
        #     # 设置label的背景颜色(这里随机)
        #     # 这里加了一个margin边距(方便区分QStackedWidget和QLabel的颜色)
        #     label.setStyleSheet('background: rgb(%d, %d, %d);' % (
        #         randint(0, 255), randint(0, 255), randint(0, 255)))
        #     self.stackedWidget.addWidget(label)

        self.page0 = RealDataWidget()
        self.page1 = ControlPanelWidget(self.pipe_conn_send)
        self.page2 = ParamSetWidget(self.pipe_conn_send, self.page1)
        self.page3 = ParamSetWidget2(self.pipe_conn_send)
        self.page4 = QLabel("page4")
        self.page5 = QLabel("page5")

        self.stackedWidget.addWidget(self.page0)
        self.stackedWidget.addWidget(self.page1)
        self.stackedWidget.addWidget(self.page2)
        self.stackedWidget.addWidget(self.page3)
        self.stackedWidget.addWidget(self.page4)
        self.stackedWidget.addWidget(self.page5)
        # self.setWindowFlags(Qt.FramelessWindowHint)

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_func)
        self.timer.start(500)

        if self.pipe_conn_recv != None:
            pipe_recv_thread = Thread(target=self.recvFromPipe, daemon=True)
            pipe_recv_thread.start()
    
    def recvFromPipe(self):
        while True:
            self.pipe_recv_data = self.pipe_conn_recv.recv()
            self.recv_data_empty = False
            if self.recv_data_empty == False:
                self.update_page(self.pipe_recv_data)
                self.recv_data_empty = True

    def timer_func(self):
        weather = self.page0.labels0[0].text().split("：")[-1]
        self.page0.labels0[0].setText("{}        天气：{}".format(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss  ddd"), weather))
        # if self.recv_data_empty == False:
        #     self.update_page(self.pipe_recv_data)
        #     self.recv_data_empty = True

    def update_page(self, data):
        for key in data:
            if key == 'wea':
                if data[key] != None:
                    self.page0.labels0[0].setText("{}        天气：{}".format(QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss  ddd"), data[key]))
            elif key == 'ti':
                self.page0.labels1[0].setText('棚内温度：{}℃'.format(data[key]))
            elif key == 'to':
                self.page0.labels1[1].setText('棚外温度：{}℃'.format(data[key]))
            elif key == 'hi':
                self.page0.labels2[0].setText('棚内湿度：{}%RH'.format(data[key]))
            elif key == 'ho':
                self.page0.labels2[1].setText('棚外湿度：{}%RH'.format(data[key]))
            elif key == 'li':
                self.page0.labels3[0].setText('棚内照度：{}Lux'.format(data[key]))
            elif key == 'lo':
                self.page0.labels3[1].setText('棚外照度：{}Lux'.format(data[key]))
            elif key == 'jua':
                self.page0.labels4[0].setText('卷帘打开：{}%'.format(data[key]))
                if self.page1.local_control_able == False:
                    self.page1.slider_jualian.setValue(data[key])
            elif key == 'fen':
                self.page0.labels4[1].setText('风口打开：{}%'.format(data[key]))
                if self.page1.local_control_able == False:
                    self.page1.slider_fengkou.setValue(data[key])
            elif key == 'set':
                self.page2.recved_ack = True
                if data[key] == True:
                    self.page2.setting_able = True
                elif data[key] == False:
                    self.page2.setting_able = False
            elif key == 'lc':
                self.page1.recved_ack = True
                if data[key] == True:
                    self.page1.local_control_able = True
                elif data[key] == False:
                    self.page1.local_control_able = False
            elif key == 't_ack':
                # {'t_ack':[th, tl]}
                self.page3.temp_threshold['high'] = data[key]['high']
                self.page3.temp_threshold['low']  = data[key]['low']
                self.page3.recved_ack = True
            else:
                pass




# 美化样式表
Stylesheet = """
/*去掉item虚线边框*/
QListWidget, QListView, QTreeWidget, QTreeView {
    outline: 0px;
}
/*设置左侧选项的最小最大宽度,文字颜色和背景颜色*/
QListWidget {
    min-width: 120px;
    max-width: 120px;
    color: black;
    background: rgb(235, 235, 235);
}
QListWidget::item {
    background: rgb(255, 255, 255);
    border-bottom: 2px solid rgb(225, 225, 225);
}

/*被选中时的背景颜色和左边框颜色*/
QListWidget::item:selected {
    background: rgb(30, 144, 255);
    border-right: 2px solid rgb(9, 187, 7);
}
/*鼠标悬停颜色*/
HistoryPanel::item:hover {
    background: rgb(52, 52, 52);
}

/*右侧的层叠窗口的背景颜色*/
QStackedWidget {
    background: rgb(240, 240, 240);
}
/*模拟的页面*/
QLabel {
    color: black;
    background: white;
    margin-top: 10px;
    margin-left: 5px;
    margin-right: 5px;
    padding:0px;
    font-size: 25px;
}

QPushButton {
    
    min-width: 80px;
    max-width: 200px;
    font-size: 25px;
}

QRadioButton {
    color: black;
    max-width: 120px;
    font-size: 25px;
    margin-top: 0px;
    margin-bottom: 0px;
}

QTextBrowser {
    font-size: 22px;
    color: black;
}

QCheckBox {
    font-size: 25px;
}

"""

if __name__ == '__main__':
    import sys
    from multiprocessing import Pipe
    parent_conn1, child_conn1 = Pipe()
    parent_conn2, child_conn2 = Pipe()
    app = QApplication(sys.argv)
    app.setStyleSheet(Stylesheet)

    widget = LeftTabWidget(parent_conn2, child_conn1)
    # w = LeftTabWidget(parent_conn2, child_conn1)
    widget.showFullScreen()
    sys.exit(app.exec_())