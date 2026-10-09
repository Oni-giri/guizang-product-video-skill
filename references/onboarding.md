# Dependency installation (read only when items are missing)

Confirm the style and initialize the video directory first, then run `check_environment.py --project <video-dir>`. If Python is absent, install Python first. The check script uses only the standard library; it runs even with missing dependencies and lists the items that need installing.

## Scope and verification

| Path | Required environment |
| --- | --- |
| Starter project | Python ≥3.9, Node ≥22, npm, FFmpeg/FFprobe; in-project React, ReactDOM, esbuild, GSAP, Three.js, Playwright and a launchable Chromium |
| Code-synthesized score (optional) | For scripts like `score-example-cinematic.py` that depend on numpy/scipy/soundfile, create a venv inside the video project and install there, not into the system Python |
| HyperFrames | The official runtime requirements for that version, FFmpeg/FFprobe, a launchable Chrome; this skill's audio scripts need Python |
| Other existing frameworks | Keep the framework and its lockfile; fill in only what is actually missing |

Reuse a working environment first. The commands below are only for missing items; before installing, check the **current official documentation** at the links for system support, package names and required versions. Stable minimums are for compatibility judgments; new installs prefer supported versions. Record the actually installed versions, lockfiles and run results in the project; a past verification date is not a promise of future compatibility.

Rerun the check afterwards. If the same error persists after installation, read the error first to tell apart permission, system library, network and version problems, then address the cause; avoid repeated downloads. Handle system permissions through the permission mechanism of the current execution environment.

## System tools

### macOS

With Homebrew present, pick commands by missing item. `brew info <formula>` can verify package details before installing:

```sh
brew install ffmpeg
brew install node
brew install python
```

Sources: [FFmpeg](https://formulae.brew.sh/formula/ffmpeg), [Node](https://formulae.brew.sh/formula/node), [Python](https://docs.brew.sh/Homebrew-and-Python). If Node LTS is needed, pick a supported LTS per the [Node download page](https://nodejs.org/en/download) and the current Homebrew formula; keep an existing working Node at its current version. For versioned formulae, determine PATH from the actual `brew --prefix <formula>` and the install output.

Without Homebrew, use existing tools or the [official installer](https://docs.brew.sh/Installation). When Homebrew itself must be installed, take the current command from the official docs, inspect the script, then run it; the install script version is not frozen here.

### Debian / Ubuntu

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg python3
```

Trim the package list when only one item is missing. Node can reuse an existing nvm:

```sh
nvm install --lts
nvm use --lts
```

If nvm is not installed, get the current versioned script URL from the [official nvm install instructions](https://github.com/nvm-sh/nvm#installing-and-updating), download and inspect it, then run it; `PROFILE=/dev/null` avoids modifying the shell config, then load the actual `nvm.sh` named in the install output. Other distributions: use their package manager and the [FFmpeg download page](https://ffmpeg.org/download.html).

### Windows / PowerShell

Search and verify the package identity first, then install the exact ID that was actually returned. For example:

```powershell
winget search --name Node.js
winget search --name FFmpeg
winget search --name Python
# Replace package-id with the exact ID after checking the search results against the official docs:
winget show --id <package-id> --exact
winget install --id <package-id> --exact
```

Sources: [WinGet search](https://learn.microsoft.com/en-us/windows/package-manager/winget/search), [WinGet install](https://learn.microsoft.com/en-us/windows/package-manager/winget/install), [Python Windows installation notes](https://docs.python.org/3/using/windows.html), [Windows builds listed by FFmpeg](https://ffmpeg.org/download.html). Python package identity / install manager follows the official docs at the time; the Store ID is not frozen. After installing, refresh the session PATH and verify with the actual `python` / `py -3` command.

## Project dependencies and browser

Inside the video project directory, use `npm ci` when package-lock.json exists; use `npm install` the first time, when there is no lockfile. Other package managers keep their existing lockfile. The pinned versions in the starter project's package.json are the reproducible baseline; upgrade after testing, not automatically for every production run.

The browser version follows the project's Playwright; only when the matching browser is missing:

```sh
npx playwright install chromium --only-shell
```

This command suits the starter project's default export with `headless:true` and no channel specified. Drop `--only-shell` when the project needs headed Chromium. On Linux with missing system libraries, use `npx playwright install --with-deps chromium`. Per the [Playwright browsers docs](https://playwright.dev/docs/browsers), the headless shell and full Chromium are separate files; **accept based on a real launch succeeding or failing**. When launch fails because of sandbox / permissions, fix the execution permissions; re-downloading the browser will not help.

The starter project's export script passes `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist` so Three.js/WebGL uses software rendering in headless mode; the environment check passes the same flags when it actually launches the browser.

## HyperFrames

Keep the existing version. When a new project needs the CLI, check the [official CLI docs](https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes-cli/references/doctor-browser.md) and the current `--help` first, then run:

```sh
npm install --save-dev --save-exact hyperframes
npx hyperframes doctor --json
# Only when Chrome is missing:
npx hyperframes browser ensure
```

Pin the actually installed version. Interpret doctor by what is actually missing: local rendering needs Node, FFmpeg, FFprobe and Chrome; TTS, Whisper, MusicGen and Docker that were not chosen are not required dependencies. When the doctor schema changes, update the check adapter instead of reinstalling software that already exists. Handle Docker dependencies only when rendering with Docker. Install the framework CLI separately from other skills, choosing by what the task actually needs.

## Recheck

```sh
python3 <skill-dir>/scripts/check_environment.py --project <video-dir> --engine browser --force
```

For HyperFrames use `--engine hyperframes`. On success, continue the original storyboard work; reread the matching section only when items are missing. Platform install syntax comes from the official sources above; real-machine coverage is whatever the verification records show.
