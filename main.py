from aiogram import Router, F, Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from config import BOT_TOKEN
from io import BytesIO
from start import log
import requests
import asyncio
import json
import g4f


whiteList = []
GPTModel = "deepseek-r1"
ADMIN_ID = [5737305913, 1816346878]
MODELS = ["gpt-4o", "gpt-3.5-turbo", "gemini-1.5-flash", "gemini-1.5-pro", "deepseek-r1"]

router = Router()

def savehistory(chatid, history):
    with open(f"history/{chatid}.json", "w", encoding="utf-8") as f:
        json.dump(history, f)

def gethistory(chatid):
    with open(f"history/{chatid}.json", "r", encoding="utf-8") as f:
        chat_context = json.load(f)
    return chat_context

def getprompt():
    with open("prompt.txt") as f:
        prompt = f.readlines()[0].strip()
    return prompt

def isUserInWhiteList(id):
    global whiteList
    if not whiteList:
        return True
    return id in whiteList

async def blacklist(message: Message):
    await message.reply("Доступ к боту ограничен", parsemod="Markdown")

async def gpt(message: Message):
    global GPTModel
    userInput = message.text.strip()
    chat_id = message.chat.id
    log(f"@{message.from_user.username} : {userInput}")
    chat_context = gethistory(chat_id)
    userInput += "\n\nНапоминаю: " + getprompt()
    chat_context.append({"role": "user", "content": userInput})
    try:
        response = g4f.ChatCompletion.create(
            model = GPTModel,
            messages = chat_context,
        )
        if isinstance(response, dict) and "choices" in response:
            assistant_message = response["choices"][0]["message"]["content"]
        else:
            assistant_message = str(response)
    except Exception as e:
        assistant_message = f"Произошла ошибка при генерации ответа: {str(e)}"
        log(assistant_message)

    def delete_think(assistant_message):
        if "<ans>" in assistant_message and "</ans>" in assistant_message:
            assistant_message = assistant_message[assistant_message.rfind("<ans>") + 5: assistant_message.rfind("</ans>")]
        if "<ans>" in assistant_message:
            assistant_message = assistant_message[assistant_message.rfind("<ans>") + 5:]
        remove = ["Started thinking...\n"]
        for phrase in remove:
            assistant_message = assistant_message.replace(phrase, "")
        return assistant_message
    
    log(assistant_message)
    assistant_message = delete_think(assistant_message)
    # decoded_response = html.unescape(assistant_message)
    chat_context.append({"role": "assistant", "content": assistant_message})
    savehistory(chat_id, chat_context)
    split_messages = split_long_message(assistant_message)
    for msg in split_messages:
        log(msg)
        try:
            await message.reply(msg, parse_mode="Markdown")
        except Exception as e:
            await message.reply("Че-то херня какая-то случилась, ответа не будет", parse_mode="Markdown")

def split_long_message(message, chunkSize=4096):
    return [message[i:i + chunkSize] for i in range(0, len(message), chunkSize)]

@router.message(Command("start"), F.chat.type == "private")
async def start(message: Message):
    if not isUserInWhiteList(message.chat.id):
        await blacklist(message)
        return
    chat_id = message.chat.id
    prompt = getprompt() + '\n'
    prompt += f"Меня зовут {message.from_user.first_name}"
    chat_context = [{"role": "user", "content": prompt}]
    savehistory(chat_id, chat_context)
    await keepTyping(message, gpt)

@router.message(Command("menu"), F.chat.type == "private")
async def menu(message: Message):
    if not isUserInWhiteList(message.chat.id):
        await blacklist(message)
        return
    await message.reply("Menu", parse_mode="Markdown")

@router.message(Command("gdz"), F.chat.type == "private")
async def gdz(message: Message):
    if not isUserInWhiteList(message.chat.id):
        await blacklist(message)
        return
    try:
        subject, taskNum = [_.lower() for _ in message.text.split()[1:3]]
        if subject in ["rus", "ru", "r", "русский", "рус"]:
            photo_url = f"https://reshak.ru/reshebniki/russkijazik/10-11/goltsova/images1/part1/{taskNum}.png"
            response = requests.get(photo_url)
            response.raise_for_status()
            photo = BytesIO(response.content)
            photo.name = f"rus{taskNum}.png"
            await router.send_photo(message.chat.id, photo, reply_to_message_id = message.message_id)
        elif subject in ["physics", "phys", "phy", "физика", "физ"]:
            photo_url = f"https://reshak.ru/reshebniki/fizika/10/rimkevich10-11/images1/{taskNum}.png"
            response = requests.get(photo_url)
            response.raise_for_status()
            photo = BytesIO(response.content)
            photo.name = f"rus{taskNum}.png"
            await router.send_photo(message.chat.id, photo, reply_to_message_id = message.message_id)
        elif subject in ["algebra", "alg", "al", "алгебра", "алг"]:
            url = f"https://gdz.fm/algebra/10-klass/merzlyak-nomirovskij-uglublennij?ysclid=m5v4pyw2zy982385215#taskContainer?t={taskNum.split('/')[0]}-par-{taskNum.split('/')[1]}"
            response = requests.get(url)
            response.raise_for_status()
            await message.reply(url)
        else:
            await message.reply("Неверный предмет")
    except requests.RequestException as e:
        await message.reply(f"Я не смогла загрузить для Вас гдз 😭: {e}")
    except IndexError:
        await message.reply(f"Неверный формат!")
    except Exception as e:
        await message.reply(f"Произошел какой-то ужас: {e}")

@router.message(Command(commands=["reset", "delcontext"]), F.chat.type == "private")
async def reset(message: Message):
    if not isUserInWhiteList(message.chat.id):
        await blacklist(message)
        return
    chat_id = message.chat.id
    with open("end-message.txt") as f:
        text = f.readlines()[0].strip()
    prompt = getprompt() + '\n'
    prompt += f"Меня зовут {message.from_user.first_name}"
    chat_context = [{"role": "user", "content": prompt}]
    savehistory(chat_id, chat_context)
    await message.bot.send_message(chat_id, text)
    await keepTyping(message, gpt)

@router.message(Command("prompt"), F.chat.type == "private")
async def prompt(message: Message):
    if not isUserInWhiteList(message.chat.id):
        await blacklist(message)
        return
    if message.from_user.id in ADMIN_ID:
        p = " ".join(message.text.split()[1:])
        with open("prompt.txt", "w") as f:
            f.write(p)
        await message.reply("Success")

async def keepTyping(message, func):
    cnt = 0

    async def typing():
        nonlocal cnt
        while 0 <= cnt <= 5:
            await message.bot.send_chat_action(message.chat.id, "typing")
            await asyncio.sleep(5)
            cnt += 1
    
    async def thinking():
        nonlocal cnt
        await func(message)
        cnt = -10000

    await asyncio.gather(typing(), thinking())

@router.message(F.chat.type == "private", F.text)
async def textGPT(message: Message):
    if not isUserInWhiteList(message.chat.id):
        await blacklist(message)
        return
    await keepTyping(message, gpt)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

asyncio.run(main())
