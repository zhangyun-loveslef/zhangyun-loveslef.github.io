# -*- coding: utf-8 -*-
"""
build.py —— 从 site-config.json 与 essays/*.md 重新生成 index.html 里的网站数据。

用法：
    python build.py
或直接双击 build.bat。

原理：读取配置文件与随笔 Markdown，生成一段 JS（PROFILE / CONTACT / ABOUT / ESSAYS），
替换 index.html 中 SITE-DATA-START 与 SITE-DATA-END 之间的内容，其余页面结构不动。
"""
import json, os, re, glob

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "index.html")
CONFIG = os.path.join(BASE, "site-config.json")
ESSAYS_DIR = os.path.join(BASE, "essays")

START = "/* ===== SITE-DATA-START ===== */"
END = "/* ===== SITE-DATA-END ===== */"


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def js_str(s):
    """把 Python 字符串转成安全的 JS 双引号字符串字面量。"""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\r", "").replace("\n", "\\n").replace("\t", "\\t")
    return '"' + s + '"'


def html_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def is_image_line(p):
    return bool(re.match(r"^!\[[^\]]*\]\([^)]+\)\s*$", p))


def inline(text):
    """把段落里的 Markdown 行内语法（图片/链接/加粗/斜体）转成 HTML。"""
    def img(m):
        alt = html_escape(m.group(1))
        src = html_escape(m.group(2))
        return '<img src="%s" alt="%s" loading="lazy">' % (src, alt)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img, text)

    def lnk(m):
        t = inline(m.group(1))
        u = html_escape(m.group(2))
        return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (u, t)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lnk, text)

    text = html_escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    return text


def render_block(p):
    """把一段文字转成 HTML 块：独占一行的图片渲染成 <figure>，其余为 <p>。"""
    if is_image_line(p):
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", p)
        alt = html_escape(m.group(1))
        src = html_escape(m.group(2))
        cap = ("<figcaption>%s</figcaption>" % alt) if alt else ""
        return '<figure class="essay-fig"><img src="%s" alt="%s" loading="lazy">%s</figure>' % (src, alt, cap)
    return "<p>" + inline(p) + "</p>"


def parse_md(path):
    text = read_text(path)
    meta = {}
    body = text

    if text.lstrip().startswith("---"):
        # 拆开第一对 --- 之间的 front matter
        first = text.index("---")
        second = text.index("---", first + 3)
        fm = text[first + 3:second]
        body = text[second + 3:]
        for line in fm.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]

    title = meta.get("title", os.path.splitext(os.path.basename(path))[0])
    excerpt = meta.get("excerpt", "")
    if not excerpt:
        for p in paragraphs:
            if not is_image_line(p):
                excerpt = p[:60] + ("…" if len(p) > 60 else "")
                break

    return {
        "title": title,
        "date": meta.get("date", ""),
        "tag": meta.get("tag", "随笔"),
        "excerpt": excerpt,
        "content": [render_block(p) for p in paragraphs],
    }


def build_data(cfg, essays):
    p = cfg["profile"]
    c = cfg["contact"]
    a = cfg["about"]

    lines = []
    lines.append("/* 以下数据由 build.py 从 essays/*.md 与 site-config.json 自动生成，请勿手动修改 */")
    lines.append("var PROFILE = {")
    lines.append("  name: %s," % js_str(p["name"]))
    lines.append("  monogram: %s," % js_str(p["monogram"]))
    lines.append("  sub: %s," % js_str(p["sub"]))
    lines.append("  lead: %s" % js_str(p["lead"]))
    lines.append("};")
    lines.append("var CONTACT = {")
    lines.append("  email: %s," % js_str(c.get("email", "")))
    lines.append("  github: %s," % js_str(c.get("github", "")))
    lines.append("  site: %s" % js_str(c.get("site", "")))
    lines.append("};")
    lines.append("var ABOUT = {")
    lines.append("  desc: %s," % js_str(a["desc"]))
    lines.append("  paragraphs: [%s]," % ", ".join(js_str(x) for x in a["paragraphs"]))
    facts = ", ".join("{k:%s,v:%s}" % (js_str(f["k"]), js_str(f["v"])) for f in a["facts"])
    lines.append("  facts: [%s]" % facts)
    lines.append("};")
    lines.append("var ESSAYS = [")
    for i, e in enumerate(essays):
        lines.append("  {")
        lines.append("    title: %s," % js_str(e["title"]))
        lines.append("    date: %s," % js_str(e["date"]))
        lines.append("    tag: %s," % js_str(e["tag"]))
        lines.append("    excerpt: %s," % js_str(e["excerpt"]))
        lines.append("    content: [%s]" % ", ".join(js_str(x) for x in e["content"]))
        lines.append("  }%s" % ("," if i < len(essays) - 1 else ""))
    lines.append("];")
    return "\n".join(lines)


def main():
    if not os.path.exists(HTML):
        print("错误：找不到 index.html（请在项目根目录运行本脚本）。")
        return 1

    cfg = json.loads(read_text(CONFIG))

    md_files = sorted(glob.glob(os.path.join(ESSAYS_DIR, "*.md")))
    essays = [parse_md(f) for f in md_files]
    essays.sort(key=lambda e: e["date"], reverse=True)  # 新的在前

    data = build_data(cfg, essays)

    html = read_text(HTML)
    if START not in html or END not in html:
        print("错误：index.html 中未找到 SITE-DATA 标记，请确认未改动模板。")
        return 1

    head = html.split(START, 1)[0]
    tail = html.split(END, 1)[1]
    new_html = head + START + "\n" + data + "\n" + END + tail

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(new_html)

    print("构建完成：已生成 %d 篇随笔，并更新 index.html。" % len(essays))
    for e in essays:
        print("  - %s  (%s / %s)" % (e["title"], e["date"], e["tag"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
