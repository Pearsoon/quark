import sqlite3

import sqlite3


def fetch_files(file_name) -> bool:
    """检索文件,如果已存在那么返回False"""
    conn = sqlite3.connect('file.db')
    c = conn.cursor()
    c.execute('SELECT FILE_NAME FROM ALL_FILE WHERE FILE_NAME =?', (file_name,))
    files = c.fetchall()
    conn.close()
    if files:
        return False
    return True


def insert_files(file_id, file_name, file_type, share_link):
    """插入文件"""
    conn = sqlite3.connect('file.db')
    c = conn.cursor()
    c.execute("INSERT INTO ALL_FILE VALUES (?,?,?,?)", (file_id, file_name, file_type, share_link))
    conn.commit()
    conn.close()


def update_files(file_id, file_name):
    conn = sqlite3.connect('file.db')
    c = conn.cursor()
    c.execute("UPDATE ALL_FILE SET FILE_ID=? WHERE FILE_NAME=?", (file_id, file_name))
    conn.commit()
    conn.close()

