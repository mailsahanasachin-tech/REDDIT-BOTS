from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import aiohttp
import os
import json

# Automatically generate clean credentials.json on startup from environment variables
try:
    cred_data = {
        "type": "service_account",
        "project_id": os.getenv("G_PROJECT_ID"),
        "private_key_id": "32ee0d35ab99116946328cc0816325d8ce314deb",
        "private_key": os.getenv("G_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("G_CLIENT_EMAIL"),
        "client_id": "114177635698212694354",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/discord-bot-sheets%40savvy-fountain-450108-t6.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    with open("credentials.json", "w") as f:
        json.dump(cred_data, f)
    print("✅ Successfully generated credentials.json locally!")
except Exception as e:
    print(f"❌ Failed to generate credentials file: {e}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
    client_gs = gspread.authorize(creds)
    sheet_posting = client_gs.open("Posting Tasks").sheet1
    print("✅ Sheet Automation Bot connected to Google Sheets successfully!")
except Exception as e:
    print(f"❌ Google Sheets Connection Error: {e}")

WORKER_TASKS_CHANNEL_ID = 1564649806482120805

@tasks.loop(hours=1)
async def automated_sheet_keeper():
    try:
        rows = sheet_posting.get_all_values()
        worker_channel = bot.get_channel(WORKER_TASKS_CHANNEL_ID)

        for idx, row in enumerate(rows[1:], start=2):
            if len(row) >= 5:
                t1_type = row[3]
                t1_link = row[4]

                if t1_link and t1_link.startswith("http") and t1_type != "Invalid":
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
                    async with aiohttp.ClientSession(headers=headers) as session:
                        try:
                            async with session.get(t1_link, timeout=10) as resp:
                                text = await resp.text()
                                if resp.status == 404 or "removed by reddit's filters" in text.lower() or "sorry, this post was removed" in text.lower() or "removed by the moderators" in text.lower():
                                    sheet_posting.update_cell(idx, 4, "Invalid")
                                    sheet_posting.update_cell(idx, 1, "Unclaimed")
                                    sheet_posting.update_cell(idx, 5, "")
                                    sheet_posting.update_cell(idx, 16, "")
                                    
                                    if worker_channel:
                                        embed = discord.Embed(title=f"🔄 Task Reset & Re-Posted: {row[1]}", description="Post was removed. Marked Invalid and reset to Unclaimed.", color=discord.Color.orange())
                                        await worker_channel.send(embed=embed)
                                else:
                                    sheet_posting.update_cell(idx, 7, "Yes")
                        except Exception:
                            pass
    except Exception as e:
        print(f"Error in Bot 2: {e}")

@bot.event
async def on_ready():
    print(f"🤖 Sheet Automation Bot online as {bot.user}")
    if not automated_sheet_keeper.is_running():
        automated_sheet_keeper.start()

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))