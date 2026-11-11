"""Prompts and validation for AI-generated quizzes and flashcards."""

MCQ, FLASH = "mcq", "flash"


def build_messages(kind, count, material):
    material = material.strip()[:6000]
    if kind == MCQ:
        task = (
            f"Create {count} multiple-choice questions from the material.\n"
            'Return JSON exactly like: {"questions":[{"q":"...","options":["...","...","...","..."],'
            '"answer":0,"explanation":"..."}]}\n'
            "Each question has exactly 4 options. 'answer' is the index (0 to 3) of the correct option."
        )
    else:
        task = (
            f"Create {count} flashcards from the material.\n"
            'Return JSON exactly like: {"cards":[{"front":"question or term","back":"answer or definition"}]}'
        )
    return [
        {"role": "system", "content": "You write study questions. Use ONLY the material given. "
                                      "Reply with valid JSON and nothing else."},
        {"role": "user", "content": f"{task}\n\nMATERIAL:\n{material}"},
    ]


def normalize(kind, obj):
    """Turn whatever the model returned into clean items, dropping broken ones."""
    items = obj if isinstance(obj, list) else obj.get("questions") or obj.get("cards") or []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if kind == MCQ:
            opts = [str(o).strip() for o in it.get("options", []) if str(o).strip()][:4]
            ans = it.get("answer", 0)
            if isinstance(ans, str):
                ans = "ABCD".find(ans.strip().upper()[:1]) if ans.strip()[:1].upper() in "ABCD" else int(ans) if ans.isdigit() else 0
            if it.get("q") and len(opts) >= 2 and isinstance(ans, int) and 0 <= ans < len(opts):
                out.append({"q": str(it["q"]).strip(), "options": opts, "answer": ans,
                            "explanation": str(it.get("explanation", "")).strip()})
        elif it.get("front") and it.get("back"):
            out.append({"front": str(it["front"]).strip(), "back": str(it["back"]).strip()})
    return out
