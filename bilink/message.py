import json
import sys
import time
from typing import Pattern, AnyStr
from typing import List, Dict, Any

import httpx
import re
import os

from bilink.models import Authorization, Api, Message
from bilink.utils.logger import Logger
from bilink.utils.tools import create_headers

import asyncio


class __BaseMatcher:
    ...


class Matcher(__BaseMatcher):
    """
    消息匹配规则
    """

    @classmethod
    def starts_with(cls, msg: str) -> bool:
        if Message.MsgContent.startswith(msg):
            return True
        else:
            return False

    @classmethod
    def ends_with(cls, msg: str) -> bool:
        if Message.MsgContent.endswith(msg):
            return True
        else:
            return False

    @classmethod
    def contains(cls, msg: str) -> bool:
        if msg in Message.MsgContent:
            return True
        else:
            return False

    @classmethod
    def regex(cls, pattern: Pattern[AnyStr], msg: str) -> bool:
        matched = re.findall(pattern, msg)
        if matched:
            return True
        else:
            return False


current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
MESSAGES_FILE = os.path.join(parent_dir, 'messages.json')


async def is_new_msg():
    """
    判断是否有新的消息（且不是自己的消息
    """
    if Message.Timestamp != Message.LastTimestamp and Message.SenderUid != Authorization.SelfUid:
        Logger.message(f"用户[{Message.SenderUid}]:{Message.MsgContent}")
        await save_message_to_file(Message)

        return True
    else:
        return False


async def auto_reply(keywords: str, msg: str) -> None:
    """
    根据关键词自动回复一条消息
    """
    if await is_new_msg() and Matcher.starts_with(keywords):
        await send_text_msg(
            msg,
            Message.SenderUid
        )


async def send_by_key(keyword: str, user_msg: str) -> None:
    """
    根据关键词查找符合条件的消息并发送用户输入的消息
    """
    all_msgs = get_msgs()
    matching_msgs = []

    for msg in all_msgs:
        # 确保 msg 是一个字典
        if isinstance(msg, dict):
            Message.MsgContent = msg.get('MsgContent', '')  # 假设消息内容存储在 'MsgContent' 键中
            if Matcher.contains(keyword):
                matching_msgs.append(msg)

    # 发送用户输入的消息
    for _ in matching_msgs:
        Message.SenderUid = msg.get('SenderUid')  # 更新 SenderUid
        await send_text_msg(user_msg, Message.SenderUid)  # 发送用户输入的消息


"""
现在找到了，还要发出去
还有格式输出，现在太丑了
"""


def get_msgs() -> List[Dict[str, Any]]:
    """
    读取文件中的消息并返回消息列表。如果文件为空或没有消息，返回空列表。
    """
    if not os.path.exists(MESSAGES_FILE):
        return []

    try:
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return []
            return json.loads(content)
    except Exception as e:
        print(f"读取消息时发生错误: {e}")
        return []


def del_msgs() -> str:
    """
    删除文件内所有内容。
    """
    if not os.path.exists(MESSAGES_FILE):
        return "文件已经不见了"

    try:
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            f.truncate(0)
        return "消息已清空"
    except Exception as e:
        return f"删除消息时发生错误: {e}"


async def send_text_msg(msg: str, receiver_id: int) -> None:
    """
    发送文本消息
    """
    data = {
        'msg[sender_uid]': Authorization.SelfUid,
        'msg[receiver_id]': receiver_id,
        'msg[receiver_type]': 1,
        'msg[msg_type]': 1,
        'msg[msg_status]': 0,
        'msg[dev_id]': '00000000-0000-0000-0000-000000000000',
        'msg[timestamp]': int(time.time()),
        'csrf': Authorization.Token,
        'csrf_token': Authorization.Token,
        'msg[content]': '{"content": "%s"}' % msg,
        'msg[new_face_version]': 0,
        'from_firework': 0,
        'build': 0,
        'mobi_app': 'web'
    }
    try:
        async with httpx.AsyncClient() as client:
            client: httpx.AsyncClient
            res: httpx.Response = await client.post(
                url=Api.SEND_MSG,
                cookies=Authorization.Cookie,
                headers=create_headers(),
                data=data
            )
            if res.status_code == 200:
                if res.json().get('code') == 0:
                    Logger.message(f'me :{msg}')
                else:
                    Logger.error(res.json().__str__())
            else:
                Logger.error('Error: Sending message failed')
    except Exception as e:
        Logger.error(f"发生错误:{e}")
        sys.exit(-1)


async def send_request() -> bool:
    """
    发送网络请求并解析数据
    """
    try:
        async with httpx.AsyncClient() as client:
            client: httpx.AsyncClient
            res: httpx.Response = await client.get(
                url=Api.GET_SESSIONS,
                cookies=Authorization.Cookie,
                headers=create_headers(),
                timeout=None
            )
            string = res.json()
            session_list = string['data']['session_list']
            last_talker = session_list[0]
            last_msg = last_talker['last_msg']
            msg_json = json.loads(
                last_msg['content'].replace('\'', '\"')
            )
            Message.TalkerId = last_talker['talker_id']
            if msg_json.get('content'):
                Message.MsgContent = msg_json['content']
            elif msg_json.get('reply_content'):
                Message.MsgContent = msg_json['reply_content']
            else:
                Message.MsgContent = ''
            Message.Timestamp = last_msg['timestamp']
            Message.SenderUid = last_msg['sender_uid']
            return True
    except (httpx.HTTPError, httpx.ConnectError):
        Logger.error(f"网络错误，请关闭代理")
        sys.exit(-1)
    except Exception as e:
        Logger.error(f"发生错误:{e},正在重试...")
        time.sleep(2)
        return False


async def save_message_to_file(message: Message):
    """
    将消息存入文件，以JSON格式存储
    """
    message_data = {
        'TalkerId': message.TalkerId,
        'MsgContent': message.MsgContent,
        'Timestamp': message.Timestamp,
        'SenderUid': message.SenderUid
    }
    try:
        lock = asyncio.Lock()
        async with lock:
            # 读取现有内容
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    existing_messages = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_messages = []

            # 添加新消息
            existing_messages.append(message_data)

            # 写回文件
            with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_messages, f, ensure_ascii=False, indent=4)
        Logger.info("新消息已存入文件")
    except Exception as e:
        Logger.error(f"保存消息到文件时发生错误: {e}")


async def fetch_msgs() -> None:
    """
    获取最新一条消息记录
    """
    while True:
        check = await send_request()
        if check:
            break
