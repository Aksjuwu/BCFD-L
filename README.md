![FDSB.png](./main_exe/icons/FDSB.png)


# FDSB - Free Design Studio Bot's

> Build and run Discord bots locally using **FDScript** — a lightweight scripting language designed specifically for this tool.

---

**Description:** A desktop application for creating and running Discord bots locally, using **FDScript** – a scripting language specifically designed for bot scripting – to run your bots as efficiently as possible.

**Goal:** To simplify the process. No hosting required (it runs on-device), no need to write structurally complex code, and no need to deal with any learning or programming limitations – just write a script and get a responsive bot in 30 seconds.

---

# How to use it? 

**APK:**

**1. Download the APK version compatible with your device.**

**2. The main interface (in English by default) will appear, displaying three buttons:**
```text
1. Discord -> Server link  
2. GitHub -> Project link  
3. New Bot -> Create a bot
```

**3. Click on the `New Bot` button to open the Discord Developer Portal link. Create your bot, make sure the three gateway intents (the toggle buttons at the bottom of the Bot tab) are enabled, and then copy your bot's token.**

**4. Inside the app, set up your bot by giving it a name and an icon, then paste your token.**

> [!NOTE]
> Naming and image selection in the app do not affect your original bot on Discord.

> [!WARNING]
> The token is stored locally on your device, but it is not encrypted.

**5. Log into the bot and go to settings to select your preferred language and interface theme.**

**6. On the same settings page, click the "wiki-fdscript" link to learn how to write commands.**

**7. Go to the commands tab and click the `+` button to create a new command. In the editor, enter a name (required) and choose your desired prefix. Write your command's code based on [wiki-fdscript](https://github.com/obgwew/FDSB/blob/main/Wiki-FDScript.md), then click the `Save` button when finished.**

**8. Return to the main interface and press the `Start` button to run your bot.**

> [!CAUTION]
> The app does not run in the background. The user interface must remain open/visible, or you must use an external device to keep the bot online 24/7.

**EXE:** *Coming soon...*

---

**Notes:**

- Some themes require a restart to take effect.
- The built-in command set is clearly designed to be deliberately simple, with FDScript handling the more complex tasks. (However, this is not related to the number of commands I plan to add later.)
- While FDScript gen 2 offers greater command-line processing capabilities, it's important to note that some poorly planned complexities may produce undesirable results (please report any such issues).

---

**Changelog:**

- **1.0.0** — Initial beta release
  - New interface
  - New language (FDScript) Gen 0
  - New control mechanism

- **1.0.1** — Patch
  - Fixed Arabic language rendering
  - Fixed translator errors
  - Fixed crash on startup
  - Fixed server connection issue

- **2.0.0** — Feature update
  - Improved UI
  - New FDScript Gen 1
  - Fixed bot file conflicts
  - Added settings panel
  - Added theme support

- **2.0.1** — FDScript Growth & Some Fixes
  - Added 20+ new commands to FDScript
  - Fixed some themes
  - Fixed button behavior in commands_view
  - Fixed inputs in settings_view
  - Replaced Kivy icon with BCFD icon

- **2.1.0** — Task integration & event commands
  - Added new admin commands (Basic Discord commands)
  - Added new event commands
  - Upload/download bot data
  - FDScript gen 2 development
  - Fixed some commands

- **2.2.0** - Upgrade UI By Flet
  - Convert from kivy to flet
  - Ui updated 
  - Ui effects
  - Fixed some ui
  - Fixed some commands

- **2.2.1** - Fixed & Add Languages
  - Fixed vars commands
  - Fixed prefix logical 
  - Fixing theme switching
  - Fix switching languages
  - add 2 languages Fr(French) & De(German)

**After the 2.2.1 update, the project name will officially become FDSB**

- **2.2.2** - Big Repair & Add Languages & Fixed Ui(flet) Command view
  - Fixed more commands & vars
  - Fixed Color-Code
  - Fixed some ui on view command
  - Fixed some ui on view command
  - Fix server
  - add 3 languages ch(chinese) & ru(russian) & tr(turkish)

- **2.2.3** - Exclusive Version For Phones(only Android)
  - APK compatibility
  - Some Fixed commands
  - Increased stability
  - Smooth control

- **2.2.4** - Update Extensions
  - Added 30+ new commands to FDScript
  - Some Fixed 
  - Various repairs
  - Better stability in the editor

---

**Developers:** @y.lw (contributor) · [@obgwew](https://github.com/obgwew) (programming)

---

## License

Copyright (C) 2026 obgwew

This program is free software: you can redistribute it and/or modify
it under the terms of the **GNU Affero General Public License** as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.