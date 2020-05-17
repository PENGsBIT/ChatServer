# -*- encoding: UTF-8 -*-
import random
import sys
import thread

reload(sys)
sys.setdefaultencoding("utf-8")
import asynchat
import asyncore
import time
import logging
from _socket import AF_INET, SOCK_STREAM
import sqlite3
import datetime

logging.basicConfig(level=logging.NOTSET)


class ChatServer(asyncore.dispatcher):
    """
    创建一个支持多用户连接的聊天服务器
    """

    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        # 创建socket
        self.create_socket(AF_INET, SOCK_STREAM)
        # 设置 socket 为可重用
        self.set_reuse_addr()
        # 监听端口
        self.bind(('', port))
        # 设置最大连接数为5,超出排队
        self.listen(5)
        self.users = {}
        self.main_room = ChatRoom(self)
        logging.debug("main room init")

    # 阻塞式监听，等待客户端的连接，生成连接对象(SSL通道，客户端地址)
    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except TypeError:
            return 'TypeError' + TypeError.message
        except self.socket.error:
            return 'Error' + self.socket.error.message
        else:
            # 建立会话
            ChatSession(self, conn)
        logging.debug("chat session generate")


class ChatSession(asynchat.async_chat):
    """
    负责和客户端通信的会话类
    """

    def __init__(self, server, sock):
        asynchat.async_chat.__init__(self, sock)
        self.server = server
        # 设置数据终止符
        self.set_terminator(b'\n')
        # 设置数据列表
        self.data = []
        self.name = None
        self.enter(LoginRoom(server))

    def enter(self, room):
        # 从当前房间移除自身，然后添加到指定房间
        try:
            cur = self.room
        except AttributeError:
            pass
        else:
            cur.remove(self)
        self.room = room
        room.add(self)

    # 重写处理客户端发来数据的方法
    def collect_incoming_data(self, data):
        # 接收客户端的数据并解码
        self.data.append(data.decode("utf-8"))

    # 重写发现数据中终止符号时的处理方法
    def found_terminator(self):
        # 将数据列表中的内容整合为一行
        line = ''.join(self.data)
        # 清理数据列表
        self.data = []
        try:
            self.room.handle(self, line.encode("utf-8"))
        # 退出聊天室的处理
        except EndSession:
            self.handle_close()

    def handle_close(self):
        # 当 session 关闭时，将进入 LogoutRoom
        asynchat.async_chat.handle_close(self)
        self.enter(LogoutRoom(self.server))


class CommandHandler:
    """
    命令处理类
    """

    def handle(self, session, line):
        # 解码
        line = line.decode()
        # 判断去掉空格后是否还有数据
        if not line.strip():
            return
        # 把数据以空格分隔符分割生成列表，最大分割数为2
        parts = line.split(' ', 1)
        # 分割的第一部分为前置命令
        frontCmd = parts[0]
        try:
            line = parts[1].strip()
        except IndexError:
            line = ''
        # 判断line是否为带$指令
        if frontCmd == 'chat' and line[0] == '$':
            backCmd = line.split(' ')[0]
            method = getattr(self, 'exec_' + backCmd[1:], None)
            # 调用获取到的方法对象
            try:
                method(session, line)
            except TypeError:
                print (TypeError.message)
                self.unknownCommend(session, line + ":except," + backCmd)
        else:
            # 获取指定名称的方法对象
            method = getattr(self, 'exec_' + frontCmd, None)
            # 调用获取到的方法对象
            try:
                method(session, line)
            except TypeError:
                self.unknownCommend(session, line + ":except," + frontCmd)

    # 定义未知命令的处理方法
    def unknownCommend(self, session, cmd):
        # 通过 aynchat.async_chat.push 方法发送消息，向客户端发送错误提示
        session.push(('unknown cmd {} \n'.format(cmd)).encode("utf-8"))


class Room(CommandHandler):
    """
    包含多个用户的环境，负责基本的命令处理和广播
    """

    def __init__(self, server):
        self.server = server
        # 会话列表
        self.sessions = []

    def add(self, session):
        # 一个用户进入房间
        self.sessions.append(session)

    def remove(self, session):
        # 一个用户离开房间
        self.sessions.remove(session)

    # 定义广播信息的处理方法
    def broadcast(self, line):
        # 遍历所有用户会话，再使用 asynchat.asyn_chat.push 方法发送数据
        for session in self.sessions:
            session.push(line)

    def exec_logout(self, session, line):
        # 退出房间
        raise EndSession


class LoginRoom(Room):
    """
    处理登录用户
    """

    def add(self, session):
        # 用户连接成功的回应
        Room.add(self, session)
        # 使用 asynchat.asyn_chat.push 方法发送数据到客户端
        session.push('Connect Success'.encode('utf-8'))

    # loginOrRegister
    def exec_login(self, session, line):
        name = line.encode('utf-8').split(' ')[0]
        password = line.encode('utf-8').split(' ')[1]
        conn = sqlite3.connect('ChatServer.db')
        sqlStr = "SELECT user_name,password FROM user_table WHERE user_name='%s'" % name
        cursor = conn.execute(sqlStr)
        # user-password-pair
        upp = cursor.fetchall()
        if not upp:
            logging.debug("register user")
            params = [name, password, str(datetime.datetime.now())]
            cursor.execute("INSERT INTO user_table (user_name,password,create_time) VALUES (?,?,?)", params)
            conn.commit()
            logging.debug("register success")
            conn.close()
            session.name = name
            session.enter(self.server.main_room)
        else:
            if password != upp[0][1].encode('utf-8'):
                session.push('Password Wrong'.encode('utf-8'))
            # 用户名检查成功后，进入主聊天室
            else:
                session.name = name
                session.enter(self.server.main_room)
        conn.close()


class LogoutRoom(Room):
    """
    处理退出用户
    """

    def add(self, session):
        # 从服务器中用户字典中移除相关记录
        try:
            del self.server.users[session.name]
        except KeyError:
            pass


class ChatRoom(Room):
    """
    聊天用的房间
    """
    rollGameStart = False
    userRollPair = []

    # 广播新用户进入
    def add(self, session):
        session.push('登录成功'.encode('utf-8'))
        self.broadcast((session.name + ' 进入房间\n').encode("utf-8"))
        # 向服务器的用户字典添加与会话的用户名相对应的会话
        self.server.users[session.name] = session
        Room.add(self, session)

    # 广播用户离开
    def remove(self, session):
        Room.remove(self, session)
        self.broadcast((session.name + ' 离开房间\n').encode("utf-8"))

    # 聊天消息
    def exec_chat(self, session, line):
        logging.debug("broadcast chat message" + line)
        self.broadcast(('time:' + time.strftime('%H:%M:%S', time.localtime(
            time.time())) + '\n' + session.name + ': ' + line + '\n').encode("utf-8"))

    # 用户信息
    def exec_info(self, session, line):
        session.push(('user ' + session.name + ' info\n').encode("utf-8"))
        session.push(('online time:' + line + '\n').encode("utf-8"))
        conn = sqlite3.connect('ChatServer.db')
        cursor = conn.execute("SELECT create_time FROM user_table WHERE user_name='%s'" % session.name)
        ct = cursor.fetchall()[0][0]
        session.push(('create time:' + ct + '\n').encode("utf-8"))

    # 开启roll game
    def exec_rollstart(self, session, line):
        logging.debug("A Roll Game Start\n")
        rollGameTime = filter(str.isdigit, line.split(' ')[1].encode("utf-8"))
        # 唯一roll game
        # self.rollGameStart = False
        if not self.rollGameStart:
            self.rollGameStart = True
            self.broadcast(session.name + " start a roll game! (will end in" + rollGameTime + ")\n")
            self.userRollPair = []
            # new_thread()产生新线程异步进行计时
            thread.start_new_thread(self.rollGame, (rollGameTime,))
        else:
            session.push(('Aready a Roll Game Pls Wait\n').encode("utf-8"))

    # 用户roll
    def exec_roll(self, session, line):
        num = random.randint(1, 100)
        logging.debug("user" + session.name + " roll:")
        userRollNumPair = [session.name, num]
        self.userRollPair.append(userRollNumPair)
        self.broadcast(session.name + " roll:" + str(num)+'\n')

    def rollGame(self, rollTime):
        time.sleep(float(rollTime))
        sorted(self.userRollPair, cmp=lambda x, y: cmp(x[1], y[1]))
        if self.userRollPair:
            winner = self.userRollPair[0]
            self.broadcast(winner[0] + "win the roll game!\n")
        else:
            self.broadcast("no one roll game,game end!\n")
        self.rollGameStart = False


# 定义结束异常类
class EndSession(Exception):
    pass
