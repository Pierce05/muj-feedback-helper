# MUJ Feedback Helper

A small local tool that logs into the MUJ student portal and fills in your pending faculty feedback forms for you, so you don't have to click 100+ YES/NO buttons by hand.

> **Unofficial.** Not affiliated with or endorsed by Manipal University Jaipur. Use at your own risk (see [Disclaimer](#disclaimer)).

## What it does

1. Logs in with the username and password you type (kept in memory only).
2. Finds every course marked **Pending** on the Feedback List page.
3. Fills each questionnaire according to the mode you pick, then submits it.
4. Prints a summary and the final status of each course.

| Mode | YES/NO questions | Dropdown questions |
|------|------------------|--------------------|
| **Positive** | all YES | most positive option |
| **Mid / balanced** | mixed, about 60% YES / 40% NO | middle option |
| **Negative** | all NO | most negative option |

The same answers are used for every faculty member. If the script can't tell which dropdown option is positive or negative, it stops for that course instead of guessing.

## Privacy and safety

- Runs **only on your computer**. There is no server.
- Your password is never written to disk, logged, or sent anywhere except the MUJ portal.
- It opens a temporary browser session, so no cookies or profile are saved.
- Submitted forms usually **cannot be edited**. Try **Preview only** (dry run) first.
- Never share your portal links (they contain an `enc=` token) or your password in issues, screenshots or commits.

## Setup

You need **Python 3.9+** and **Google Chrome or Microsoft Edge** (Edge is built into Windows).

### Windows
Double-click **`start.bat`**. It installs the one dependency and opens the window.

### Mac / Linux
```bash
chmod +x start.sh
./start.sh
```
(On Linux you may need `sudo apt install python3-tk` for the window.)

### Manual
```bash
pip install -r requirements.txt
python muj_feedback_gui.py     # window
python muj_feedback.py         # terminal version (add --dry-run to preview)
```

If no Chrome or Edge is found, run `python -m playwright install chromium` once.

## Using the window

1. Pick **Positive**, **Mid** or **Negative**.
2. Enter your username (without `@muj.manipal.edu`) and password.
3. Tick **Preview only** the first time. It shows what would be chosen and clicks nothing.
4. Click the big button and watch the progress log.

If login needs a captcha or OTP, the tool stops; it doesn't try to get around it.

## Windows .exe (no Python needed)

This repo includes a GitHub Actions workflow that builds a single `.exe`:

1. Push the code to GitHub.
2. Create a release tag, e.g. `git tag v1.0.0 && git push origin v1.0.0`.
3. Download `MUJ-Feedback-Helper.exe` from the **Releases** page (or from the workflow's artifacts).

Note: unsigned `.exe` files often trigger Windows SmartScreen or antivirus warnings. Building it yourself from source avoids that.

## Troubleshooting

- **A course still says Pending afterwards:** the portal's Submit button or a confirmation pop-up may differ from what the script expects. Open an issue with the output from the log (remove any personal details).
- **"Nothing detected":** the questionnaire layout may have changed. Open an issue.
- **Login failed:** check your password, or whether the portal is asking for a captcha/OTP.
- **The portal changes sometimes.** If it redesigns its pages this tool may stop working until it's updated.

## Disclaimer

This tool is provided as-is with no warranty. Using automation on a university portal may go against your institution's rules, and answering every question the same way doesn't give faculty honest, useful feedback. You are responsible for how you use it and for reading MUJ's policies. The authors accept no liability for any consequences.

## License

MIT, see [LICENSE](LICENSE). Replace `<your name>` in the license file with your own name before publishing.
