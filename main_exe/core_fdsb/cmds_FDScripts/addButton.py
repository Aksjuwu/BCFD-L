# cmds_FDScripts/addButton.py
import discord

from FDScript import ExecutionContext, Command
from FDCore import BUTTON_STYLES, FDSyntaxError, FDLogicError, _send_error

MAX_BUTTONS_PER_MESSAGE = 25

def _build_button(is_link: bool, url_or_id: str, label: str, style: discord.ButtonStyle,
                   disabled: bool, emoji: str | None) -> discord.ui.Button:
    if is_link:
        return discord.ui.Button(label=label, url=url_or_id, disabled=disabled, emoji=emoji)
    return discord.ui.Button(custom_id=url_or_id, label=label, style=style, disabled=disabled, emoji=emoji)

def _has_duplicate_id(view: discord.ui.View, custom_id: str) -> bool:
    return any(
        isinstance(item, discord.ui.Button) and item.custom_id == custom_id
        for item in view.children
    )

async def _edit_target_with_button(ch: discord.abc.Messageable, target_message: discord.Message,
                                    btn: discord.ui.Button, is_link: bool, url_or_id: str) -> bool:
    """Fetches the current view on target_message, appends btn, edits it in place.
    Returns True on success, False if an error was already sent to the channel."""
    existing_view = discord.ui.View.from_message(target_message, timeout=None)

    if len(existing_view.children) >= MAX_BUTTONS_PER_MESSAGE:
        await _send_error(ch, FDLogicError(
            f"`$addButton` — that message already has {MAX_BUTTONS_PER_MESSAGE} buttons"
        ))
        return False

    if not is_link and _has_duplicate_id(existing_view, url_or_id):
        await _send_error(ch, FDLogicError(
            f"`$addButton` — duplicate custom_id `{url_or_id}` on that message"
        ))
        return False

    existing_view.add_item(btn)
    try:
        await target_message.edit(view=existing_view)
    except discord.HTTPException as e:
        await _send_error(ch, FDLogicError(
            f"`$addButton` — failed to edit message `{target_message.id}`: `{e}`"
        ))
        return False

    return True

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) < 4:
        await _send_error(ch, FDSyntaxError(
            "`$addButton` requires at least 4 arguments: "
            "`$addButton[isLink; ID/URL; label; style; (disabled; emoji; messageID)]`"
        ))
        return

    is_link = args[0].strip().lower() == "yes"
    url_or_id = args[1].strip()
    label = args[2]
    style_str = args[3].strip().lower()
    disabled = len(args) > 4 and args[4].strip().lower() == "yes"
    emoji = args[5].strip() if len(args) > 5 and args[5].strip() else None
    message_id_arg = args[6].strip() if len(args) > 6 and args[6].strip() else None

    if style_str not in BUTTON_STYLES:
        await _send_error(ch, FDLogicError(
            f"`$addButton` — unknown style `{args[3]}`. "
            f"Valid styles: primary, secondary, success, danger, link"
        ))
        return

    if not url_or_id:
        await _send_error(ch, FDLogicError(
            "`$addButton` — the ID/URL argument (2nd arg) cannot be empty"
        ))
        return

    if is_link and not (url_or_id.startswith("http://") or url_or_id.startswith("https://")):
        await _send_error(ch, FDLogicError(
            "`$addButton` — link buttons need a URL starting with http:// or https://"
        ))
        return

    style = BUTTON_STYLES[style_str]
    btn = _build_button(is_link, url_or_id, label, style, disabled, emoji)

    if message_id_arg is not None:
        if not message_id_arg.isdigit():
            await _send_error(ch, FDLogicError(
                "`$addButton` — the message ID (7th arg) must be a valid snowflake (numbers only)"
            ))
            return

        try:
            target_message = await ctx.message.channel.fetch_message(int(message_id_arg))
        except discord.NotFound:
            await _send_error(ch, FDLogicError(
                f"`$addButton` — no message found with ID `{message_id_arg}` in this channel"
            ))
            return
        except discord.HTTPException as e:
            await _send_error(ch, FDLogicError(
                f"`$addButton` — failed to fetch message `{message_id_arg}`: `{e}`"
            ))
            return

        if ctx.bot.user is None or target_message.author.id != ctx.bot.user.id:
            await _send_error(ch, FDLogicError(
                "`$addButton` — the message ID (7th arg) must point to a message sent by this bot"
            ))
            return

        ok = await _edit_target_with_button(ch, target_message, btn, is_link, url_or_id)
        if not ok:
            return

        ctx.log_event(f"$addButton → attached [{label or url_or_id}] to message {message_id_arg}")
        return

    if ctx.view is None:
        ctx.view = discord.ui.View(timeout=None)

    if len(ctx.view.children) >= MAX_BUTTONS_PER_MESSAGE:
        await _send_error(ch, FDLogicError(
            f"`$addButton` — a message can have at most {MAX_BUTTONS_PER_MESSAGE} buttons"
        ))
        return

    if not is_link and _has_duplicate_id(ctx.view, url_or_id):
        await _send_error(ch, FDLogicError(
            f"`$addButton` — duplicate custom_id `{url_or_id}` in the same message"
        ))
        return

    ctx.view.add_item(btn)
    ctx.log_event(f"$addButton → queued [{label or url_or_id}] style={style_str} id={url_or_id}")