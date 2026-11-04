"""data/*.json sınav dosyalarından statik HTML sayfaları üretir.

Kullanım:  python build.py
Çıktı:     index.html ve exams/<id>.html
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "exams"

COURSES = {
    "ES 411": "İş Sağlığı ve Güvenliği I",
    "ES 412": "İş Sağlığı ve Güvenliği II",
}

SOURCE_LABEL = {
    "marked": "Kâğıtta/ekranda işaretli cevap",
    "key": "Öğrenci cevap listesine göre",
    "solved": "Çözüm (kaynakta işaret yok, doğrulanmamış)",
    "disputed": "İşaretli cevapla çelişiyor, gözden geçirin",
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def para(s):
    return "<br>".join(esc(line) for line in str(s or "").split("\n"))


def load_exams():
    exams = []
    for p in sorted(DATA.glob("*.json")):
        exam = json.loads(p.read_text(encoding="utf-8"))
        exam.setdefault("id", p.stem)
        exams.append(exam)
    return exams


def page(title, body, depth):
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
{body}
<script src="{prefix}assets/quiz.js"></script>
</body>
</html>
"""


def render_question(exam_id, q):
    n = q["n"]
    parts = [f'<article class="q" id="q{n}" data-answer="{esc(q.get("answer") or "")}">']
    parts.append(f'<h3><span class="qn">{n}.</span> {para(q.get("text"))}</h3>')
    if q.get("list"):
        parts.append("<ul class=\"stmts\">" + "".join(f"<li>{para(s)}</li>" for s in q["list"]) + "</ul>")
    if q.get("table"):
        rows = q["table"]
        head = "".join(f"<th>{para(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{para(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
        parts.append(f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
    if q.get("image"):
        parts.append(f'<figure><img src="../{esc(q["image"])}" alt="Soru {n} görseli" loading="lazy"></figure>')
    parts.append('<div class="opts">')
    for o in q.get("options", []):
        k = str(o["k"]).upper()
        parts.append(
            f'<label class="opt" data-k="{esc(k)}"><input type="checkbox" name="{esc(exam_id)}-q{n}" value="{esc(k)}">'
            f'<span class="k">{esc(k)})</span> <span class="t">{para(o.get("t"))}</span></label>'
        )
    parts.append("</div>")

    ans = q.get("answer")
    src = q.get("answerSource")
    note = []
    if ans:
        note.append(f"<b>Doğru cevap: {esc(ans)}</b>")
    else:
        note.append("<b>Cevap belirlenemedi.</b>")
    if src in SOURCE_LABEL:
        note.append(SOURCE_LABEL[src])
    if src == "disputed" and q.get("marked"):
        note.append(f"kâğıtta {esc(q['marked'])} işaretli")
    if q.get("confidence") == "low":
        note.append("emin değiliz")
    if q.get("remark"):
        note.append(esc(q["remark"]))
    parts.append(f'<p class="feedback" hidden>{" · ".join(note)}</p>')
    parts.append("</article>")
    return "\n".join(parts)


def render_exam(exam):
    eid = exam["id"]
    course = exam.get("course", "")
    title = f'{course} {exam.get("type", "")} – {exam.get("date", "")}'
    items = []
    questions = []
    for it in exam.get("items", []):
        if "passage" in it:
            items.append(f'<div class="passage">{para(it["passage"])}</div>')
        else:
            questions.append(it)
            items.append(render_question(eid, it))

    notes = list(exam.get("notes", []))
    for m in exam.get("missing", []):
        rng = f'{m["from"]}–{m["to"]}' if m["from"] != m["to"] else str(m["from"])
        notes.append(f'Soru {rng} kaynaklarda yok. {m.get("note", "")}'.strip())
    notes_html = "".join(f"<li>{esc(x)}</li>" for x in notes)

    key_rows = []
    for q in questions:
        flag = ""
        if q.get("answerSource") in ("solved", "disputed") or q.get("confidence") == "low":
            flag = ' <span class="flag" title="Doğrulanmamış">*</span>'
        key_rows.append(f'<li><a href="#q{q["n"]}">{q["n"]}</a> <b>{esc(q.get("answer") or "?")}</b>{flag}</li>')

    body = f"""<header class="top">
  <a class="back" href="../index.html">← Tüm sınavlar</a>
  <h1>{esc(title)}</h1>
  <p class="sub">{esc(exam.get("courseName") or COURSES.get(course, ""))}{" · Online sınav" if exam.get("format") == "online" else ""}</p>
</header>
<main>
  <section class="meta">
    {f'<p class="hdr">{esc(exam["header"])}</p>' if exam.get("header") else ""}
    {f'<p class="ins">{para(exam["instructions"])}</p>' if exam.get("instructions") else ""}
    {f'<ul class="notes">{notes_html}</ul>' if notes_html else ""}
    <p class="how">Bir şıkkı işaretlediğinizde doğru cevap görünür. Seçiminiz bu tarayıcıda saklanır.</p>
  </section>
  <div class="bar" data-exam="{esc(eid)}">
    <span class="score">0 / {len(questions)} cevaplandı</span>
    <button type="button" class="show-all">Tüm cevapları göster</button>
    <button type="button" class="reset">Sıfırla</button>
  </div>
  {"".join(items)}
  <section class="key">
    <details>
      <summary>Cevap anahtarı</summary>
      <ol class="keylist">{"".join(key_rows)}</ol>
      <p class="legend"><span class="flag">*</span> Kaynakta işaret yok ya da işaretli cevapla çelişiyor; cevap tarafımızca çözüldü, doğrulanmamıştır.</p>
    </details>
  </section>
</main>"""
    return title, page(title, body, 1)


def card(exam):
    qs = sum(1 for it in exam.get("items", []) if "passage" not in it)
    missing = sum(m["to"] - m["from"] + 1 for m in exam.get("missing", []))
    extra = f" · {missing} soru eksik" if missing else ""
    m = re.search(r"examid=(\d+)", exam.get("header", ""))
    tag = f" (sınav no {m.group(1)})" if m else ""
    return (
        f'<li><a href="exams/{esc(exam["id"])}.html"><span class="ct">{esc(exam.get("type", ""))} – {esc(exam.get("date", ""))}{tag}</span>'
        f'<span class="cm">{qs} soru{extra}</span></a></li>'
    )


def render_index(exams):
    def key(e):
        return e.get("sortKey", "0000")

    sections = []
    for course, name in COURSES.items():
        for fmt, label in (("paper", "Kâğıt sınavlar"), ("online", "Online sınavlar")):
            group = sorted((e for e in exams if e.get("course") == course and e.get("format") == fmt), key=key, reverse=True)
            if group:
                sections.append(f'<section><h2>{esc(course)} · {esc(name)} <small>{label}</small></h2><ul class="cards">{"".join(card(e) for e in group)}</ul></section>')
    body = f"""<header class="top">
  <h1>İSG Çıkmış Sorular</h1>
  <p class="sub">ES 411 / ES 412 Occupational Health and Safety. Her sınav ayrı sayfada, sonunda cevap anahtarıyla.</p>
</header>
<main>
{"".join(sections)}
<p class="legend">Sorular öğrencilerin paylaştığı fotoğraflardan yazıya geçirildi. Cevap anahtarlarında <span class="flag">*</span> ile işaretli cevaplar doğrulanmamıştır. Hata görürseniz <code>data/</code> klasöründeki JSON dosyasını düzeltip <code>python build.py</code> çalıştırın.</p>
</main>"""
    return page("İSG Çıkmış Sorular", body, 0)


def main():
    exams = load_exams()
    OUT.mkdir(exist_ok=True)
    for exam in exams:
        _, doc = render_exam(exam)
        (OUT / f'{exam["id"]}.html').write_text(doc, encoding="utf-8")
    (ROOT / "index.html").write_text(render_index(exams), encoding="utf-8")
    print(f"{len(exams)} sınav üretildi.")


if __name__ == "__main__":
    main()
