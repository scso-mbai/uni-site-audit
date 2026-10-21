# Nanyang Technological University (NTU) · usability audit · 2026-10-21

> Sample written during set-up on 21 Oct 2026, by hand, from the raw files in `reports/_sample/raw/`.
> It shows the shape of a report for a site whose pages could be read.

Pages read: home https://www.ntu.edu.sg/ (ok, HTTP 200, 156 ms, 145 KB) ·
admissions https://www.ntu.edu.sg/admissions (ok, HTTP 200, 156 ms, 140 KB)
robots.txt: read; both pages allowed for "*".

## Heuristics

| # | Heuristic | Severity | Evidence from the HTML |
|---|---|---|---|
| 1 | Visibility of system status | 1 | `admissions:breadcrumbs.present` = true; `admissions:title` = "Admissions \| NTU Singapore"; `home:navigation.aria_current_count` = 0; `admissions:navigation.aria_current_count` = 0 (the menu does not mark the section you are in); `home:http.response_ms` = 156 |
| 2 | Match between system and the real world | 1 | `home:navigation.landmarks.0.top_level_links` = ["About Us", "Admissions", "Education", "Research", "Innovation", "Life at NTU", "Alumni"] (plain words); `admissions:navigation.landmarks.1.top_level_links` = ["Corporate NTU", "Admissions"] (the breadcrumb starts with an internal-sounding label) |
| 3 | User control and freedom | 1 | `home:navigation.home_links` = 2; `admissions:breadcrumbs.present` = true; `home:autoplay_media` = 0; `home:carousel_or_slider_hints` = 18 (sliders are present; whether they move on their own and can be paused needs a human check) |
| 4 | Consistency and standards | 2 | `home:headings.h1_count` = 0; `admissions:headings.h1_count` = 0; `home:landmarks.main` = false; `home:links.empty_text` = 5; `home:images.missing_alt` = 0; `admissions:images.missing_alt` = 0 |
| 5 | Error prevention | 1 | `home:forms.inputs` = 1; `home:forms.unlabelled_with_placeholder_only` = 1 (the page's only text field, most likely the search box, has a placeholder but no label); `admissions:forms.inputs` = 38; `admissions:forms.inputs_without_label` = 1 |
| 6 | Recognition rather than recall | 0 | `home:navigation.landmarks.0.top_level_link_count` = 7; `home:links.vague_text_total` = 0; `admissions:links.vague_text_total` = 0; `admissions:search.search_input` = true |
| 7 | Flexibility and efficiency of use | 2 | `home:skip_link.present` = false; `admissions:skip_link.present` = false; `home:navigation.landmarks.0.links` = 303 (keyboard users pass every menu link first); `home:search.search_form` = true; `home:meta_viewport` = "width=device-width, initial-scale=1.0" |
| 8 | Aesthetic and minimalist design | not judged | not judged from HTML: the layout cannot be seen. A human should look at how the menu of `home:navigation.landmarks.0.links` = 303 links is shown, and at the cookie notice (`home:cookie_banner_hints` = "page text mentions cookies") |
| 9 | Help users recognise, diagnose and recover from errors | not judged | not judged from HTML: neither page shows an error state; `home:forms.forms` = 1 |
| 10 | Help and documentation | 0 | `home:help_faq_contact_links` = "Frequently Asked Questions"; `admissions:help_faq_contact_links` = "Contact Us"; `home:footer_contact.phone_pattern` = true; `home:footer_contact.postal_address_pattern` = true |

Severity: 0 no problem, 1 cosmetic, 2 minor, 3 major, 4 severe (see HEURISTICS.md). Lower is better.

## Three suggestions for the web team
1. **The main heading on the home and admissions pages · Consistency and standards.** Neither page has an
   `<h1>` in its HTML (`h1_count` = 0 on both). Give each page one main heading that names it, such as
   "Admissions", so that screen-reader users and search engines know what the page is about.
2. **A "Skip to content" link before the site menu · Flexibility and efficiency of use.** The main menu holds
   303 links and neither page has a skip link, so keyboard users pass the whole menu on every page. Add a skip
   link as the first item on the page and wrap the page content in a `<main>` element (`landmarks.main` =
   false today).
3. **The search box on the home page · Error prevention.** The page's only text field has a placeholder but
   no label. Add a label (it can be visually hidden) so the field keeps its name once someone starts typing
   and screen readers announce what it is for.

## Since last week
First audit; nothing to compare yet.

## Limits
Judged from the HTML of two pages only. Visual design, colour contrast and real tasks were not judged.
These findings are prompts for a human evaluator, not verdicts.
