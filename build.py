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
PLAN_LOG = os.path.join(BASE, "plan-log.md")

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
    lines.append("var PROFILE = {")
    lines.append("  name: %s," % js_str(p["name"]))
    lines.append("  monogram: %s," % js_str(p["monogram"]))
    lines.append("  sub: %s," % js_str(p["sub"]))
    lines.append("  lead: %s" % js_str(p["lead"]))
    lines.append("};")
    lines.append("var CONTACT = {")
    lines.append("  email: %s," % js_str(c.get("email", "")))
    lines.append("  github: %s," % js_str(c.get("github", "")))
    lines.append("  douyin: %s" % js_str(c.get("douyin", "")))
    lines.append("};")
    lines.append("var ABOUT = {")
    lines.append("  desc: %s," % js_str(a["desc"]))
    lines.append("  paragraphs: [%s]," % ", ".join(js_str(x) for x in a["paragraphs"]))
    facts = ", ".join("{k:%s,v:%s}" % (js_str(f["k"]), js_str(f["v"])) for f in a.get("facts", []) or [])
    lines.append("  facts: [%s]" % facts)
    lines.append("};")
    pl = cfg.get("plan", {})
    lines.append("var PLAN = {")
    lines.append("  title: %s," % js_str(pl.get("title", "100天计划")))
    lines.append("  startDate: %s," % js_str(pl.get("startDate", "")))
    _habs = []
    for _h in pl.get("habits", [{"name": "早起", "target": ""}, {"name": "跑步", "target": ""}, {"name": "喝水", "target": ""}, {"name": "阅读", "target": ""}, {"name": "早睡", "target": ""}]):
        if isinstance(_h, str):
            _habs.append("{name:%s,target:%s}" % (js_str(_h), js_str("")))
        else:
            _habs.append("{name:%s,target:%s}" % (js_str(_h.get("name", "")), js_str(_h.get("target", ""))))
    lines.append("  habits: [%s]," % ", ".join(_habs))
    lines.append("  startWeight: %s," % (pl.get("startWeight", 150) or 150))
    lines.append("  targetWeight: %s," % (pl.get("targetWeight", 126) or 126))
    _wt = pl.get("weights", {}) or {}
    lines.append("  weights: {%s}," % ", ".join("%s:%s" % (k, v) for k, v in _wt.items()))
    _done = pl.get("done", {}) or {}
    _done_parts = []
    for _dk, _dv in _done.items():
        if isinstance(_dv, (list, tuple)):
            _done_parts.append("%s:[%s]" % (_dk, ", ".join(js_str(x) for x in _dv)))
        else:
            _done_parts.append("%s:true" % _dk)
    lines.append("  done: {%s}," % ", ".join(_done_parts))
    _rec = pl.get("records", {}) or {}
    _rec_parts = []
    for _rk, _rv in _rec.items():
        _inner = ", ".join("%s:%s" % (js_str(_h), js_str(_v)) for _h, _v in _rv.items())
        _rec_parts.append("%s:{%s}" % (_rk, _inner))
    lines.append("  records: {%s}" % ", ".join(_rec_parts))
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


def parse_plan_log(cfg):
    """从 plan-log.md 解析每天的完成标记(done)与体重(weights)，叠加到配置值之上。"""
    base = cfg.get("plan", {}) or {}
    done = dict(base.get("done", {}) or {})
    weights = dict(base.get("weights", {}) or {})
    records = {}
    habits = []
    for h in base.get("habits", []):
        if isinstance(h, str):
            habits.append(h)
        else:
            habits.append(h.get("name", ""))
    habits = [x for x in habits if x]
    if not os.path.exists(PLAN_LOG):
        return done, weights, records
    cur = None
    day_done = {}
    day_rec = {}
    CHECK = re.compile(r"[✅✓√xX]|完成")
    for ln in read_text(PLAN_LOG).splitlines():
        t = ln.strip()
        m = re.match(r"^#+\s*第\s*(\d+)\s*天", t)
        if m:
            cur = int(m.group(1)); continue
        if cur is None:
            continue
        wm = re.match(r"^[-*]?\s*体重\s*[:：]?\s*([\d.]+)", t)
        if wm:
            v = wm.group(1)
            weights[str(cur)] = float(v) if "." in v else int(v)
            continue
        for hname in habits:
            hm = re.match(r"^[-*]?\s*" + re.escape(hname) + r"\s*[:：]?\s*(.*)$", t)
            if hm:
                val = hm.group(1).strip()
                if not val:
                    break
                day_done.setdefault(cur, set()).add(hname)
                vclean = CHECK.sub("", val).strip().lstrip(":：").strip()
                if vclean:
                    day_rec.setdefault(cur, {})[hname] = vclean
                break
    allset = set(habits)
    for d, st in day_done.items():
        dl = sorted(st)
        if dl and allset and set(dl) == allset:
            done[str(d)] = True
        elif dl:
            done[str(d)] = dl
    for d, rec in day_rec.items():
        records[str(d)] = rec
    return done, weights, records


def main():
    if not os.path.exists(HTML):
        print("错误：找不到 index.html（请在项目根目录运行本脚本）。")
        return 1

    cfg = json.loads(read_text(CONFIG))

    # 用 plan-log.md 覆盖 plan.done / plan.weights / plan.records（每天在 Typora 里更新）
    d, w, r = parse_plan_log(cfg)
    _pl = dict(cfg.get("plan", {}) or {})
    _pl["done"] = d
    _pl["weights"] = w
    _pl["records"] = r
    cfg["plan"] = _pl

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

    # 同步浏览器标签页标题与 meta 描述
    name = cfg["profile"].get("name", "个人主页")
    new_html = re.sub(r"<title>.*?</title>", "<title>%s · 个人主页</title>" % html_escape(name), new_html, count=1, flags=re.S)
    new_html = re.sub(r'name="description" content="[^"]*"', 'name="description" content="%s 的个人简介与生活随笔"' % html_escape(name), new_html, count=1)

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(new_html)

    print("构建完成：已生成 %d 篇随笔，并更新 index.html。" % len(essays))
    for e in essays:
        print("  - %s  (%s / %s)" % (e["title"], e["date"], e["tag"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
