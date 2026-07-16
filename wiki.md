# FDScript Wiki

> **FDScript** is a lightweight scripting language for Discord bots — built into **FDSB**.  
> Scripts run line‑by‑line; commands start with `$` and take arguments inside `[]` separated by `;`.

---

## 📑 Table of Contents

<details>
<summary>Click to expand</summary>

1. [Getting Started](#-getting-started)
   - [Syntax Rules](#syntax-rules)
   - [Plain Text Lines](#plain-text-lines)
   - [Inline Comments](#inline-comments)
   - [Variable Resolution Order](#variable-resolution-order)
   - [Error System](#error-system)
2. [Variables & Data](#-variables--data)
   - [`$var` – Temporary Variables](#var--temporary-variables)
   - [`$setVar` / `$getVar` – Persistent Variables](#setvar--getvar--persistent-variables)
   - [Built‑in Variables](#built-in-variables)
3. [Messaging](#-messaging)
   - [`$sendMessage`](#sendmessage)
   - [`$reply`](#reply)
   - [`$dm`](#dm)
   - [`$image`](#image)
4. [Embed Builder](#-embed-builder)
   - [Inline Embed Commands](#inline-embed-commands)
   - [`$sendEmbedMessage`](#sendembedmessage)
5. [Buttons & Reactions](#-buttons--reactions)
   - [`$addButton`](#addbutton)
   - [`$editButton`](#editbutton)
   - [`$removeButtons`](#removebuttons)
   - [`$removeComponent`](#removecomponent)
   - [`$addBotReactions`](#addbotreactions)
   - [`$addUserReactions`](#adduserreactions)
6. [Moderation](#-moderation)
   - [`$ban` / `$unban`](#ban--unban)
   - [`$kick`](#kick)
   - [`$timeout` / `$untimeout`](#timeout--untimeout)
   - [`$slowmode`](#slowmode)
   - [`$deletecommand`](#deletecommand)
   - [`$clear`](#clear)
   - [`$createRole` / `$cloneRole` / `$deleteRole` / `$roleAssign`](#role-management)
   - [`$changeUsername`](#changeusername)
7. [Access Control](#-access-control)
   - [`$onlyAdmin`](#onlyadmin)
   - [`$onlyIf`](#onlyif)
   - [`$strictArgs`](#strictargs)
   - [`$cooldown`](#cooldown)
8. [Math & Numbers](#-math--numbers)
   - [`$math` (advanced)](#math-advanced)
   - [`$sum` `$sub` `$mul` `$div` `$mod`](#basic-math-commands)
   - [`$round`](#round)
   - [`$isNumber`](#isnumber)
   - [`$charCount`](#charcount)
9. [Randomness](#-randomness)
   - [`$randomint`](#randomint)
   - [`$randomstr`](#randomstr)
   - [`$randomUserID`](#randomuserid)
   - [`$randomRoleID` / `$randomRoleMention`](#randomroleid--randomrolemention)
10. [String Utilities](#-string-utilities)
    - [`$replaceText`](#replacetext)
    - [`$splitIn` / `$splitOut`](#splitin--splitout)
    - [`$switch`](#switch)
11. [Flow Control](#-flow-control)
    - [`$if` / `$elif` / `$else` / `$endif`](#if--elif--else--endif)
    - [`$and` / `$or` – Compound Conditions](#and--or--compound-conditions)
    - [`$while` / `$endwhile`](#while--endwhile)
    - [`$for` / `$endfor`](#for--endfor)
    - [`$break`](#break)
    - [`$return` (return variables)](#return)
12. [Timing & Delays](#-timing--delays)
    - [`$wait`](#wait)
    - [`$replyIn`](#replyin)
    - [`$editIn`](#editin)
    - [`$addTimestamp`](#addtimestamp)
13. [Bot Info & Utilities](#-bot-info--utilities)
    - [`$ping`](#ping)
    - [`$uptime`](#uptime)
    - [`$getBotInvent`](#getbotinvent)
    - [`$clientTyping`](#clienttyping)
    - [`$log`](#log)
14. [Return Commands (Data Fetching)](#-return-commands-data-fetching)
    - [`$returnGuildUsersID`](#returnguildusersid)
    - [`$returnGuildChannelsID`](#returnguildchannelsid)
    - [`$returnGuildRolesID`](#returnguildrolesid)
    - [`$returnGetReactions`](#returngetreactions)
15. [Events](#-events)
    - [`$alwaysReply`](#alwaysreply)
    - [`$messageContains`](#messagecontains)
    - [`$messageContainsAll`](#messagecontainsall)
    - [`$onInteraction`](#oninteraction)
    - [`$onJoined`](#onjoined)
    - [`$onLeave`](#onleave)
    - [`$onVoiceJoined`](#onvoicejoined)
    - [`$onVoiceLeave`](#onvoiceleave)
16. [Reference](#-reference)
    - [Separators](#separators)
    - [Color Names](#color-names)
    - [Full Examples](#full-examples)
</details>

---

## 🚀 Getting Started

### Syntax Rules

| Rule | Example |
|------|---------|
| Commands start with `$` | `$sendMessage[Hello]` |
| Arguments go inside `[]` | Separated by `;` |
| Whitespace is ignored | Around tokens |
| `#` starts a comment (whole line or inline outside brackets) | `$var[x; 5]  # set x` |
| Plain text lines are sent verbatim | `Welcome!` |
| Unclosed `[` or extra `]` | → Syntax Error |
| **Pre‑execution validation** catches all errors before anything runs | |

### Plain Text Lines

Any line that does **not** start with `$` is sent directly to the channel. Built‑in variables and inline commands are resolved inside it.

```
Welcome, $authorName!
Your channel is #$channelName.
```
**Output:**
```
Welcome, user!
Your channel is #general.
```

### Inline Comments

Comments appear after a bare `#` at bracket depth 0.

```
$var[score; 100]           # set initial score
$sendMessage[$var[score]]  # send it
```

### Variable Resolution Order

When `$var[name]` is used, the interpreter checks:
1. Temporary variables (`$var[name; value]`)
2. Built‑in read‑only variables (`$authorID`, `$channelName`, etc.)

> Persistent variables (`$setVar`) are **only** accessible via `$getVar[name]`.  
> Return variables are **only** accessible via `$return[name]`.

### Error System

All errors are reported before execution; nothing runs if any error is found.

| Icon | Category | Common Causes |
|------|----------|---------------|
| 🔴 | **Syntax Error** | Unknown command, unclosed bracket, mismatched block |
| 🟠 | **Logic Error** | Wrong arg count, invalid operator, `$break` outside loop |
| 🟡 | **Runtime Error** | Division by zero, non‑numeric argument |
| 🔵 | **Environment Error** | Channel/guild not found, missing permissions |

**Example:**
```
$wew[now]
```
```
🔴 Syntax Error — Line 1: Unknown command `wew`
```

---

## 📊 Variables & Data

### `$var` – Temporary Variables

Lives only for the current script execution.

**Set:**
```
$var[name; value]
```
**Get (inline):**
```
$var[name]
```
**Example:**
```
$var[score; 10]
$sendMessage[Your score is $var[score]]
```
→ `Your score is 10`

---

### `$setVar` / `$getVar` – Persistent Variables

Saved to disk (`.json`). Survive across executions.

```
$setVar[name; value]
$getVar[name]          ← inline only
```
Variable names are sanitised to alphanumeric, `-`, and `_`.

**Example:**
```
$setVar[visits; 42]
$sendMessage[Total visits: $getVar[visits]]
```
→ `Total visits: 42`

---

### Built‑in Variables

Read‑only; resolved at runtime.

| Variable | Value |
|----------|-------|
| `$authorID` | Numeric ID of the message author |
| `$authorName` | Username of the author |
| `$mention` | Mention string (`<@id>`) |
| `$channelID` | ID of current channel |
| `$channelName` | Name of current channel |
| `$guildID` | ID of current server (or `DM`) |
| `$guildName` | Name of current server |
| `$membersCount` | Total member count of current server |
| `$message` | All text after command trigger |
| `$message[n]` | nth word after trigger (1‑based) |
| `$messageID` | ID of triggering message |
| `$botName` | Bot's username |
| `$botID` | Bot's numeric ID |
| `$ping` | Bot's WebSocket latency (e.g. `42ms`) |
| `$uptime` | Time since bot started (`Xd Xh Xm Xs`) |
| `$addTimestamp` | Discord timestamp for now (default `T`) |
| `$randomUserID` | ID of a random non‑bot member |
| `$randomRoleID` / `$randomRoleMention` | Random role ID / mention |
| `$serverOwnerID` | ID of server owner |

---

## 💬 Messaging

### `$sendMessage`

Sends text to the current channel (or DM if `$dm` used).

```
$sendMessage[text]
```
```
$sendMessage[Hello from the bot!]
```

---

### `$reply`

Makes all subsequent output reply to the triggering message.

```
$reply
$sendMessage[Here is your answer, $mention!]
```
> In `$alwaysReply` events, replies are automatic.

---

### `$dm`

Redirects all subsequent output to a DM.

**DM the author:**
```
$dm
```
**DM a specific user:**
```
$dm[userID]
$dm[<@userID>]
```
```
$dm
$sendMessage[This goes to your DMs, $authorName!]
```

---

### `$image`

Sends an image as a Discord embed (image‑only). URL must be direct (`http://` or `https://`).

```
$image[url]
$image[$var[myImageUrl]]    ← inline
```
```
$image[https://example.com/photo.png]
```

---

## 🖼️ Embed Builder

Set embed fields individually. The embed is sent automatically at the end of execution if at least one field is set.

```
$title[text]
$description[text]
$color[hex or name]
$footer[text]
```
**Example:**
```
$title[Server Update]
$description[Maintenance starts at 10 PM.]
$color[orange]
$footer[Posted by the admin team]
```

### Color Names

| Name | Hex | Name | Hex |
|------|-----|------|-----|
| `red` | `#E74C3C` | `green` | `#2ECC71` |
| `blue` | `#3498DB` | `yellow` | `#F1C40F` |
| `orange` | `#E67E22` | `purple` | `#9B59B6` |
| `pink` | `#FF69B4` | `white` | `#FFFFFF` |
| `black` | `#000000` | `gray` / `grey` | `#95A5A6` |
| `cyan` | `#1ABC9C` | `gold` | `#F9A825` |
| `navy` | `#2C3E50` | `lime` | `#27AE60` |
| `brown` | `#A0522D` | `teal` | `#008080` |
| `magenta` | `#FF00FF` | `blurple` | `#5865F2` |
| `dark` (default) | `#2B2D31` | | |

---

### `$sendEmbedMessage`

Sends a full embed to a **specific channel by ID**. All 5 args required.

```
$sendEmbedMessage[channelID; title; description; color; footer]
```
```
$sendEmbedMessage[123456789012345678; Announcement; The vote is now open.; blurple; FDBot]
```

---

## 🔘 Buttons & Reactions

### `$addButton`

Adds a button to the pending message (or to an existing bot message by ID).

```
$addButton[isLink; ID/URL; label; style; (disabled; emoji; messageID)]
```
- `isLink` – `yes` / `no`
- `style` – `primary`, `secondary`, `success`, `danger`, `link`
- `disabled` – `yes` / `no` (optional)
- `emoji` – optional custom or Unicode emoji
- `messageID` – optional, to attach to an already sent bot message

**Example (queue for next message):**
```
$addButton[no; vote_yes; Yes; success]
$addButton[no; vote_no; No; danger]
$sendMessage[Cast your vote!]
```
**Example (add to existing message):**
```
$addButton[no; confirm; Confirm; primary; no; ; 123456789012345678]
```

---

### `$editButton`

Edits an existing button (by custom ID or URL) on a queued message, an interaction source, or a specific message ID.

```
$editButton[ID/URL; label; style; (disabled; emoji; messageID)]
```
```
$editButton[vote_yes; Absolutely Yes; success; no; ✅]
```

---

### `$removeButtons`

Removes **all** buttons from a queued message, interaction source, or a specific message ID.

```
$removeButtons[(messageID)]
```
```
$removeButtons[123456789012345678]
```

---

### `$removeComponent`

Removes one or more specific buttons (by custom ID or URL) from a queued message, interaction source, or a specific message ID.

```
$removeComponent[customID1; customID2; ...; (messageID)]
```
```
$removeComponent[vote_no; vote_yes]
```

---

### `$addBotReactions`

Adds reactions to the **last bot message** in this execution. Max 20 emojis.

```
$addBotReactions[emoji1; emoji2; ...]
```
```
$sendMessage[Vote now!]
$addBotReactions[👍; 👎]
```

---

### `$addUserReactions`

Adds reactions to the **user's triggering message**. Max 20 emojis.

```
$addUserReactions[emoji1; emoji2; ...]
```
```
$addUserReactions[❤️; 🎉]
```

---

## 🛡️ Moderation

### `$ban` / `$unban`

**Ban** a user; **unban** by ID. Requires `Ban Members`.

```
$ban                    ← bans the author
$ban[userID]
$ban[<@userID>]
$unban[userID]
```

---

### `$kick`

Kicks a user. Requires `Kick Members`.

```
$kick[userID]
$kick[<@userID>]
```

---

### `$timeout` / `$untimeout`

Timeout mutes a user; untimeout removes it. Requires `Moderate Members`.

```
$timeout[userID or mention; duration]
$untimeout[userID or mention]
```
Duration: number + unit (`s`, `m`, `h`, `d`). Max 28 days.

```
$timeout[$message[1]; 10m]
```

---

### `$slowmode`

Sets slowmode interval (seconds) for the current channel. Requires `Manage Channels`. Use `0` to disable.

```
$slowmode[channelID; seconds]
```
```
$slowmode[$channelID; 5]
```

---

### `$deletecommand`

Deletes the triggering message. Requires `Manage Messages`.

```
$deletecommand
```

---

### `$clear`

Bulk‑deletes messages from the current channel. Requires `Manage Messages`. Max 100.

```
$clear           ← deletes last 10 (default)
$clear[count]    ← max 100
```
```
$clear[25]
```

---

### Role Management

| Command | Description |
|---------|-------------|
| `$createRole[name; color; permissions; (hoist; mentionable)]` | Creates a role. Permissions: `cosmetic`, `member`, `mod`, `manager`, or raw integer. |
| `$cloneRole[roleID; (newName)]` | Clones an existing role. |
| `$deleteRole[roleID]` | Deletes a role. |
| `$roleAssign[user; +role1; -role2; ...]` | Add (`+`) or remove (`-`) roles from a user. |

```
$createRole[Moderator; #FF0000; mod; yes; yes]
$roleAssign[$authorID; +123456789; -987654321]
```

---

### `$changeUsername`

Changes a member's nickname. Requires `Manage Nicknames`.

```
$changeUsername[userID or mention; newName]
```
```
$changeUsername[$authorID; CoolUser]
```

---

## 🛡️ Access Control

### `$onlyAdmin`

Restricts execution to server administrators. Stops script immediately if not.

```
$onlyAdmin
$onlyAdmin[error message]
```
```
$onlyAdmin[❌ You need Administrator permission.]
$sendMessage[Admin command executed.]
```

---

### `$onlyIf`

Stops execution if condition is false. Optionally sends an error.

```
$onlyIf[condition]
$onlyIf[condition; error message]
```
```
$onlyIf[$authorID == 123456789; ❌ Owner only.]
$sendMessage[Owner command executed.]
```

---

### `$strictArgs`

Validates the number of words after the command trigger. If fails, sends error and **continues**.

```
$strictArgs[comparison; error text]
```
Operators: `>` `<` `=` `>=` `<=` `!=`

```
$strictArgs[>0; Please provide a username.]
$strictArgs[=2; Exactly two words required.]
```

---

### `$cooldown`

Limits usage frequency per user per script. If triggered again before cooldown ends, sends error and stops.

```
$cooldown[duration; error message]
```
Units: `s`, `m`, `h`, `d`. Use `{time}` or `%time%` to show remaining seconds.

```
$cooldown[30s; ⏳ Wait {time} before using this again!]
$sendMessage[Command executed!]
```

---

## ➕ Math & Numbers

### `$math` (advanced)

Evaluates a mathematical expression. Supports `+`, `-`, `*`, `/`, `//` (floor), `%`, `**`, `sqrt()`, `abs()`, `ceil()`, `floor()`, `round()`, `log()`, `sin()`, `cos()`, `tan()`, constants `pi`, `e`, `inf`.

```
$math[expression]
```
```
$sendMessage[$math[2 + 2 * 3]]   → 8
$sendMessage[$math[sqrt(16)]]    → 4
```

---

### Basic Math Commands

Standalone **or** inline. Work with two numeric arguments.

```
$sum[a; b]   $sub[a; b]   $mul[a; b]   $div[a; b]   $mod[a; b]
```
```
$sendMessage[$sum[8; 2]]   → 10
$sendMessage[Result is $sub[10; 3]]   → Result is 7
```

---

### `$round`

Rounds a number to the nearest integer (standard rounding).

```
$round[number]
```
```
$sendMessage[$round[1.7]]   → 2
```

---

### `$isNumber`

Checks if a value matches a numeric type/condition.

```
$isNumber[formula; value]
```
Formulas: `int`, `nat` (positive integer), `pos`, `neg`, `zero`, `even`, `odd`, `dec` (decimal), `frac` (fraction), `num` (any number).

```
$if[$isNumber[int; $message]]
  $sendMessage[It's a whole number!]
$endif
```

---

### `$charCount`

Counts letters (Unicode letters) and digits in a string.

```
$charCount[text]
```
```
$sendMessage[$charCount[Hello 123]]   → 8 (5 letters + 3 digits)
```

---

## 🎲 Randomness

### `$randomint`

Random integer between min and max (inclusive). Swaps if min>max.

```
$randomint[min; max]
```
```
$sendMessage[Lucky number: $randomint[1; 100]]
```

---

### `$randomstr`

Picks a random string from a list.

```
$randomstr[option1; option2; ...]
```
```
$randomstr[rock; paper; scissors]
```

---

### `$randomUserID`

Returns a random non‑bot member's ID from the current server.

```
$randomUserID
$sendMessage[Random member: $randomUserID]
```

---

### `$randomRoleID` / `$randomRoleMention`

Returns the ID or mention of a random role (excluding `@everyone`).

```
$randomRoleID
$randomRoleMention
```
```
$sendMessage[Random role: $randomRoleMention]
```

---

## 📝 String Utilities

### `$replaceText`

Replaces occurrences of a substring. Optional count (default = all).

```
$replaceText[text; search; replacement; (count)]
```
```
$sendMessage[$replaceText[hello world; world; FDScript]]   → hello FDScript
```

---

### `$splitIn` / `$splitOut`

Split a text by a delimiter and later retrieve a part by index.

```
$splitIn[text; delimiter]
$splitOut[index]   ← inline or standalone
```
Index can be a number (1‑based), `<` (first), or `>` (last).

```
$splitIn[apple;banana;cherry; ;]
$sendMessage[$splitOut[2]]   → banana
```

---

### `$switch`

Returns one of the given items based on a 1‑based index. The last argument is the index.

```
$switch[item1; item2; ... ; index]
```
```
$sendMessage[$switch[Red; Green; Blue; 2]]   → Green
```

---

## 🔄 Flow Control

### `$if` / `$elif` / `$else` / `$endif`

Evaluates conditions and executes the matching branch.

```
$if[condition]
  ...
$elif[condition]
  ...
$else
  ...
$endif
```
Operators: `==`, `!=`, `>`, `<`, `>=`, `<=`. Numeric strings compared numerically, others lexicographically.

```
$var[score; 75]
$if[$var[score] >= 90]
  $sendMessage[Grade: A]
$elif[$var[score] >= 60]
  $sendMessage[Grade: B]
$else
  $sendMessage[Grade: F]
$endif
```
→ `Grade: B`

---

### `$and` / `$or` – Compound Conditions

Use inside `$if` / `$elif` to combine conditions.

```
$if[$and[condition1; condition2; ...]]
$if[$or[condition1; condition2; ...]]
```
```
$var[age; 20]
$var[score; 85]
$if[$and[$var[age] >= 18; $var[score] >= 80]]
  $sendMessage[Eligible!]
$endif
```

---

### `$while` / `$endwhile`

Repeats a block while condition is true.

```
$while[condition]
  ...
$endwhile
```
```
$var[n; 1]
$while[$var[n] <= 3]
  $sendMessage[Iteration $var[n]]
  $var[n; $sum[$var[n]; 1]]
$endwhile
```

---

### `$for` / `$endfor`

Repeats a block a fixed number of times (count is a whole number).

```
$for[count]
  ...
$endfor
```
```
$for[3]
  $sendMessage[Hello!]
$endfor
```

---

### `$break`

Exits the nearest enclosing `$while` or `$for` loop immediately.

```
$break
```
```
$var[n; 0]
$while[$var[n] < 10]
  $var[n; $sum[$var[n]; 1]]
  $if[$var[n] == 4]
    $break
  $endif
$endwhile
$sendMessage[Stopped at $var[n]]
```
→ `Stopped at 4`

---

### `$return`

Reads a value stored by a return command. **Inline only**.

```
$return[varName]
```
Used after `$returnGuildUsersID`, `$returnGuildChannelsID`, `$returnGuildRolesID`, or `$returnGetReactions`.

---

## ⏱️ Timing & Delays

### `$wait`

Pauses the **entire script** for the specified duration.

```
$wait[duration]
```
Units: `s`, `m`, `h`, `d`.

```
$sendMessage[Starting...]
$wait[5s]
$sendMessage[Done after 5 seconds.]
```

---

### `$replyIn`

Delays **only the bot's reply** – the script continues running in the background.

```
$replyIn[duration]
```
```
$replyIn[10s]
$sendMessage[This appears 10 seconds later.]
```

---

### `$editIn`

Edits the last bot message after a delay.

```
$editIn[duration; newMessage]
```
```
$sendMessage[Initial message]
$editIn[5s; Updated message]
```
→ After 5 seconds, the message changes.

---

### `$addTimestamp`

Sends a Discord timestamp for the current time. Default format `T`. Optionally pass a format code.

```
$addTimestamp[(format)]
```
Formats: `t`, `T`, `d`, `D`, `f`, `F`, `R`.

```
$sendMessage[Event starts: $addTimestamp[R]]
```

---

## 🤖 Bot Info & Utilities

### `$ping`

Sends current WebSocket latency in milliseconds.

```
$ping
$sendMessage[Latency: $ping]
```
→ `Latency: 42ms`

---

### `$uptime`

Sends time since bot started.

```
$uptime
$sendMessage[Bot has been running for $uptime]
```
→ `Bot has been running for 2d 4h 12m 7s`

---

### `$getBotInvent`

Sends the bot's OAuth2 invite link (with Admin permissions). Inline‑capable.

```
$getBotInvent
$sendMessage[Invite the bot: $getBotInvent]
```

---

### `$clientTyping`

Shows a "Bot is typing…" indicator until a message is sent.

```
$clientTyping
```

---

### `$log`

Takes a snapshot of the execution log and sends it to a specified channel after the script finishes.

```
$log[channelID]
$log[channelID; name_code]
```
- Short logs → code block
- Long logs (>2000 chars) → `.txt` attachment

```
$log[987654321098765432; admin-audit]
```

---

## 📊 Return Commands (Data Fetching)

These commands populate return variables that can be read with `$return[name]`.

### `$returnGuildUsersID`

Fetches IDs of all non‑bot members.

```
$returnGuildUsersID[guildID; fetchMode; var; separator]
```
- `fetchMode`: `cache` (fast, cached) or `chunk` (fetches all from Discord – use with caution on large servers).
```
$returnGuildUsersID[$guildID; cache; members; com]
$sendMessage[Member IDs: $return[members]]
```

---

### `$returnGuildChannelsID`

Fetches channel IDs filtered by type.

```
$returnGuildChannelsID[guildID; channelType; var; separator]
```
Types: `text`, `voice`, `category`, `forum`, `stage`, `all`.
```
$returnGuildChannelsID[$guildID; text; channels; com]
$sendMessage[Text channels: $return[channels]]
```

---

### `$returnGuildRolesID`

Fetches role IDs, optionally filtered by permission. Excludes `@everyone`.

```
$returnGuildRolesID[guildID; permission; var; separator]
```
Leave empty or use `all` for all roles. Named permissions: `admin`, `manage_guild`, `manage_roles`, `kick_members`, `ban_members`, `moderate_members`, etc.
```
$returnGuildRolesID[$guildID; admin; adminRoles; com]
$sendMessage[Admin roles: $return[adminRoles]]
```

---

### `$returnGetReactions`

Fetches reaction data from a specific message.

```
$returnGetReactions[channelID; messageID; type; var; separator; emoji]
```
- `type`: `usersID` (list of reactor IDs) or `tr` (total reaction count)
- If `type = tr` and emoji not found, result is `0`.

```
$returnGetReactions[$channelID; $messageID; tr; voteCount; com; 👍]
$sendMessage[Total 👍 votes: $return[voteCount]]
```

---

## 🚀 Events

Event scripts are triggered automatically by Discord events. They start with a special first‑line declaration:

```
#PREFIX:$eventName[channelID]   (most events)
#PREFIX:$alwaysReply            (no channel ID)
#PREFIX:$onInteraction          (optional custom_id)
#PREFIX:$messageContains[word1; word2; ...]   (case‑insensitive)
#PREFIX:$messageContainsAll[word1; word2; ...]
```

The `channelID` tells the bot where to send messages produced by the script. For `$alwaysReply`, output is automatically replied to the triggering message.

> All event scripts are placed in the `events/` folder and are monitored by the bot.

---

### `$alwaysReply`

Triggered on **every** non‑bot message. All output is automatically replied.

**First line:**
```
#PREFIX:$alwaysReply
```

**Available variables:** All standard built‑in variables are available. `$message` returns the **full message content** (no trigger prefix).

**Example:**
```
#PREFIX:$alwaysReply
$if[$or[$message == hello; $message == hi]]
  $sendMessage[Hey $mention! 👋]
$endif
```
> Use carefully – it fires on all messages.

---

### `$messageContains`

Triggered when the message contains **any** of the listed words (case‑insensitive).

**First line:**
```
#PREFIX:$messageContains[word1; word2; ...]
```

**Example:**
```
#PREFIX:$messageContains[hello; hi; hey]
$sendMessage[Hello to you too, $mention!]
```

---

### `$messageContainsAll`

Triggered when the message contains **all** of the listed words (case‑insensitive).

**First line:**
```
#PREFIX:$messageContainsAll[word1; word2; ...]
```

**Example:**
```
#PREFIX:$messageContainsAll[ping; bot]
$sendMessage[Yes, I am online!]
```

---

### `$onInteraction`

Triggered when a button or select menu is interacted with. You can either listen to **all** interactions, or filter by a specific `custom_id`.

**First line (all interactions):**
```
#PREFIX:$onInteraction
```

**First line (specific custom_id):**
```
#PREFIX:$onInteraction[custom_id]
```

**Available variables:** Standard built‑ins (`$authorID`, `$authorName`, `$guildID`, etc.) are available via the original message. `$message` is not available.

**Example (specific button):**
```
#PREFIX:$onInteraction[confirm_btn]
$sendMessage[You confirmed the action!]
```

---

### `$onJoined`

Triggered when a member joins the server.

**First line:**
```
#PREFIX:$onJoined[channelID]
```

**Available variables:** `$authorID`, `$authorName`, `$mention`, `$guildID`, `$guildName`, `$membersCount`, `$botID`, `$botName`.  
`$message` and `$messageID` are **not** available.

**Example:**
```
#PREFIX:$onJoined[123456789012345678]
$sendMessage[Welcome $mention! You are member number $membersCount. 🎉]
```

---

### `$onLeave`

Triggered when a member leaves or is removed.

**First line:**
```
#PREFIX:$onLeave[channelID]
```

**Available variables:** Same as `$onJoined` – refers to the user who left.

**Example:**
```
#PREFIX:$onLeave[123456789012345678]
$sendMessage[**$authorName** has left the server. 👋]
```

---

### `$onVoiceJoined`

Triggered when a member joins a voice channel.

**First line:**
```
#PREFIX:$onVoiceJoined[channelID]
```

**Available variables:** Same as `$onJoined` (the member refers to the user who joined voice). The voice channel itself is not directly exposed as a variable, but you can use `$channelName` or `$channelID` (if defined via the script context) – note that the target channel is the one in the first line.

**Example:**
```
#PREFIX:$onVoiceJoined[123456789012345678]
$sendMessage[**$authorName** just joined a voice channel! 🎧]
```

---

### `$onVoiceLeave`

Triggered when a member leaves a voice channel.

**First line:**
```
#PREFIX:$onVoiceLeave[channelID]
```

**Available variables:** Same as `$onVoiceJoined`.

**Example:**
```
#PREFIX:$onVoiceLeave[123456789012345678]
$sendMessage[**$authorName** left the voice channel. 👋]
```

---

## 📚 Reference

### Separators

Used in list‑returning commands. Pass a literal character or a named alias.

| Name | Character |
|------|-----------|
| `dot` | `.` |
| `com` | `,` |
| `apo` | `'` |
| `sem` | `;` |
| `colon` | `:` |

> You **cannot** pass `;` directly – use `sem`.

### Color Names

See [Color Names](#color-names) section above.

---

## Full Examples

### Server Info Embed
```
$color[blurple]
$title[📊 Server Info]
$description[**Name:** $guildName
**ID:** $guildID
**Members:** $membersCount
**Channel:** $channelName]
$footer[Requested by $authorName]
```

### Persistent Hit Counter
```
$var[count; $getVar[hits]]
$var[count; $sum[$var[count]; 1]]
$setVar[hits; $var[count]]
$sendMessage[$authorName, you have used this command $var[count] times.]
```

### Cooldown Command
```
$cooldown[30s; ⏳ Wait {time} before using this again!]
$sendMessage[Command executed!]
```

### Guessing Game
```
$strictArgs[>0; Please provide a number.]
$var[guess; $message]
$var[answer; 7]
$if[$var[guess] == $var[answer]]
  $sendMessage[Correct!]
$else
  $sendMessage[Wrong, try again.]
$endif
```

### Reaction Vote
```
$sendMessage[Vote now! 👍 for yes, 👎 for no.]
$addBotReactions[👍; 👎]
```

### Audit Log Snapshot
```
$sendMessage[Command executed.]
$log[987654321098765432; command-audit]
```

### Auto‑Reply to Greetings (Event)
```
#PREFIX:$alwaysReply
$if[$or[$message == hello; $message == hi; $message == hey]]
  $sendMessage[Hey $mention! 👋]
$endif
```

### Button Interaction (Event)
```
#PREFIX:$onInteraction[confirm_btn]
$sendMessage[You confirmed the action!]
```

### Welcome on Join (Event)
```
#PREFIX:$onJoined[123456789012345678]
$sendMessage[Welcome $mention! You are member number $membersCount. 🎉]
```

---

*FDScript is part of [BCFD-L](https://github.com/obgwew/BCFD-L) — licensed under AGPLv3.*