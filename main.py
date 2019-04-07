#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author  : Amos
# @FileName: main.py
# @Blog    ：https://daogu.fun

import json, os
import telegram.ext
import telegram
import threading
import logging

# enable logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )

# 加载预设置项
CONFIG_LOCK = False
def_dir = os.path.join(os.getcwd(), 'config.json')  # 解决Windows和linux路径不一致问题
LANG = json.loads(open(def_dir, 'rb').read())

# 加载对话表
DATA_LOCK = False
# data_temp = json.loads(open(PATH + 'data.json', 'r').read())
data_dir = os.path.join(os.getcwd(), 'data.json')
data_temp = json.loads(open(data_dir, 'r').read())


# 将信息存入json 中
def store():
    global DATA_LOCK
    while DATA_LOCK:
        time.sleep(0.05)
    DATA_LOCK = True
    with open('data.json', 'w', encoding='utf-8') as fw:
        json.dump(data_temp, fw, ensure_ascii=False, indent=4)
    DATA_LOCK = False


# 保存配置到config.json
def save_config():
    global CONFIG_LOCK
    while CONFIG_LOCK:
        time.sleep(0.05)
    CONFIG_LOCK = True
    with open('config.json', 'w', encoding='utf-8') as fw:
        json.dump(LANG, fw, ensure_ascii=False, indent=4)
    CONFIG_LOCK = False


# 从对话表data.json中获取信息
def find(keyword):
    with open('data.json', 'r') as f:
        info = json.load(f)[keyword]
        # rs = json.dumps(info, ensure_ascii=False)  # 解决输出中文问题，又注释掉，是因为已存在的key机制更改
        return info


updater = telegram.ext.Updater(LANG["Token"], use_context=True)
dp = updater.dispatcher

print(LANG["Loading"])

me = updater.bot.get_me()
LANG["bot_username"] = '@' + me.username
print(me["first_name"] + '为您服务')


# 初始化bot配置
def init_bot(user):
    if LANG["Owner"] == "":
        return False
    if str(user.id) in LANG["Owner"]:
        return True


# 处理命令
def process_command(update, context):
    global data_temp
    # 判断是否为所有者，并提示进行bot设置
    command = update.message.text[1:].replace(LANG["bot_username"], '').split(' ', 2)
    if init_bot(update.message.from_user):
        # 判断是否已设置工作群组，并设置
        if LANG["Group"] == "":
            if command[0] != 'setgroup':
                update.message.reply_text(LANG["GroupNeeded"])
            elif command[0] == 'setgroup':
                LANG["Group"] = str(update.message.chat_id)
                获取管理员列表并设置
                p = updater.bot.get_chat_administrators(update.message.chat.id)
                admin0 = ""
                for i in range(0, len(p)):
                    temp = str(p[i]["user"]["id"])
                    admin0 = temp + "," + admin0
                LANG["Admin"] = admin0
                threading.Thread(target=save_config).start()
                updater.bot.sendMessage(chat_id=update.message.chat_id, text=LANG["GroupSeted"])
    else:
        if command[0] == 'setowner':
            LANG["Owner"] = str(update.message.from_user.id)
            threading.Thread(target=save_config).start()
            updater.bot.sendMessage(chat_id=update.message.chat_id, text=LANG["Owner_set_succeed"])
        else:
            update.message.reply_text(LANG["OwnerNeeded"])
    # 处理日常指令，/set = 设置信息及反馈；/get = 获取反馈;/help获取帮助;/group_id 获取群组id
    if str(update.message.chat_id) in LANG["Group"]:
        if str(update.message.from_user) in LANG["Admin"]:
            if command[0] == 'start':
                update.message.reply_text(LANG["Start"])
            elif command[0] == 'set' and len(command) > 2:
                key = command[1]
                if not command[1] in data_temp:
                    data_temp[key] = command[2]
                    threading.Thread(target=store).start()
                elif command[1] in data_temp:
                    temp = data_temp[command[1]] + '\n' + command[2]  # 更改方式，替换为字符串叠加
                    data_temp[key] = temp
                    threading.Thread(target=store).start()
            elif command[0] == 'renew' and len(command) == 2:
                key = command[1]
                data_temp[key] = command[2]
                threading.Thread(target=store).start()
            elif command[0] == 'del' and len(command) == 2:
                todel = command[1]
                data_temp.pop(todel)
                threading.Thread(target=store).start()
        elif LANG["Group"] == "" and command[0] == 'setgroup':
            if init_bot(update.message.from_user):
                LANG["Group"] = str(update.message.chat_id)
                threading.Thread(target=save_config).start()
                updater.bot.sendMessage(chat_id=update.message.chat_id, text=LANG["GroupSeted"])
        elif command[0] == 'get' and len(command) == 2:
            if command[1] in data_temp:
                keyword = command[1]
                p = find(keyword)
                update.message.reply_text(p)
            else:
                update.message.reply_text(LANG["NotFound"])
        # 获取群组id
        elif command[0] == 'get_id':
            update.message.reply_text(LANG["Get_id"] + str(update.message.chat_id))
        # 获取使用说明
        elif command[0] == 'help':
            update.message.reply_text(LANG["Help"])
    # 揪出群里的二五仔！
    elif not str(update.message.chat_id) in LANG["Owner"] and command[0] == 'setowner':
        updater.bot.sendMessage(chat_id=update.message.chat_id,text=LANG["OwnerExists"])

# 处理特殊消息,通过'&'唤醒此功能
def process_message(update, context):
    global data_temp
    if str(update.message.chat_id) in LANG["Group"]:
        info = update.message.text[1:].split()
        if update.message.text[0] == '&':
            if info[0] in data_temp:
                output = find(info[0])
                update.message.reply_text(output)
            if info[0] == 'all':
                print(LANG["GetAll"])
                output = []
                for key in data_temp.keys():
                    output.append(key)
                rs = json.dumps(output, ensure_ascii=False)
                update.message.reply_text(rs)


# 添加处理器
dp.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.command, process_command))
dp.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.all
                                           & ~telegram.ext.Filters.private
                                           & ~telegram.ext.Filters.command,
                                           process_message))

updater.start_polling()
print('开始运行')

updater.idle()
print("停止运行...")

store()
save_config()

print('退出')
