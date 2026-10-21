# National University of Singapore (NUS) · usability audit · 2026-10-21

> Sample written during set-up on 21 Oct 2026, by hand, from the raw files in `reports/_sample/raw/`.

Pages read: home https://www.nus.edu.sg/ (bot_check_page, HTTP 200, 121 ms, 1 KB) ·
admissions https://www.nus.edu.sg/admissions (bot_check_page, HTTP 200, 35 ms, 1 KB)
robots.txt: answered with an HTML page, not a rules file, so no rules apply.

## Heuristics

| # | Heuristic | Severity | Evidence from the HTML |
|---|---|---|---|
| 1 | Visibility of system status | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 2 | Match between system and the real world | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 3 | User control and freedom | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 4 | Consistency and standards | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 5 | Error prevention | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 6 | Recognition rather than recall | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 7 | Flexibility and efficiency of use | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 8 | Aesthetic and minimalist design | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 9 | Help users recognise, diagnose and recover from errors | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |
| 10 | Help and documentation | not judged | not judged from HTML: `home:outcome` = "bot_check_page"; `admissions:outcome` = "bot_check_page" |

Severity: 0 no problem, 1 cosmetic, 2 minor, 3 major, 4 severe (see HEURISTICS.md). Lower is better.

## Three suggestions for the web team
No suggestions this week. Both pages answered with a bot-check page from Imperva Incapsula
(`home:challenge.vendor` = "Imperva Incapsula") instead of their content, so there was no evidence to judge.
The audit records this and does not try to get past it.

## Since last week
First audit; nothing to compare yet.

## Limits
Judged from the HTML of two pages only. Visual design, colour contrast and real tasks were not judged.
These findings are prompts for a human evaluator, not verdicts.
