from telethon import TelegramClient, events, functions, types
import random
import asyncio
import os
import time
import json
import sqlite3

# File paths
ACCOUNTS_FILE = 'accounts.json'
CAPTION_FILE = 'caption.txt'
TARGETS_FILE = 'targets.txt'
DELAY_FILE = 'delay.txt'
APPROVED_USERS_FILE = 'approved_users.txt'
REPORT_TARGETS_FILE = 'report_targets.txt'

# Default configuration
DEFAULT_CONFIG = {
    "accounts": [
        {
            "api_id": 26245670,
            "api_hash": "a02a7cdf60f9c7beaae80470227f3d04",
            "session_name": "my_account",
            "active": True
        }
    ],
    "admin_id": 7218474237
}

# Speed presets (messages per second)
SPEED_PRESETS = {
    'low': 20,
    'medium': 50,
    'high': 100,
    'ultra': 250,
    'ultra++': 2000,
    'superultra': 5000,
    'ultra+++': 10000,
    'extreme': 20000
}

# Default settings
DEFAULT_DELAY = 1
MAX_MESSAGES = 50000
pending_logins = {}

# Emojis
EMOJIS = ["💣", "🔥", "⚡", "🎯", "👊", "💢", "🤬", "🚀", "💥", "🔪", "🖕", "🍆", "💦", "👅", "🤡"]

# Vulgar word banks
VULGAR_NOUNS = ["maa", "behen", "bhosda", "lund", "chut", "gaand", "randi", "kutta", "madarchod", "harami", "gandu", "chutmarike", "bhenchod"]
VULGAR_VERBS = ["chod", "pel", "mara", "nanga", "chusa", "kaata", "phoda", "daba", "ghusa", "latka", "jhuka", "nacha", "dala"]
VULGAR_ADJECTIVES = ["sasti", "gandi", "kamina", "besharam", "nalayak", "chutiya", "bhadwa", "lulli", "jhaant", "randi", "kamine", "bewakoof"]

# Text Styles
STYLES = [
    lambda t: f"**{t}**",
    lambda t: f"__{t}__",
    lambda t: f"~~{t}~~",
    lambda t: f"`{t}`",
    lambda t: f"🔥 {t} 🔥",
    lambda t: f"⚡ {t} ⚡",
    lambda t: f"💢 {t} 💢",
    lambda t: f"||{t}||",
    lambda t: f"😈 {t} 😈",
]

# Global variables
is_sending = False
current_delay = DEFAULT_DELAY
message_count = 0
max_messages = MAX_MESSAGES
clients = []

# Helper functions
def load_config():
    if not os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except:
        return False

def save_to_file(filename, text):
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{text}\n")
        return True
    except Exception as e:
        print(f"Error saving to file: {e}")
        return False

def read_file(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def clear_file(filename):
    try:
        open(filename, 'w').close()
        return True
    except Exception as e:
        print(f"Error clearing file: {e}")
        return False

def remove_line(filename, text):
    try:
        lines = read_file(filename)
        if text in lines:
            lines.remove(text)
            if clear_file(filename):
                for line in lines:
                    save_to_file(filename, line)
                return True
        return False
    except Exception as e:
        print(f"Error removing line: {e}")
        return False

def generate_vulgar_caption():
    patterns = [
        f"{random.choice(VULGAR_NOUNS)} ki {random.choice(VULGAR_NOUNS)}",
        f"{random.choice(VULGAR_ADJECTIVES)} {random.choice(VULGAR_NOUNS)}",
        f"{random.choice(VULGAR_VERBS)} diya {random.choice(VULGAR_NOUNS)} ko",
        f"{random.choice(VULGAR_NOUNS)} {random.choice(VULGAR_VERBS)}ne wala",
        f"{random.choice(VULGAR_NOUNS)} {random.choice(VULGAR_VERBS)} ke chod",
        f"{random.choice(VULGAR_NOUNS)} {random.choice(VULGAR_VERBS)} {random.choice(VULGAR_NOUNS)}",
        f"{random.choice(VULGAR_NOUNS)} ke {random.choice(VULGAR_NOUNS)} mein {random.choice(VULGAR_VERBS)}",
        f"{random.choice(VULGAR_ADJECTIVES)} {random.choice(VULGAR_NOUNS)} ka {random.choice(VULGAR_NOUNS)}"
    ]
    return random.choice(patterns)

def random_style(text):
    words = text.split()
    styled = []
    for word in words:
        style = random.choice(STYLES)
        styled.append(style(word))
    return ' '.join(styled)

def get_delay():
    if os.path.exists(DELAY_FILE):
        try:
            with open(DELAY_FILE, 'r') as f:
                content = f.read().strip()
                return float(content) if content else DEFAULT_DELAY
        except:
            return DEFAULT_DELAY
    return DEFAULT_DELAY

def set_delay(seconds):
    try:
        with open(DELAY_FILE, 'w') as f:
            f.write(str(seconds))
        return True
    except Exception as e:
        print(f"Error setting delay: {e}")
        return False

def is_user_approved(user_id):
    approved_users = read_file(APPROVED_USERS_FILE)
    return str(user_id) in approved_users

# Initialize main client
config = load_config()
admin_id = config.get("admin_id", 7681062358)
main_client = TelegramClient(config["accounts"][0]["session_name"], 
                           config["accounts"][0]["api_id"], 
                           config["accounts"][0]["api_hash"])

# Account Management
@main_client.on(events.NewMessage(pattern='/addaccount'))
async def add_account(event):
    if event.sender_id != admin_id:
        await event.reply("🚫 Only admin can add accounts!")
        return
    
    args = event.raw_text.split()
    if len(args) != 4:
        await event.reply("⚠️ Format: /addaccount api_id api_hash session_name")
        return
    
    try:
        new_account = {
            "api_id": int(args[1]),
            "api_hash": args[2],
            "session_name": args[3],
            "active": True
        }
        
        config["accounts"].append(new_account)
        if save_config(config):
            await event.reply(f"✅ Account added!\nSession: {args[3]}")
        else:
            await event.reply("⚠️ Failed to save account!")
    except Exception as e:
        await event.reply(f"⚠️ Error: {str(e)}")

@main_client.on(events.NewMessage(pattern='/removeaccount'))
async def remove_account(event):
    if event.sender_id != admin_id:
        await event.reply("🚫 Only admin can remove accounts!")
        return
    
    session_name = event.raw_text.replace('/removeaccount', '').strip()
    if not session_name:
        await event.reply("⚠️ Please provide session name!")
        return
    
    updated_accounts = [acc for acc in config["accounts"] if acc["session_name"] != session_name]
    
    if len(updated_accounts) < len(config["accounts"]):
        config["accounts"] = updated_accounts
        if save_config(config):
            await event.reply(f"✅ Account removed: {session_name}")
        else:
            await event.reply("⚠️ Failed to save changes!")
    else:
        await event.reply("⚠️ Account not found!")

@main_client.on(events.NewMessage(pattern='/listaccounts'))
async def list_accounts(event):
    if event.sender_id != admin_id:
        await event.reply("🚫 Only admin can view accounts!")
        return
    
    reply = "📋 **CONFIGURED ACCOUNTS:**\n\n"
    for i, acc in enumerate(config["accounts"], 1):
        status = "🟢" if acc.get("active", True) else "🔴"
        reply += f"{i}. {status} {acc['session_name']} (ID: {acc['api_id']})\n"
    
    await event.reply(reply)

# Mass Reporting System
@main_client.on(events.NewMessage(pattern='/addreport'))
async def add_report_target(event):
    if event.sender_id != admin_id and not is_user_approved(event.sender_id):
        await event.reply("🚫 You are not approved to use this command!")
        return
    
    target = event.raw_text.replace('/addreport', '').strip()
    if not target:
        await event.reply("⚠️ Please provide target (username or link)!")
        return
    
    if save_to_file(REPORT_TARGETS_FILE, target):
        await event.reply(f"✅ Target added for reporting: {target}")
    else:
        await event.reply("⚠️ Failed to add target!")

@main_client.on(events.NewMessage(pattern='/removereport'))
async def remove_report_target(event):
    if event.sender_id != admin_id and not is_user_approved(event.sender_id):
        await event.reply("🚫 You are not approved to use this command!")
        return
    
    target = event.raw_text.replace('/removereport', '').strip()
    if not target:
        await event.reply("⚠️ Please provide target to remove!")
        return
    
    if remove_line(REPORT_TARGETS_FILE, target):
        await event.reply(f"❌ Target removed: {target}")
    else:
        await event.reply("⚠️ Target not found!")

@main_client.on(events.NewMessage(pattern='/listreports'))
async def list_report_targets(event):
    if event.sender_id != admin_id and not is_user_approved(event.sender_id):
        await event.reply("🚫 You are not approved to use this command!")
        return
    
    targets = read_file(REPORT_TARGETS_FILE)
    if not targets:
        await event.reply("📭 No report targets saved!")
        return
    
    reply = "🎯 **REPORT TARGETS:**\n\n"
    for i, target in enumerate(targets, 1):
        reply += f"{i}. {target}\n"
    
    await event.reply(reply)

@main_client.on(events.NewMessage(pattern='/massreport'))
async def mass_report(event):
    if event.sender_id != admin_id:
        await event.reply("🚫 Only admin can initiate mass reports!")
        return
    
    targets = read_file(REPORT_TARGETS_FILE)
    if not targets:
        await event.reply("⚠️ No report targets set! Use /addreport first.")
        return
    
    await event.reply(f"🚨 Starting mass report of {len(targets)} targets...")
    
    for account in config["accounts"]:
        if not account.get("active", True):
            continue
            
        try:
            client = TelegramClient(account["session_name"], account["api_id"], account["api_hash"])
            await client.start()
            
            for target in targets:
                try:
                    entity = await client.get_entity(target)
                    await client(functions.messages.ReportRequest(
                        peer=entity,
                        reason=types.InputReportReasonSpam(),
                        message_ids=[]
                    ))
                    await event.reply(f"✅ Reported {target} with {account['session_name']}")
                    await asyncio.sleep(5)
                except Exception as e:
                    await event.reply(f"⚠️ Failed to report {target} with {account['session_name']}: {str(e)}")
            
            await client.disconnect()
        except Exception as e:
            await event.reply(f"⚠️ Error with account {account['session_name']}: {str(e)}")
    
    await event.reply("✅ Mass report completed!")

# Spam Commands
@main_client.on(events.NewMessage(pattern='/chodo'))
async def chodo(event):
    if event.sender_id != admin_id and not is_user_approved(event.sender_id):
        await event.reply("🚫 You are not approved to spam!")
        return
    
    global is_sending, current_delay, message_count, max_messages
    is_sending = True
    message_count = 0
    current_delay = get_delay()
    await event.reply(f"**💣 BOMBING STARTED! 💣**\n__Speed:__ `{1/current_delay:.1f} msg/s`\n__Max:__ `{max_messages}`\n__Mode:__ `ULTRA SPAM`")
    
    while is_sending and message_count < max_messages:
        captions = read_file(CAPTION_FILE)
        targets = read_file(TARGETS_FILE)
        
        if not captions:
            caption = generate_vulgar_caption()
        else:
            caption = random.choice(captions)
        
        if not targets:
            await event.reply("⚠️ No targets! Use /madarchod")
            is_sending = False
            return
        
        target = random.choice(targets)
        emoji = random.choice(EMOJIS)
        styled_caption = random_style(caption)
        final_msg = f"__{target}__\n\n{emoji} {styled_caption} {emoji}"
        
        try:
            await event.respond(final_msg)
            message_count += 1
            if current_delay > 0:
                await asyncio.sleep(current_delay)
        except Exception as e:
            await event.reply(f"⚠️ Error: `{str(e)}`")
            is_sending = False
            return
    
    is_sending = False
    await event.reply(f"✅ **BOMBING COMPLETE!**\n__Messages sent:__ `{message_count}`")
    
@main_client.on(events.NewMessage(pattern='/login'))
async def handle_login(event):
    if event.sender_id != admin_id:
        return
    
    args = event.raw_text.split()
    if len(args) < 2:
        await event.reply("Format: /login session_name [phone]")
        return
    
    session_name = args[1]
    phone = args[2] if len(args) > 2 else None
    account = next((acc for acc in config["accounts"] if acc["session_name"] == session_name), None)
    
    if not account:
        await event.reply("Account not found!")
        return
    
    try:
        client = TelegramClient(account["session_name"], account["api_id"], account["api_hash"])
        
        if phone:
            # Store the phone number in the account config
            account["phone"] = phone
            save_config(config)
        
        # Store the client and event in pending_logins
        pending_logins[session_name] = {
            "client": client,
            "event": event
        }
        
        await client.connect()
        await client.send_code_request(phone or account.get("phone"))
        await event.reply(f"📲 Login code requested for {session_name}. Send code with /code [session_name] [code]")
        
    except Exception as e:
        await event.reply(f"⚠️ Login failed: {str(e)}")
        if session_name in pending_logins:
            del pending_logins[session_name]

@main_client.on(events.NewMessage(pattern='/code'))
async def handle_code(event):
    if event.sender_id != admin_id:
        return
    
    args = event.raw_text.split()
    if len(args) < 3:
        await event.reply("Format: /code [session_name] [code]")
        return
    
    session_name = args[1]
    code = args[2]
    
    if session_name not in pending_logins:
        await event.reply("⚠️ No pending login for this session!")
        return
    
    try:
        login_data = pending_logins[session_name]
        client = login_data["client"]
        original_event = login_data["event"]
        
        # Sign in with the code
        await client.sign_in(code=code)
        clients.append(client)
        await original_event.reply(f"✅ Successfully logged in to {session_name}!")
        del pending_logins[session_name]
        
    except Exception as e:
        await event.reply(f"⚠️ Code verification failed: {str(e)}")

async def request_code_from_admin(event):
    await event.reply("Please send the OTP code in format: /code [session_name] [code]")
    # You would need additional logic to wait for and handle the code response

@main_client.on(events.NewMessage(pattern='/ruko'))
async def ruko(event):
    if event.sender_id != admin_id and not is_user_approved(event.sender_id):
        await event.reply("🚫 You are not approved to use this command!")
        return
    
    global is_sending
    is_sending = False
    await event.reply(f"🛑 **SPAM STOPPED!**\n__Messages sent:__ `{message_count}`")

# ... [include all the other existing commands like /ac, /dc, /cc, etc.] ...

@main_client.on(events.NewMessage(pattern='/help'))
async def show_help(event):
    if event.sender_id != admin_id:
        return
    
    help_text = """
    💣 **ULTRA SPAM BOT v4.0 HELP** 💣

    👑 **ADMIN COMMANDS:**
    /addaccount api_id api_hash session_name - Add new account
    /removeaccount session_name - Remove account
    /listaccounts - List all accounts
    /approve [user_id] - Approve a user
    /disapprove [user_id] - Remove user approval
    /approved_list - List approved users

    🚨 **MASS REPORT SYSTEM:**
    /addreport [target] - Add report target
    /removereport [target] - Remove report target
    /listreports - List report targets
    /massreport - Mass report all targets
    /login - login ke time

    🎯 **TARGET MANAGEMENT:**
    /madarchod [@user] - Add target
    /nikal [@user] - Remove target
    /saaf - Clear all targets
    /list - View targets

    📜 **CAPTION MANAGEMENT:**
    /ac [text] - Add caption
    /dc [text] - Delete caption
    /cc - Clear all captions
    /viewcaptions - View captions

    ⚡ **SPAM CONTROL:**
    /chodo - Start bombing
    /ruko - Stop spam
    /speed [preset|seconds] - Set speed
    /setmax [number] - Set max messages
    /status - Show bot status

    🔥 **Auto-Generates:** Strong vulgar abuse
    """
    await event.reply(help_text)

async def initialize_clients():
    global clients
    for account in config["accounts"]:
        try:
            # Add retry logic for locked database
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    client = TelegramClient(
                        account["session_name"], 
                        account["api_id"], 
                        account["api_hash"]
                    )
                    await client.start()
                    clients.append(client)
                    print(f"Logged in as: {await client.get_me()}")
                    break
                except sqlite3.OperationalError as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Failed to initialize {account['session_name']}: {str(e)}")
            
async def main():
    # Create files if they don't exist
    for file in [CAPTION_FILE, TARGETS_FILE, DELAY_FILE, APPROVED_USERS_FILE, REPORT_TARGETS_FILE]:
        if not os.path.exists(file):
            open(file, 'w').close()
    
    print("💣 **ULTRA SPAM BOT v4.0 STARTED!**")
    try:
        await initialize_clients()
        await main_client.run_until_disconnected()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Force disconnect without saving state
        await main_client.disconnect()

