from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import aiohttp

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
                    headers = {'User-Agent': 'Mozilla/5.0'}
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
    bot.run("YOUR_BOT_2_TOKEN")