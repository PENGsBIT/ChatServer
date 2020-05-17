# encoding=utf8
import datetime

import wx
import telnetlib
from time import sleep
import thread as thread
import logging
logging.basicConfig(level=logging.NOTSET)
lastLogin=datetime.datetime.now()
class LoginFrame(wx.Frame):
    """
    登录窗口类，继承wx.Frame类
    """
    def __init__(self, parent, id, title, size):
        wx.Frame.__init__(self, parent, id, title)
        # 设置窗体大小、位置
        self.SetSize(size)
        self.Center()
        # 服务器地址框标签
        self.serverAddressLabel = wx.StaticText(self, label="Adress", pos=(40, 20), size=(120, 25))
        # 用户名框标签
        self.userNameLabel = wx.StaticText(self, label="UserName", pos=(40, 50), size=(120, 25))
        # 密码框标签
        self.passwordLabel = wx.StaticText(self, label="Password", pos=(40, 90), size=(120, 25))
        # 服务器地址框
        self.serverAddress = wx.TextCtrl(self, pos=(120, 20), size=(150, 25))
        # 用户名框
        self.userName = wx.TextCtrl(self, pos=(120, 50), size=(150, 25))
        # 密码名框
        self.password = wx.TextCtrl(self, pos=(120, 90), size=(150, 25))
        # 登录/注册按钮
        self.loginButton = wx.Button(self, label='Login/Register', pos=(120, 145), size=(100, 30))
        # 绑定方法
        self.loginButton.Bind(wx.EVT_BUTTON, self.loginOrRegister)
        # 显示组件
        self.Show()
        logging.debug("init LoginFrame")

    def loginOrRegister(self, event):
        logging.debug("loginOrRegister func")
        # 登录注册处理
        try:
            serverAddress = self.serverAddress.GetLineText(0).split(':')
            con.open(serverAddress[0], port=int(serverAddress[1]), timeout=10)
            # 判断链接情况
            response = con.read_some()
            if response != 'Connect Success'.encode('utf-8'):
                self.showDialog('Error', 'Connect Fail!', (200, 100))
                return
            # 发送登录操作名
            if not self.userName.GetLineText(0):
                self.showDialog('Error', 'userName None!', (200, 100))
                return
            con.write(('login ' +str(self.userName.GetLineText(0))+' '+str(self.password.GetLineText(0))+'\n').encode("utf-8"))
            response = con.read_some()
            if response == 'Password Wrong'.encode('utf-8'):
                self.showDialog('Error', 'Password Wrong!', (200, 100))
            elif response == 'UserName Existed':
                self.showDialog('Error', 'UserName Existed!', (200, 100))
            else:
                self.Close()
                ChatFrame(None, 2, title='Chat Room Demo', size=(500, 400))
                global lastLogin
                lastLogin=datetime.datetime.now()
        except Exception:
            self.showDialog('Error', 'Connect Exception!', (195, 120))

    def showDialog(self, title, content, size):
        # 显示错误信息对话框
        dialog = wx.Dialog(self, title=title, size=size)
        dialog.Center()
        wx.StaticText(dialog, label=content)
        # 显示对话窗口
        dialog.ShowModal()


class ChatFrame(wx.Frame):
    """
    聊天窗口类，继承wx.Frame类
    """

    def __init__(self, parent, id, title, size):
        # 记录时间
        self.loginTime = datetime.datetime.now()
        # 初始化，添加控件
        wx.Frame.__init__(self, parent, id, title)
        self.SetSize(size)
        self.Center()
        # 显示对话文本框，style设置其文本高亮显示和只读
        self.chatFrame = wx.TextCtrl(self, pos=(5, 5), size=(490, 310), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.message = wx.TextCtrl(self, pos=(5, 320), size=(300, 25))
        self.sendButton = wx.Button(self, label="Send", pos=(310, 320), size=(58, 25))
        self.usersButton = wx.Button(self, label="Info", pos=(373, 320), size=(58, 25))
        self.closeButton = wx.Button(self, label="Close", pos=(436, 320), size=(58, 25))
        # 绑定发送方法
        self.sendButton.Bind(wx.EVT_BUTTON, self.send)
        # 绑定信息方法
        self.usersButton.Bind(wx.EVT_BUTTON, self.userInfo)
        # 绑定关闭方法
        self.closeButton.Bind(wx.EVT_BUTTON, self.close)
        # start_new_thread()产生新线程接收服务器信息
        thread.start_new_thread(self.receive, ())
        self.Show()

    def send(self, event):
        # 发送消息
        message = str(self.message.GetLineText(0)).strip()
        if message != '':
            con.write(('chat ' + message + '\n').encode("utf-8"))
            self.message.Clear()

    def userInfo(self, event):
        global lastLogin
        loginTime = (datetime.datetime.now() - lastLogin).seconds
        # 查看当前用户信息
        con.write(b'info ' + str(loginTime) + '\n')

    def close(self, event):
        # 关闭窗口
        con.write(b'logout\n')
        con.close()
        self.Close()

    def receive(self):
        # 接受服务器的消息
        while True:
            sleep(0.6)
            # 在I/O中读取数据，存在result变量中
            result = con.read_very_eager()
            if result != '':
                self.chatFrame.AppendText(result)


if __name__ == '__main__':
    # 应用程序对象
    app = wx.App()
    # 客户端使用telnetlib连接目标主机
    con = telnetlib.Telnet()
    # 顶级窗口对象
    LoginFrame(None, -1, title="Login", size=(320, 250))
    # 进入应用程序的主事件循环
    app.MainLoop()
