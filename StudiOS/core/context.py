"""Context injection: what the student is studying becomes the system prompt."""

MAX_NOTE_CHARS = 6000  # keeps small models inside their context window


def build_system_prompt(exam=None, course=None, subject=None, notes=()):
    lines = [
        "You are StudiOS, a patient study assistant running locally on the student's computer.",
        "Explain clearly, step by step, in simple language. Use short paragraphs.",
        "When study notes are provided, answer from them first. If the notes do not cover the "
        "question, say so, then answer from general knowledge and mark it as such.",
        "Never invent facts, formulas, or references. If unsure, say you are unsure.",
    ]
    if exam:
        lines.append(f"The student is preparing for: {exam}.")
    subject = subject or (course or {}).get("subject")
    if subject:
        lines.append(f"Current subject: {subject}.")
    if course and course.get("title"):
        plat = f" ({course['platform']})" if course.get("platform") else ""
        lines.append(f"Current course: {course['title']}{plat}.")
        if course.get("description"):
            lines.append(f"Course description: {course['description']}")
    if notes:
        budget, blocks = MAX_NOTE_CHARS, []
        for n in notes:
            if budget <= 0:
                break
            body = n.get("body", "")[:budget]
            budget -= len(body)
            blocks.append(f"### {n.get('title', 'Note')}\n{body}")
        lines += ["", "Student's notes:", "\n\n".join(blocks)]
    return "\n".join(lines)
