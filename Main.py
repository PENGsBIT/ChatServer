# encoding=utf8
from Server import *
from Config import *
import DataBase
import os
import logging
logging.basicConfig(level=logging.NOTSET)

if __name__ == '__main__':

    # 判断当前目录是否存在这个文件。
    if not os.path.isfile(db_file):
        logging.debug("create DB")
        DataBase.CreateDB(db_file)
    # 开启Server
    s = ChatServer(ServerPort)
    try:
        logging.debug("chat serve run at '127.0.0.1:{0}'".format(ServerPort))
        # 开启循环监听网络事件
        asyncore.loop()
    except KeyboardInterrupt:
        logging.debug("chat server exit")
