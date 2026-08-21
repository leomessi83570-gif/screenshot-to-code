# Welkom in Breda

A single-file recreation of the Breda city-tourism site shown in `bred_website.mp4`.

`index.html` is fully self-contained — no build step, no network. Open it in a browser.

- **Imagery** is extracted from the source video (the aerial hero, the five category
  photos). In the hero the baked-in navigation, headline and button were painted out
  so the page can render its own; the softened band behind the headline is what covers
  that repair.
- **Fonts** (Outfit, Mulish — latin subset) are embedded as base64 `@font-face` rules.
- **The tower in front of the headline** is a second copy of the hero photo, clipped to
  the tower's column and stacked above the type. Identical pixels in an identical
  position, so the seam is invisible and only the headline passes behind it.
- **Motion**: page-load headline reveal, scroll progress bar, sticky nav, hero
  parallax/fade, IntersectionObserver reveals with stagger, counting figures, and an
  auto-advancing card rail with buttons, drag, swipe and arrow keys. All of it is
  disabled under `prefers-reduced-motion`.

Sections below the news carousel (agenda, nieuws, newsletter, footer) are invented —
the video only shows the hero, the "Laat je inspireren" rail and the top of the
"Activiteiten" section.
