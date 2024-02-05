import requests
import re
import time
import random
import logging

logging.getLogger().setLevel(logging.INFO)


def get_id_from_url(url) -> str:
    """pwd_id"""
    pattern = r"/s/(\w+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return ""


def generate_timestamp(length):
    timestamps = str(time.time() * 1000)
    return int(timestamps[0:length])


class Quark:
    ad_pwd_id = "0df525db2bd0"

    def __init__(self, cookie: str) -> None:
        self.headers = {
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'origin': 'https://pan.quark.cn',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://pan.quark.cn/',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': cookie}

    def store(self, url: str):
        pwd_id = get_id_from_url(url)
        stoken = self.get_stoken(pwd_id)
        detail = self.detail(pwd_id, stoken)
        file_name = detail.get('title')
        from sqlite import fetch_files
        if fetch_files(file_name):
            first_id, share_fid_token, file_type = detail.get("fid"), detail.get("share_fid_token"), detail.get(
                "file_type")
            task = self.save_task_id(pwd_id, stoken, first_id, share_fid_token)
            data = self.task(task)
            file_id = data.get("data").get("save_as").get("save_as_top_fids")[0]
            if not file_type:
                dir_file_list = self.get_dir_file(file_id)
                self.del_ad_file(dir_file_list)
                self.add_ad(file_id)
            share_task_id = self.share_task_id(file_id, file_name)
            share_id = self.task(share_task_id).get("data").get("share_id")
            share_link = self.get_share_link(share_id)
            from sqlite import insert_files
            insert_files(file_id, file_name, file_type, share_link)

    def get_stoken(self, pwd_id: str):
        url = f"https://drive-pc.quark.cn/1/clouddrive/share/sharepage/token?pr=ucpro&fr=pc&uc_param_str=&__dt=405&__t={generate_timestamp(13)}"
        payload = {"pwd_id": pwd_id, "passcode": ""}
        headers = self.headers
        response = requests.post(url, json=payload, headers=headers).json()
        if response.get("data"):
            return response["data"]["stoken"]
        else:
            return ""

    def detail(self, pwd_id, stoken):
        url = f"https://drive-pc.quark.cn/1/clouddrive/share/sharepage/detail"
        headers = self.headers
        params = {
            "pwd_id": pwd_id,
            "stoken": stoken,
            "pdir_fid": 0,
            "_page": 1,
            "_size": "50",
        }
        response = requests.request("GET", url=url, headers=headers, params=params)
        id_list = response.json().get("data").get("list")[0]
        if id_list:
            data = {
                "title": id_list.get("file_name"),
                "file_type": id_list.get("file_type"),
                "fid": id_list.get("fid"),
                "pdir_fid": id_list.get("pdir_fid"),
                "share_fid_token": id_list.get("share_fid_token")
            }
            return data

    def save_task_id(self, pwd_id, stoken, first_id, share_fid_token, to_pdir_fid=0):
        logging.info("获取保存文件的TASKID")
        url = "https://drive.quark.cn/1/clouddrive/share/sharepage/save"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "__dt": int(random.uniform(1, 5) * 60 * 1000),
            "__t": generate_timestamp(13),
        }
        data = {"fid_list": [first_id],
                "fid_token_list": [share_fid_token],
                "to_pdir_fid": to_pdir_fid, "pwd_id": pwd_id,
                "stoken": stoken, "pdir_fid": "0", "scene": "link"}
        response = requests.request("POST", url, json=data, headers=self.headers, params=params)
        logging.info(response.json())
        task_id = response.json().get('data').get('task_id')
        return task_id

    def task(self, task_id, trice=10):
        """根据task_id进行任务"""
        logging.info("根据TASKID执行任务")
        trys = 0
        for i in range(trice):
            url = f"https://drive-pc.quark.cn/1/clouddrive/task?pr=ucpro&fr=pc&uc_param_str=&task_id={task_id}&retry_index={range}&__dt=21192&__t={generate_timestamp(13)}"
            trys += 1
            response = requests.get(url, headers=self.headers).json()
            logging.info(response)
            if response.get('data').get('status'):
                return response
        return False

    def share_task_id(self, file_id, file_name):
        """创建分享任务ID"""
        url = "https://drive-pc.quark.cn/1/clouddrive/share?pr=ucpro&fr=pc&uc_param_str="
        data = {"fid_list": [file_id],
                "title": file_name,
                "url_type": 1, "expired_type": 1}
        response = requests.request("POST", url=url, json=data, headers=self.headers)
        return response.json().get("data").get("task_id")

    def get_share_link(self, share_id):
        url = "https://drive-pc.quark.cn/1/clouddrive/share/password?pr=ucpro&fr=pc&uc_param_str="
        data = {"share_id": share_id}
        response = requests.post(url=url, json=data, headers=self.headers)
        return response.json().get("data").get("share_url")

    def get_all_file(self):
        """获取所有文件id"""
        logging.info("正在获取所有文件")
        all_file = []
        url = "https://drive-pc.quark.cn/1/clouddrive/file/sort?pr=ucpro&fr=pc&uc_param_str=&pdir_fid=0&_page=1&_size=50&_fetch_total=1&_fetch_sub_dirs=0&_sort=file_type:asc,updated_at:desc"
        response = requests.get(url, headers=self.headers)
        files_list = response.json().get('data').get('list')
        for files in files_list:
            file_list = files.get("files")
            for i in file_list:
                all_file.append(i)
        return all_file

    def get_dir_file(self, dir_id) -> list:
        logging.info("正在遍历父文件夹")
        """获取指定文件夹的文件,后期可能会递归"""
        url = f"https://drive-pc.quark.cn/1/clouddrive/file/sort?pr=ucpro&fr=pc&uc_param_str=&pdir_fid={dir_id}&_page=1&_size=50&_fetch_total=1&_fetch_sub_dirs=0&_sort=updated_at:desc"
        response = requests.get(url=url, headers=self.headers)
        files_list = response.json().get('data').get('list')
        return files_list

    def del_file(self, file_id):
        logging.info("正在删除文件")
        url = "https://drive-pc.quark.cn/1/clouddrive/file/delete?pr=ucpro&fr=pc&uc_param_str="
        data = {"action_type": 2, "filelist": [file_id], "exclude_fids": []}
        response = requests.post(url=url, json=data, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("data").get("task_id")
        return False

    def del_ad_file(self, file_list):
        logging.info("删除可能存在广告的文件")
        for file in file_list:
            file_name = file.get("file_name")
            from ad_check import ad_check
            if ad_check(file_name):
                task_id = self.del_file(file.get("fid"))
                self.task(task_id)

    def add_ad(self, dir_id):
        logging.info("添加个人自定义广告")
        pwd_id = self.ad_pwd_id
        stoken = self.get_stoken(pwd_id)
        detail = self.detail(pwd_id, stoken)
        first_id, share_fid_token = detail.get("fid"), detail.get("share_fid_token")
        task_id = self.save_task_id(pwd_id, stoken, first_id, share_fid_token, dir_id)
        self.task(task_id, 1)
        logging.info("广告移植成功")

    def search_file(self, file_name):
        logging.info("正在从网盘搜索文件🔍")
        url = "https://drive-pc.quark.cn/1/clouddrive/file/search?pr=ucpro&fr=pc&uc_param_str=&_page=1&_size=50&_fetch_total=1&_sort=file_type:desc,updated_at:desc&_is_hl=1"
        params = {"q": file_name}
        response = requests.get(url=url, headers=self.headers, params=params)
        return response.json().get('data').get('list')


if __name__ == '__main__':
    cookie = ''
    quark = Quark(cookie)
    quark.store('https://pan.quark.cn/s/92e708f45ca6#/list/share')

