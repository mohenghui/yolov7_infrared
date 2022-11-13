
import cv2
from git import Object
import torch
import torch.backends.cudnn as cudnn

from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import check_img_size,non_max_suppression,scale_coords
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel
import numpy as np
from MvImport.MvCameraControl_class import *
from params import ChildWindow
import sys
import socket
import json
class Detect_app(Object):
    def __init__(self,weights,device,half,augment,conf_thres,iou_thres,classes,agnostic_nms,img_size):
        # super(Detect_app,self).__init__()
        self.device=select_device(device)
        self.model=attempt_load(weights, map_location=self.device)
        
        self.half=half
        self.augment=augment
        self.conf_thres=conf_thres
        self.iou_thres=iou_thres
        self.classes=classes
        self.agnostic_nms=agnostic_nms
        self.img=None
        cudnn.benchmark = True
        self.track=True
        self.img_size=int(img_size)
        if self.track:
            self.model = TracedModel(self.model, self.device, self.img_size)
        if self.half:
            self.model.half()  # to FP16
        self.client=None
        # self.init_client()
        # self.child=ChildWindow()
        # self.child.initUI()
        self.h=None
        self.w=None
    @torch.no_grad()
    def run(self,frame):
        if not self.h and not self.w:self.h,self.w=frame.shape[0],frame.shape[1]
        img0=frame.copy()
        img=frame.copy()

        stride = int(self.model.stride.max())  # model stride
        imgsz = check_img_size(self.img_size, s=stride)  # check img_size
        # print(imgsz)
        img = letterbox(img, imgsz, stride=stride)[0]
        # cv2.imshow("show",img)
        # cv2.waitKey(0)
            # Stack
        img = np.stack(img, 0)
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img = np.ascontiguousarray(img)


        img = torch.from_numpy(img).to(self.device)
        img = img.half() if self.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        old_img_w = old_img_h = imgsz
        old_img_b = 1
        # Warmup
        if self.device.type != 'cpu' and (old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
            old_img_b = img.shape[0]
            old_img_h = img.shape[2]
            old_img_w = img.shape[3]
            for i in range(3):
                self.model(img, augment=self.augment)[0]
                    # with torch.no_grad():   # Calculating gradients would cause a GPU memory leak
        pred = self.model(img, augment=self.augment)[0]
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=self.classes, agnostic=self.agnostic_nms)
        # if self.classify:
        #     modelc = load_classifier(name='resnet101', n=2)  # initialize
        #     modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()
        # if self.classify:
        #     pred = apply_classifier(pred, modelc, img, img0)
        for i, det in enumerate(pred):  # detections per image
            if det is not None and len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
                info_list = []
                for *xyxy, conf, cls in reversed(det):
                    xyxy = torch.tensor(xyxy).view(-1).tolist()
                    info = [xyxy[0], xyxy[1], xyxy[2], xyxy[3], int(cls)]
                    info_list.append(info)
                x1,y1=int(info_list[0][0]),int(info_list[0][1])
                x2,y2=int(info_list[0][2]),int(info_list[0][3])
                return [x1,y1,x2,y2,int(info_list[0][4])]
            else:
                return None
    def init_client(self):
        host = "192.168.1.62"  # 设置IP
        port = 5500  # 设置端口号
        tcpclient = socket.socket()  # 创建TCP/IP套接字
        try:
            tcpclient.connect((host, port))  # 主动初始化TCP服务器连接
            self.client=tcpclient
            print("已连接服务端")
        except:
            print("没有连接服务器")
    def close_client(self):
        self.client.close()
    def SingleSendText(self,send_data):
        """
        单次发送接收文字
        """
        # host = socket.gethostname()  # 获取主机地址  socket.gethostname()
        data = json.dumps(send_data)
        self.client.send(data.encode('utf-8'))  # 发送TCP数据
        info = self.client.recv(1024).decode()
        
        print("接收到的内容：", info)
        # self.client.close()
    
def cap_video(src):
    # 使用openCV中的VideoCapture函数，读取视频
    cap = cv2.VideoCapture(src)
    # 初始化定义frame_id，便于后面跳帧
    frame_id = 0
    # 判断cap是否读取成功

    weight_path="best.pt"
    my_detect=Detect_app(weights=weight_path,device="0",half=True,augment=False,conf_thres=0.25,iou_thres=0.45,classes=None,agnostic_nms=False,img_size=640)

    while cap.isOpened():
        # 因为视频采集，每秒可能会采集N帧，因此使用read函数，逐帧读取
        # ret 返回True或False，表示是否读取到图片
        ret, frame = cap.read()
        # 当ret为False时，not ret为True，表示没有读取到图片，说明采集结束
        if not ret:
            # 打印输出，提示信息
            print('Camera cap over')
            continue
        # frame_id加1，便于跳帧
        frame_id += 1
        # 如果frame除以2，不等于0，则不断循环，只有等于0时，才进行到下面的显示步骤，这样可以达到跳帧的效果
        if not int(frame_id) % 2 == 0:
            continue
        # 便于观察，缩放图片，，比如（1000,800），即宽1000像素，高800像素
        # frame = cv2.resize(frame, (1000,800))
        result=my_detect.run(frame)
        # print(result)
        if result:
            x1,y1=int(result[0][0]),int(result[0][1])
            x2,y2=int(result[0][2]),int(result[0][3])
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),1)
            my_detect.SingleSendText([x1,y1,x2,y2])
        if cv2.waitKey(1)&0xff == 27:
            break
        cv2.imshow('Image', frame)
        cv2.waitKey(1)
if __name__=="__main__":

    cap_video("20220527204932317.avi")