"""
MUJ feedback form helper.

Run:
    python muj_feedback.py            (fills and submits every pending form)
    python muj_feedback.py --dry-run  (only shows what it would do)

It asks: positive or negative (p/n), then username and password.
Credentials stay in memory only. The browser is a temporary one, nothing is saved.

  p -> every YES/NO question = YES, every dropdown = most positive option
  n -> every YES/NO question = NO,  every dropdown = most negative option
  m -> YES/NO mixed (about 60% YES, 40% NO), every dropdown = middle option
"""
import argparse
import getpass
import sys

from playwright.sync_api import sync_playwright

BASE = "https://mujslcm.jaipur.manipal.edu"
LIST_URL = BASE + "/Student/Survey/FeedbackList"

# Higher score = more positive. Longer phrases are checked first.
SCORES = {
    "strongly agree": 5, "strongly disagree": 1, "disagree": 2, "agree": 4,
    "neither": 3, "neutral": 3, "undecided": 3,
    "outstanding": 5, "excellent": 5, "very good": 4.5, "good": 4,
    "average": 3, "satisfactory": 3, "fair": 2.5, "very poor": 1, "poor": 1.5,
    "always": 5, "often": 4, "sometimes": 3, "rarely": 2, "never": 1,
    "yes": 5, "no": 1,
}
ORDERED = sorted(SCORES, key=len, reverse=True)


def score(option):
    o = option.lower().strip()
    if o in SCORES:
        return SCORES[o]
    for k in ORDERED:
        if k in o:
            return SCORES[k]
    return None


def choose_option(options, mode):
    """Return index of the most positive / most negative / middle option, or None if unsure."""
    scored = [(i, score(o)) for i, o in enumerate(options) if o and o.lower() != "select"]
    if len(scored) < 2 or any(s is None for _, s in scored):
        return None
    values = [s for _, s in scored]
    if max(values) == min(values):
        return None
    if mode == "m":
        mid = (max(values) + min(values)) / 2
        # closest to the middle; on a tie, take the more positive of the two
        return min(scored, key=lambda t: (abs(t[1] - mid), -t[1]))[0]
    target = max(values) if mode == "p" else min(values)
    return next(i for i, s in scored if s == target)


# Finds every YES/NO pair and every dropdown, tags them, returns their texts.
TAG_JS = r"""
() => {
  const norm = s => (s || "").replace(/\s+/g, " ").trim();
  const label = el => norm(el.value && !el.textContent.trim() ? el.value : el.textContent).toUpperCase();
  const all = [...document.querySelectorAll("button, label, a, input[type=button], input[type=radio]")];
  const yes = all.filter(e => label(e) === "YES");
  const no  = all.filter(e => label(e) === "NO");
  const qText = el => norm(el.textContent.replace(/\bYES\b|\bNO\b/g, ""));
  const out = [];
  yes.forEach(y => {
    let p = y.parentElement;
    while (p && !(no.filter(n => p.contains(n)).length === 1 &&
                  yes.filter(x => p.contains(x)).length === 1)) p = p.parentElement;
    if (!p) return;
    const n = no.find(n => p.contains(n));
    let r = p;
    while (r && qText(r).length < 6) r = r.parentElement;
    const i = out.length;
    y.setAttribute("data-auto-yes", i);
    n.setAttribute("data-auto-no", i);
    out.push(r ? qText(r) : "?");
  });
  const sel = [...document.querySelectorAll("select")].map((s, i) => {
    s.setAttribute("data-auto-sel", i);
    let p = s, q = "?";
    while (p && p.parentElement) {
      let prev = p.previousElementSibling;
      while (prev && !norm(prev.textContent)) prev = prev.previousElementSibling;
      if (prev) { q = norm(prev.textContent); break; }
      p = p.parentElement;
    }
    return { question: q, options: [...s.options].map(o => norm(o.textContent)) };
  });
  return { yn: out, sel: sel };
}
"""


def read_list(page):
    page.goto(LIST_URL)
    page.wait_for_load_state("networkidle")
    rows = []
    trs = page.locator("table tbody tr")
    for i in range(trs.count()):
        cells = [c.strip() for c in trs.nth(i).locator("td").all_inner_texts()]
        if len(cells) >= 5:
            rows.append({"idx": i, "course": cells[2], "faculty": cells[3], "status": cells[4]})
    return rows


def open_row(page, idx):
    row = page.locator("table tbody tr").nth(idx)
    target = row.locator("a, button").first
    if target.count() == 0:
        target = row.locator("td").nth(4)
    target.click()
    page.wait_for_load_state("networkidle")


def login(page, username, password):
    page.goto(BASE)
    page.wait_for_load_state("networkidle")
    page.locator("input[type=text]:visible").first.fill(username)
    page.locator("input[type=password]:visible").first.fill(password)
    page.get_by_role("button", name="Sign In").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    if page.locator("input[type=password]:visible").count():
        sys.exit("Login seems to have failed (wrong password, captcha or OTP?). Stopping.")


BALANCED_PATTERN = ["YES", "YES", "NO", "YES", "NO"]  # about 60% YES, 40% NO


def process_form(page, mode, dry):
    found = page.evaluate(TAG_JS)
    questions, selects = found["yn"], found["sel"]
    if not questions and not selects:
        return "nothing detected"
    if mode == "p":
        answers = ["YES"] * len(questions)
    elif mode == "n":
        answers = ["NO"] * len(questions)
    else:
        answers = [BALANCED_PATTERN[i % len(BALANCED_PATTERN)] for i in range(len(questions))]
    print(f"  {len(questions)} YES/NO questions -> {answers.count('YES')} YES, {answers.count('NO')} NO")

    picks = []
    for s in selects:
        idx = choose_option(s["options"], mode)
        shown = s["options"][idx] if idx is not None else "?"
        print(f"  dropdown '{s['question'][:50]}' -> {shown}   (options: {[o for o in s['options'] if o]})")
        if idx is None:
            return "stopped: could not tell which dropdown option is positive/negative"
        picks.append(idx)

    if dry:
        return "dry run"

    for i, a in enumerate(answers):
        attr = "data-auto-yes" if a == "YES" else "data-auto-no"
        page.locator(f"[{attr}='{i}']").click()
    for i, idx in enumerate(picks):
        page.locator(f"[data-auto-sel='{i}']").select_option(index=idx)

    page.get_by_role("button", name="Submit").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    # Some portals show a confirmation dialog
    for name in ("Yes", "OK", "Confirm"):
        btn = page.get_by_role("button", name=name)
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            page.wait_for_load_state("networkidle")
            break
    return "submitted"


def launch_browser(pw):
    """Use the Chrome or Edge already installed; fall back to Playwright's own Chromium."""
    last = None
    for channel in ("chrome", "msedge", None):
        try:
            if channel:
                return pw.chromium.launch(channel=channel, headless=False)
            return pw.chromium.launch(headless=False)
        except Exception as e:
            last = e
    raise RuntimeError(
        "No usable browser found. Install Google Chrome or Microsoft Edge, "
        "or run: python -m playwright install chromium"
    ) from last


def run(mode, username, password, dry_run=False):
    """Log in and process every pending form. Used by both the terminal and the GUI."""
    with sync_playwright() as pw:
        browser = launch_browser(pw)
        try:
            page = browser.new_context().new_page()  # temporary, nothing persisted
            login(page, username, password)

            seen = set()
            report = []
            while True:
                rows = read_list(page)
                pending = [r for r in rows
                           if "pending" in r["status"].lower() and (r["course"], r["faculty"]) not in seen]
                if not pending:
                    break
                r = pending[0]
                seen.add((r["course"], r["faculty"]))
                print(f"\n{r['course']} - {r['faculty']}")
                try:
                    open_row(page, r["idx"])
                    result = process_form(page, mode, dry_run)
                except Exception as e:  # keep going with the other courses
                    result = f"error: {str(e).splitlines()[0]}"
                print(f"  -> {result}")
                report.append((r["course"], r["faculty"], result))

            print("\n=== Summary ===")
            for course, fac, result in report:
                print(f"{result:12} {course} - {fac}")
            if not dry_run:
                print("\nFinal statuses on the portal:")
                for r in read_list(page):
                    print(f"  {r['course']}: {r['status']}")
        finally:
            browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="show what would be done, click nothing")
    args = ap.parse_args()

    mode = ""
    while mode not in ("p", "n", "m"):
        mode = input("Feedback type: positive, negative or mid/balanced? (p/n/m): ").strip().lower()
    username = input("Username (without @muj.manipal.edu): ").strip()
    password = getpass.getpass("Password: ")
    run(mode, username, password, args.dry_run)


if __name__ == "__main__":
    main()
