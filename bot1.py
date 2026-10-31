import datetime
import json
import os
import random
import traceback
import discord
from discord.ext import commands
import gspread
from keep_alive import keep_alive
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ["googleapis.com", "googleapis.com"]

try:
    raw_env = os.getenv("G_PRIVATE_KEY")
    if not raw_env:
        raise ValueError("❌ Error: G_PRIVATE_KEY environment variable is missing!")
    cred_dict = json.loads(raw_env)
    if "private_key" in cred_dict:
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    with open("credentials.json", "w") as f:
        json.dump(cred_dict, f)
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scopes=SCOPES
    )
    client_gs = gspread.authorize(creds)
    sheet_posting = client_gs.open("Posting Tasks").sheet1
    sheet_payment = client_gs.open("Payment Tracking").sheet1
    print("✅ Messenger Bot connected to Google Sheets successfully!")
except Exception as e:
    print("❌ Google Sheets Connection Error:")
    traceback.print_exc()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

WORKER_TASKS_CHANNEL_ID = 1564649806482120805
CLIENT_ANSWERS_CHANNEL_ID = 1565406309950685287
PRIVATE_PAYMENTS_CHANNEL_ID = 1565708632278958100
CLIENT_USER_ID = 1518961433281433611

PENDING_TASKS = {}
OPEN_QUESTIONS = {}


class AskClientModal(discord.ui.Modal, title="Ask Client a Question"):
    post_number = discord.ui.TextInput(
        label="Post Number",
        style=discord.TextStyle.short,
        placeholder="e.g., Post #11",
        required=True,
    )
    question_text = discord.ui.TextInput(
        label="Your Question",
        style=discord.TextStyle.paragraph,
        placeholder="Type your question anonymously...",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        post_no = self.post_number.value.strip()
        q_text = self.question_text.value.strip()
        q_id = f"Q-{random.randint(100, 999)}"
        OPEN_QUESTIONS[q_id] = {"post_no": post_no, "question": q_text}
        client_channel = bot.get_channel(CLIENT_ANSWERS_CHANNEL_ID)
        if client_channel:
            embed = discord.Embed(
                title=f"❓ Anonymous Question ({q_id}) | {post_no}",
                description=f"Question:\n{q_text}",
                color=discord.Color.purple(),
            )
            embed.set_footer(
                text="Client: Click 'Answer Question' below to respond!"
            )
            await client_channel.send(
                content=f"🔔 <@{CLIENT_USER_ID}> New Question Received ({q_id})",
                embed=embed,
                view=ClientAnswerTriggerView(),
            )
        await interaction.followup.send(
            f"✅ Question {q_id} posted anonymously!", ephemeral=True
        )


class QuestionSelectDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        for q_id, data in list(OPEN_QUESTIONS.items())[-25:]:
            options.append(
                discord.SelectOption(
                    label=f"{q_id} ({data['post_no']})",
                    description=data["question"][:50],
                    value=q_id,
                )
            )
        if not options:
            options.append(
                discord.SelectOption(label="No open questions", value="none")
            )
        super().__init__(
            placeholder="Select the question you want to answer...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_q_id = self.values[0]
        if selected_q_id == "none" or selected_q_id not in OPEN_QUESTIONS:
            await interaction.response.send_message(
                "⚠️ There are no open questions right now.", ephemeral=True
            )
            return
        q_info = OPEN_QUESTIONS.get(selected_q_id)
        await interaction.response.send_modal(
            ClientAnswerModal(
                selected_q_id, q_info["post_no"], q_info["question"]
            )
        )


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
        self.answer_text = discord.ui.TextInput(
            label="Your Answer",
            style=discord.TextStyle.paragraph,
            placeholder="Type answer or notes here...",
            required=True,
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ans = self.answer_text.value.strip()
        files_to_send = (
            [
                await att.to_file()
                for att in interaction.message.attachments
            ]
            if interaction.message and interaction.message.attachments
            else []
        )
        worker_channel = bot.get_channel(WORKER_TASKS_CHANNEL_ID)
        if worker_channel:
            embed = discord.Embed(
                title=f"💬 Client Answer for {self.post_no} ({self.q_id})",
                description=f"Original Question:\n*{self.orig_q}*\n\nClient Answer:\n{ans}",
                color=discord.Color.green(),
            )
            await worker_channel.send(embed=embed, files=files_to_send)
        OPEN_QUESTIONS.pop(self.q_id, None)
        await interaction.followup.send(
            f"✅ Answer for {self.q_id} sent to workers channel!", ephemeral=True
        )


class ClientAnswerTriggerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="💬 Answer Question",
        style=discord.ButtonStyle.success,
        custom_id="client_answer_select_btn",
    )
    async def answer_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if not OPEN_QUESTIONS:
            await interaction.response.send_message(
                "⚠️ No open questions waiting for answers!", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Select the question you are replying to:",
            view=ClientAnswerDropdownView(),
            ephemeral=True,
        )


class AskClientView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="❓ Ask Client",
        style=discord.ButtonStyle.secondary,
        custom_id="ask_client_main_btn",
    )
    async def ask_btn(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(AskClientModal())


class TaskImagePromptView(discord.ui.View):
    def __init__(self, task_data):
        super().__init__(timeout=180.0)
        self.task_data = task_data

    @discord.ui.button(
        label="🚀 No Image, Post Now",
        style=discord.ButtonStyle.secondary,
        custom_id="no_image_btn",
    )
    async def no_image_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        await publish_task_to_workers(self.task_data, files_list=[])
        await interaction.edit_original_response(
            content=f"✅ Task {self.task_data['post_no']} published successfully!",
            view=None,
        )

    @discord.ui.button(
        label="📷 Yes, Attach Images via Command",
        style=discord.ButtonStyle.success,
        custom_id="yes_image_btn",
    )
    async def yes_image_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        PENDING_TASKS[interaction.user.id] = self.task_data
        await interaction.response.edit_message(
            content=f"📸 Type !img and attach your screenshot(s) right now to publish Task {self.task_data['post_no']}.",
            view=None,
        )


@bot.command()
@commands.has_permissions(administrator=True)
async def img(ctx):
    if ctx.author.id not in PENDING_TASKS:
        await ctx.send("⚠️ No pending task waiting for images.", delete_after=10)
        return
    if not ctx.message.attachments:
        await ctx.send(
            "⚠️ Please attach image(s) along with your !img command!",
            delete_after=10,
        )
        return
    task_data = PENDING_TASKS.pop(ctx.author.id)
    files_list = [await att.to_file() for att in ctx.message.attachments]
    await publish_task_to_workers(task_data, files_list)
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await ctx.send(
        f"✅ Task {task_data['post_no']} published with images!", delete_after=5
    )


async def publish_task_to_workers(task_data, files_list):
    post_no =