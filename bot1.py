from keep_alive import keep_alive
import discord
from discord.ext import commands
import gspread
from google.oauth2.service_account import Credentials
import datetime
import random
import os
import json

# 1. Automatically write credentials.json on startup to prevent parsing errors
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

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

cred_data = {
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

with open("credentials.json", "w") as f:
    json.dump(cred_data, f)

try:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
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
CLIENT_USER_ID = 1518961433281433611                # Your Client ID

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
            await interaction.response.send_message("⚠️ There are no open questions right now.", ephemeral=True)
            return
        q_info = OPEN_QUESTIONS.get(selected_q_id)
        await interaction.response.send_modal(ClientAnswerModal(selected_q_id, q_info["post_no"], q_info["question"]))

class ClientAnswerDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(QuestionSelectDropdown())

class ClientAnswerModal(discord.ui.Modal):
    def __init__(self, q_id, post_no, orig_q):
        super().__init__(title=f"Answer {q_id} ({post_no})")
        self.q_id = q_id
        self.post_no = post_no
        self.orig_q = orig_q
        self.answer_text = discord.ui.TextInput(label="Your Answer", style=discord.TextStyle.paragraph, placeholder="Type answer or notes here...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ans = self.answer_text.value.strip()
        files_to_send = [await att.to_file() for att in interaction.message.attachments] if interaction.message and interaction.message.attachments else []

        worker_channel = bot.get_channel(WORKER_TASKS_CHANNEL_ID)
        if worker_channel:
            embed = discord.Embed(title=f"💬 Client Answer for {self.post_no} ({self.q_id})", description=f"**Original Question:**\n*{self.orig_q}*\n\n**Client Answer:**\n{ans}", color=discord.Color.green())
            await worker_channel.send(embed=embed, files=files_to_send)

        OPEN_QUESTIONS.pop(self.q_id, None)
        await interaction.followup.send(f"✅ Answer for **{self.q_id}** sent to workers channel!", ephemeral=True)

class ClientAnswerTriggerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💬 Answer Question", style=discord.ButtonStyle.success, custom_id="client_answer_select_btn")
    async def answer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not OPEN_QUESTIONS:
            await interaction.response.send_message("⚠️ No open questions waiting for answers!", ephemeral=True)
            return
        await interaction.response.send_message("Select the question you are replying to:", view=ClientAnswerDropdownView(), ephemeral=True)

class AskClientView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❓ Ask Client", style=discord.ButtonStyle.secondary, custom_id="ask_client_main_btn")
    async def ask_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AskClientModal())

class TaskImagePromptView(discord.ui.View):
    def __init__(self, task_data):
        super().__init__(timeout=180.0)
        self.task_data = task_data

    @discord.ui.button(label="🚀 No Image, Post Now", style=discord.ButtonStyle.secondary, custom_id="no_image_btn")
    async def no_image_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await publish_task_to_workers(self.task_data, files_list=[])
        await interaction.edit_original_response(content=f"✅ **Task {self.task_data['post_no']} published successfully!**", view=None)

    @discord.ui.button(label="📷 Yes, Attach Images via Command", style=discord.ButtonStyle.success, custom_id="yes_image_btn")
    async def yes_image_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        PENDING_TASKS[interaction.user.id] = self.task_data
        await interaction.response.edit_message(content=f"📸 Type `!img` and attach your screenshot(s) right now to publish **Task {self.task_data['post_no']}**.", view=None)

@bot.command()
@commands.has_permissions(administrator=True)
async def img(ctx):
    if ctx.author.id not in PENDING_TASKS:
        await ctx.send("⚠️ No pending task waiting for images.", delete_after=10)
        return
    if not ctx.message.attachments:
        await ctx.send("⚠️ Please attach image(s) along with your `!img` command!", delete_after=10)
        return

    task_data = PENDING_TASKS.pop(ctx.author.id)
    files_list = [await att.to_file() for att in ctx.message.attachments]
    await publish_task_to_workers(task_data, files_list)
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await ctx.send(f"✅ **Task {task_data['post_no']} published with images!**", delete_after=5)

async def publish_task_to_workers(task_data, files_list):
    post_no = task_data["post_no"]
    t_type = task_data["t_type"]
    content_text = task_data["content_text"]
    standard_worker_pay = task_data["standard_worker_pay"]
    p1_details = task_data["p1_details"]
    t2_type = task_data["t2_type"]
    p2_details = task_data["p2_details"]

    embed = discord.Embed(title=f"📌 Task Available: {post_no}", description=f"**Instructions / Content:**\n{content_text}", color=discord.Color.blue())
    embed.add_field(name="Task Type", value=f"{t_type}", inline=True)
    embed.add_field(name="Phase 1", value=f"💰 **Pay:** ${standard_worker_pay}\n⏳ **Retention:** {p1_details}", inline=True)
    if t2_type and p2_details:
        embed.add_field(name="Phase 2", value=f"💰 **Pay:** ${standard_worker_pay}\n⏳ **Retention:** {p2_details}", inline=True)
    embed.set_footer(text="Click 'Claim Task' to assign this post or 'Ask Client' for questions.")

    worker_channel = bot.get_channel(WORKER_TASKS_CHANNEL_ID)
    if worker_channel:
        view = WorkerTaskInteractionView(post_no, task_data["t1_client_rate"], task_data["t2_client_rate"])
        await worker_channel.send(embed=embed, files=files_list, view=view)

class WorkerClaimModal(discord.ui.Modal, title="Claim Task & Enter UPI"):
    upi_address = discord.ui.TextInput(label="Payment UPI Address", style=discord.TextStyle.short, placeholder="e.g., name@upi", required=True)

    def __init__(self, post_no, t1_rate, t2_rate, button_view):
        super().__init__()
        self.post_no = post_no
        self.t1_rate = t1_rate
        self.t2_rate = t2_rate
        self.button_view = button_view

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
        except Exception as e:
            print(f"Sheet error on claim: {e}")

        self.button_view.children[0].label = f"🔒 Claimed by @{profile_name}"
        self.button_view.children[0].style = discord.ButtonStyle.secondary
        self.button_view.children[0].disabled = True
        try:
            await interaction.message.edit(view=self.button_view)
        except Exception:
            pass
        await interaction.followup.send(f"🎉 You claimed **{self.post_no}** under profile: `{profile_name}`.", ephemeral=True)

class WorkerTaskInteractionView(discord.ui.View):
    def __init__(self, post_no, t1_rate, t2_rate):
        super().__init__(timeout=None)
        self.post_no = post_no
        self.t1_rate = t1_rate
        self.t2_rate = t2_rate

    @discord.ui.button(label="✋ Claim Task", style=discord.ButtonStyle.primary, custom_id="claim_task_btn")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WorkerClaimModal(self.post_no, self.t1_rate, self.t2_rate, self))

    @discord.ui.button(label="❓ Ask Client", style=discord.ButtonStyle.secondary, custom_id="ask_client_btn")
    async def ask_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AskClientModal())

class ClientPaymentModal(discord.ui.Modal, title="Confirm Task Payment"):
    post_number = discord.ui.TextInput(label="Post Number", style=discord.TextStyle.short, placeholder="e.g., Post #11", required=True)
    worker_name = discord.ui.TextInput(label="Worker Name", style=discord.TextStyle.short, placeholder="e.g., FistMyBump", required=True)
    task_phase = discord.ui.TextInput(label="Task Phase (Task 1 or Task 2)", style=discord.TextStyle.short, placeholder="Task 1", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        post_no = self.post_number.value.strip()
        w_name = self.worker_name.value.strip()
        phase = self.task_phase.value.strip().lower()

        try:
            rows_posting = sheet_posting.get_all_values()
            target_posting_row = None
            for idx, row in enumerate(rows_posting[1:], start=2):
                if len(row) >= 2 and row[1] == post_no and row[0].lower() == w_name.lower():
                    target_posting_row = idx
                    break
            if target_posting_row:
                sheet_posting.update_cell(target_posting_row, 14 if "1" in phase else 15, "Yes")

            rows_payment = sheet_payment.get_all_values()
            target_payment_row = None
            for idx, row in enumerate(rows_payment[1:], start=2):
                if len(row) >= 2 and row[1] == post_no and row[0].lower() == w_name.lower():
                    target_payment_row = idx
                    break
            if target_payment_row:
                sheet_payment.update_cell(target_payment_row, 14 if "1" in phase else 17, "Yes")

            embed = discord.Embed(title=f"💳 Payment Verified: {post_no}", description=f"Paid **{phase.title()}** for **{w_name}**.", color=discord.Color.green())
            if (p_chan := bot.get_channel(PRIVATE_PAYMENTS_CHANNEL_ID)):
                await p_chan.send(embed=embed)
            await interaction.followup.send("✅ Payment logged across sheets!", ephemeral=True)
        except Exception as e:
            print(f"Error: {e}")

class PaymentProofView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 Confirm Payment Sent", style=discord.ButtonStyle.primary, custom_id="client_payment_sent_btn")
    async def payment_sent_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClientPaymentModal())

class ClientSubmissionModal(discord.ui.Modal, title="Submit New Task & Rates"):
    post_number = discord.ui.TextInput(label="Post Number", style=discord.TextStyle.short, placeholder="Post #11", required=True)
    task_type = discord.ui.TextInput(label="Task Type", style=discord.TextStyle.short, placeholder="Post", required=True)
    phase1_info = discord.ui.TextInput(label="Phase 1", style=discord.TextStyle.short, placeholder="Rate: $6, Retention: 48 hours", required=True)
    phase2_info = discord.ui.TextInput(label="Phase 2 (Optional)", style=discord.TextStyle.short, required=False)
    post_content = discord.ui.TextInput(label="Content / Instructions", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        post_no = self.post_number.value.strip()
        t_type = self.task_type.value.strip().title()
        content_text = self.post_content.value.strip()
        standard_worker_pay = "2" if t_type == "Post" else "1"

        p1_text = self.phase1_info.value.strip()
        p2_text = self.phase2_info.value.strip() if self.phase2_info.value else ""

        task_data = {
            "post_no": post_no,
            "t_type": t_type,
            "content_text": content_text,
            "standard_worker_pay": standard_worker_pay,
            "p1_details": p1_text,
            "t2_type": "Post" if p2_text else "",
            "p2_details": p2_text,
            "t1_client_rate": p1_text,
            "t2_client_rate": p2_text
        }
        await interaction.response.send_message(f"📝 Task **{post_no}** created! Attach images?", view=TaskImagePromptView(task_data), ephemeral=True)

class ClientHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Create New Task", style=discord.ButtonStyle.success, custom_id="client_create_task_btn")
    async def create_task_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ClientSubmissionModal())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_client_hub(ctx):
    await ctx.send(embed=discord.Embed(title="Client Task Submission Panel", color=discord.Color.green()), view=ClientHubView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_client_answers(ctx):
    await ctx.send(embed=discord.Embed(title="💬 Need Clarification?", color=discord.Color.purple()), view=AskClientView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_payment_proofs(ctx):
    await ctx.send(embed=discord.Embed(title="Payment VerificationPanel", color=discord.Color.gold()), view=PaymentProofView())

@bot.event
async def on_ready():
    bot.add_view(ClientHubView())
    bot.add_view(AskClientView())
    bot.add_view(PaymentProofView())
    bot.add_view(ClientAnswerTriggerView())
    print(f"🤖 Messenger Bot online as {bot.user}!")

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))