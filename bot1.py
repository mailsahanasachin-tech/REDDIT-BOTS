from keep_alive import keep_alive
import discord
from discord.ext import commands
import gspread
from google.oauth2.service_account import Credentials
import datetime
import random
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    private_key_lines = [
        "-----BEGIN PRIVATE KEY-----",
        "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDY14TKq0CDYf3g",
        "uE3LEsvuQ+F4MHFgtAyQ6q4pB3iYhF7JCAgCdN1ORlhsxZjmRN3tolo0ZbUggBLt",
        "P+F5LxKHidCjEz7aTDp+Rg3xzb525iXBYnFDp9fxND5SC+52rjVPhgFYTeyatnDr",
        "1+gu/esM4TR9E3ZKLEFg8zRxmWBof+c0vcYStLaqS0ReMgroqhBAp6l5n1vgATJV",
        "VjiqAgbNXXJ7p+7pcs3MNYRccAo0zZLKkuyfGVvCRELn0WZh6hrzvrCdXQGLWe8r",
        "oi+CyLWNQByuaB5eSKW4t/gusFAfW84Nb96vypilc0HDK7CDeryssWh2tQ9mryVt",
        "vCy7sM4zAgMBAAECggEAajh8wKjOE+3jJvsxhGpDQoa3AqC8UVIxm6WSRd/2h8PE",
        "CLcp8UYdCJR2CWZsJVST4C35ARTXesGyQ8zYnvvbmFB+xvuM/PN9bdDUUOBnziek",
        "VAxsjmdAZVQhuSBGIpXo4Hk03HRjlFANlcIwZyCUTT1ecGyhs+jk5+CLDqDC9LzX",
        "oCpsgV5VByAjrlNkIxCgGt0fWQ9s9iCSFEfPlorB7XM97GMK8TWXat2BJqgI0MPS",
        "xPdHBEpzAR4oMxB+AE5DH8UESs1k3Y8uvaFo3EmFbt1bTPDROBQUSHMtT91S3mkx",
        "xLJHYhjYS+OPtOWAkGao0Jqj362EQrNnEbSdkC8gKBgQD6FEsTIIMVp4a47VQo",
        "muVIson6VnuuyuHC0lxWrgXnIeJpXuHYdzrOqGI5tvbldbUS3XqsXRg5ZXj4Ckym",
        "k8l7mVwLMeyxcpEzYUW7vmDLcfli0RNerxnnaadMiQdVO1+IcTRLLl7Bs8yyMlZx",
        "5bMoLc6El0Epnxv/gEt6SNrGCwKBgQDd+cbXa/gjxKrSSbuUSdjlp2RzFgYKL1mG",
        "q393vbo6pRqXsLIT6IouiwASFH4eosYxksEqMVGUZaj/MDSguzbpM7OKP78d3RjG",
        "uX+cTnfjmLVQpYG0wakSpdhCRIJb7UVZoWI4+bC/5YjypEKu1Yqdknqx/+eWf470",
        "nn0J14Mp5eQKBgQDp7EeZeaUEgXMk0mMRpGprCQ7Fy1XgV8i8CzfyoM/Gt0xpUiah",
        "7E1m990BraLfWq5pGiFgz6gUMFXqdv/iJYWnhvmxQx7rkYY+8HNhPaCfTVqA059x",
        "xwrNC2hB0D+6u1IOeA35cUOTn1MPMMTpv3pJUCfIoQ+EFmADLIftt+5kpwKBgQDX",
        "na/pvQhc1Dz4AixICHZDjf4parjr6U2185p70JCrBk021fQO1km3YMYnGAiFLtgjG",
        "P3g7bFWRwP87eRr6CfaGZ2iMeMUPRG0xHwEbPoPXW3JLa/Pu6isdL9oqpbYlZKVz",
        "EM30IU5JTYeUg5k7d33o4ik06fdk9TJVcOHc6GVXcQKBgQDSasz8KvGXExrUH2Wd",
        "CShf9kzGTcxEl2TfsgEWQt9l3h/+w5a/r53/gqHU9FoO9idoXWM8UsjqmQXv5ypG",
        "DlRvjcQ/v1/7OpsCNfzePsxt9vAwtMgyqgB8n7u4KRxY6tV4EviBJLBciwYwNX9g",
        "EC23bUOCEup8jZzRUVME4tn3pA==",
        "-----END PRIVATE KEY-----"
    ]

    creds_info = {
        "type": "service_account",
        "project_id": "savvy-fountain-450108-t6",
        "private_key_id": "32ee0d35ab99116946328cc0816325d8ce314deb",
        "private_key": "\n".join(private_key_lines),
        "client_email": "discord-bot-sheets@savvy-fountain-450108-t6.iam.gserviceaccount.com",
        "client_id": "114177635698212694354",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/discord-bot-sheets%40savvy-fountain-450108-t6.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }

    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client_gs = gspread.authorize(creds)
    sheet_posting = client_gs.open("Posting Tasks").sheet1
    sheet_payment = client_gs.open("Payment Tracking").sheet1
    print("✅ Messenger Bot connected to Google Sheets successfully!")
except Exception as e:
    print(f"❌ Google Sheets Connection Error: {e}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

WORKER_TASKS_CHANNEL_ID = 1564649806482120805     # #reddit-tasks
CLIENT_ANSWERS_CHANNEL_ID = 1565406309950685287   # #client-answers
PRIVATE_PAYMENTS_CHANNEL_ID = 1565708632278958100 # Private Payment Ledger
CLIENT_USER_ID = 1518961433281433611               # Your Client ID

PENDING_TASKS = {}
OPEN_QUESTIONS = {}

class AskClientModal(discord.ui.Modal, title="Ask Client a Question"):
    post_number = discord.ui.TextInput(label="Post Number", style=discord.TextStyle.short, placeholder="e.g., Post #11", required=True)
    question_text = discord.ui.TextInput(label="Your Question", style=discord.TextStyle.paragraph, placeholder="Type your question anonymously...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        post_no = self.post_number.value.strip()
        q_text = self.question_text.value.strip()
        q_id = f"Q-{random.randint(100, 999)}"
        OPEN_QUESTIONS[q_id] = {"post_no": post_no, "question": q_text}

        client_channel = bot.get_channel(CLIENT_ANSWERS_CHANNEL_ID)
        if client_channel:
            embed = discord.Embed(title=f"❓ Anonymous Question ({q_id}) | {post_no}", description=f"**Question:**\n{q_text}", color=discord.Color.purple())
            embed.set_footer(text="Client: Click 'Answer Question' below to respond!")
            await client_channel.send(content=f"🔔 <@{CLIENT_USER_ID}> **New Question Received ({q_id})**", embed=embed, view=ClientAnswerTriggerView())
            await interaction.followup.send(f"✅ Question **{q_id}** posted anonymously!", ephemeral=True)

class QuestionSelectDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        for q_id, data in list(OPEN_QUESTIONS.items())[-25:]:
            options.append(discord.SelectOption(label=f"{q_id} ({data['post_no']})", description=data['question'][:50], value=q_id))
        if not options:
            options.append(discord.SelectOption(label="No open questions", value="none"))
        super().__init__(placeholder="Select the question you want to answer...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_q_id = self.values[0]
        if selected_q_id == "none":
            await interaction.response.send_message("⚠️ There are no open questions