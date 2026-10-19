#!/usr/bin/env python3
"""Apply the trteeb (Creative Studio) branding on top of upstream DesignCraft.

Only user-visible text is rebranded; crate names, the file format and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 studio/rebrand.py
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'trteeb'
NAME_AR = 'ترتيب'
REPO = 'https://github.com/7mz410/CreativeStudio-trteeb'
SITE = 'https://studio.creative.ps'
APP_SITE = 'https://trteeb.studio.creative.ps'
LOGO = ROOT / 'docs/studio/trteeb.svg'
# Persisted paths and legal lines; renaming them would lose settings or misstate copyright.
KEEP = ('Application Support/DesignCraft', '/roaming/DesignCraft', 'the DesignCraft authors')

# The rest of the suite, for About › "More Creative Studio apps" (slug, name, what it is).
SIBLINGS = '''pub const SIBLINGS: &[(&str, &str, &str)] = &[
    ("rsm", "rsm", "vector illustration"),
    ("tlween", "tlween", "image editing"),
    ("tsweer", "tsweer", "video editing, color and sound"),
    ("ttshat", "ttshat", "photo library and raw development"),
    ("sf7aat", "sf7aat", "reading, organizing and protecting PDFs"),
    ("effectat", "effectat", "motion graphics and visual effects"),
];'''

# (file, upstream text, our text). Applied once each: skipped when our text is already there.
RULES = [
    # Links: our site and repo. Discord stays defined (help.discord, CLI) but is not shown.
    ('crates/engine/src/links.rs', 'pub const WEBSITE: &str = "https://getartcraft.com";', f'pub const WEBSITE: &str = "{SITE}";'),
    ('crates/engine/src/links.rs', 'pub const APP_PAGE: &str = "https://getartcraft.com/apps/designcraft";', f'pub const APP_PAGE: &str = "{APP_SITE}";'),
    ('crates/engine/src/links.rs', 'pub const GITHUB: &str = "https://github.com/storytold/designcraft";', f'pub const GITHUB: &str = "{REPO}";'),
    ('crates/engine/src/links.rs', 'pub const ISSUES: &str = "https://github.com/storytold/designcraft/issues";', f'pub const ISSUES: &str = "{REPO}/issues";'),
    ('crates/engine/src/links.rs', '''        assert!(APP_PAGE.ends_with(&format!("/apps/{APP}")));
        assert!(GITHUB.ends_with(&format!("/storytold/{APP}")));''', '''        assert!(APP_PAGE.starts_with("https://trteeb."));
        assert!(GITHUB.ends_with("/CreativeStudio-trteeb"));'''),
    # The mark: our star (studio_mark.rs, generated from docs/studio/trteeb.svg) in its own colours.
    ('crates/ui-egui/src/lib.rs', 'pub mod about;\n', 'pub mod about;\npub mod studio_mark;\n', 'pub mod studio_mark;'),
    ('crates/ui-egui/src/about.rs', '''        let k = px as f64 / 136.34;
        rc.set_transform(kurbo::Affine::scale(k) * kurbo::Affine::translate((10.0, 19.42)));
        let [r, g, b, a] = color.to_srgba_unmultiplied();
        rc.set_paint(peniko::Color::from_rgba8(r, g, b, a));
        if let Ok(p) = kurbo::BezPath::from_svg(MARK_PATH) {
            rc.fill_path(&p);
        }''', '''        // Creative Studio: the trteeb star, centred, in its own colours (`color` is unused).
        let _ = (color, MARK_PATH);
        let (w, h) = crate::studio_mark::SIZE;
        let k = px as f64 / w.max(h);
        rc.set_transform(kurbo::Affine::scale(k) * kurbo::Affine::translate(((h - w).max(0.0) / 2.0, (w - h).max(0.0) / 2.0)));
        for (d, [r, g, b]) in crate::studio_mark::PATHS {
            rc.set_paint(peniko::Color::from_rgba8(*r, *g, *b, 255));
            if let Ok(p) = kurbo::BezPath::from_svg(d) {
                rc.fill_path(&p);
            }
        }'''),
    # ArtCraft's mark outline is their trademark: not kept in the code.
    ('crates/ui-egui/src/about.rs', 'const MARK_PATH: &str = "M104.28,49.49L81.55,0h-31.23l-3.17,4.76L14.75,53.63,0,75.85l21.55,21.55,63.79-36.94,16.99,37.04,14.01-21.74-12.06-26.27ZM32.89,65.66l32.42-48.87,10.91,23.77-43.32,25.09Z";',
     'const MARK_PATH: &str = ""; // Creative Studio: the mark is crate::studio_mark'),
    # About: no Discord, Creative Studio wording, our sibling apps on their subdomains.
    ('crates/ui-egui/src/about.rs', '''            if discord_button(ui, crate::i18n::tr(&app.ui.language, "Join the ArtCraft Discord"), vec2(300.0, 40.0)) {
                open = Some("discord");
            }
            ui.add_space(4.0);
            ui.label(crate::rtl::widget(
                ui,
                egui::RichText::new(crate::i18n::tr(&app.ui.language, "discord.gg/artcraft — help, feedback and show-and-tell"))
                    .size(11.0)
                    .color(t.text_dim),
            ));''', '            // No Discord button here: the upstream community is in the Help menu.'),
    ('crates/ui-egui/src/about.rs', '[("DesignCraft page", "appPage"), ("GitHub", "github"), ("getartcraft.com", "website"), ("Report an issue", "issues")]',
     '[("DesignCraft page", "appPage"), ("GitHub", "github"), ("studio.creative.ps", "website"), ("Report an issue", "issues")]'),
    ('crates/ui-egui/src/about.rs', 'let url = format!("{}/apps/{slug}", links::WEBSITE);', 'let url = format!("https://{slug}.studio.creative.ps");'),
    ('crates/ui-egui/src/about.rs', '"Part of the ArtCraft suite of open creative tools."', '"Part of the Creative Studio suite of open creative tools."'),
    ('crates/ui-egui/src/about.rs', '"More ArtCraft apps"', '"More Creative Studio apps"'),
    # Top bar and start screen: no Discord button; the card introduces Creative Studio.
    ('crates/ui-egui/src/chrome.rs', '''                            // Always one click away: the ArtCraft community Discord.
                            if crate::about::discord_button(ui, "Discord", vec2(78.0, 22.0)) {
                                let _ = app.run("help.discord", json!({}));
                            }
''', '                            // No Discord button in the app bar: the Help menu has the upstream community.\n'),
    # Start screen: the Discord button on the right of the card.
    ('crates/ui-egui/src/chrome.rs', '''            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                if crate::about::discord_button(ui, crate::i18n::tr(&app.ui.language, "Join our Discord"), BUTTON) {
                    let _ = app.run("help.discord", json!({}));
                }
            });
''', '            // No Discord button on the start screen (the Help menu has the upstream community).\n'),
    ('crates/ui-egui/src/chrome.rs', '"Join the ArtCraft community"', '"Creative Studio"'),
    ('crates/ui-egui/src/chrome.rs', '"Get help, share your layouts and shape what we build next."', '"Part of the Creative Studio suite of open creative tools."'),
    ('crates/ui-egui/src/chrome.rs', '[("DesignCraft page", "help.appPage"), ("GitHub", "help.github"), ("getartcraft.com", "help.website")]',
     '[("DesignCraft page", "help.appPage"), ("GitHub", "help.github"), ("studio.creative.ps", "help.website")]'),
    # Help menu: Discord is upstream's community, labelled as such; the site is ours.
    ('crates/ui-egui/src/menus.rs', '"ArtCraft Website…"', '"Creative Studio Website…"'),
    ('crates/ui-egui/src/menus.rs', '"ArtCraft App Page…"', '"Creative Studio App Page…"'),
    ('crates/ui-egui/src/menus.rs', '"{} — opens https://getartcraft.com/apps/designcraft"', f'"{{}} — opens {APP_SITE}"'),
    ('crates/ui-egui/src/menus.rs', '"{} — opens https://github.com/storytold/designcraft"', f'"{{}} — opens {REPO}"'),
    ('crates/ui-egui/src/menus.rs', '"{} — opens https://getartcraft.com"', f'"{{}} — opens {SITE}"'),
    # Web page.
    ('apps/designcraft-web/index.html', '<title>DesignCraft</title>', f'<title>{NAME}</title>'),
    ('apps/designcraft-web/index.html', 'Loading DesignCraft&hellip;', f'Loading {NAME}&hellip;', 'ss-scene'),  # or the splash
    # Graphics help text links to the README, which is ours now.
    ('apps/designcraft/src/gpu.rs', 'https://github.com/storytold/designcraft/blob/main/README.md', f'{REPO}/blob/main/README.md'),
    # The command list in the engine: the app's own links.
    ('crates/engine/src/cmd/inspect.rs', '(ArtCraft Discord, website, DesignCraft page and repository)', '(upstream Discord, Creative Studio website, trteeb page and repository)'),
    # macOS bundle.
    ('packaging/macos/Info.plist.in', '<string>ai.storyteller.designcraft</string>', '<string>ps.creative.studio.trteeb</string>'),
]
# Text in string literals and catalogs, before the general rename.
LITERALS = [
    ('DesignCraft page', 'trteeb page'),
    ('Join the ArtCraft Discord', 'Upstream community on Discord'),
    ('ArtCraft', 'Creative Studio'),  # the suite's name (URLs are lowercase and untouched)
]
STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def rename(lit: str, name: str) -> str:
    for a, b in LITERALS:
        lit = lit.replace(a, b)
    if any(k in lit for k in KEEP):
        return lit
    return lit.replace('DesignCraft', name)


def apply_rules() -> list:
    changed = []
    for rel, a, b, *marker in RULES:
        p = ROOT / rel
        s = p.read_text(encoding='utf-8')
        if marker and marker[0] in s:
            continue
        renamed = STRING.sub(lambda m: rename(m.group(0), NAME), a)
        if a not in s and renamed in s:
            a = renamed  # the general rename got there first
        if a in s:
            if b and a in b and b in s:
                continue  # a is part of b and b is in: applied
            p.write_text(s.replace(a, b), encoding='utf-8')
            changed.append(rel)
            continue
        if b and (b in s or STRING.sub(lambda m: rename(m.group(0), NAME), b) in s):
            continue  # applied on an earlier run
        print(f'warning: {rel}: upstream text not found (did upstream change it?): {a[:70]!r}')
    about = ROOT / 'crates/ui-egui/src/about.rs'
    s = about.read_text(encoding='utf-8')
    o = re.sub(r'pub const SIBLINGS: &\[\(&str, &str, &str\)\] = &\[.*?\];', lambda m: SIBLINGS, s, count=1, flags=re.S)
    if o != s:
        about.write_text(o, encoding='utf-8')
        changed.append('crates/ui-egui/src/about.rs')
    return changed


def write_mark() -> bool:
    svg = LOGO.read_text(encoding='utf-8')
    _, _, w, h = (float(x) for x in re.search(r'viewBox="([^"]+)"', svg).group(1).split())
    fills = dict(re.findall(r'\.(cls-\d+)\s*\{\s*fill:\s*#([0-9a-fA-F]{6})', svg))
    rows = []
    for attrs in re.findall(r'<path\b([^>]*)>', svg):
        cls = re.search(r'class="(cls-\d+)"', attrs).group(1)
        d = re.search(r'\bd="([^"]+)"', attrs).group(1)
        c = fills[cls]
        rgb = ', '.join(str(int(c[i:i + 2], 16)) for i in (0, 2, 4))
        rows.append(f'    ("{d}", [{rgb}]),')
    out = ('//! Creative Studio: the trteeb star (docs/studio/trteeb.svg), generated by studio/rebrand.py.\n\n'
           f'/// The artwork size (its viewBox).\npub const SIZE: (f64, f64) = ({w}, {h});\n\n'
           '/// SVG path data and fill colour, painted in order.\npub const PATHS: &[(&str, [u8; 3])] = &[\n'
           + '\n'.join(rows) + '\n];\n')
    p = ROOT / 'crates/ui-egui/src/studio_mark.rs'
    # Compare as rustfmt would write it, so `cargo fmt` and this script agree.
    out = subprocess.run(['rustfmt', '--edition', '2024', '--emit', 'stdout', '--config-path', str(ROOT)], input=out, capture_output=True, text=True).stdout or out
    if p.exists() and p.read_text(encoding='utf-8') == out:
        return False
    p.write_text(out, encoding='utf-8')
    return True


# Files whose names are where user data lives on disk: never renamed (their tests pin the paths).
PERSISTED = {'apps/designcraft/src/profile.rs'}


def rename_literals() -> list:
    changed = []
    files = list((ROOT / 'crates/ui-egui').rglob('*.rs')) + list((ROOT / 'apps').rglob('*.rs'))
    for p in files:
        if p.relative_to(ROOT).as_posix() in PERSISTED:
            continue
        name = NAME_AR if p.name == 'ar.rs' else NAME
        s = p.read_text(encoding='utf-8')
        o = STRING.sub(lambda m: rename(m.group(0), name), s)
        if o != s:
            p.write_text(o, encoding='utf-8')
            changed.append(p.relative_to(ROOT).as_posix())
    plist = ROOT / 'packaging/macos/Info.plist.in'
    s = plist.read_text(encoding='utf-8')
    o = re.sub(r'(<key>CFBundle(?:Display|Executable)?Name</key>\s*<string>)DesignCraft(</string>)', rf'\g<1>{NAME}\2', s)
    o = o.replace('<string>DesignCraft Document</string>', f'<string>{NAME} Document</string>')
    if o != s:
        plist.write_text(o, encoding='utf-8')
        changed.append('packaging/macos/Info.plist.in')
    return changed


def main():
    changed = apply_rules()
    if write_mark():
        changed.append('crates/ui-egui/src/studio_mark.rs')
    changed += rename_literals()
    for c in sorted(set(changed)):
        print('rebranded', c)


# Creative Studio: the macOS app folder in the .dmg and the volume name carry our name
# (packaging/macos/package.sh). Bundle and binary names inside the package stay as upstream has them.
PACKAGING_NAMES = {
    'packaging/macos/package.sh': [
        ('DesignCraft.app', 'trteeb.app'),
        ('-volname "DesignCraft"', '-volname "trteeb"'),
        ('-hfs-volume-name "DesignCraft"', '-hfs-volume-name "trteeb"'),
    ],
}


def apply_packaging_names() -> list:
    changed = []
    for rel, pairs in PACKAGING_NAMES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    return changed


if __name__ == '__main__':
    main()
    for _p in apply_packaging_names():
        print('rebranded', _p.relative_to(ROOT))
