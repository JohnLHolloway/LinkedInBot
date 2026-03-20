import io
import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import MODES, DEFAULT_MODE
from image_gen import generate_image, edit_image, generate_text
from prompts import build_image_prompt, build_text_prompt, sanitize_prompt, resolve_mode
from rate_limit import RateLimiter

log = logging.getLogger(__name__)
_limiter = RateLimiter()


def _image_url_from_message(msg: discord.Message) -> str | None:
    for att in msg.attachments:
        if att.content_type and att.content_type.startswith("image/"):
            return att.url
    for embed in msg.embeds:
        if embed.image and embed.image.url:
            return embed.image.url
        if embed.thumbnail and embed.thumbnail.url:
            return embed.thumbnail.url
    return None


class GenerateModal(discord.ui.Modal, title="LinkedIn-ify"):
    prompt_input = discord.ui.TextInput(
        label="What do you want to LinkedIn-ify?",
        style=discord.TextStyle.paragraph,
        placeholder="Paste text or describe an image to generate...",
        required=True,
        max_length=500,
    )

    def __init__(self, mode_key: str):
        super().__init__()
        self.mode_key = mode_key

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        user_text = self.prompt_input.value
        mode = resolve_mode(self.mode_key)

        try:
            if mode["type"] == "text":
                system, user = build_text_prompt(user_text, mode)
                result = await generate_text(system, user)
                await interaction.followup.send(result)
            else:
                system, user = build_image_prompt(user_text, mode)
                img_bytes = await generate_image(system, user)
                if len(img_bytes) > 25 * 1024 * 1024:
                    await interaction.followup.send("Generated image too large to upload.")
                    return
                await interaction.followup.send(
                    file=discord.File(io.BytesIO(img_bytes), filename="linkedin.png")
                )
        except Exception:
            log.exception("Generation failed")
            await interaction.followup.send("Something went wrong — try again later.")


class ModeSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for key, mode in MODES.items():
            options.append(
                discord.SelectOption(
                    label=mode["label"],
                    value=key,
                    description=mode["description"][:100],
                    default=(key == DEFAULT_MODE),
                )
            )
        super().__init__(placeholder="Pick a mode", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(GenerateModal(self.values[0]))


class ModeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ModeSelect())


class GenerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="generate", description="Convert text or images into LinkedIn speak")
    async def generate(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "Pick a mode, then enter your prompt:",
            view=ModeView(),
            ephemeral=True,
        )

    @app_commands.command(name="help", description="Show available modes and how to use the bot")
    async def help_cmd(self, interaction: discord.Interaction) -> None:
        lines = ["**LinkedIn Bot** — Turn anything into LinkedIn speak\n"]
        lines.append("**Mention me** with text → corporate jargon")
        lines.append("**Mention me** on an image → everyone gets suited up")
        lines.append("**/generate** → pick a specific mode\n")
        lines.append("**Available modes:**")
        for key, mode in MODES.items():
            lines.append(f"• **{mode['label']}** — {mode['description']}")
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        log.info("MSG from %s: %r (mentions: %s, bot_user: %s)",
                 message.author, message.content[:80],
                 [m.id for m in message.mentions],
                 self.bot.user.id if self.bot.user else None)
        if not self.bot.user:
            return
        # Check for direct @user mention OR @role mention for the bot's role
        mentioned_user = self.bot.user.id in [m.id for m in message.mentions]
        mentioned_role = any(r.is_bot_managed() for r in message.role_mentions)
        if not mentioned_user and not mentioned_role:
            return
        if not _limiter.check(message.author.id):
            return

        log.info("Mention from %s: %s", message.author, message.content[:80])

        # Check for image in the message or the replied-to message
        image_url = _image_url_from_message(message)
        ref_message = None
        if not image_url and message.reference and message.reference.message_id:
            try:
                ref_message = await message.channel.fetch_message(message.reference.message_id)
                image_url = _image_url_from_message(ref_message)
            except discord.NotFound:
                pass

        # If replying to another message, use that message's text as input
        user_text = sanitize_prompt(message.content)
        if ref_message and ref_message.content:
            ref_text = sanitize_prompt(ref_message.content)
            if ref_text:
                user_text = ref_text

        async with message.channel.typing():
            try:
                if image_url:
                    # Image mode — put them in suits
                    mode = resolve_mode("suits")
                    system, user = build_image_prompt(user_text or "make it corporate", mode)
                    img_bytes = await edit_image(system, user, image_url)
                    if len(img_bytes) > 25 * 1024 * 1024:
                        await message.reply("Generated image too large to upload.")
                        return
                    await message.reply(
                        file=discord.File(io.BytesIO(img_bytes), filename="linkedin.png")
                    )
                else:
                    # Text mode — corporate jargon
                    if not user_text:
                        await message.reply("Give me some text to LinkedIn-ify!")
                        return
                    mode = resolve_mode(DEFAULT_MODE)
                    system, user = build_text_prompt(user_text, mode)
                    result = await generate_text(system, user)
                    await message.reply(result)
            except Exception:
                log.exception("Generation failed")
                await message.reply("Something went wrong — try again later.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenerationCog(bot))
