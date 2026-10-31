import os
import discord
from discord.ext import tasks, commands
import gspread
from google.oauth2.service_account import Credentials
import traceback

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n")

creds_info = {
    "type": "service_account",
    "project_id": "savvy-fountain-450108-t6",
    "private_key_id": "32ee0d35ab99116946328cc0816325d8ce314deb",
    "private_key": private_key,
    "client_email": "discord-bot-sheets@savvy-fountain-450108-t6.iam.gserviceaccount.com",
    "client_id": "114177635698212694354",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/discord-bot-sheets%40savvy-fountain-450108-t6.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

CLIENT_CONFIG = {
    "1": {
        "discord_id": 1559166978734821427,
        "posting_sheet": "Posting Tasks",
        "payment_sheet": "Payment Tracking"
    }
}

try:
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client_gs = gspread.authorize(creds)
    print("✅ Bot 2 connected to Google Sheets!")
except Exception as e:
    traceback.print_exc()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

NOTIFIED_RETAINED_POSTS = set()

@tasks.loop(minutes=2)
async def check_sheet_retentions():
    for client_id_num, cfg in CLIENT_CONFIG.items():
        try:
            sheet = client_gs.open(cfg["posting_sheet"]).sheet1
            rows = sheet.get_all_values()
            discord_id = cfg["discord_id"]

            for idx, row in enumerate(rows[1:], start=2):
                if len(row) < 7:
                    continue

                worker_profile = row[0] if len(row) > 0 else "N/A"
                post_no = row[1] if len(row) > 1 else "Unknown Post"
                p1_link = row[4] if len(row) > 4 else "No link provided"
                p1_duration = row[5] if len(row) > 5 else "specified"
                p1_retained = row[6].strip() if len(row) > 6 else ""
                pay_rate = row[7] if len(row) > 7 else "$2"
                upi_details = row[15] if len(row) > 15 else "N/A"

                if p1_retained.lower() in ["yes", "1"] and f"C{client_id_num}_{post_no}_P1" not in NOTIFIED_RETAINED_POSTS:
                    NOTIFIED_RETAINED_POSTS.add(f"C{client_id_num}_{post_no}_P1")
                    await send_client_dm(discord_id, client_id_num, post_no, worker_profile, upi_details, pay_rate, p1_duration, p1_link)

        except Exception as e:
            print(f"Error checking retentions: {e}")

async def send_client_dm(discord_id, client_id_num, post_no, worker_name, upi, pay, duration, link):
    try:
        if discord_id and discord_id != 0:
            user = await bot.fetch_user(discord_id)
            if user:
                embed = discord.Embed(
                    title=f"🎉 Task Verified Live & Retained! ({post_no})",
                    description=f"**Client ID:** `{client_id_num}`\n**Worker Profile:** `{worker_name}`\n**Pay Rate:** `{pay}`\n**Worker UPI:** `{upi}`\n\n🔗 **Post Link:** {link}\n⏳ **Retention Duration:** {duration}",
                    color=discord.Color.green()
                )
                await user.send(embed=embed)
    except Exception as e:
        print(f"Failed to DM client: {e}")

@bot.event
async def on_ready():
    check_sheet_retentions.start()
    print(f"🤖 Sheet Automation Bot online as {bot.user}!")

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN_BOT2"))