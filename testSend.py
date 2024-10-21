# main.py
import asyncio
from bilink.message import send_by_key
from asyncio import sleep
from bilink import message
from bilink.login.qr_scan import login_by_qrcode
from bilink.utils.cookies import Cookies
import sys
# from bilink.message import del_msgs


async def login() -> None:
    """
    通用bilibili登录
    :return:
    """
    cookies = Cookies()
    check = cookies.check()
    if check:
        cookies.load()
    else:
        token = await login_by_qrcode()
        cookies.save(token)


async def main():
    await login()
    await message.fetch_msgs()
    try:
        while True:
            await message.fetch_msgs()

            # argv
            # keywords = sys.argv[0]
            # user_msg = sys.argv[1]

            keywords = "test"  # 要搜索的关键词
            user_msg = "111"  # 要搜索的关键词

            await send_by_key(keywords, user_msg)
            # 现在会重复发送
            # del_msgs() #现在就删了你怎么知道给谁发消息？

            await sleep(2)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
