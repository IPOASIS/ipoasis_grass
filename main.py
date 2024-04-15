import asyncio
import csv
import json
import os
import random
import ssl
import time
import uuid
from collections import defaultdict

import httpx
from loguru import logger
from websockets_proxy import proxy_connect, Proxy

title = '''
██ ██████   ██████   █████  ███████ ██ ███████      ██████  ██████   █████  ███████ ███████ 
██ ██   ██ ██    ██ ██   ██ ██      ██ ██          ██       ██   ██ ██   ██ ██      ██      
██ ██████  ██    ██ ███████ ███████ ██ ███████     ██   ███ ██████  ███████ ███████ ███████ 
██ ██      ██    ██ ██   ██      ██ ██      ██     ██    ██ ██   ██ ██   ██      ██      ██ 
██ ██       ██████  ██   ██ ███████ ██ ███████      ██████  ██   ██ ██   ██ ███████ ███████ 
'''


class GrassTask:
    def __init__(self, email, password, proxy_list):  # replace column1, column2, column3 with actual column names
        self.email = email
        self.password = password
        self.proxy_list = proxy_list
        self.login_token = None
        self.user_id = None
        self.total_points = None
        self.ip_points_map = {}

    def random_get_proxy(self):
        proxy = random.choice(self.proxy_list)
        if len(proxy.split(":")) == 2:
            ip, port = proxy.split(":")
            proxy = {
                "all://": f"socks5://{ip}:{port}"
            }
        elif len(proxy.split(":")) == 4:
            ip, port, username, password = proxy.split(":")
            proxy = {
                "all://": f"socks5://{username}:{password}@{ip}:{port}"
            }
        return proxy

    def get_socks5_proxy(self, normal_proxy):
        if len(normal_proxy.split(":")) == 2:
            ip, port = normal_proxy.split(":")
            return f"socks5://{ip}:{port}"
        elif len(normal_proxy.split(":")) == 4:
            ip, port, username, password = normal_proxy.split(":")
            return f"socks5://{username}:{password}@{ip}:{port}"

    async def login(self):
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'text/plain;charset=UTF-8',
            'dnt': '1',
            'origin': 'https://app.getgrass.io',
            'pragma': 'no-cache',
            'referer': 'https://app.getgrass.io/',
            'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }

        data = {
            "username": self.email,
            "password": self.password
        }

        while True:
            try:
                async with httpx.AsyncClient(proxies=self.random_get_proxy(), verify=False) as client:
                    response = await client.post('https://api.getgrass.io/login', headers=headers, json=data)
                    if response.status_code == 200:
                        self.login_token = response.cookies.get("token")
                        logger.success("login success: {}", self.email)
                        break
            except Exception as e:
                logger.error(e)
            await asyncio.sleep(60)

    async def get_total_points(self):
        try:
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'authorization': self.login_token,
                'cache-control': 'no-cache',
                'dnt': '1',
                'origin': 'https://app.getgrass.io',
                'pragma': 'no-cache',
                'referer': 'https://app.getgrass.io/',
                'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            }
            async with httpx.AsyncClient(proxies=self.random_get_proxy(), verify=False) as client:
                response = await client.get('https://api.getgrass.io/retrieveUser', headers=headers)
                j = response.json()
                self.user_id = j["result"]["data"]["userId"]
                self.total_points = j["result"]["data"]["totalPoints"]
        except Exception as e:
            logger.error(e)

    async def get_all_ip_points(self):
        while True:
            await self.get_total_points()
            logger.success("account: {} user_id: {} total_point: {}", self.email, self.user_id, self.total_points)
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'authorization': self.login_token,
                'cache-control': 'no-cache',
                'dnt': '1',
                'origin': 'https://app.getgrass.io',
                'pragma': 'no-cache',
                'referer': 'https://app.getgrass.io/',
                'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            }

            try:
                async with httpx.AsyncClient(proxies=self.random_get_proxy(), verify=False) as client:
                    resp = await client.get('https://api.getgrass.io/activeIps', headers=headers)
                    j = resp.json()
                    for ip in j["result"]["data"]:
                        self.ip_points_map[ip["ipAddress"]] = ip["ipScore"]
                    for ip in self.proxy_list:
                        ip_address = ip.split(":")[0]
                        if ip_address in self.ip_points_map:
                            logger.success("ip: {} score: {}", ip_address, self.ip_points_map[ip_address])
            except Exception as e:
                logger.error(e)

            await asyncio.sleep(60)

    async def run_one_wss(self, normal_proxy):
        device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, normal_proxy))
        while True:
            try:
                await asyncio.sleep(random.randint(1, 10) / 10)
                custom_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                }
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                uri = "wss://proxy.wynd.network:4650/"
                server_hostname = "proxy.wynd.network"
                proxy = Proxy.from_url(self.get_socks5_proxy(normal_proxy))
                async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                         extra_headers=custom_headers) as websocket:
                    async def send_ping():
                        while True:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                            logger.debug("{} send ping", self.email)
                            await websocket.send(send_message)
                            await asyncio.sleep(20)

                    await asyncio.sleep(1)
                    asyncio.create_task(send_ping())

                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)
                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": self.user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "3.3.3"
                                }
                            }
                            logger.success("{} auth success", self.email)
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug("{} receive pong", self.email)
                            await websocket.send(json.dumps(pong_response))
            except Exception as e:
                logger.error("{} wss with proxy {} failed, retrying", self.email, normal_proxy)

    async def start_run_all_wss(self):
        tasks = [self.run_one_wss(proxy) for proxy in self.proxy_list]
        tasks.append(self.get_all_ip_points())
        await asyncio.gather(*tasks)

    async def run_all(self):
        await self.login()
        await self.start_run_all_wss()


def check_and_create_csv():
    if not os.path.exists("tasks.csv"):
        with open("tasks.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "password", "proxy"])


def read_tasks_info():
    check_and_create_csv()
    with open("tasks.csv", "r") as f:
        tasks = []
        reader = csv.reader(f)
        next(reader)  # skip the first row
        account_proxy_map = defaultdict(list)
        for row in reader:
            if len(row[0]) == 0:
                continue
            account_proxy_map[(row[0], row[1])].append(row[2])

        for k, v in account_proxy_map.items():
            task = GrassTask(k[0], k[1], v)
            tasks.append(task)

        return tasks


async def main():
    print(title)
    tasks = read_tasks_info()
    wss_tasks = []
    for task in tasks:
        wss_tasks.append(asyncio.create_task(task.run_all()))
    await asyncio.gather(*wss_tasks)


if __name__ == '__main__':
    asyncio.run(main())
