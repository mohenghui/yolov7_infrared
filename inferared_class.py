# coding=utf-8

import os
import platform
import tkinter
from tkinter import *
from HCNetSDK import *
from PlayCtrl import *
from time import sleep
# do this before importing pylab or pyplot
# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
from ctypes import *

class Camera_server(object):
    def __init__(self) -> None:
    # 登录的设备信息
        self.DEV_IP = create_string_buffer(b'192.168.1.30')
        self.DEV_PORT = 8000
        self.DEV_USER_NAME = create_string_buffer(b'admin')
        self.DEV_PASSWORD = create_string_buffer(b'z88888888')

        self.WINDOWS_FLAG = True
        self.win = None  # 预览窗口
        self.funcRealDataCallBack_V30 = None  # 实时预览回调函数，需要定义为全局的

        self.PlayCtrl_Port = c_long(-1)  # 播放句柄
        self.Playctrldll = None  # 播放库
        self.FuncDecCB = None   # 播放库解码回调函数，需要定义为全局的
        self.Objdll=None
        self.Playctrldll=None
        self.root_path="./lib/win"
        self.success=0
    def init_tk(self):
        # 创建窗口
        self.win = tkinter.Tk()
        #固定窗口大小
        # self.win.resizable(0, 0)
        # self.win.overrideredirect(True)

        # sw = self.win.winfo_screenwidth()
        # # 得到屏幕宽度
        # sh = self.win.winfo_screenheight()
        # # 得到屏幕高度

        # # 窗口宽高
        # ww = 512
        # wh = 384
        # x = (sw - ww) / 2
        # y = (sh - wh) / 2
        # self.win.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

        # # 创建退出按键
        # self.b = Button(self.win, text='退出', command=self.win.quit)
        # self.b.pack()
        # # 创建一个Canvas，设置其背景色为白色
        # self.cv = tkinter.Canvas(self.win, bg='white', width=ww, height=wh)
        # self.cv.pack()
        self.win.withdraw()
    # 获取当前系统环境
    def GetPlatform(self):
        sysstr = platform.system()
        print('' + sysstr)
        if sysstr != "Windows":
            # global WINDOWS_FLAG
            self.WINDOWS_FLAG = False
    # 设置SDK初始化依赖库路径
    def SetSDKInitCfg(self):
        # 设置HCNetSDKCom组件库和SSL库加载路径
        # print(os.getcwd())
        if self.WINDOWS_FLAG:
            # strPath = self.root_path
            strPath=os.getcwd().encode('gbk')
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
            self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
            self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
        else:
            strPath = os.getcwd().encode('utf-8')
            sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
            sdk_ComPath.sPath = strPath
            self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
            self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
            self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))

    def LoginDev(self,Objdll):
        # 登录注册设备
        device_info = NET_DVR_DEVICEINFO_V30()
        lUserId = Objdll.NET_DVR_Login_V30(self.DEV_IP, self.DEV_PORT, self.DEV_USER_NAME, self.DEV_PASSWORD, byref(device_info))
        return (lUserId, device_info)

    def DecCBFun(self,nPort, pBuf, nSize, pFrameInfo, nUser, nReserved2):
        # 解码回调函数
        if pFrameInfo.contents.nType == 3:
            # 解码返回视频YUV数据，将YUV数据转成jpg图片保存到本地
            # 如果有耗时处理，需要将解码数据拷贝到回调函数外面的其他线程里面处理，避免阻塞回调导致解码丢帧
            sFileName = ('../../pic/test_stamp.jpg')
            nWidth = pFrameInfo.contents.nWidth
            nHeight = pFrameInfo.contents.nHeight
            nType = pFrameInfo.contents.nType
            dwFrameNum = pFrameInfo.contents.dwFrameNum
            nStamp = pFrameInfo.contents.nStamp
            # print(nWidth, nHeight, nType, dwFrameNum, nStamp, sFileName)
            # print(c_wchar_p(pBuf))
            # print(pBuf)
            # Alarm_struct = cast(pBuf,
            #         LPNET_DVR_ACS_ALARM_INFO).contents  #
            # PicDataLen = Alarm_struct.dwPicDataLen
            # if PicDataLen != 0:
            #     buff1 = string_at(Alarm_struct.pPicData, PicDataLen)
            #     with open('./catch/Acs_Capturetest.jpg', 'wb') as fp:
            #         fp.write(buff1)
            lRet = self.Playctrldll.PlayM4_ConvertToJpegFile(pBuf, nSize, nWidth, nHeight, nType, c_char_p(sFileName.encode()))
            # print(lRet)
            self.success=lRet
            # if lRet == 0:
            #     print('PlayM4_ConvertToJpegFile fail, error code is:', self.Playctrldll.PlayM4_GetLastError(nPort))
            # else:
            #     print('PlayM4_ConvertToJpegFile success')

    def RealDataCallBack_V30(self,lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
        # 码流回调函数
        if dwDataType == NET_DVR_SYSHEAD:
            # 设置流播放模式
            self.Playctrldll.PlayM4_SetStreamOpenMode(self.PlayCtrl_Port, 0)
            # 打开码流，送入40字节系统头数据
            if self.Playctrldll.PlayM4_OpenStream(self.PlayCtrl_Port, pBuffer, dwBufSize, 1024*1024):
                # 设置解码回调，可以返回解码后YUV视频数据
                global FuncDecCB
                FuncDecCB = DECCBFUNWIN(self.DecCBFun)
                self.Playctrldll.PlayM4_SetDecCallBackExMend(self.PlayCtrl_Port, FuncDecCB, None, 0, None)
                # self.Playctrldll.PlayM4_SetDecCallBackExMend(self.PlayCtrl_Port, None, None, 0, None)
                # 开始解码播放
                if self.Playctrldll.PlayM4_Play(self.PlayCtrl_Port, 0):
                    print(u'播放库播放成功')
                else:
                    print(u'播放库播放失败')
            else:
                print(u'播放库打开流失败')
        elif dwDataType == NET_DVR_STREAMDATA:
            self.Playctrldll.PlayM4_InputData(self.PlayCtrl_Port, pBuffer, dwBufSize)
        else:
            print (u'其他数据,长度:', dwBufSize)

    def OpenPreview(self,Objdll, lUserId, callbackFun):
        '''
        打开预览
        '''
        preview_info = NET_DVR_PREVIEWINFO()
        preview_info.hPlayWnd = 0
        preview_info.lChannel = 1  # 通道号
        preview_info.dwStreamType = 0  # 主码流
        preview_info.dwLinkMode = 0  # TCP
        preview_info.bBlocked = 1  # 阻塞取流

        # 开始预览并且设置回调函数回调获取实时流数据
        lRealPlayHandle = Objdll.NET_DVR_RealPlay_V40(lUserId, byref(preview_info), callbackFun, None)
        return lRealPlayHandle

    def InputData(self,fileMp4, Playctrldll):
        while True:
            pFileData = fileMp4.read(4096)
            if pFileData is None:
                break

            if not Playctrldll.PlayM4_InputData(self.PlayCtrl_Port, pFileData, len(pFileData)):
                break
    def catch_frame(self,Objdll,lRealPlayHandle):
        pFileName = ctypes.c_char_p()
        pFileName.value = bytes("../../catch/image.jpg", "utf-8")
            # 开始抓图。
        res = Objdll.NET_DVR_CapturePicture(lRealPlayHandle, pFileName)
        # print(res)
        if res:
            print("Successfullly capture picture, ", pFileName.value)
    def work(self):
        self.init_tk()
        
        self.GetPlatform()
        # 加载库,先加载依赖库
        if self.WINDOWS_FLAG:
            os.chdir(r'./lib/win')
            # print(os.path.join(self.root_path,'HCNetSDK.dll'))
            self.Objdll = ctypes.CDLL('HCNetSDK.dll')  # 加载网络库
            # self.Playctrldll = ctypes.CDLL(os.path.join(self.root_path,'PlayCtrl.dll'))  # 加载播放库
            self.Playctrldll = ctypes.CDLL('PlayCtrl.dll')  # 加载播放库
        else:
            os.chdir(r'./lib/linux')
            self.Objdll = cdll.LoadLibrary(r'./libhcnetsdk.so')
            self.Playctrldll = cdll.LoadLibrary(r'./libPlayCtrl.so')

        self.SetSDKInitCfg()  # 设置组件库和SSL库加载路径
        # 初始化DLL
        self.Objdll.NET_DVR_Init()
        # 启用SDK写日志
        self.Objdll.NET_DVR_SetLogToFile(3, bytes(os.path.join(self.root_path,'SdkLog_Python/'), encoding="utf-8"), False)
        # os.getcwd()
        # 获取一个播放句柄
        if not self.Playctrldll.PlayM4_GetPort(byref(self.PlayCtrl_Port)):
            print(u'获取播放库句柄失败')

        # 登录设备
        (self.lUserId, device_info) = self.LoginDev(self.Objdll)
        if self.lUserId < 0:
            err = self.Objdll.NET_DVR_GetLastError()
            print('Login device fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
            # 释放资源
            self.Objdll.NET_DVR_Cleanup()
            exit()
        
        # 定义码流回调函数
        funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)
        
        # 开启预览
        self.lRealPlayHandle = self.OpenPreview(self.Objdll, self.lUserId, callbackFun=funcRealDataCallBack_V30)
        # self.catch_frame(Objdll=self.Objdll,lRealPlayHandle=self.lRealPlayHandle)
        if self.lRealPlayHandle < 0:
            print ('Open preview fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
            # 登出设备
            self.Objdll.NET_DVR_Logout(self.lUserId)
            # 释放资源
            self.Objdll.NET_DVR_Cleanup()
            exit()
    # 开始云台控制
        # lRet = self.Objdll.NET_DVR_PTZControl(self.lRealPlayHandle, PAN_LEFT, 0)
        # if lRet == 0:
        #     print ('Start ptz control fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
        # else:
        #     print ('Start ptz control success')

        # # 转动一秒
        # sleep(1)

        # # 停止云台控制
        # lRet = self.Objdll.NET_DVR_PTZControl(lRealPlayHandle, PAN_LEFT, 1)
        # if lRet == 0:
        #     print('Stop ptz control fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
        # else:
        #     print('Stop ptz control success')

        # # 关闭预览
        # self.Objdll.NET_DVR_StopRealPlay(lRealPlayHandle)

        # # 停止解码，释放播放库资源
        # if self.PlayCtrl_Port.value > -1:
        #     self.Playctrldll.PlayM4_Stop(self.PlayCtrl_Port)
        #     self.Playctrldll.PlayM4_CloseStream(self.PlayCtrl_Port)
        #     self.Playctrldll.PlayM4_FreePort(self.PlayCtrl_Port)
        #     self.PlayCtrl_Port = c_long(-1)

        # # 登出设备
        # self.Objdll.NET_DVR_Logout(lUserId)

        # # 释放资源
        # self.Objdll.NET_DVR_Cleanup()
        self.win.mainloop()
    def close(self):
        # 停止云台控制
        # lRet = self.Objdll.NET_DVR_PTZControl(self.lRealPlayHandle, PAN_LEFT, 1)
        # if lRet == 0:
        #     print('Stop ptz control fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
        # else:
        #     print('Stop ptz control success')

        # 关闭预览
        self.Objdll.NET_DVR_StopRealPlay(self.lRealPlayHandle)

        # 停止解码，释放播放库资源
        if self.PlayCtrl_Port.value > -1:
            self.Playctrldll.PlayM4_Stop(self.PlayCtrl_Port)
            self.Playctrldll.PlayM4_CloseStream(self.PlayCtrl_Port)
            self.Playctrldll.PlayM4_FreePort(self.PlayCtrl_Port)
            self.PlayCtrl_Port = c_long(-1)

        # 登出设备
        self.Objdll.NET_DVR_Logout(self.lUserId)

        # 释放资源
        self.Objdll.NET_DVR_Cleanup()
        self.win.destroy()
if __name__ == '__main__':




    camera_server=Camera_server()
    # 获取系统平台
    # camera_server.GetPlatform()
    camera_server.work()





    #show Windows
    # win.mainloop()

    