from bilink.message import get_msgs
# from bilink.message import del_msgs


def main():
    messages = get_msgs()
    print(f"从文件读取的消息:\n{messages}")
    # del_msgs() #现在就删了你怎么知道给谁发消息？


if __name__ == "__main__":
    main()
