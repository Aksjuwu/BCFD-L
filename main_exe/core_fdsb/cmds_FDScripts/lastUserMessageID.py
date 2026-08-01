# cmds_FDScripts/lastUserMessageID.py
"""
Returns the ID of the user message that triggered the current script.

Usage (inline only):
    $lastUserMessageID[]
    $lastUserMessageID

Examples:
    $setVar[triggerID; $lastUserMessageID[]]
    $sendMessage[Your message ID is $lastUserMessageID]

When used inline, the command resolves to the snowflake ID of the
message that started this script's execution (``ctx.message.id``).
This is always the original author's message — the one that contained
the ``$`` command being processed — and does not change during the
script's lifetime.

This is similar to the built-in ``$messageID`` token but is available
explicitly as a named command for clarity in scripts.

This command does not provide an ``execute()`` function and therefore
cannot be used as a standalone statement — it must be placed inside
another command's argument brackets or used as a bare inline token.
"""
import discord
from FDScript import ExecutionContext


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    """Resolve the triggering user message ID.

    Parameters
    ----------
    args : list[str]
        Command arguments. This command currently accepts no arguments;
        if any are provided they are silently ignored.
    ctx : ExecutionContext
        The current execution context carrying the bot, message, and
        runtime state. The relevant attribute is ``ctx.message``.

    Returns
    -------
    str
        The snowflake ID of ``ctx.message`` (the user message that
        triggered this script execution) as a string.
    """
    # ctx.message is the original user message that triggered this
    # script execution. Its ID is guaranteed to be available.
    return str(ctx.message.id)
