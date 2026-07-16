# cmds_FDScripts/editButton.py
import discord
from FDScript import ExecutionContext, Command
from FDCore import BUTTON_STYLES, FDSyntaxError, FDLogicError, _send_error


def _find_button(view: discord.ui.View, target_id: str):
    for item in view.children:
        if isinstance(item, discord.ui.Button) and (item.custom_id == target_id or item.url == target_id):
            return item
    return None


def _apply(btn: discord.ui.Button, label: str, style: discord.ButtonStyle, disabled: bool, emoji: str | None):
    btn.label = label or None
    btn.disabled = disabled
    btn.emoji = emoji
    if btn.style != discord.ButtonStyle.link:
        btn.style = style


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) < 3:
        await _send_error(ch, FDSyntaxError(
            "`$editButton` requires at least 3 arguments: "
            "`$editButton[ID/URL; label; style; (disabled; emoji; messageID)]`"
        ))
        return

    target_id = args[0].strip()
    label = args[1]
    style_str = args[2].strip().lower()
    disabled = len(args) > 3 and args[3].strip().lower() == "yes"
    emoji = args[4].strip() if len(args) > 4 and args[4].strip() else None
    message_id_arg = args[5].strip() if len(args) > 5 and args[5].strip() else None

    if not target_id:
        await _send_error(ch, FDLogicError("`$editButton` — the ID/URL argument (1st arg) cannot be empty"))
        return

    if style_str not in BUTTON_STYLES:
        await _send_error(ch, FDLogicError(
            f"`$editButton` — unknown style `{args[2]}`. "
            f"Valid styles: primary, secondary, success, danger, link"
        ))
        return

    style = BUTTON_STYLES[style_str]

    if message_id_arg is not None:
        if not message_id_arg.isdigit():
            await _send_error(ch, FDLogicError(
                "`$editButton` — the message ID (6th arg) must be a valid snowflake (numbers only)"
            ))
            return

        try:
            target_message = await ctx.message.channel.fetch_message(int(message_id_arg))
        except discord.NotFound:
            await _send_error(ch, FDLogicError(
                f"`$editButton` — no message found with ID `{message_id_arg}` in this channel"
            ))
            return
        except discord.HTTPException as e:
            await _send_error(ch, FDLogicError(
                f"`$editButton` — failed to fetch message `{message_id_arg}`: `{e}`"
            ))
            return

        if ctx.bot.user is None or target_message.author.id != ctx.bot.user.id:
            await _send_error(ch, FDLogicError(
                "`$editButton` — the message ID (6th arg) must point to a message sent by this bot"
            ))
            return

        view = discord.ui.View.from_message(target_message, timeout=None)
        btn = _find_button(view, target_id)
        if btn is None:
            await _send_error(ch, FDLogicError(
                f"`$editButton` — no button with ID `{target_id}` found on that message"
            ))
            return

        _apply(btn, label, style, disabled, emoji)
        try:
            await target_message.edit(view=view)
        except discord.HTTPException as e:
            await _send_error(ch, FDLogicError(
                f"`$editButton` — failed to edit message `{message_id_arg}`: `{e}`"
            ))
            return

        ctx.log_event(f"$editButton → edited [{target_id}] on message {message_id_arg}")
        return

    if ctx.view is not None:
        btn = _find_button(ctx.view, target_id)
        if btn is not None:
            _apply(btn, label, style, disabled, emoji)
            ctx.log_event(f"$editButton → edited [{target_id}] in pending view")
            return
        
    if ctx.interaction is not None and ctx.interaction.message is not None:
        source_message = ctx.interaction.message
        view = discord.ui.View.from_message(source_message, timeout=None)
        btn = _find_button(view, target_id)
        if btn is None:
            await _send_error(ch, FDLogicError(f"`$editButton` — no button with ID `{target_id}` found"))
            return

        _apply(btn, label, style, disabled, emoji)
        try:
            await source_message.edit(view=view)
        except discord.HTTPException as e:
            await _send_error(ch, FDLogicError(f"`$editButton` — failed to edit the source message: `{e}`"))
            return

        ctx.log_event(f"$editButton → edited [{target_id}] on interaction source message")
        return

    await _send_error(ch, FDLogicError(
        f"`$editButton` — no button with ID `{target_id}` found "
        f"(nothing queued yet, and no messageID / interaction context to look in)"
    ))