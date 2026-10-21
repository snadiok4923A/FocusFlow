"""FocusFlow: task and habit manager using SQLite. Python standard library only."""
import argparse
import csv
import sqlite3
from datetime import date, datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent / "focusflow.db"

def connect_db(path=DEFAULT_DB):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS tasks(
      id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
      priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high')),
      due_date TEXT, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','completed')),
      created_at TEXT NOT NULL, completed_at TEXT);
    CREATE TABLE IF NOT EXISTS habits(
      id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
      active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS habit_logs(
      id INTEGER PRIMARY KEY, habit_id INTEGER NOT NULL, log_date TEXT NOT NULL,
      note TEXT DEFAULT '', UNIQUE(habit_id,log_date),
      FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE);
    """)
    db.commit()
    return db

def add_task(db, title, description="", priority="medium", due_date=None):
    title = title.strip()
    if not title: raise ValueError("Task title cannot be empty.")
    if priority not in ("low","medium","high"): raise ValueError("Priority must be low, medium, or high.")
    if due_date: date.fromisoformat(due_date)
    cur = db.execute("INSERT INTO tasks(title,description,priority,due_date,created_at) VALUES(?,?,?,?,?)",
        (title,description.strip(),priority,due_date,datetime.now().isoformat(timespec="seconds")))
    db.commit()
    return cur.lastrowid

def list_tasks(db, status="all"):
    if status not in ("all","open","completed"): raise ValueError("Status must be all, open, or completed.")
    sql = "SELECT * FROM tasks"
    args = ()
    if status != "all": sql += " WHERE status=?"; args = (status,)
    sql += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, due_date, id"
    return db.execute(sql,args).fetchall()

def complete_task(db, task_id):
    cur = db.execute("UPDATE tasks SET status='completed',completed_at=? WHERE id=? AND status='open'",
        (datetime.now().isoformat(timespec="seconds"),task_id))
    db.commit()
    return cur.rowcount == 1

def delete_task(db, task_id):
    cur = db.execute("DELETE FROM tasks WHERE id=?",(task_id,))
    db.commit()
    return cur.rowcount == 1

def add_habit(db, name):
    name = name.strip()
    if not name: raise ValueError("Habit name cannot be empty.")
    cur = db.execute("INSERT INTO habits(name,created_at) VALUES(?,?)",
        (name,datetime.now().isoformat(timespec="seconds")))
    db.commit()
    return cur.lastrowid

def list_habits(db):
    return db.execute("SELECT * FROM habits WHERE active=1 ORDER BY name COLLATE NOCASE").fetchall()

def log_habit(db, habit_id, log_date=None, note=""):
    day = date.fromisoformat(log_date or date.today().isoformat()).isoformat()
    if not db.execute("SELECT id FROM habits WHERE id=? AND active=1",(habit_id,)).fetchone():
        raise ValueError("Active habit not found.")
    try:
        db.execute("INSERT INTO habit_logs(habit_id,log_date,note) VALUES(?,?,?)",(habit_id,day,note.strip()))
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("This habit is already logged for that date.") from exc

def habit_summary(db):
    result = []
    today = date.today()
    for habit in list_habits(db):
        dates = {date.fromisoformat(r["log_date"]) for r in db.execute(
            "SELECT log_date FROM habit_logs WHERE habit_id=?",(habit["id"],)).fetchall()}
        cursor = today if today in dates else date.fromordinal(today.toordinal()-1)
        streak = 0
        while cursor in dates:
            streak += 1
            cursor = date.fromordinal(cursor.toordinal()-1)
        result.append({"id":habit["id"],"name":habit["name"],"total":len(dates),
          "month":sum(d.year==today.year and d.month==today.month for d in dates),
          "streak":streak,"done_today":today in dates})
    return result

def dashboard(db):
    today = date.today().isoformat()
    tasks = db.execute("""SELECT
      SUM(status='open') open_tasks, SUM(status='completed') completed_tasks,
      SUM(status='completed' AND substr(completed_at,1,10)=?) completed_today
      FROM tasks""",(today,)).fetchone()
    overdue = db.execute("SELECT COUNT(*) n FROM tasks WHERE status='open' AND due_date<?",(today,)).fetchone()["n"]
    habits = db.execute("SELECT COUNT(*) n FROM habits WHERE active=1").fetchone()["n"]
    logged = db.execute("SELECT COUNT(*) n FROM habit_logs WHERE log_date=?",(today,)).fetchone()["n"]
    return {"open_tasks":tasks["open_tasks"] or 0,"completed_tasks":tasks["completed_tasks"] or 0,
      "completed_today":tasks["completed_today"] or 0,"overdue_tasks":overdue,
      "active_habits":habits,"habits_logged_today":logged}

def export_csv(db, output="tasks_export.csv"):
    rows = db.execute("SELECT id,title,description,priority,due_date,status,created_at,completed_at FROM tasks ORDER BY id").fetchall()
    path = Path(output)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=rows[0].keys() if rows else
          ["id","title","description","priority","due_date","status","created_at","completed_at"])
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])
    return len(rows)

def show_tasks(rows):
    if not rows: print("No tasks found."); return
    print(f"\n{'ID':<4} {'STATUS':<10} {'PRIORITY':<9} {'DUE':<12} TITLE")
    print("-"*72)
    for r in rows: print(f"{r['id']:<4} {r['status']:<10} {r['priority']:<9} {(r['due_date'] or '-'):<12} {r['title']}")

def menu(db):
    while True:
        print("\n====== FOCUSFLOW PRODUCTIVITY MANAGER ======")
        print("1 Add task  2 List tasks  3 Complete task  4 Delete task")
        print("5 Add habit  6 Habit summary  7 Log habit today")
        print("8 Dashboard  9 Export tasks to CSV  0 Exit")
        choice = input("Select: ").strip()
        try:
            if choice == "1":
                title=input("Title: "); desc=input("Description: ")
                priority=input("Priority low/medium/high [medium]: ").strip().lower() or "medium"
                due=input("Due date YYYY-MM-DD (optional): ").strip() or None
                print("Created task ID",add_task(db,title,desc,priority,due))
            elif choice == "2":
                status=input("all/open/completed [all]: ").strip().lower() or "all"
                show_tasks(list_tasks(db,status))
            elif choice == "3":
                print("Task completed." if complete_task(db,int(input("Task ID: "))) else "Open task not found.")
            elif choice == "4":
                print("Deleted." if delete_task(db,int(input("Task ID: "))) else "Task not found.")
            elif choice == "5":
                print("Created habit ID",add_habit(db,input("Habit name: ")))
            elif choice == "6":
                items=habit_summary(db)
                if not items: print("No habits yet.")
                for h in items:
                    print(f"#{h['id']} {h['name']} | streak {h['streak']} day(s) | this month {h['month']} | total {h['total']} | {'done today' if h['done_today'] else 'not logged today'}")
            elif choice == "7":
                for h in list_habits(db): print(f"#{h['id']} {h['name']}")
                log_habit(db,int(input("Habit ID: ")),note=input("Note (optional): "))
                print("Habit logged.")
            elif choice == "8":
                for key,value in dashboard(db).items(): print(f"{key.replace('_',' ').title()}: {value}")
            elif choice == "9":
                path=input("Output file [tasks_export.csv]: ").strip() or "tasks_export.csv"
                print(f"Exported {export_csv(db,path)} task(s) to {path}")
            elif choice == "0":
                print("Goodbye!"); return
            else: print("Choose a valid menu option.")
        except (ValueError,sqlite3.IntegrityError) as exc:
            print("Error:",exc)

def main():
    parser=argparse.ArgumentParser(description="FocusFlow productivity manager")
    parser.add_argument("--db",default=str(DEFAULT_DB),help="Path to SQLite database")
    args=parser.parse_args()
    db=connect_db(args.db)
    try: menu(db)
    finally: db.close()

if __name__ == "__main__": main()
