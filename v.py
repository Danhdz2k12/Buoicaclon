# =========================================================
# XWORLD TELEGRAM BOT - ULTRA FAST PREMIUM VERSION
# =========================================================

import telebot
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# =========================================================
# CONFIG
# =========================================================

TOKEN = "8717258749:AAEgG8r9vXteD75bqAD6ePPJL6LT-oXzQfk"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

session = requests.Session()

# =========================================================
# DATA
# =========================================================

users_data = {}

# =========================================================
# API FUNCTIONS
# =========================================================

def get_code_remaining(code):

    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://xworld-app.com',
        'referer': 'https://xworld-app.com/',
        'user-agent': 'Mozilla/5.0',
    }

    json_data = {
        'code': code,
        'os_ver': 'android',
        'platform': 'h5',
        'appname': 'app',
    }

    try:

        response = session.post(
            'https://web3task.3games.io/v1/task/redcode/detail',
            headers=headers,
            json=json_data,
            timeout=3
        ).json()

        if response.get("code") == 0:

            total = response["data"]["user_cnt"]
            progress = response["data"]["progress"]

            return total - progress

    except:
        return None

    return None


def redeem_code(user_id, secret_key, code):

    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://xworld.info',
        'referer': 'https://xworld.info/',
        'user-agent': 'Mozilla/5.0',
        'user-id': user_id,
        'user-secret-key': secret_key,
    }

    json_data = {
        'code': code,
        'os_ver': 'android',
        'platform': 'h5',
        'appname': 'app',
    }

    try:

        response = session.post(
            'https://web3task.3games.io/v1/task/redcode/exchange',
            headers=headers,
            json=json_data,
            timeout=3
        ).json()

        if response.get("code") == 0:

            value = response["data"]["value"]
            currency = response["data"]["currency"]

            return f"✅ <code>{user_id}</code> | +{value} {currency}"

        else:
            return f"❌ <code>{user_id}</code> | Fail"

    except:
        return f"⚠️ <code>{user_id}</code> | Network Error"


# =========================================================
# CHECK LOOP
# =========================================================

def code_checker(chat_id):

    last_sent = {}

    while True:

        if chat_id not in users_data:
            break

        data = users_data[chat_id]

        # pause
        if not data["running"]:
            time.sleep(0.5)
            continue

        # no code
        if len(data["codes"]) == 0:
            time.sleep(1)
            continue

        for code in data["codes"]:

            # anti duplicate
            if code in data["done_codes"]:
                continue

            remaining = get_code_remaining(code)

            current_time = time.strftime("%H:%M:%S")

            # log terminal only
            print(f"[{current_time}] {code} => {remaining}")

            # anti spam telegram
            if remaining is not None:

                if (
                    code not in last_sent
                    or time.time() - last_sent[code] > 10
                ):

                    try:
                        bot.send_message(
                            chat_id,
                            f"🎯 <b>{code}</b>\n"
                            f"📦 Remaining: <b>{remaining}</b>"
                        )

                    except:
                        pass

                    last_sent[code] = time.time()

            # trigger
            if remaining is not None and remaining <= data["threshold"]:

                data["done_codes"].add(code)

                try:
                    bot.send_message(
                        chat_id,
                        f"🚀 <b>CODE HIT:</b> {code}\n"
                        f"⚡ Start redeem..."
                    )
                except:
                    pass

                results = []

                with ThreadPoolExecutor(
                    max_workers=len(data["accounts"])
                ) as executor:

                    futures = []

                    for uid, skey in data["accounts"]:

                        futures.append(
                            executor.submit(
                                redeem_code,
                                uid,
                                skey,
                                code
                            )
                        )

                    for future in futures:

                        try:
                            results.append(future.result())
                        except:
                            pass

                result_text = (
                    f"🔥 <b>RESULT:</b> {code}\n\n"
                )

                for r in results:
                    result_text += r + "\n"

                try:
                    bot.send_message(
                        chat_id,
                        result_text
                    )
                except:
                    pass

        time.sleep(0.3)


# =========================================================
# COMMANDS
# =========================================================

@bot.message_handler(commands=['start'])
def start(message):

    chat_id = message.chat.id

    users_data[chat_id] = {
        "accounts": [],
        "threshold": 0,
        "codes": [],
        "running": False,
        "done_codes": set()
    }

    text = """
🔥 <b>XWORLD PREMIUM BOT</b> 🔥

📌 COMMANDS:

/setup - setup bot
/td - pause
/tt - continue
/tc - add more code
/list - show codes
/stop - clear all

⚡ Ultra Fast Version
⚡ Anti Spam
⚡ Multi Code
⚡ Multi Account
⚡ Realtime
"""

    bot.send_message(chat_id, text)


# =========================================================
# SETUP
# =========================================================

@bot.message_handler(commands=['setup'])
def setup(message):

    chat_id = message.chat.id

    msg = bot.send_message(
        chat_id,
        "📌 Number of accounts:"
    )

    bot.register_next_step_handler(
        msg,
        process_account_amount
    )


def process_account_amount(message):

    chat_id = message.chat.id

    try:

        amount = int(message.text)

        users_data[chat_id]["temp_amount"] = amount
        users_data[chat_id]["temp_accounts"] = []

        ask_account(chat_id, 1)

    except:
        bot.send_message(chat_id, "❌ Invalid Number")


def ask_account(chat_id, index):

    amount = users_data[chat_id]["temp_amount"]

    if index > amount:

        msg = bot.send_message(
            chat_id,
            "🎯 Remaining trigger:"
        )

        bot.register_next_step_handler(
            msg,
            process_threshold
        )

        return

    msg = bot.send_message(
        chat_id,
        f"🔗 Send account link {index}:"
    )

    bot.register_next_step_handler(
        msg,
        lambda m: process_account_link(m, index)
    )


def process_account_link(message, index):

    chat_id = message.chat.id

    try:

        link = message.text.strip()

        uid = link.split('?userId=')[1].split('&')[0]
        skey = link.split('secretKey=')[1].split('&')[0]

        users_data[chat_id]["temp_accounts"].append(
            (uid, skey)
        )

        bot.send_message(
            chat_id,
            f"✅ Added account {index}"
        )

        ask_account(chat_id, index + 1)

    except:
        bot.send_message(
            chat_id,
            "❌ Invalid Link"
        )


def process_threshold(message):

    chat_id = message.chat.id

    try:

        threshold = int(message.text)

        users_data[chat_id]["threshold"] = threshold
        users_data[chat_id]["accounts"] = users_data[chat_id]["temp_accounts"]

        msg = bot.send_message(
            chat_id,
            "🎟 Send first code:"
        )

        bot.register_next_step_handler(
            msg,
            process_first_code
        )

    except:
        bot.send_message(chat_id, "❌ Invalid Number")


def process_first_code(message):

    chat_id = message.chat.id

    code = message.text.strip().upper()

    users_data[chat_id]["codes"].append(code)
    users_data[chat_id]["running"] = True

    bot.send_message(
        chat_id,
        f"🚀 Started:\n<code>{code}</code>"
    )

    thread = threading.Thread(
        target=code_checker,
        args=(chat_id,),
        daemon=True
    )

    thread.start()


# =========================================================
# PAUSE
# =========================================================

@bot.message_handler(commands=['td'])
def pause_bot(message):

    chat_id = message.chat.id

    if chat_id in users_data:

        users_data[chat_id]["running"] = False

        bot.send_message(
            chat_id,
            "⏸ Bot Paused"
        )


# =========================================================
# RESUME
# =========================================================

@bot.message_handler(commands=['tt'])
def resume_bot(message):

    chat_id = message.chat.id

    if chat_id in users_data:

        users_data[chat_id]["running"] = True

        bot.send_message(
            chat_id,
            "▶️ Bot Continued"
        )


# =========================================================
# ADD CODE
# =========================================================

@bot.message_handler(commands=['tc'])
def add_code(message):

    chat_id = message.chat.id

    msg = bot.send_message(
        chat_id,
        "🎟 Send new code:"
    )

    bot.register_next_step_handler(
        msg,
        process_add_code
    )


def process_add_code(message):

    chat_id = message.chat.id

    code = message.text.strip().upper()

    if code not in users_data[chat_id]["codes"]:

        users_data[chat_id]["codes"].append(code)

        bot.send_message(
            chat_id,
            f"✅ Added code:\n<code>{code}</code>"
        )

    else:

        bot.send_message(
            chat_id,
            "⚠️ Code already exists"
        )


# =========================================================
# LIST CODE
# =========================================================

@bot.message_handler(commands=['list'])
def list_codes(message):

    chat_id = message.chat.id

    if len(users_data[chat_id]["codes"]) == 0:

        bot.send_message(
            chat_id,
            "❌ No Codes"
        )

        return

    text = "📜 <b>CODE LIST:</b>\n\n"

    for code in users_data[chat_id]["codes"]:
        text += f"• <code>{code}</code>\n"

    bot.send_message(chat_id, text)


# =========================================================
# STOP
# =========================================================

@bot.message_handler(commands=['stop'])
def stop_bot(message):

    chat_id = message.chat.id

    users_data[chat_id]["codes"] = []
    users_data[chat_id]["done_codes"] = set()

    bot.send_message(
        chat_id,
        "🛑 Cleared All Codes"
    )


# =========================================================
# RUN
# =========================================================

print("🔥 BOT RUNNING ULTRA FAST VERSION 🔥")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60
)
