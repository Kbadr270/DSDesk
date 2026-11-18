#!/usr/bin/env python3
"""
Apply company branding to a RustDesk source tree.

Run from the repository root (after the submodules are checked out):

    python3 brand/apply_brand.py

Settings come from brand/brand.json. The server address and public key can be
supplied through the environment (BRAND_SERVER, BRAND_KEY) so they never have
to be written into the repository. Every patch is checked: if the upstream
code no longer looks the way this script expects, it stops with an error
instead of silently producing an unbranded build.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path.cwd()
BRAND_DIR = pathlib.Path(__file__).resolve().parent
ASSETS = BRAND_DIR / "assets"


def die(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read(rel):
    path = ROOT / rel
    if not path.is_file():
        die(f"file not found: {rel} (are the submodules checked out?)")
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(rel, text):
    with open(ROOT / rel, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def patch_regex(rel, pattern, repl, expected=1, flags=0):
    """Replace regex matches; the number of matches must equal `expected`."""
    text = read(rel)
    new_text, count = re.subn(pattern, repl, text, flags=flags)
    if count != expected:
        die(f"{rel}: expected {expected} match(es) for {pattern!r}, found {count}")
    write(rel, new_text)
    print(f"patched {rel} ({count})")


def patch_literal(rel, old, new, expected=1):
    text = read(rel)
    if "\r\n" in text:  # Windows runners check files out with CRLF
        old = old.replace("\r\n", "\n").replace("\n", "\r\n")
        new = new.replace("\r\n", "\n").replace("\n", "\r\n")
    count = text.count(old)
    if count != expected:
        die(f"{rel}: expected {expected} occurrence(s) of {old!r}, found {count}")
    write(rel, text.replace(old, new))
    print(f"patched {rel} ({count})")


# ---------------------------------------------------------------- settings
with open(BRAND_DIR / "brand.json", encoding="utf-8") as f:
    cfg = json.load(f)

mode = (os.environ.get("BRAND_MODE") or cfg.get("mode", "support")).strip()
if mode not in ("support", "customer"):
    die("BRAND_MODE must be support or customer")
app_name = cfg.get("app_name", "").strip()
if mode == "customer":
    app_name = cfg.get("customer_app_name", "").strip() or app_name
company = cfg.get("company_name", "").strip()
copyright_text = cfg.get("copyright", "").strip()
description = cfg.get("description", "Remote Support").strip()
website = cfg.get("website", "").strip()
privacy_url = cfg.get("privacy_url", "").strip()
ticket_url = cfg.get("ticket_url", "").strip()
company_fa = cfg.get("company_name_fa", "").strip()
description_fa = cfg.get("description_fa", "").strip()
description_en = cfg.get("description_en", "").strip()
app_version = cfg.get("app_version", "1.0.0").strip()
update_url = cfg.get("update_url", "").strip()
developer = cfg.get("developer", "").strip()
developer_email = cfg.get("developer_email", "").strip()
server = (os.environ.get("BRAND_SERVER") or cfg.get("server", "")).strip()
key = (os.environ.get("BRAND_KEY") or cfg.get("key", "")).strip()

if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,30}", app_name):
    die("app_name must be 2-31 ASCII letters/digits/_/- and start with a letter "
        "(it is used for folder, service and registry names)")
if app_name.lower() == "rustdesk":
    die("choose an app_name different from RustDesk")
if not server or re.search(r"[\s/\"'\\:]", server):
    die("server is missing or invalid: use only the host name or IP, "
        "with no port, scheme or spaces (set the RENDEZVOUS_SERVER secret)")
if not re.fullmatch(r"[A-Za-z0-9+/]{42,44}={0,2}", key):
    die("key is missing or is not a valid public key "
        "(set the RS_PUB_KEY secret to the content of id_ed25519.pub)")
for name, value in (("company_name", company), ("copyright", copyright_text),
                    ("website", website), ("privacy_url", privacy_url)):
    if not value:
        die(f"{name} is empty in brand.json")
    if '"' in value or "\\" in value or "'" in value or "$" in value or "\n" in value:
        die(f"{name} must not contain quotes, backslashes, $ or line breaks")
for name, value in (("website", website), ("privacy_url", privacy_url),
                    ("ticket_url", ticket_url)):
    if not value.startswith(("https://", "http://")):
        die(f"{name} must start with http:// or https://")
for name, value in (("company_name_fa", company_fa),
                    ("description_fa", description_fa),
                    ("description_en", description_en)):
    if not value:
        die(f"{name} is empty in brand.json")
    if any(c in value for c in "'\"\\$\n"):
        die(f"{name} must not contain quotes, backslashes, $ or line breaks")


if not re.fullmatch(r"[0-9]+(\.[0-9]+){1,3}", app_version):
    die("app_version must look like 1.0.0")
if update_url and not update_url.startswith(("https://", "http://")):
    die("update_url must be empty or start with http:// or https://")
for name, value in (("update_url", update_url), ("developer", developer),
                    ("developer_email", developer_email)):
    if any(c in value for c in "'\"\\$\n"):
        die(f"{name} must not contain quotes, backslashes, $ or line breaks")


def ascii_only(value):
    return value.encode("ascii", "ignore").decode("ascii")


# --------------------------------------------- 1. server, key and app name
cfg_rs = "libs/hbb_common/src/config.rs"
patch_regex(cfg_rs,
            r'(pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[)"[^"]*"(\];)',
            lambda m: f'{m.group(1)}"{server}"{m.group(2)}')
patch_regex(cfg_rs,
            r'(pub const RS_PUB_KEY: &str = )"[^"]*";',
            lambda m: f'{m.group(1)}"{key}";')
patch_regex(cfg_rs,
            r'(pub static ref APP_NAME: RwLock<String> = RwLock::new\()"RustDesk"(\.to_owned\(\)\);)',
            lambda m: f'{m.group(1)}"{app_name}"{m.group(2)}')

# ---------------- 1b. customer build: incoming only (no outgoing connections)
if mode == "customer":
    patch_regex(cfg_rs,
                r'(pub fn is_incoming_only\(\) -> bool \{)\s*HARD_SETTINGS\s*\.read\(\)\s*\.unwrap\(\)\s*\.get\("conn-type"\)\s*\.map_or\(false, \|x\| x == \("incoming"\)\)\s*\}',
                lambda m: m.group(1) + " true }", flags=re.S)
    for fn, opt in (("is_disable_ab", "disable-ab"),
                    ("is_disable_account", "disable-account")):
        patch_literal(cfg_rs,
                      f'pub fn {fn}() -> bool {{\n    is_some_hard_opton("{opt}")\n}}',
                      f'pub fn {fn}() -> bool {{\n    true\n}}')
    patch_regex("src/common.rs",
                r'(pub fn get_builtin_option\(key: &str\) -> String \{)(\r?\n)',
                lambda m: (m.group(1) + m.group(2) +
                           '    if ["disable-change-id", "hide-help-cards", '
                           '"hide-network-settings", "hide-server-settings", '
                           '"hide-proxy-settings", "hide-websocket-settings", '
                           '"hide-remote-printer-settings"].contains(&key) {' + m.group(2) +
                           '        return "Y".to_owned();' + m.group(2) + '    }' + m.group(2)))
    print("customer mode: incoming-only, network/server settings hidden")

# ----------------------------------------- 2. Windows file properties (.rc)
rc = "flutter/windows/runner/Runner.rc"
rc_company = ascii_only(company)
rc_copyright = ascii_only(copyright_text)
rc_desc = ascii_only(f"{app_name} {description}")
patch_regex(rc, r'(VALUE "CompanyName", )"[^"]*"( "\\0")',
            lambda m: f'{m.group(1)}"{rc_company}"{m.group(2)}')
patch_regex(rc, r'(VALUE "FileDescription", )"[^"]*"( "\\0")',
            lambda m: f'{m.group(1)}"{rc_desc}"{m.group(2)}')
patch_regex(rc, r'(VALUE "LegalCopyright", )"[^"]*"( "\\0")',
            lambda m: f'{m.group(1)}"{rc_copyright}"{m.group(2)}')
patch_regex(rc, r'(VALUE "ProductName", )"[^"]*"( "\\0")',
            lambda m: f'{m.group(1)}"{app_name}"{m.group(2)}')

# ---------------------------------------------------- 3. Windows runner name
patch_literal("flutter/windows/runner/main.cpp",
              'std::wstring app_name = L"RustDesk";',
              f'std::wstring app_name = L"{app_name}";')

# ------------------------------------------- 4. About page (links, company)
about = "flutter/lib/desktop/pages/desktop_setting_page.dart"
patch_literal(about, "launchUrlString('https://rustdesk.com/privacy.html')",
              f"launchUrlString('{privacy_url}')")
patch_literal(about, "launchUrlString('https://rustdesk.com')",
              f"launchUrlString('{website}')")
patch_literal(about, "Purslane Tech Pte. Ltd.", company)

# --------------------------------- 5. never offer upstream RustDesk updates
patch_regex("src/common.rs",
            r"pub fn check_software_update\(\) \{(\r?\n)",
            lambda m: ("pub fn check_software_update() {" + m.group(1) +
                       "    if true {" + m.group(1) +
                       "        return; // branded build: no upstream update prompts" + m.group(1) +
                       "    }" + m.group(1)))

# ------------------------------------- 6. product name in translated texts
# Only the displayed value is changed, never the lookup key.
entry = re.compile(
    r'^(?P<head>\s*\(\s*"(?P<key>(?:[^"\\]|\\.)*)"\s*,\s*")'
    r'(?P<val>(?:[^"\\]|\\.)*)'
    r'(?P<tail>"\s*\)\s*,.*)$')
word = re.compile(r"\bRustDesk\b")
changed_files = 0
for path in sorted((ROOT / "src" / "lang").glob("*.rs")):
    if path.name in ("mod.rs", "template.rs"):
        continue
    out, touched = [], False
    with open(path, encoding="utf-8", newline="") as f:
        lines = f.read().split("\n")
    for line in lines:
        m = entry.match(line)
        if m:
            val = m.group("val")
            if val == "" and word.search(m.group("key")) and path.name == "en.rs":
                val = m.group("key")  # English falls back to the key itself
            new_val = word.sub(app_name, val)
            if new_val != m.group("val"):
                line = m.group("head") + new_val + m.group("tail")
                touched = True
        out.append(line)
    if touched:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("\n".join(out))
        changed_files += 1
print(f"patched translation files: {changed_files}")

# ------------------ 6a. "Powered by" caption under the logo opens our site
patch_literal("flutter/lib/common.dart",
              "launchUrl(Uri.parse('https://rustdesk.com'));",
              f"launchUrl(Uri.parse('{website}'));")

# ------------------------------------------- 6b. brand colour (both builds)
patch_regex("flutter/lib/common.dart",
            r"static const Color accent = Color\(0xFF0071FF\);",
            "static const Color accent = Color(0xFFF39F1F);")
patch_regex("flutter/lib/common.dart",
            r"static const Color accent50 = Color\(0x770071FF\);",
            "static const Color accent50 = Color(0x77F39F1F);")
patch_regex("flutter/lib/common.dart",
            r"static const Color accent80 = Color\(0xAA0071FF\);",
            "static const Color accent80 = Color(0xAAF39F1F);")

# ----------------------------- 6c. branded widgets (both builds) + footer
tpl = (BRAND_DIR / "dart" / "brand_footer.dart").read_text(encoding="utf-8")
for token, value in (("@@SITE@@", website), ("@@TICKET@@", ticket_url),
                     ("@@COMPANY_FA@@", company_fa), ("@@COMPANY_EN@@", company),
                     ("@@DESC_FA@@", description_fa), ("@@DESC_EN@@", description_en),
                     ("@@COPYRIGHT@@", copyright_text),
                     ("@@APP_VERSION@@", app_version),
                     ("@@DEVELOPER@@", developer), ("@@DEV_EMAIL@@", developer_email),
                     ("@@UPDATE_URL@@", update_url)):
    if token not in tpl:
        die(f"brand_footer.dart lacks {token}")
    tpl = tpl.replace(token, value)
dst = ROOT / "flutter/lib/desktop/widgets/brand_footer.dart"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(tpl, encoding="utf-8", newline="")


def add_import(rel, line):
    text = read(rel)
    nl = "\r\n" if "\r\n" in text else "\n"
    new_text, count = re.subn(r"^import ", line + nl + "import ", text,
                              count=1, flags=re.M)
    if count != 1:
        die(f"{rel}: no import line found")
    write(rel, new_text)
    print(f"patched {rel} (import)")


# About page of the settings: own slogan (red company word), own version, colour
setting = "flutter/lib/desktop/pages/desktop_setting_page.dart"
add_import(setting, "import 'package:flutter_hbb/desktop/widgets/brand_footer.dart';")
patch_regex(setting,
            r"Text\(\s*translate\('Slogan_tip'\),\s*style: TextStyle\(\s*fontWeight: FontWeight\.w800,\s*color: Colors\.white\),?\s*\)",
            "const BrandSlogan()")
patch_literal(setting, "final version = data['version'].toString();",
              "const version = brandVersion;")
patch_literal(setting, "decoration: const BoxDecoration(color: Color(0xFF2c8cff)),",
              "decoration: const BoxDecoration(color: Color(0xFF22263A)),")

if mode == "customer":
    home = "flutter/lib/desktop/pages/desktop_home_page.dart"
    patch_literal(home, "import '../widgets/button.dart';",
                  "import '../widgets/button.dart';\nimport '../widgets/brand_footer.dart';")
    patch_literal(home, "      if (!isOutgoingOnly) buildPasswordBoard(context),",
                  "      if (!isOutgoingOnly) buildPasswordBoard(context),\n"
                  "      if (isIncomingOnly) const BrandFooter(),")

# ------------------------------------------------------------- 7. icons/logo


def copy_file(src, dst_rel):
    dst = ROOT / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    print(f"copied {src.name} -> {dst_rel}")


def ensure_pillow():
    try:
        import PIL  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])


ico = ASSETS / "icon.ico"
if ico.is_file():
    for dst in ("res/icon.ico", "res/tray-icon.ico",
                "flutter/windows/runner/resources/app_icon.ico"):
        copy_file(ico, dst)
else:
    print("note: brand/assets/icon.ico not found, keeping the default icon")

icon_png = ASSETS / "icon.png"
if icon_png.is_file():
    ensure_pillow()
    from PIL import Image
    img = Image.open(icon_png).convert("RGBA")
    if img.width != img.height or img.width < 256:
        die("brand/assets/icon.png must be square and at least 256x256")
    copy_file(icon_png, "flutter/assets/icon.png")
    copy_file(icon_png, "res/icon.png")
    for size, name in ((32, "32x32.png"), (64, "64x64.png"),
                       (128, "128x128.png"), (256, "128x128@2x.png")):
        img.resize((size, size), Image.LANCZOS).save(ROOT / "res" / name)
        print(f"generated res/{name}")
else:
    print("note: brand/assets/icon.png not found, keeping the default picture")

logo = ASSETS / "logo.png"
if logo.is_file():
    copy_file(logo, "flutter/assets/logo.png")
    copy_file(ASSETS / "logo_light.png" if (ASSETS / "logo_light.png").is_file() else logo,
              "flutter/assets/logo_light.png")
    copy_file(ASSETS / "logo_dark.png" if (ASSETS / "logo_dark.png").is_file() else logo,
              "flutter/assets/logo_dark.png")
else:
    print("note: brand/assets/logo.png not found, no company logo added")

env_file = os.environ.get("GITHUB_ENV")
if env_file:
    with open(env_file, "a", encoding="utf-8") as f:
        f.write(f"BRAND_APP_NAME={app_name}\n")
print("branding applied")
