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


# trteeb saves documents as `.trteeb` (the same contents as upstream's `.designcraft`, which still
# opens), with its own document icon in Finder. Applied as is, without the general rename. Each
# (upstream text, our text) pair is skipped once our text is in the file.
EXT_FILES = {
    'crates/format/src/lib.rs': [
        ('/// The file name extension of a DesignCraft document.\npub const EXTENSION: &str = "designcraft";\n',
         '/// The file name extension of upstream DesignCraft documents: still opened.\n'
         'pub const EXTENSION: &str = "designcraft";\n'
         '/// The file name extension trteeb saves documents with (the same contents as `EXTENSION`).\n'
         'pub const STUDIO_EXTENSION: &str = "trteeb";\n\n'
         '/// Is `ext` (without the dot, any case) a document extension this app opens?\n'
         'pub fn is_native_ext(ext: &str) -> bool {\n'
         '    ext.eq_ignore_ascii_case(STUDIO_EXTENSION) || ext.eq_ignore_ascii_case(EXTENSION)\n'
         '}\n'),
    ],
    'crates/engine/src/cmd/file.rs': [
        ('/// `path` ending in `.designcraft`: the extension is added when it is missing or another one, so\n'
         '/// the file opens from the file manager. A path without a file name is left for the write to fail.\n'
         'pub fn with_document_extension(path: &str) -> String {\n'
         '    let p = std::path::Path::new(path);\n'
         '    let ext = p.extension().and_then(|e| e.to_str());\n'
         '    if p.file_name().is_none() || ext.is_some_and(|e| e.eq_ignore_ascii_case(designcraft_format::EXTENSION)) {\n'
         '        return path.to_string();\n'
         '    }\n'
         '    format!("{path}.{}", designcraft_format::EXTENSION)\n'
         '}',
         '/// `path` ending in `.trteeb`: the extension is added when it is missing or another one, so the\n'
         '/// file opens from the file manager. An old `.designcraft` name takes the new extension. A path\n'
         '/// without a file name is left for the write to fail.\n'
         'pub fn with_document_extension(path: &str) -> String {\n'
         '    let p = std::path::Path::new(path);\n'
         '    let ext = p.extension().and_then(|e| e.to_str());\n'
         '    if p.file_name().is_none() || ext.is_some_and(|e| e.eq_ignore_ascii_case(designcraft_format::STUDIO_EXTENSION)) {\n'
         '        return path.to_string();\n'
         '    }\n'
         '    if ext.is_some_and(|e| e.eq_ignore_ascii_case(designcraft_format::EXTENSION)) {\n'
         '        return p.with_extension(designcraft_format::STUDIO_EXTENSION).to_string_lossy().into_owned();\n'
         '    }\n'
         '    format!("{path}.{}", designcraft_format::STUDIO_EXTENSION)\n'
         '}'),
        ('if !native && ext != designcraft_format::EXTENSION {', 'if !native && !designcraft_format::is_native_ext(&ext) {'),
        ('without the .designcraft extension gets it', 'without the .trteeb extension gets it'),
    ],
    'crates/doc/src/vars.rs': [
        ('format!("{}.designcraft", self.title)', 'format!("{}.trteeb", self.title)'),
    ],
    'apps/designcraft/src/main.rs': [
        ('suggests (`Brochure.designcraft`)', 'suggests (`Brochure.trteeb`)'),
        ('if ext.eq_ignore_ascii_case("designcraft") {', 'if ext.eq_ignore_ascii_case("trteeb") {'),
        ('A document always ends in `.designcraft`', 'A document always ends in `.trteeb`'),
        ('OpenFilter { name: "trteeb, IDML or InDesign", extensions: &["designcraft", "idml", "indd", "indt"] },',
         'OpenFilter { name: "trteeb, IDML or InDesign", extensions: &["trteeb", "designcraft", "idml", "indd", "indt"] },'),
        ('OpenFilter { name: "trteeb", extensions: &["designcraft"] },', 'OpenFilter { name: "trteeb", extensions: &["trteeb", "designcraft"] },'),
        ('"idml",\n                    "designcraft",\n                    "mp4",', '"idml",\n                    "trteeb",\n                    "designcraft",\n                    "mp4",'),
        ('for ext in ["designcraft", "idml", "indd", "indt"] {', 'for ext in ["trteeb", "designcraft", "idml", "indd", "indt"] {'),
        ('"Untitled.designcraft"', '"Untitled.trteeb"'),
        ('PathBuf::from("/d/Brochure.designcraft")', 'PathBuf::from("/d/Brochure.trteeb")'),
        ('PathBuf::from("/d/Brochure.idml.designcraft")', 'PathBuf::from("/d/Brochure.idml.trteeb")'),
    ],
    'apps/designcraft-web/src/web.rs': [
        ('const DOC_EXTS: &[&str] = &["designcraft", "idml", "indd", "indt"];', 'const DOC_EXTS: &[&str] = &["trteeb", "designcraft", "idml", "indd", "indt"];'),
        ('"idml",\n    "designcraft",\n];', '"idml",\n    "trteeb",\n    "designcraft",\n];'),
    ],
    'apps/designcraft-web/src/graphics.rs': [
        ('format!("{}.designcraft", ', 'format!("{}.trteeb", '),
    ],
    'apps/designcraft-web/src/browser_policy.rs': [
        ('Some("designcraft") => designcraft_format::MIME,', 'Some("trteeb" | "designcraft") => designcraft_format::MIME,'),
    ],
    'apps/designcraft-cli/src/main.rs': [
        ('Some("designcraft") => Export::Document,', 'Some("trteeb" | "designcraft") => Export::Document,'),
    ],
    'packaging/macos/Info.plist.in': [
        ('<key>CFBundleTypeIconFile</key>\n      <string>DesignCraft</string>', '<key>CFBundleTypeIconFile</key>\n      <string>trteeb-document</string>'),
        ('<key>UTTypeIconFile</key>\n      <string>DesignCraft</string>', '<key>UTTypeIconFile</key>\n      <string>trteeb-document</string>'),
        ('<array><string>designcraft</string></array>', '<array><string>trteeb</string><string>designcraft</string></array>'),
        ('saving writes a .designcraft file', 'saving writes a .trteeb file'),
    ],
    'packaging/macos/package.sh': [
        ('cp "$ROOT/assets/app-icon/designcraft.icns" "$APP/Contents/Resources/DesignCraft.icns"\n',
         'cp "$ROOT/assets/app-icon/designcraft.icns" "$APP/Contents/Resources/DesignCraft.icns"\n'
         'cp "$ROOT/assets/app-icon/trteeb-document.icns" "$APP/Contents/Resources/trteeb-document.icns"\n'),
    ],
    'studio/CHANGES.md': [
        ('Crate names, settings folders and the file format keep their upstream names.',
         'Crate names and settings folders keep their upstream names. Documents save as `.trteeb` (`STUDIO_EXTENSION`\n'
         '  in `crates/format`); `.designcraft` files still open, and the file format itself is unchanged.'),
        ('- App icon: the trteeb star on navy (`assets/app-icon/`).',
         '- App icon: the trteeb star on navy (`assets/app-icon/`). Document icon for `.trteeb` files:\n'
         '  `assets/app-icon/trteeb-document.icns`, from `file icons/trteeb.svg`.'),
    ],
}
# Files this script creates (skipped when they exist).
EXT_NEW_FILES = {
    'crates/engine/tests/trteeb_extension.rs': '''//! trteeb saves documents as `.trteeb`, and upstream's `.designcraft` files still open.
//! Written by studio/rebrand.py.

use designcraft_engine::{Session, cmd};
use serde_json::json;

#[test]
fn save_writes_trteeb_and_designcraft_still_opens() {
    assert_eq!(cmd::with_document_extension("/d/Brochure"), "/d/Brochure.trteeb");
    assert_eq!(cmd::with_document_extension("/d/Brochure.designcraft"), "/d/Brochure.trteeb");

    let dir = std::env::temp_dir().join(format!("trteeb-extension-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let saved = dir.join("doc.trteeb");
    let mut session = Session::new();
    session.execute("file.new", &json!({})).unwrap();
    session.execute("file.saveAs", &json!({"path": saved.to_str().unwrap()})).unwrap();
    assert!(saved.exists(), "the save writes the .trteeb file");

    let old = dir.join("old.designcraft");
    std::fs::copy(&saved, &old).unwrap();
    let mut reopened = Session::new();
    reopened.execute("file.open", &json!({"path": old.to_str().unwrap()})).expect("a .designcraft file still opens");
    let _ = std::fs::remove_dir_all(&dir);
}
''',
}
# Icon and asset table: the document icon for .trteeb files, rendered from the file icon.
DOC_ICON_SVG = 'assets/app-icon/trteeb-document.svg'
DOC_ICON = 'assets/app-icon/trteeb-document.icns'
DOC_ICON_SOURCE = ROOT.parent / 'file icons/trteeb.svg'
ASSET_ROWS = [
    f'| `{DOC_ICON_SVG}` | Hamza Abu Ayyash (Creative Studio) | copy of `file icons/trteeb.svg` | MIT OR Apache-2.0 (`assets/app-icon/LICENSE.txt`) | Document icon for `.trteeb` files (see `assets/app-icon/README.md`) |',
    f'| `{DOC_ICON}` | Hamza Abu Ayyash (Creative Studio) | rendered from `{DOC_ICON_SVG}` with rsvg-convert, packed with iconutil by `studio/rebrand.py` | MIT OR Apache-2.0 (`assets/app-icon/LICENSE.txt`) | Document icon for `.trteeb` files (macOS document type; `packaging/macos/package.sh` copies it into the app) |',
]


def document_icon() -> list:
    import shutil
    import tempfile
    changed = []
    svg = ROOT / DOC_ICON_SVG
    if not svg.exists():
        if not DOC_ICON_SOURCE.exists():
            print(f'warning: {DOC_ICON_SOURCE} not found; no trteeb document icon')
            return changed
        svg.write_bytes(DOC_ICON_SOURCE.read_bytes())
        changed.append(svg)
    icns = ROOT / DOC_ICON
    if not icns.exists():
        if not (shutil.which('rsvg-convert') and shutil.which('iconutil')):
            print('warning: rsvg-convert or iconutil missing; trteeb-document.icns not made')
            return changed
        with tempfile.TemporaryDirectory() as tmp:
            iconset = Path(tmp) / 'trteeb-document.iconset'
            iconset.mkdir()
            for base in (16, 32, 128, 256, 512):
                for scale in (1, 2):
                    px = base * scale
                    name = f'icon_{base}x{base}' + ('@2x' if scale == 2 else '') + '.png'
                    subprocess.run(['rsvg-convert', '-w', str(px), '-h', str(px), str(svg), '-o', str(iconset / name)], check=True)
            subprocess.run(['iconutil', '-c', 'icns', '-o', str(icns), str(iconset)], check=True)
        changed.append(icns)
    assets = ROOT / 'ASSETS.md'
    text = assets.read_text(encoding='utf-8')
    if DOC_ICON_SVG not in text:
        lines = text.split('\n')
        at = next(i for i, l in enumerate(lines) if l.startswith('| `assets/app-icon/designcraft.svg` '))
        lines[at + 1:at + 1] = ASSET_ROWS
        assets.write_text('\n'.join(lines), encoding='utf-8')
        changed.append(assets)
    return changed


def apply_ext() -> list:
    changed = []
    for rel, pairs in EXT_FILES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            if b in out:
                continue  # applied on an earlier run
            if a not in out:
                print(f'warning: {rel}: text not found (did upstream change it?): {a[:70]!r}')
                continue
            out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    for rel, text in EXT_NEW_FILES.items():
        path = ROOT / rel
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
            changed.append(path)
    changed += document_icon()
    return changed


if __name__ == '__main__':
    main()
    for _p in apply_packaging_names():
        print('rebranded', _p.relative_to(ROOT))
    for _p in apply_ext():
        print('rebranded', _p.relative_to(ROOT))
