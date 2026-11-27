# The Friday World — 27 November 2026 in one image

[![make.fun](https://make.fun/badge/news-image-20261127)](https://make.fun/bounty/news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/rank)](https://make.fun/bounty/news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/reward)](https://make.fun/bounty/news-image-20261127)

**"The Friday World"** sums up Friday 27 November 2026 in a single 1024×1024
broadsheet: 37 stories across 7 regions, every one dated — happened, or first
reported — on 27 November 2026, in any time zone.

## What is on the page

- **Masthead + dek** — the day's three biggest stories in one line.
- **13 pictured cards, numbered 1–13** — three leads on top, ten features below,
  each with its own hand-drawn flat scene, dateline, headline, deck, source tag
  and a REPORTED / CONFIRMED / CLAIM status chip.
- **THE DAY IN NUMBERS** — six big numbers from the day's stories:
  961,000 homes without power in the US storm · 7,000 tonnes of diesel off
  Ibiza · 77,000 UK net migration · 168 lives remembered in Hong Kong ·
  €45bn EU loan for Ukraine · 100,000 UK reservists told to prepare.
- **Region strip** — Middle East 4 · Europe 13 · North America 5 · Asia 6 ·
  Africa 3 · Oceania 3 · Latin America 3 = 37 stories.
- **THE DAY IN TIME (UTC)** — five moments from the day.
- **WHERE IT HAPPENED** — a hand-drawn world map with numbered pins 1–13
  matching the pictured stories.
- **DATE CHECK** — six big stories deliberately left out because they belong
  to another day (Cairo tanker fire 25 Nov, Macy's parade postponement
  announced 25 Nov, Bangkok refinery blast 26 Nov, Trump 25% India tariff
  proposed 26 Nov, cargo ship Halima sinks off Cuba 26 Nov, Guardian's Mali
  investigation published 24 Nov).
- **ALSO ON FRIDAY 27 NOVEMBER — 24 MORE STORIES** — briefs 14–37, each with
  dateline and source.
- **Footer** — the date rule, the source list, and the status-chip legend.

## The stories

**Leads:** 1. Drones kill two Italians at a Kuwait air-defence site (Reuters) ·
2. Thanksgiving storm cuts power to 961,000 homes (AP) · 3. Israeli strikes kill
10 in Gaza; Hamas weighs its reply (Reuters).

**Features:** 4. Zelenskyy warns Russia readies a new massive grid strike
(Ukrinform) · 5. Tanker capsizes off Ibiza with 7,000 tonnes of diesel (Reuters) ·
6. UK net migration falls to 77,000, lowest since 1997 (BBC) · 7. Depardieu ordered
to stand trial over 2018 rape (AP) · 8. Hong Kong mourns 168 dead, a year after the
tower fire (AP) · 9. Tube drivers begin eight days of winter strikes (Reuters) ·
10. Germany arrests two Iraqis over synagogue plot (Reuters) · 11. Gukesh–Sindarov
Game 3 drawn; match level 1.5–1.5 (Chess.com) · 12. Black Friday: shoppers chase
essentials, not luxury (AP) · 13. Musk pledges two SpaceX shares for every US
child (Reuters).

**Briefs 14–37:** EU split over the €45bn Ukraine loan · Britain puts 100,000
reservists on standby · Spain's ex-central bank chief to lead the ECB · nearly
2,000 migrants reach the Canaries in one day · boat dealer 'supplied Channel
smuggling gangs' · Spain's young voters weigh housing · strike on a Saudi refinery
kills one worker · Israeli strikes hit Lebanon's Jenta town · Trump tells Putin to
'pull back' · Trump calls GDP data 'fake' · Myanmar rejects parts of the ICJ
Rohingya ruling · Kim vows more nuclear weapons · China launches Shenzhou 24 ·
tear gas as Bangladesh garment workers march · Pakistan to host Saudi–Turkey
defence talks · Guinea-Bissau junta delays civilian rule to 2028 · Ebola in DR
Congo passes 12,000 cases · South Africa's Biovac to scale up vaccine output ·
Lyon set to be dropped for the first NZ Test · Qantas and Air NZ jets too close at
Sydney · NZ coalition falls one seat short of a majority · Mexico's president
blasts the DEA · Costa Rica bars the UN Palestine rapporteur · Brazil weighs
inviting an Argentine rival to Lula's event.

## How it is made

`build_poster.py` (Python 3 + Pillow, standard fonts only) draws the whole
broadsheet from scratch — gradients, flat-scene illustrations, the map, and all
text — deterministically: fixed seed, no clock, no network, no external assets.
It asserts that the region counts sum to the story total and that story numbers
run 1–37. Run it to regenerate the image:

```
python3 build_poster.py
```

`main.ts` (Node 22, standard library only) copies `entry.png` to the output
directory:

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

Both runs write byte-identical output. The image is 1024×1024, under 1 MiB,
with over 80,000 unique colours, and stays legible at 300 px wide.

Verified 27 Nov 2026: `entry.png` is 929,982 bytes, 1024×1024, 83,082 unique
colours, sha256 `9ac853c88f6066ceee85528693f51f3fd8e6ed7b2dd501fee7693783a8463c05`;
`main.ts` run twice produces byte-identical output, and rebuilding the poster
from `build_poster.py` reproduces the same bytes.

## Sources

Reuters · AP · AFP · BBC · Guardian · Ukrinform · Chess.com · ESPNcricinfo.
All artwork is original, drawn by the generator; no photographs, no logos,
no copied assets.
