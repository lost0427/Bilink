import sys
from asyncio import sleep
from .logger import Logger
from .tools import create_banner
from .. import message
from ..models import Message
from bilink.message import send_by_key


async def run():
    await message.fetch_msgs()
    Message.LastTimestamp = Message.Timestamp
    create_banner()
    Logger.info("bilibili消息助手正在运行...")
    try:
        while True:
            await message.fetch_msgs()

            # autoReply
            await message.auto_reply('你好', '(*´▽｀)ノノ你好鸭~~')

            # testSend
            # keywords = "test"  # 要搜索的关键词
            # user_msg = "111"  # 要发送的消息
            # await send_by_key(keywords, user_msg)

            # testGet
            # messages = message.get_msgs()
            # print(f"从文件读取的消息: \n{messages}")
            Message.LastTimestamp = Message.Timestamp
            await sleep(2)
    except KeyboardInterrupt:
        Logger.info('进程被用户手动终止')
        sys.exit()
