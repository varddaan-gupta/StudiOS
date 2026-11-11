"""Simple, verifiable progress numbers. No predictions."""
from datetime import date, timedelta


def last_days(db, n=7):
    sessions = db.list("sessions")
    out = []
    for i in range(n - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        mins = sum(s.get("minutes", 0) for s in sessions if s.get("date") == d.isoformat())
        out.append((d.strftime("%a"), mins))
    return out


def minutes_today(db):
    return last_days(db, 1)[0][1]


def streak(db):
    days = {s["date"] for s in db.list("sessions") if s.get("minutes", 0) > 0}
    d, n = date.today(), 0
    if d.isoformat() not in days:  # today not studied yet should not break the streak
        d -= timedelta(days=1)
    while d.isoformat() in days:
        n += 1
        d -= timedelta(days=1)
    return n


def tasks_done(db):
    tasks = db.list("tasks")
    return sum(1 for t in tasks if t.get("done")), len(tasks)


def quiz_average(db):
    res = [r for r in db.list("results") if r.get("total")]
    if not res:
        return None
    return round(sum(r["score"] / r["total"] for r in res) / len(res) * 100)
