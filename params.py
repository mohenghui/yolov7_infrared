import time
import serial.tools.list_ports
from CamOperation_class import *

import sys
from PyQt5 import  QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import math
import cv2
import threading
from utils import *
from PIL import Image
import onnxruntime
import numpy as np
from PIL import Image
from MvImport.MvCameraControl_class import *
import qdarkstyle
class ChildWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.devList = []
        self.cam = None
        self.obj_cam_operation = None
        self.c_width = 0
        self.c_height = 0
        self.offsetx = 0
        self.offsety = 0
        self.exposure = 0
        self.gain = 0
        self.frame = 0
        self.ser = None
        self.serial_list = []

    def initUI(self):
        # self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setWindowTitle('设置工业相机参数')
        self.resize(500, 720)
        self.cb = QComboBox(self)
        self.cb.resize(120, 40)
        self.cb.move(130, 20)
        self.cb.currentTextChanged.connect(self.get_device)
        self.ser_cb = QComboBox(self)
        self.ser_cb.resize(120, 40)
        self.ser_cb.move(280, 20)
        self.ser_cb.currentTextChanged.connect(self.get_ser_device)
        self.device_button = QPushButton("搜索列表", self,
                                         objectName="RedButton", minimumHeight=20)
        # self.bind_trigger()
        self.device_button.clicked.connect(self.enum_devices)
        self.device_button.move(200, 70)
        self.device = None
        self.device_lable = QLabel(self)
        # self.label.setText("  {}".format(text))
        self.device_lable.setFixedSize(600, 20)
        # self.device_lable.setStyleSheet("font-size: 27pt")
        self.device_lable.move(60, 95)

        self.serial_lable = QLabel(self)
        # self.label.setText("  {}".format(text))
        self.serial_lable.setFixedSize(600, 20)
        # self.device_lable.setStyleSheet("font-size: 27pt")
        self.serial_lable.move(60, 120)

        self.get_param_button = QPushButton("获取参数", self,
                                            objectName="RedButton", minimumHeight=20)
        # self.bind_trigger()
        self.tip_text1 = QLabel(self)
        self.tip_text1.setFixedSize(40, 20)
        self.tip_text1.move(100, 175)
        self.tip_text1.setText("Width：")
        self.get_param_button.clicked.connect(self.get_param)
        self.get_param_button.move(200, 130)
        self.width_edit = QTextEdit(self)
        self.width_edit.resize(70, 40)
        self.width_edit.move(200, 160)
        self.tip_text2 = QLabel(self)
        self.tip_text2.setFixedSize(40, 20)
        self.tip_text2.move(100, 215)
        self.tip_text2.setText("Hidth：")
        self.height_edit = QTextEdit(self)
        self.height_edit.resize(70, 40)
        self.height_edit.move(200, 200)
        self.tip_text3 = QLabel(self)
        self.tip_text3.setFixedSize(50, 20)
        self.tip_text3.move(100, 255)
        self.tip_text3.setText("offsetx：")
        self.offsetx_edit = QTextEdit(self)
        self.offsetx_edit.resize(70, 40)
        self.offsetx_edit.move(200, 240)
        self.tip_text4 = QLabel(self)
        self.tip_text4.setFixedSize(50, 20)
        self.tip_text4.move(100, 295)
        self.tip_text4.setText("offsety：")
        self.offsety_edit = QTextEdit(self)
        self.offsety_edit.resize(70, 40)
        self.offsety_edit.move(200, 280)
        self.tip_text5 = QLabel(self)
        self.tip_text5.setFixedSize(50, 20)
        self.tip_text5.move(100, 335)
        self.tip_text5.setText("exposure：")
        self.exposure_edit = QTextEdit(self)
        self.exposure_edit.resize(70, 40)
        self.exposure_edit.move(200, 320)
        self.tip_text6 = QLabel(self)
        self.tip_text6.setFixedSize(40, 20)
        self.tip_text6.move(100, 375)
        self.tip_text6.setText("gain：")
        self.gain_edit = QTextEdit(self)
        self.gain_edit.resize(70, 40)
        self.gain_edit.move(200, 360)
        self.tip_text7 = QLabel(self)
        self.tip_text7.setFixedSize(40, 20)
        self.tip_text7.move(100, 415)
        self.tip_text7.setText("frame：")
        self.frame_edit = QTextEdit(self)
        self.frame_edit.resize(70, 40)
        self.frame_edit.move(200, 400)
        self.edit_button = QPushButton("修改参数", self,
                                       objectName="RedButton", minimumHeight=20)
        self.edit_button.clicked.connect(self.edit_param)
        self.edit_button.move(300, 450)
        self.edit_success = QLabel(self)
        self.edit_success.setFixedSize(90, 20)
        self.edit_success.move(300, 490)

    def get_device(self):
        self.device = self.cb.currentText()
        self.device_index = self.cb.currentIndex()
        self.device_lable.setText("你选择的工业摄像头是{}".format(self.device))
        if self.obj_cam_operation:
            self.obj_cam_operation.obj_cam.MV_CC_CloseDevice()
            self.obj_cam_operation.obj_cam.MV_CC_DestroyHandle()
        self.obj_cam_operation = CameraOperation(
            self.cam, deviceList, int(self.device_index))
        ret = self.obj_cam_operation.Open_device()
        self.get_param()
        if 0 != ret:
            print("检查占用")
        else:
            print("正常运行")

    def get_ser_device(self):
        self.ser_device = self.ser_cb.currentText()
        self.serial_lable.setText("你选择的串口是{}".format(self.ser_device))
        print("你选择的串口是{}".format(self.ser_device))
        try:
            self.ser = serial.Serial(
                self.ser_device, 9600, timeout=0.5)
        except:
            msg_box = QMessageBox(QMessageBox.Critical, '错误', '出现错误')
            msg_box.exec_()

    def get_param(self):
        c_width, c_height, offsetx, offsety, exposure, gain, frame, _ = self.obj_cam_operation.Get_parameter()
        # print(c_width,c_height,offsetx ,offsety ,exposure,gain,frame,_)
        self.width_edit.setPlainText(str(self.obj_cam_operation.width))
        self.height_edit.setPlainText(str(self.obj_cam_operation.height))
        self.offsetx_edit.setPlainText(str(self.obj_cam_operation.offsetx))
        self.offsety_edit.setPlainText(str(self.obj_cam_operation.offsety))
        self.exposure_edit.setPlainText(
            str(self.obj_cam_operation.exposure_time))
        self.gain_edit.setPlainText(str(self.obj_cam_operation.gain))
        self.frame_edit.setPlainText(str(self.obj_cam_operation.frame_rate))
        self.edit_success.setText("")

    def edit_param(self):
        width = int(self.width_edit.toPlainText())
        height = int(self.height_edit.toPlainText())
        offsetx = int(self.offsetx_edit.toPlainText())
        offsety = int(self.offsety_edit.toPlainText())
        exposure = float(self.exposure_edit.toPlainText())
        frame = float(self.frame_edit.toPlainText())
        gain = float(self.gain_edit.toPlainText())
        c_width, c_height, offsetx, offsety, exposure, frame, gain = self.obj_cam_operation.Set_parameter(
            width, height, offsetx, offsety, exposure, frame, gain)
        print(c_width, c_height, offsetx, offsety, exposure, frame, gain)
        if c_width == 0 and c_height == 0 and offsetx == 0 and offsety == 0 and exposure == 0 and frame == 0 and gain == 0:
            self.edit_success.setText("修改参数成功")
        else:
            print(c_width, c_height, offsetx, offsety, exposure, frame, gain)
            self.edit_success.setText("修改参数成功")

    def enum_devices(self):
        global deviceList
        global obj_cam_operation
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        if ret != 0:
            print('show error', 'enum devices fail! ret = ' + ToHexStr(ret))

        if deviceList.nDeviceNum == 0:
            print('show info', 'find no device!')

        print("Find %d devices!" % deviceList.nDeviceNum)

        devList = []
        for i in range(0, deviceList.nDeviceNum):
            mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(
                MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                chUserDefinedName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName:
                    if 0 == per:
                        break
                    chUserDefinedName = chUserDefinedName + chr(per)
                print("device model name: %s" % chUserDefinedName)

                nip1 = (
                    (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = (
                    (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = (
                    (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
                devList.append("["+str(i)+"]GigE: " + chUserDefinedName +
                               "(" + str(nip1)+"."+str(nip2)+"."+str(nip3)+"."+str(nip4) + ")")
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                chUserDefinedName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName:
                    if per == 0:
                        break
                    chUserDefinedName = chUserDefinedName + chr(per)
                print("device model name: %s" % chUserDefinedName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
                devList.append(
                    "["+str(i)+"]USB: " + chUserDefinedName + "(" + str(strSerialNumber) + ")")
        for i in devList:
            if i not in self.devList:
                self.devList.append(i)
                self.cb.addItem(i)
        ports_list = list(serial.tools.list_ports.comports())
        if len(ports_list) <= 0:
            print("无串口设备。")
        else:
            for comport in ports_list:
                name, detail = list(comport)[0], list(comport)[1]
                if name not in self.serial_list:
                    self.serial_list.append(name)
                    self.ser_cb.addItem(name)