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
from utils.general import scale_coords,scale_coords_new
#nuitka --standalone --show-progress --show-memory --enable-plugin=pyqt5 --output-dir=out demo_onnx.py
#第一套机械臂方案
from detect_app import Detect_app
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
        self.resize(480, 640)
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
class ResizeWindow(QMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)
        self.scale=1
        self.initUI()
    
    def initUI(self):
        pass
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super(MainWindow, self).__init__(*args, **kwargs)
        self.initUI()
        self.init_model()
        self.t1 = None
        self.t2 = None
        self.img=None
        self.g_open = False
        self.open = False
        self.start_predict = False
        NO1_open = '01 05 00 00 FF 00 8C 3A'  # "上灯"
        NO1_down = "01 05 00 00 00 00 CD CA"

        NO2_open = "01 05 00 01 FF 00 DD FA"
        NO2_down = "01 05 00 01 00 00 9C 0A"

        NO3_open = "01 05 00 02 FF 00 2D FA"
        NO3_down = "01 05 00 02 00 00 6C 0A"

        NO4_open = "01 05 00 03 FF 00 7C 3A"
        NO4_down = "01 05 00 03 00 00 3D CA"

        self.NO1_collect="01 02 00 00 00 04 79 C9"
        self.NO1_get_on="01 02 01 01"
        self.NO1_get_off="01 02 01 00"
        self.predict_index = 0
        self.light_num = 4
        self.t4=None
        self.index=0
        self.listen_open=True
        self.predict_light = [NO1_open, NO2_open, NO3_open,
                              NO4_open, NO1_down, NO2_down, NO3_down, NO4_down]
        self.show_timeout_open=True
        self.send_open=False
        self.move_start=False
        self.catch_start=False

        self.out_start=False
        if self.listen_open:
            self.t3 = threading.Thread(target=self.listen_sign)
            self.t3.start()
        # if self.show_timeout_open:
        #     self.t4 = threading.Thread(target=self.show_timeout)
        #     self.t4.start()  
    def preprocess(self,img):
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img=Image.fromarray(img)
        img = img.resize((self.w, self.h), Image.BILINEAR)
        img_data = np.array(img)
        img_data=img_data.reshape((self.h,self.w,-1))
        img_data = np.transpose(img_data, [2, 0, 1])
        img_data = np.expand_dims(img_data, 0)
        mean_vec = np.array([0.5])
        stddev_vec = np.array([0.5])
        norm_img_data = np.zeros(img_data.shape).astype('float32')
        for i in range(img_data.shape[1]):
            norm_img_data[:, i, :, :] = (img_data[:, i, :, :] / 255 - mean_vec[i]) / stddev_vec[i]
        return norm_img_data.astype('float32'), np.array(img)
    def init_model(self):
        # self.w,self.h=224,224
        # self.NUMCLASS = 3
        # self.INPUT_CHANNEL = 1
        # self.INPUT_SIZE = 224
        # self.model = onnxruntime.InferenceSession('output/chicken_model.onnx')
        # self.model.get_modelmeta()
        weight_path="best_head.pt"
        self.model=Detect_app(weights=weight_path,device="0",half=True,augment=False,conf_thres=0.25,iou_thres=0.45,classes=None,agnostic_nms=False,img_size=640)
        # self.model=Detect_app(weights=weight_path,device="cpu",half=False,augment=False,conf_thres=0.25,iou_thres=0.45,classes=None,agnostic_nms=False,img_size=640)
# python export.py --weights yolov7-tiny.pt --grid --end2end --simplify --topk-all 100 --iou-thres 0.65 --conf-thres 0.35 --img-size 640 640 --max-wh 640
    def out_serial(self):
        if self.predict_index == 2 or not self.child.ser:
            return
        k = bytes.fromhex(self.predict_light[self.predict_index])
        d = bytes.fromhex(
            self.predict_light[self.predict_index+self.light_num])

        # 串口发送数据
        success_bytes = self.child.ser.write(k)
        end_code=success_bytes//2+4
        data=[]
        for _ in range(end_code):
            tmp=self.child.ser.read(1)
            data.append(tmp.hex())
        time.sleep(2)
        success_bytes =self.child.ser.write(d)
        data=[]
        end_code=success_bytes//2+4
        for _ in range(end_code):
            tmp=self.child.ser.read(1)
            data.append(tmp.hex())
    def predict(self, img):
        start_time=time.time()
        result=self.model.run(img)
        end_time=time.time()
        print("推理的时间是",end_time-start_time)
        return result

    def get_start_predict(self):
        self.start_predict = True

    def get_close_predict(self):
        self.start_predict = False

    def init_pic_label(self, text):
        self.label = QLabel(self)
        self.label.setText("  {}".format(text))
        self.label.setStyleSheet("font-size: 27pt")
        self.label.setFixedSize(640, 480)
        self.label.move(500, 300)

    def initUI(self):
        self.resize(1920, 1080)
        self.setWindowTitle("智屏微小鸡性别检测")
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("&配置参数")
        # self.button_menu = QAction(QIcon("./assests/编辑.svg"), "设置镜头参数", self)
        self.button_menu = QAction( "设置镜头参数", self)
        self.button_menu.setStatusTip("编辑你的设置")
        self.button_menu.triggered.connect(self.changeCheck1)

        self.button_setsize=QAction("设置窗口大小",self)
        self.button_setsize.setStatusTip("设置窗口分辨率")
        self.button_setsize.triggered.connect(self.set_size)
        self.file_menu.addAction(self.button_menu)
        self.file_menu.addAction(self.button_setsize)
        self.child = ChildWindow()
        self.button1 = QPushButton("从文件夹中选择", self,
                                   objectName="RedButton", minimumHeight=48)
        # self.bind_trigger()
        self.init_pic_label("显示图片")
        self.button1.clicked.connect(self.open_image)
        self.button1.move(10, 40)
        self.cap = cv2.VideoCapture(0)
        # 摄像头
        self.button_c_open_g = QPushButton('打开工业摄像头', self,
                                           objectName="RedButton", minimumHeight=48)

        self.button_c_open_g.move(10, 110)
        self.button_c_open_g.clicked.connect(self.open_camera_g)
        self.button_c_open = QPushButton('打开网络摄像头', self,
                                         objectName="RedButton", minimumHeight=48)
        self.button_c_open.move(10, 178)
        self.button_c_open.clicked.connect(self.open_camera)
        self.button_c_close = QPushButton('关闭摄像头', self,
                                          objectName="RedButton", minimumHeight=48)
        self.button_c_close.clicked.connect(self.close_camera)
        self.button_c_close.move(10, 276)

        self.predict_lable = QLabel(self)
        self.classes = ["小鸡"]

        self.predict_lable.setGeometry(QRect(150, 50, 900, 27*6))
        self.predict_lable.setWordWrap(True)
        self.predict_lable.setStyleSheet("font-size: 27pt")
        self.predict_lable.setAlignment(QtCore.Qt.AlignTop)
        # 设置垂直盒布局的控件间距大小
        # self.layout.setSpacing(20)
        # self.setLayout(self.layout)
        self.button_s_predict = QPushButton('开始预测', self,
                                            objectName="RedButton", minimumHeight=48)
        self.button_s_predict.clicked.connect(self.get_start_predict)
        self.button_s_predict.move(10, 334)
        self.button_c_predict = QPushButton('关闭预测', self,
                                            objectName="RedButton", minimumHeight=48)
        self.button_c_predict.clicked.connect(self.get_close_predict)
        self.button_c_predict.move(10, 422)
        self.listen_open_button= QPushButton('开始监听', self,
                                            objectName="RedButton", minimumHeight=48)
        self.listen_open_button.clicked.connect(self.listen_sign)
        self.listen_open_button.move(10,510)
        self.listen_close_button= QPushButton('停止监听', self,
                                            objectName="RedButton", minimumHeight=48)
        self.listen_close_button.clicked.connect(self.close_listen)
        self.listen_close_button.move(10,600)
        self.send_open_button= QPushButton('开始发送', self,
                                            objectName="RedButton", minimumHeight=48)
        self.send_open_button.clicked.connect(self.send_result)
        self.send_open_button.move(10,690)
        self.send_close_button= QPushButton('停止发送', self,
                                            objectName="RedButton", minimumHeight=48)
        self.send_close_button.clicked.connect(self.close_result)
        self.send_close_button.move(10,800)

        self.send_move_button= QPushButton('开始移动', self,
                                            objectName="RedButton", minimumHeight=48)
        self.send_move_button.clicked.connect(self.move_sign)
        self.send_move_button.move(10,910)

        self.send_catch_button= QPushButton('开始抓取', self,
                                            objectName="RedButton", minimumHeight=48)
        self.send_catch_button.clicked.connect(self.catch_sign)
        self.send_catch_button.move(10,960)

        self.send_out_button= QPushButton('开始移除', self,
                                            objectName="RedButton", minimumHeight=48)
        self.send_out_button.clicked.connect(self.out_sign)
        self.send_out_button.move(10,1010)
    def move_sign(self):
        self.move_start=True
        self.catch_start=False
        self.out_start=False
    def catch_sign(self):
        self.move_start=False
        self.catch_start=True
        self.out_start=False
    def out_sign(self):
        self.move_start=False
        self.catch_start=False
        self.out_start=True
    def send_result(self):
        self.send_open=True
        self.model.init_client()
    def close_result(self):
        self.send_close=False
        self.model.close_client()
    def set_size(self):
        self.scale=1
    def pause_show_timeout(self):
        if self.t4:
            self.show_timeout_open=False
    def start_show_timeout(self):
        if self.t4:
            self.show_timeout_open=True
    def open_listen(self):
        self.listen_open=True
    def close_listen(self):
        self.listen_open=False
        if self.t3:
            self.t3.join()
            self.t3=None
    def hexsend(self,string_data=''):
        hex_data = string_data.decode("hex")
        return hex_data
    def show_timeout(self):
        while self.show_timeout_open:
            time.sleep(2)
            self.predict_lable.setText(
                "")
            # self.show_timeout_open=False
    def listen_sign(self):
        data=[]
        while self.listen_open:
            # print(self.child.ser)
            if self.child.ser:
                time.sleep(0.5)
                success_bytes = self.child.ser.write(bytes.fromhex(self.NO1_collect))
                end_code=success_bytes//2+2
                for _ in range(end_code):
                    tmp=self.child.ser.read(1)
                    if tmp==b'':break
                    data.append(tmp.hex())
                revice=' '.join(data[:end_code-2])
                # print(revice,self.NO1_get_on)
                # print(revice)
                self.show_timeout_open=True
                
                if revice==self.NO1_get_on:
                    self.get_frame_single()
                    predict_label, conf = self.predict(self.img)
                    self.predict_lable.setText(
                        "预测的类别为：{},置信度为：{}".format(str(predict_label), str(conf)))
                    self.out_serial()
                data=[]
        #105000.0000
    def open_camera_g(self):
        # ch:开始取流 | en:Start grab image

        self.g_open = True
        # self.get_frame_g()
        self.t2 = threading.Thread(target=self.get_frame_g_mutil)
        self.t2.start()
        # print ("Save Image succeed!")

    def open_image(self):
        # self.pause_show_timeout()
        imgName, imgType = QFileDialog.getOpenFileName(
            self, "打开图片", "", "All Files(*)")
        print(self.start_predict , imgName)
        if self.open or self.g_open:
            self.close_camera()
        if self.start_predict and imgName:
            gary_img = cv2.imread(imgName, 1)
            # cv2.imshow()
            predict_label, conf = self.predict(gary_img)
            # print(predict_label,conf)
            self.predict_lable.setText(
                "预测的类别为：{},置信度为：{}%".format(str(predict_label), str(conf)))
            self.out_serial()
        get_img = QtGui.QPixmap(imgName).scaled(
            self.label.width(), self.label.height())
        # print(imgName)
        if imgName:
            self.label.setPixmap(get_img)
            if self.open or self.g_open:
                self.close_camera()
    # def predict(self):
        # self.start_show_timeout()
    def get_frame(self):
        while self.open:
            flag, img = self.cap.read()
            self.img=img
            if not flag:
                self.predict_lable.setText("没有检测到摄像头，请检查是否插入")
                break
            get_img = cv2.resize(
                img, (self.label.width(), self.label.height()))
            
            # get_img = cv2.cvtColor(get_img, cv2.COLOR_BGR2RGB)
            if not self.open:
                break
            if self.start_predict:
                predict_label, conf = self.predict(img)
                self.predict_lable.setText(
                    "预测的类别为：{},置信度为：{}".format(str(predict_label), str(conf)))
                self.out_serial()
            showImage = QtGui.QImage(
                get_img.data, get_img.shape[1], get_img.shape[0], QtGui.QImage.Format_RGB888)
            if flag:
                self.label.setPixmap(QtGui.QPixmap.fromImage(showImage))

    def get_frame_single(self):
        ret = self.child.obj_cam_operation.obj_cam.MV_CC_StartGrabbing()

        stDeviceList = MV_FRAME_OUT_INFO_EX()
        memset(byref(stDeviceList), 0, sizeof(stDeviceList))
        self.data_buf = (
            c_ubyte * self.child.obj_cam_operation.nPayloadSize)()

        ret = self.child.obj_cam_operation.obj_cam.MV_CC_GetOneFrameTimeout(byref(
            self.data_buf), self.child.obj_cam_operation.nPayloadSize, stDeviceList, 1000)
        if ret == 0:
            # print ("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stDeviceList.nWidth, stDeviceList.nHeight, stDeviceList.nFrameNum))
            nRGBSize = stDeviceList.nWidth * stDeviceList.nHeight * 3
            stConvertParam = MV_SAVE_IMAGE_PARAM_EX()
            stConvertParam.nWidth = stDeviceList.nWidth
            stConvertParam.nHeight = stDeviceList.nHeight
            stConvertParam.pData = self.data_buf
            stConvertParam.nDataLen = stDeviceList.nFrameLen
            stConvertParam.enPixelType = stDeviceList.enPixelType
            stConvertParam.nImageLen = stConvertParam.nDataLen
            stConvertParam.nJpgQuality = 70
            stConvertParam.enImageType = MV_Image_Jpeg
            stConvertParam.pImageBuffer = (c_ubyte * nRGBSize)()
            stConvertParam.nBufferSize = nRGBSize
            # ret = self.cam.MV_CC_ConvertPixelType(stConvertParam)
            # print(stConvertParam.nImageLen)
            # print(stDeviceList)
            ret = self.child.obj_cam_operation.obj_cam.MV_CC_SaveImageEx2(
                stConvertParam)
            if ret != 0:
                print("convert pixel fail ! ret[0x%x]" % ret)
                del self.data_buf
                sys.exit()
            self.file_path = "./AfterConvert_RGB" + \
                str(self.child.device_index)+".png"
            self.file_save_path = "./images/AfterConvert_RGB" + \
                str(self.child.device_index)+"_"+str(self.index)+"_"+"3"+".png"
            self.index+=1         
            file_open = open(self.file_path.encode('ascii'), 'wb+')
            # file_save = open(self.file_save_path.encode('ascii'), 'wb+')
            img_buff = (c_ubyte * stConvertParam.nImageLen)()
            cdll.msvcrt.memcpy(
                byref(img_buff), stConvertParam.pImageBuffer, stConvertParam.nImageLen)
            file_open.write(img_buff)
            # file_save.write(img_buff)
        img = cv2.imread(self.file_path)
        img=img[223:914,136:1089,:]
        # print(img.shape)
        img=cv2.resize(img,(self.label.height(), self.label.width()))
        # print(img.shape)
        # self.og_img=img.copy()
        self.img=img.copy()
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        self.get_img = cv2.resize(
            img, (self.label.width(), self.label.height()))
        # get_img = cv2.cvtColor(get_img, cv2.COLOR_BGR2RGB)
    # def get_frame_g_single(self):
    #     pass
        showImage = QtGui.QImage(
            self.get_img.data, self.get_img.shape[1], self.get_img.shape[0], QtGui.QImage.Format_RGB888)
        self.label.setPixmap(QtGui.QPixmap.fromImage(showImage))
    def get_frame_g_mutil(self):
        while self.g_open:
            # print("工业摄像机进来了")
            self.get_frame_single()
            if not self.g_open:
                break
            if self.start_predict:
                result = self.predict(self.img)
                if result:
                    # print(self.model.h,self.model.w,self.get_img.shape[0], self.get_img.shape[1])
                    new_result = scale_coords_new((self.model.h,self.model.w), result[:4], (self.get_img.shape[0], self.get_img.shape[1]))
                    self.predict_lable.setText(
                        "预测的坐标为：{},类别为：{}".format(str([(new_result[2]+new_result[0])//2,(new_result[3]+new_result[1])//2]), str(self.classes[result[4]])))
                    self.get_img=cv2.rectangle(self.get_img,(new_result[0],new_result[1]-1),(new_result[2],new_result[3]-1),(0,255,0))
                    showImage = QtGui.QImage(
                        self.get_img.data, self.get_img.shape[1], self.get_img.shape[0], QtGui.QImage.Format_RGB888)
                    self.label.setPixmap(QtGui.QPixmap.fromImage(showImage))
                    if self.send_open:
                        self.model.SingleSendText(new_result)


    def open_camera(self):
        self.open = True
        # while self.open:
        print("open")
        if self.open:
            self.t1 = threading.Thread(target=self.get_frame)
            self.t1.start()
        # else:
    def close_all(self):
        print("close")
        self.open = False
        self.g_open = False
        self.listen_open=False
        self.show_timeout_open=False
        # self.send_open=False
        if self.send_open:
            self.close_result()
        if self.t1:
            self.t1.join()
            self.t1 = None
        if self.t2:
            self.t2.join()
            self.t2 = None
        if self.t3:
            self.t3.join()
            self.t3=None 
        if self.t4:
            self.t4.join()
            self.t4=None 
    def close_camera(self):
        print("close")
        self.open = False
        self.g_open = False
        # self.listen_open=False
        if self.t1:
            self.t1.join()
            self.t1 = None
        if self.t2:
            self.t2.join()
            self.t2 = None
        # if self.t3:
        #     self.t3=None
    def changeCheck1(self):
        self.child.show()

    def changeCheck2(self):
        if self.check2.checkState() == Qt.Checked:
            self.check1.setChecked(False)
            self.check3.setChecked(False)

    def changeCheck3(self):
        if self.check3.checkState() == Qt.Checked:
            self.check1.setChecked(False)
            self.check2.setChecked(False)

    def conv_cal(self):
        ans = 0
        image_size = int(self.edit3.text()) if self.edit3.text() else None
        stride = int(self.edit1.text()) if self.edit1.text() else None
        padding = int(self.edit2.text()) if self.edit2.text() else None
        kernel_size = int(self.edit4.text()) if self.edit4.text() else None
        if self.check1.isChecked():
            ans = int(math.ceil(image_size/stride))
            self.label_set(image_size, ans)

        elif self.check2.isChecked():
            ans = int(math.ceil((image_size-kernel_size+1)/stride))
            self.label_set(image_size, ans)
        elif self.check3.isChecked():
            ans = int(math.floor((image_size+2*padding-kernel_size)/stride)+1)
            self.label_set(image_size, ans)

    def label_set(self, input, ouput):
        self.label5.setText("卷积前卷积为{}卷积后的尺寸为{}".format(str(input), str(ouput)))
        # self.label5.setText("<b style='color:red'>Button has been clicked!</b>")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '提示',
                                     "是否要关闭所有窗口?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            if self.open or self.g_open or self.listen_open or self.show_timeout_open or self.send_open:
                self.close_all()
            if self.child.obj_cam_operation:
                self.child.obj_cam_operation.obj_cam.MV_CC_CloseDevice()
                self.child.obj_cam_operation.obj_cam.MV_CC_DestroyHandle()
            if self.child.ser:
                self.child.ser.close()
            sys.exit(0)   # 退出程序
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyleSheet('.QLabel { font-size: 14pt;}')
    # QFontDatabase.addApplicationFont(
    #     "Data/Fonts/FontAwesome/fontawesome-webfont.ttf")
    # app.setStyleSheet(StyleSheet)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())