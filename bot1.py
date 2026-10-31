import os
from keep_alive import keep_alive
import discord
from discord.ext import tasks, commands
import gspread
from google.oauth2.service_account import Credentials
import datetime
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

try:
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client_gs = gspread.authorize(creds)
    sheet_posting = client_gs.open("Posting Tasks").sheet1
    sheet_payment = client_gs.open("Payment Tracking").sheet1
    print("✅ Bot 1 connected to Google Sheets!")
except Exception as e:
    traceback.print_exc()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

WORKER_TASKS_CHANNEL_ID = 1564649806482120805
PRIVATE_PAYMENTS_CHANNEL_ID = 1564649838233256056
CLIENT_PAYMENTS_CHANNEL_ID = 1565650024552210523

PENDING_TASKS = {}
PENDING_PAYMENTS = {}
ACTIVE_UNCLAIMED_TASKS = {}

@tasks.loop(minutes=30)
async def repost_unclaimed_tasks():
    for post_no, task_data in list(ACTIVE_UNCLAIMED_TASKS.items()):
        worker_channel = bot.get_channel(WORKER_TASKS_CHANNEL_ID)
        if worker_channel:
            embed = discord.Embed(title=f"📌 [RE-POSTED] Task Available: {post_no}", description=f"**Instructions / Content:**\n{task_data['content_text']}", color=discord.Color.gold())
            embed.add_field(name="Task Type", value=f"{task_data['t_type']}", inline=True)
            embed.add_field(name="Phase 1", value=f"💰 **Pay:** ${task_data['standard_worker_pay']}\n⏳ **Retention:** {task_data['p1_details']}", inline=True)
            view = WorkerTaskInteractionView(post_no, task_data["t1_client_rate"], "", "1")
            await worker_channel.send(embed=embed, view=view)

class ClientPaymentModal(discord.ui.Modal, title="Confirm Task Payment"):
    worker_name = discord.ui.TextInput(label="Name (Worker Profile)", style=discord.TextStyle.short, placeholder="e.g. FistMyBump", required=True)
    post_number = discord.ui.TextInput(label="Post No", style=discord.TextStyle.short, placeholder="Post #11", required=True)
    pay_amount = discord.ui.TextInput(label="Pay", style=discord.TextStyle.short, placeholder="2 or 6", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        w_name = self.worker_name.value.strip()
        post_no = self.post_number.value.strip()
        pay = self.pay_amount.value.strip()

        PENDING_PAYMENTS[interaction.user.id] = {"w_name": w_name, "post_no": post_no, "pay": pay}
        await interaction.followup.send(f"✅ Payment details recorded for **{w_name}** ({post_no} - ${pay})!\n📸 Now type `!img` and attach your screenshot.", ephemeral=True)

class PaymentProofView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Confirm Payment Sent", style=discord.ButtonStyle.primary, custom_id="client_payment_sent_btn")
    async def payment_sent_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClientPaymentModal())

@bot.command()
async def img(ctx):
    if ctx.author.id in PENDING_PAYMENTS:
        if not ctx.message.attachments:
            await ctx.send("⚠️ Please attach screenshot along with `!img`!", delete_after=10)
            return
        pay_info = PENDING_PAYMENTS.pop(ctx.author.id)
        files_list = [await att.to_file() for att in ctx.message.attachments]
        
        worker_ledger_chan = bot.get_channel(PRIVATE_PAYMENTS_CHANNEL_ID)
        if worker_ledger_chan:
            guild_member = discord.utils.get(ctx.guild.members, display_name=pay_info['w_name']) or discord.utils.get(ctx.guild.members, name=pay_info['w_name'])
            tag_str = guild_member.mention if guild_member else pay_info['w_name']

            embed = discord.Embed(title=f"💳 Payment Made: {pay_info['post_no']}", description=f"**Worker:** {tag_str}\n**Post No:** {pay_info['post_no']}\n**Pay:** ${pay_info['pay']}", color=discord.Color.green())
            await worker_ledger_chan.send(content=f"🔔 {tag_str} You have been paid **${pay_info['pay']}** for **{pay_info['post_no']}**!", embed=embed, files=files_list)
        
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send("✅ Payment proof published!", delete_after=5)
        return

    if ctx.author.id in PENDING_TASKS:
        if not ctx.message.attachments:
            await ctx.send("⚠️ Please attach image(s) along with `!img`!", delete_after=10)
            return
        task_data = PENDING_TASKS.pop(ctx.author.id)
        files_list = [await att.to_file() for att in ctx.message.attachments]
        await publish_task_to_workers(task_data, files_list)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        await ctx.send(f"✅ **Task {task_data['post_no']} published with images!**", delete_after=5)

class WorkerClaimModal(discord.ui.Modal, title="Claim Task & Enter UPI"):
    upi_address = discord.ui.TextInput(label="Payment UPI Address", style=discord.TextStyle.short, placeholder="name@upi", required=True)

    def __init__(self, post_no, t1_rate, t2_rate, client_id_num):
        super().__init__()
        self.post_no = post_no
        self.t1_rate = t1_rate
        self.t2_rate = t2_rate
        self.client_id_num = client_id_num

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        profile_name = interaction.user.display_name
        upi = self.upi_address.value.strip()
        today_str = str(datetime.date.today())

        try:
            next_row = len(sheet_posting.get_all_values()) + 1
            sheet_posting.append_row([
                profile_name, self.post_no, today_str, "Post", "", "", "No",
                f'=IF(OR(D{next_row}="", D{next_row}="Invalid"), "", "$" & IF(D{next_row}="Post", 2, IF(D{next_row}="Comment", 1, IF(D{next_row}="Mod", 5, 0))))',
                "", "", "", "No", "", "No", "No", upi
            ], value_input_option="USER_ENTERED")

            sheet_payment.append_row([
                profile_name, self.post_no, today_str, "", "", "", "", "", "", "", "", "", "",
                self.t1_rate, "", self.t2_rate if self.t2_rate else ""
            ], value_input_option="USER_ENTERED")

            ACTIVE_UNCLAIMED_TASKS.pop(self.post_no, None)
        except Exception as e:
            print(f"Sheet error on claim: {e}")

        await interaction.followup.send(f"🎉 You claimed **{self.post_no}** under `{profile_name}`.", ephemeral=True)

class WorkerTaskInteractionView(discord.ui.View):
    def __init__(self, post_no, t1_rate, t2_rate, client_id_num):
        super().__init__(timeout=None)
        self.post_no = post_no
        self.t1_rate = t1_rate
        self.t2_rate = t2_rate
        self.client_id_num = client_id_num

    @discord.ui.button(label="✋ Claim Task", style=discord.ButtonStyle.primary, custom_id="claim_task_btn")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WorkerClaimModal(self.post_no, self.t1_rate, self.t2_rate, self.client_id_num))

async def publish_task_to_workers(task_data, files_list):
    post_no = task_data["post_no"]
    t_type = task_data["t_type"]
    content_text = task_data["content_text"]
    standard_worker_pay = "2" if t_type == "Post" else "1"
    p1_details = task_data["p1_details"]

    ACTIVE_UNCLAIMED_TASKS[post_no] = task_data

    embed = discord.Embed(title=f"📌 Task Available: {post_no}", description=f"**Instructions / Content:**\n{content_text}", color=discord.Color.blue())
    embed.add_field(name="Task Type", value=f"{t_type}", inline=True)
    embed.add_field(name="Phase 1", value=f"💰 **Pay:** ${standard_worker_pay}\n⏳ **Retention:** {p1_details}", inline=True)
    embed.set_footer(text="Click 'Claim Task' to assign this post.")

    worker_channel = bot.get_channel(WORKER_TASKS_CHANNEL_ID)
    if worker_channel:
        view = WorkerTaskInteractionView(post_no, task_data["t1_client_rate"], "", "1")
        await worker_channel.send(embed=embed, files=files_list, view=view)

class ClientSubmissionModal(discord.ui.Modal, title="Submit New Task & Rates"):
    client_id_num = discord.ui.TextInput(label="Client ID Number", style=discord.TextStyle.short, placeholder="1", required=True)
    post_number = discord.ui.TextInput(label="Post Number", style=discord.TextStyle.short, placeholder="Post #11", required=True)
    task_type = discord.ui.TextInput(label="Task Type", style=discord.TextStyle.short, placeholder="Post", required=True)
    phase1_info = discord.ui.TextInput(label="Phase 1 Details", style=discord.TextStyle.short, placeholder="Rate: $6, Retention: 48 hours", required=True)
    post_content = discord.ui.TextInput(label="Content / Instructions", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        c_id_num = self.client_id_num.value.strip()
        post_no = self.post_number.value.strip()
        t_type = self.task_type.value.strip().title()
        content_text = self.post_content.value.strip()
        p1_text = self.phase1_info.value.strip()

        task_data = {
            "client_id_num": c_id_num, "post_no": post_no, "t_type": t_type,
            "content_text": content_text, "p1_details": p1_text,
            "t1_client_rate": p1_text, "standard_worker_pay": "2" if t_type == "Post" else "1"
        }
        PENDING_TASKS[interaction.user.id] = task_data
        await interaction.response.send_message(f"📝 Task **{post_no}** created! Type `!img` to attach images.", ephemeral=True)

class ClientHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Create New Task", style=discord.ButtonStyle.success, custom_id="client_create_task_btn")
    async def create_task_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClientSubmissionModal())

@bot.command()
async def setup_client_hub(ctx):
    await ctx.send(embed=discord.Embed(title="Client Task Submission Panel", color=discord.Color.green()), view=ClientHubView())

@bot.command()
async def setup_payment_proofs(ctx):
    await ctx.send(embed=discord.Embed(title="Client Payment Verification Panel", color=discord.Color.gold()), view=PaymentProofView())

@bot.event
async def on_ready():
    bot.add_view(ClientHubView())
    bot.add_view(PaymentProofView())
    repost_unclaimed_tasks.start()
    print(f"🤖 Messenger Bot online as {bot.user}!")

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN_BOT1"))