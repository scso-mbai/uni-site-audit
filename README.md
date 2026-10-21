# University site audit

This Claude Code cloud routine audits three Singapore university websites every Monday at 7:07 AM Singapore
time. It reads the home page and the admissions page of NUS, NTU and SMU, judges each site against Jakob
Nielsen's ten usability heuristics, and stores the findings as Markdown files in `reports/`, one dated folder
per week, so each week's findings sit beside the last.

MGMT 6110, Week 8, exercise 2. We met heuristic evaluation in the Week 5 lesson.

## How it works
1. `tools/page_facts.py` reads each site's `robots.txt`, fetches only the pages in `config.json`, and pulls
   out evidence an evaluator can use without seeing the screen: the title, headings, menus, search box,
   breadcrumbs, images without alt text, vague link texts such as "read more", form fields without labels,
   skip link, contact details in the footer, cookie banner hints, scripts, and help or FAQ links.
2. Claude reads that evidence against `HEURISTICS.md` and writes one report per site, a comparison of the
   three, and the scoreboard below.
3. `tools/validate.py` checks that every piece of evidence quoted in a report is in the raw data.
4. The routine commits the week's folder and pushes it to `main`, and can email you a five-line summary.

See `reports/_sample/` for the shape of a report, written by hand during set-up from real data.

## Set it up
1. On GitHub, use this template to create a repository in your own account.
2. In `config.json`, put your email address in `owner_email`. Set `send_email_summary` to `false` if you do
   not want the email.
3. In Claude Code, create a routine with these values:

| Setting | Value |
|---|---|
| Instructions | `Read PROMPT.md and CLAUDE.md in this repository and do the job in PROMPT.md. Push your changes to main.` |
| Repository | this repository |
| Network access | Custom. Allowed domains: `www.nus.edu.sg`, `www.ntu.edu.sg`, `www.smu.edu.sg`. Tick "Also include default list". |
| Schedule | Weekly, Monday, 7:07 AM |
| Connectors | Gmail only (optional) |

4. Press "Run now" once to check the set-up, then read the new folder in `reports/` and the commit the run made.

A request to a host that is not on the allowed list gets HTTP 403 and the header
`x-deny-reason: host_not_allowed`. The tool reports that as `blocked_by_routine_network` and names the host.

## What to expect
When this template was tested on 21 October 2026, NTU answered with its pages, but NUS and SMU answered
automated visitors with a bot-check page instead of their content. The audit records this as
`bot_check_page`, marks those rows "not judged", and does not try to get past the check, because whether to
let automated visitors in is the site's decision. If you would rather audit sites that answer, replace them in
`config.json` and add their hosts under Custom network access.

## Files
- `config.json`: the sites and pages, your email address, the report folder and the schedule.
- `tools/page_facts.py`: the evidence collector (Python 3.9 or later, standard library only).
- `tools/validate.py`: the check that runs before every commit.
- `HEURISTICS.md`: the ten heuristics, the 0 to 4 severity scale, what evidence bears on each, and the limits.
- `PROMPT.md`: the routine's job, step by step.
- `CLAUDE.md`: the house rules every run follows.
- `reports/<date>/`: one folder per run, with `raw/` evidence, a report per site and `comparison.md`.

## Run it on your own computer

    python3 tools/page_facts.py https://www.ntu.edu.sg/
    python3 tools/page_facts.py --all --date 2026-10-26
    python3 tools/validate.py reports/2026-10-26

The first line prints the evidence for one page. The second fetches every page in `config.json` and writes
the raw files for that date.

## Latest scoreboard

<!-- scoreboard:start -->
Audit of 2026-10-21 ([comparison](reports/2026-10-21/comparison.md))

| Site | Heuristics judged | Total severity (lower is better) | Highest single severity | Report |
|---|---|---|---|---|
| NUS | 0 of 10 | not judged | not judged | [nus.md](reports/2026-10-21/nus.md) |
| NTU | 8 of 10 | 8 | 2 (Consistency and standards) | [ntu.md](reports/2026-10-21/ntu.md) |
| SMU | 0 of 10 | not judged | not judged | [smu.md](reports/2026-10-21/smu.md) |
<!-- scoreboard:end -->
