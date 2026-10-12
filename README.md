<p align="center">
  <img alt="trteeb" src="docs/studio/trteeb.svg" width="140">
</p>

<h1 align="center">trteeb</h1>

<p align="center">
  <b>Free, open-source page layout — part of the Creative Studio creative suite.</b><br>
  <b>تنسيق الصفحات، مجاني ومفتوح المصدر — جزء من حزمة Creative Studio.</b>
</p>

<p align="center">
  <a href="https://studio.creative.ps/">studio.creative.ps</a>
</p>

<p align="center">
  <img alt="License: MIT OR Apache-2.0" src="https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-555555">
  <img alt="Based on DesignCraft" src="https://img.shields.io/badge/based%20on-DesignCraft-0d2d3f">
</p>

## Built on DesignCraft

trteeb is a fork of **[DesignCraft](https://github.com/storytold/designcraft)**, the
open-source, clean-room page-layout application written in Rust by the
**[ArtCraft](https://getartcraft.com/)** team and the DesignCraft contributors. Almost everything
that makes this app work is their work. Thank you. If you like trteeb, please star and
support the upstream project as well.

What we add: the Creative Studio identity, the Arabic interface (upstream ships Arabic and right-to-left layout), and Arabic
features to come. Our changes are listed in [`studio/CHANGES.md`](studio/CHANGES.md).
Upstream's own README, with the full feature list and build instructions, is in
[`docs/UPSTREAM-README.md`](docs/UPSTREAM-README.md).

## The Creative Studio suite

| App | What it's for | Based on |
|---|---|---|
| [rsm](https://github.com/7mz410/CreativeStudio-rsm) | Vector illustration | VectorCraft |
| [ttshat](https://github.com/7mz410/CreativeStudio-ttshat) | Photo library and raw development | LightCraft |
| [tlween](https://github.com/7mz410/CreativeStudio-tlween) | Image editing | PhotoCraft |
| [tsweer](https://github.com/7mz410/CreativeStudio-tsweer) | Video editing | FilmCraft |
| [effectat](https://github.com/7mz410/CreativeStudio-effectat) | Motion graphics and effects | EffectCraft |
| [sf7aat](https://github.com/7mz410/CreativeStudio-sf7aat) | PDF documents | PdfCraft |
| **trteeb** | Page layout | DesignCraft |

More apps are on the way: see [studio.creative.ps](https://studio.creative.ps/).

## Building

```sh
cargo run --release -p designcraft
# after merging upstream:
git fetch upstream && git merge upstream/main && python3 studio/rebrand.py
```

## Licence

Code: MIT OR Apache-2.0 (`LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`), like upstream. The Creative Studio
name and logos in `docs/studio/` belong to the Creative Studio project.
