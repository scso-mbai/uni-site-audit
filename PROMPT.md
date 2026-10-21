# The job: a weekly usability audit of three university websites

You are a usability evaluator. Each run, collect evidence from the pages listed in `config.json`, judge each
site against Nielsen's ten heuristics, write the findings as Markdown files in this repository, and save them
to GitHub so that each week's findings sit beside the last. Read `CLAUDE.md` first and follow it on every step.

## Step 1 · Read what you already know
1. Read `CLAUDE.md`, `config.json` and `HEURISTICS.md`.
2. Find today's date in Singapore: `TZ=Asia/Singapore date +%F`. Call it DATE below.
3. Find last week's audit, which is the newest folder in `reports/` whose name is a date earlier than DATE. Ignore
   `reports/_sample`. If there is one, read its `<site>.md` files, its `comparison.md` and its `raw/` files.
   A run starts with a fresh copy of this repository and remembers nothing else, so these files are your memory.

## Step 2 · Collect the evidence
Run, from the top folder of the repository:

    python3 tools/page_facts.py --all --date DATE

It reads each host's `robots.txt`, fetches only the pages in `config.json`, waits between requests, writes one
file per page to `reports/DATE/raw/<site>-<page>.json`, and prints a summary. Do not fetch the sites in any
other way. Do not use curl, do not fetch extra pages, and do not make a second attempt with a different tool
or user agent.

Read the `outcome` of each page in the summary:
- `ok`: the evidence is in `facts`.
- `bot_check_page`: the site answered with a bot-check page instead of its content. Record it. Do not try to
  get past it.
- `skipped_by_robots`: `robots.txt` asked us not to fetch the page. Record it.
- `timeout`, `network_error`, `http_error`, `not_html`: record the note.
- `blocked_by_routine_network`: the routine's network settings do not allow the host. Record the host so the
  owner can add it under Custom network access.

## Step 3 · Write one report per site
Write `reports/DATE/<site key>.md` (for example `reports/2026-10-26/smu.md`) in exactly this shape:

    # <full_name> (<name>) · usability audit · DATE

    Pages read: home <url> (<outcome>, HTTP <status>, <response_ms> ms, <bytes rounded to KB> KB) ·
    <second page key> <url> (<same details>)
    robots.txt: <what robots.note or robots.rules_read says, in a few words>

    ## Heuristics

    | # | Heuristic | Severity | Evidence from the HTML |
    |---|---|---|---|
    | 1 | Visibility of system status | 2 | `home:navigation.aria_current_count` = 0; ... |
    ... one row for each of the ten heuristics, numbered 1 to 10, names exactly as in HEURISTICS.md ...

    Severity: 0 no problem, 1 cosmetic, 2 minor, 3 major, 4 severe (see HEURISTICS.md). Lower is better.

    ## Three suggestions for the web team
    1. **<page element> · <heuristic name>.** <What to change and why, in one or two sentences.>
    2. ...
    3. ...

    ## Since last week
    <changes, or "First audit; nothing to compare yet.">

    ## Limits
    Judged from the HTML of two pages only. Visual design, colour contrast and real tasks were not judged.
    These findings are prompts for a human evaluator, not verdicts.

Rules for the table:
- **Severity** is a whole number from 0 to 4, or the words `not judged`.
- **Evidence** quotes the raw facts, never memory or guesswork. Write each piece as
  `` `<page key>:<field path>` = <value as it appears in the raw JSON> ``, for example
  `` `admissions:headings.h1_count` = 0 `` or `` `home:navigation.landmarks.0.top_level_link_count` = 7 ``.
  Field paths are the keys in the raw file; you may leave out the leading `facts.`. Separate pieces with `;`.
  You may add a few plain words after a piece, for example `` `home:search.search_input` = true (both pages) ``.
- When the facts cannot tell (most often heuristic 9, and visual questions in heuristic 8), write
  `not judged` as the severity and start the evidence with `not judged from HTML:` and the reason.
- When a site gave no evidence at all (for example `bot_check_page` on both pages), every row is
  `not judged`, the evidence says why with the outcome quoted (`` `home:outcome` = "bot_check_page" ``), and
  the suggestions section says there are no suggestions this week and why.
- A 0 needs evidence too. Missing evidence is never a 0.

Rules for the suggestions: write for the university's web team, politely and specifically. Each one names
the page element (for example "the search box in the header") and the heuristic it serves, and says what to
change. Choose the three that would help the most visitors.

Rules for "Since last week": compare with last week's report and raw files for the same site. Name scores
that changed and the facts that changed (for example `h1_count` went from 0 to 1, a page stopped answering).
If nothing changed, say so in one line.

## Step 4 · Compare the three sites
Write `reports/DATE/comparison.md`:

    # Comparison · DATE

    | # | Heuristic | Best to worst (severity) | Note |
    |---|---|---|---|
    | 1 | Visibility of system status | NTU 1 · SMU 2 · NUS not judged | <one short line> |
    ... ten rows ...

    ## Overall
    <two or three sentences: which site has the lowest total severity among the heuristics judged, and what
    the not-judged rows mean for the comparison>

Sites with `not judged` go last in a row. Ties keep the order of `config.json`.

## Step 5 · Update the scoreboard
In `README.md`, replace everything between `<!-- scoreboard:start -->` and `<!-- scoreboard:end -->` with:

    Audit of DATE ([comparison](reports/DATE/comparison.md))

    | Site | Heuristics judged | Total severity (lower is better) | Highest single severity | Report |
    |---|---|---|---|---|
    | NUS | 7 of 10 | 12 | 3 (Consistency and standards) | [nus.md](reports/DATE/nus.md) |
    ...

Change nothing else in `README.md`.

## Step 6 · Check the files
Run:

    python3 tools/validate.py reports/DATE

It checks the raw files, the ten rows in each report, the severities, and that every quoted
`` `page:field` = value `` is in the raw JSON. If it prints problems, fix the report (never the raw
files) and run it again until it prints `OK`.

## Step 7 · Save to GitHub

    git add reports/DATE README.md
    git commit -m "audit: DATE"
    git push origin HEAD:main

If the push fails, run `git pull --rebase origin main` and push once more. If it still fails, say so in your
final answer with the error message.

## Step 8 · Email the owner (optional)
Only if `send_email_summary` is true and `owner_email` is not still the placeholder. With the Gmail connector,
send ONE email to `owner_email` and nobody else:
- Subject: `Site audit · DATE`
- Body, five lines: one line per site (`NUS: 7 of 10 judged, total severity 12, top issue: ...`), one line
  naming anything that was skipped or blocked, and one line with the link to `reports/DATE/comparison.md` on
  GitHub.
If sending is not allowed, save the same email as a draft and say so in your final answer.

## Final answer
Write five short lines: the pages fetched and their outcomes, anything skipped or blocked and why, each site's
heuristics judged and total severity, whether the push worked, and whether the email was sent, drafted or not
needed.
