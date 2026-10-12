# trteeb: changes from upstream DesignCraft

Required by the Apache License 2.0 (section 4b): files we changed carry this notice through
this list.

- Branding (user-visible only, applied by `studio/rebrand.py`): the app name trteeb (ترتيب in
  Arabic), the bundle id `ps.creative.studio.trteeb`, Help links to studio.creative.ps and this
  repository. Crate names, settings folders and the file format keep their upstream names.
- The ArtCraft mark gives way to the trteeb star (`crates/ui-egui/src/studio_mark.rs`, generated
  from `docs/studio/trteeb.svg`) in About and on the start screen.
- No Discord buttons (top bar, start screen, About); the Help menu labels Discord as the upstream
  community. About lists the Creative Studio apps.
- App icon: the trteeb star on navy (`assets/app-icon/`).
- Removed upstream's ArtCraft brand assets (`docs/brand/`), as their brand terms require of forks.
- README (upstream's is `docs/UPSTREAM-README.md`) and NOTICE: the fork, its credits and the suite.
