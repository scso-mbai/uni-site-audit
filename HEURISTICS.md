# The ten usability heuristics, and what the HTML can tell us

Jakob Nielsen's ten heuristics are broad rules of thumb for spotting usability problems. We met them in the
Week 5 lesson on heuristic evaluation. The names below are Nielsen's; the one-line explanations are ours,
written for this exercise. For Nielsen's own descriptions, see nngroup.com.

Each line ends with the evidence from `tools/page_facts.py` that bears on the heuristic. Field names are the
keys in the raw JSON files (inside `facts` unless the name starts with `http.`, `robots.` or `outcome`).

## The heuristics

1. **Visibility of system status.** People can always tell where they are on the site and what has just
   happened, without waiting or guessing.
   Evidence: `title`, `headings.h1`, `breadcrumbs.present`, `navigation.aria_current_count` (marks the current
   page in a menu), `http.response_ms`, `http.bytes`.

2. **Match between system and the real world.** Labels and page order follow how visitors think about a
   university (courses, fees, applying), not the names of internal offices.
   Evidence: `navigation.landmarks.N.top_level_links`, `headings.h1`, `headings.h2`, `title`, `lang`.

3. **User control and freedom.** A visitor who takes a wrong turn can step back, start again or stop a moving
   element, without being trapped.
   Evidence: `navigation.home_links`, `breadcrumbs.present`, `carousel_or_slider_hints`, `autoplay_media`,
   `skip_link.present`.

4. **Consistency and standards.** The same thing is named and placed the same way on every page, and the site
   follows the habits people bring from other websites and the published web standards (including the
   accessibility standard, WCAG).
   Evidence: `headings.h1_count` (one per page is the convention), `lang`, `landmarks.main`,
   `images.missing_alt`, `links.empty_text`, `forms.inputs_without_label`, and whether `title` and the
   top-level menu follow the same pattern on both pages.

5. **Error prevention.** The design makes slips unlikely, for example with clear field labels and sensible
   choices, instead of relying on messages after the fact.
   Evidence: `forms.forms`, `forms.inputs`, `forms.inputs_without_label`,
   `forms.unlabelled_with_placeholder_only` (a placeholder disappears as soon as someone types).

6. **Recognition rather than recall.** What a visitor needs to choose is on the page in front of them, so they
   recognise it instead of having to remember it from an earlier page.
   Evidence: `navigation.landmarks.N.top_level_links`, `breadcrumbs.present`, `links.vague_text_total`
   ("read more" makes people remember what it referred to), `search.search_input`.

7. **Flexibility and efficiency of use.** First-time and regular visitors can both reach what they want in few
   steps; search and shortcuts help those who already know what they are after.
   Evidence: `search.search_form`, `search.search_input`, `skip_link.present`, `http.response_ms`,
   `http.bytes`, `scripts.external`, `scripts.third_party_hosts`, `meta_viewport` (phone-friendly layout).

8. **Aesthetic and minimalist design.** Every page shows what supports the visitor's task and leaves out what
   competes with it for attention.
   Evidence (indirect only): `navigation.landmarks.N.links` (size of the menu), `headings.h2_count`,
   `visible_word_count`, `carousel_or_slider_hints`, `cookie_banner_hints`.

9. **Help users recognise, diagnose and recover from errors.** When something fails, the page says in ordinary
   words what went wrong and what to do next.
   Evidence: there is almost none on a normal page. `forms.inputs_without_label` matters because error
   messages are tied to labels. The usual answer is "not judged from HTML".

10. **Help and documentation.** Help, FAQs and contact details are easy to find from any page and answer the
    question the visitor came with.
    Evidence: `help_faq_contact_links`, `footer_contact.phone_pattern`, `footer_contact.email_pattern`,
    `footer_contact.postal_address_pattern`.

## Severity scale (0 to 4, higher is worse)

| Score | Meaning |
|---|---|
| 0 | No problem: the evidence shows nothing worth changing. |
| 1 | Cosmetic: a small polish item; fix when convenient. |
| 2 | Minor: slows some visitors down; schedule a fix. |
| 3 | Major: many visitors will struggle; fix soon. |
| 4 | Severe: visitors may fail or give up on a task; fix before anything else. |
| not judged | The HTML cannot show this. Write "not judged from HTML" and say why. |

When choosing a score, think about how many visitors meet the problem, how badly it gets in their way, and
whether they meet it once or on every visit. A missing piece of evidence never counts as a 0. If the facts cannot
tell, the answer is "not judged".

## Limits

Reading a page's HTML is not the same as looking at it or using it. This audit cannot judge visual design,
layout, colour contrast, font size, images, animation, or anything a page builds with JavaScript after it
loads. It cannot follow a real task such as finding the fees for a programme and applying, and it does not
watch real visitors. Some sites refuse automated visitors altogether (a "bot-check" page), and then there is
nothing to judge. Treat every finding as a prompt for a human evaluator to go and look, not as a verdict on
the site or the people who run it.
