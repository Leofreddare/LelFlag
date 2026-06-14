> [!CAUTION]
> The only official place to download LelFlag is this GitHub repository.  
> If someone reuploads LelFlag somewhere else, be careful and verify the source before running it.

<div align="center">

# LelFlag

### Tweak Roblox and Roblox Studio like never before.

LelFlag is a lightweight Windows tool for managing Roblox and Roblox Studio FastFlags through a simple dark-themed interface.

Instead of manually finding `ClientAppSettings.json`, editing JSON by hand, and hoping you did not break the format, LelFlag gives you quick toggleable modules for common Roblox tweaks, performance options, rendering changes, and interface adjustments.

<br>

![License](https://img.shields.io/github/license/Leofreddare/LelFlag?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/Leofreddare/LelFlag?style=for-the-badge)
![Repo Size](https://img.shields.io/github/repo-size/Leofreddare/LelFlag?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)

</div>

---

## What is LelFlag?

LelFlag is a FastFlag manager for Roblox Player and Roblox Studio.

FastFlags are configuration values used by Roblox. They can affect rendering, performance, graphics backends, UI behavior, and other client-side settings. LelFlag helps manage these values by writing them to Roblox’s `ClientAppSettings.json` file for you.

The goal is simple:

- Make Roblox tweaking easier
- Avoid manual JSON editing for common flags
- Support both Roblox Player and Roblox Studio
- Keep everything local and transparent
- Provide a clean interface similar in spirit to tools like Bloxstrap

LelFlag does not inject into Roblox, exploit Roblox, modify live game code, or require your `.ROBLOSECURITY` cookie.

---

## Features

### FastFlag module toggles

Enable or disable included tweak modules with simple switches.

Current module categories include:

- **Performance**  
  FPS, stutter reduction, level-of-detail, texture quality, and performance-related flags.

- **Rendering**  
  Graphics API preferences, lighting behavior, anti-aliasing, resolution behavior, and fullscreen-related flags.

- **Environment**  
  Sky, grass, clouds, wind, and world-visual settings.

- **Interface**  
  UI-related flags, reduced motion options, titlebar behavior, and other interface tweaks.

---

### Roblox and Roblox Studio support

LelFlag supports separate settings for:

- Roblox Player
- Roblox Studio

You can switch between them inside the app. Each client gets its own `ClientAppSettings.json`, so Roblox Player tweaks and Roblox Studio tweaks can be managed separately.

---

### Custom FFlags editor

Need to add your own flags?

LelFlag includes a custom JSON editor for directly editing `ClientAppSettings.json`.

This is useful if:

- You already know the FastFlag you want to use
- A flag is not included as a built-in module yet
- You want full control over the generated JSON file

The editor warns you that valid JSON is required before saving.

---

### Open JSON path

LelFlag can open the Roblox `ClientSettings` folder directly, making it easier to inspect or back up your configuration.

No more manually digging through Roblox version folders.

---

### Reset modules

LelFlag includes a reset option for the currently selected client.

Resetting modules replaces `ClientAppSettings.json` with an empty JSON object:

```json
{}
