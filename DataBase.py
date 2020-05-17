# encoding=utf8
import sqlite3
import logging
import os
logging.basicConfig(level=logging.NOTSET)

def CreateDB(db_file):
    # 连接或创建数据库
    con = sqlite3.connect(db_file)
    #创建表
    query = """CREATE TABLE user_table
                (user_name VARCHAR(20),
                password VARCHAR(20),
                create_time VARCHAR(40));"""
    #使用连接对象的execute()方法执行query中的SQL命令
    con.execute(query)
    #使用连接对象的commit()方法将修改提交（保存）到数据库
    con.commit()
    #向表中插入几行数据
    data = [
            ('netease1','123','2020-04-02'),
            ('netease2','123','2020-04-02'),
            ('netease3','123','2020-04-02')
            ]
    #将插入语句赋给变量statement，？是占位符
    statement = "INSERT INTO user_table VALUES(?,?,?)"
    #statement中的SQL命令，这里执行了四次insert命令
    con.executemany(statement,data)
    #将修改保存到数据库
    con.commit()
    con.close()
