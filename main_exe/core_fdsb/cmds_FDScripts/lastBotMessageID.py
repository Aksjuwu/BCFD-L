# cmds_FDScripts/lastBotMessageID.py
"""
Returns the ID of the last message sent by the bot during the
current script execution.

Usage (inline only):
    $lastBotMessageID[]
    $lastBotMessageID

Examples:
    $setVar[lastMessageID; $lastBotMessageID[]]
    $editIn[10s; The last message ID was $lastBotMessageID]

When used inline, the command resolves to the snowflake ID of the
most recent message the bot sent. This is tracked via the context's
``last_bot_message`` attribute, which is updated automatically by
commands such as ``$sendMessage``, ``$reply``, and ``$sendEmbedMessage``.

If no message has been sent yet, an empty string is returned so that
your script can handle this gracefully.

This command does not provide an ``execute()`` function and therefore
cannot be used as a standalone statement — it must be placed inside
another command's argument brackets or used as a bare inline token.
"""
import discord
from FDScript import ExecutionContext


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    """Resolve the last bot message ID.

    Parameters
    ----------
    args : list[str]
        Command arguments. This command currently accepts no arguments;
        if any are provided they are silently ignored.
    ctx : ExecutionContext
        The current execution context carrying the bot, message, and
        runtime state such as ``last_bot_message``.

    Returns
    -------
    str
        The snowflake ID of ``ctx.last_bot_message`` as a string, or
        an empty string if ``last_bot_message`` is ``None`` (i.e. the
        bot has not sent any message yet in this execution flow).
    """
    # Retrieve the last bot message from the execution context.
    # This is set automatically by most output-producing commands
    # (e.g. sendMessage, reply, sendEmbedMessage).
    last_msg = ctx.last_bot_message

    # Guard against the case where no message has been sent yet.
    if last_msg is None:
        return ""

    # Return the snowflake ID of the last bot message as a string.
    return str(last_msg.id)
