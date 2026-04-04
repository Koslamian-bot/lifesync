import json
import re
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────────────────
#  ANSI colour helpers  (pure terminal, no deps)
# ─────────────────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
WHITE  = "\033[97m"

def header(text):
    width = 58
    print(f"\n{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{CYAN}{'─' * width}{RESET}")

def info(text):   print(f"  {DIM}{WHITE}{text}{RESET}")
def ok(text):     print(f"  {GREEN}✓  {text}{RESET}")
def warn(text):   print(f"  {YELLOW}⚠  {text}{RESET}")
def error(text):  print(f"  {RED}✗  {text}{RESET}")
def ask(text):    return input(f"  {CYAN}▸{RESET} {text} ").strip()


# ─────────────────────────────────────────────────────────────────────────────
#  Input helpers
# ─────────────────────────────────────────────────────────────────────────────
def get_time(prompt, default=None):
    """Strict HH:MM 24-hour input.  Pass a default to show as hint."""
    hint = f" [{default}]" if default else ""
    while True:
        val = ask(f"{prompt}{hint}:")
        if default and val == "":
            return default
        if re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", val):
            return val
        error("Hmm, that doesn't look right. Try something like  07:30  or  22:00  (always HH:MM)")


def get_hours(prompt):
    """Accepts decimal hours like 1.5 -> returns float."""
    while True:
        val = ask(f"{prompt} (in hours — e.g. type  1  or  1.5  for 90 mins):")
        try:
            h = float(val)
            if h >= 0:
                return h
        except ValueError:
            pass
        error("Just type a number like  1  or  0.5  — no words needed!")


def get_int(prompt, min_val=0):
    while True:
        val = ask(f"{prompt}:")
        if val.isdigit() and int(val) >= min_val:
            return int(val)
        error(f"Please type a whole number like  1  or  2  (minimum: {min_val})")


def yes(prompt):
    while True:
        val = ask(f"{prompt} (Y/N)").lower()
        if val in ("y", "n"):
            return val == "y"
        error("Just type  Y  for yes  or  N  for no")


# ─────────────────────────────────────────────────────────────────────────────
#  Time arithmetic helpers
# ─────────────────────────────────────────────────────────────────────────────
FMT = "%H:%M"

def to_dt(t: str) -> datetime:
    return datetime.strptime(t, FMT)

def add_mins(t: str, mins: float) -> str:
    return (to_dt(t) + timedelta(minutes=mins)).strftime(FMT)

def sub_mins(t: str, mins: float) -> str:
    return (to_dt(t) - timedelta(minutes=mins)).strftime(FMT)

def mins_between(start: str, end: str) -> float:
    """Returns minutes from start → end (handles next-day end)."""
    s, e = to_dt(start), to_dt(end)
    if e <= s:
        e += timedelta(days=1)
    return (e - s).total_seconds() / 60

def fmt_window(start: str, end: str) -> str:
    return f"{start} → {end}"


def compute_free_slots(wake, sleep, work_start=None, work_end=None,
                       prep_mins=0, travel_mins=0):
    """
    Returns a list of free-time window strings.

    Logic:
      morning window  : wake  →  work_start − prep − travel
      evening window  : work_end + travel + 30min_unwind  →  sleep
    """
    if not work_start or not work_end:
        return [fmt_window(wake, sleep)]

    # Latest you can leave home to reach work on time
    latest_leave   = sub_mins(work_start, travel_mins)
    # Latest you can start prep to leave on time
    morning_cutoff = sub_mins(latest_leave, prep_mins)

    # Earliest usable evening time
    arrive_home    = add_mins(work_end, travel_mins)
    evening_start  = add_mins(arrive_home, 30)   # 30-min decompression buffer

    slots = []

    if mins_between(wake, morning_cutoff) > 0:
        slots.append(fmt_window(wake, morning_cutoff))

    if mins_between(evening_start, sleep) > 0:
        slots.append(fmt_window(evening_start, sleep))

    return slots if slots else ["(no free slots on this day)"]


# ─────────────────────────────────────────────────────────────────────────────
#  Main extractor class
# ─────────────────────────────────────────────────────────────────────────────
class LifeSyncEngine:

    def __init__(self):
        self.profile = {
            "commute": {},
            "weekly_schedule": {},
            "goals": [],
            "hobbies": [],
            "rigid_blocks": []
        }
        self.prep_mins   = 0
        self.travel_mins = 0

    # ── SECTION 1 : Anchors (work / college obligations) ─────────────────────
    def _collect_anchors(self):
        """
        Ask about fixed obligations first — these are the immovable rocks
        around which everything else is scheduled.
        """
        header("STEP 1 OF 5  —  School, Work or College")
        info("First things first — when do you HAVE to be somewhere?")
        info("This could be school, college, work, or any class you can't skip.")
        info("We'll plan everything else around these times.\n")

        schedule = {}

        uniform = yes("Do you go to school / work at the SAME time every Monday to Friday?")

        if uniform:
            work_start = get_time("What time does it START")
            work_end   = get_time("What time does it END")

            for day in ["monday","tuesday","wednesday","thursday","friday"]:
                schedule[day] = {
                    "has_obligation": True,
                    "work_start": work_start,
                    "work_end":   work_end
                }
        else:
            for day in ["monday","tuesday","wednesday","thursday","friday"]:
                print(f"\n  {BOLD}{day.capitalize()}{RESET}")
                has_work = yes(f"  Do you have school / work on {day.capitalize()}?")
                if has_work:
                    work_start = get_time("  What time does it START")
                    work_end   = get_time("  What time does it END")
                    schedule[day] = {
                        "has_obligation": True,
                        "work_start": work_start,
                        "work_end":   work_end
                    }
                else:
                    schedule[day] = {"has_obligation": False}

        # Weekends
        for day in ["saturday", "sunday"]:
            print(f"\n  {BOLD}{day.capitalize()}{RESET}")
            has_work = yes(f"  Do you have anything you MUST do on {day.capitalize()}? (class, job, etc.)")
            if has_work:
                work_start = get_time("  What time does it START")
                work_end   = get_time("  What time does it END")
                schedule[day] = {
                    "has_obligation": True,
                    "work_start": work_start,
                    "work_end":   work_end
                }
            else:
                schedule[day] = {"has_obligation": False}

        self._raw_schedule = schedule

    # ── SECTION 2 : Commute & Prep ───────────────────────────────────────────
    def _collect_commute(self):
        header("STEP 2 OF 5  —  Getting Ready & Getting There")
        info("How long does it take you to get ready in the morning?")
        info("(Think: shower, breakfast, getting dressed, packing your bag.)")
        info("And how long is your trip to school/work?")
        info("We use this so we don't accidentally plan things when you're busy getting ready!\n")

        prep_h   = get_hours("How long to get ready in the morning")
        travel_h = get_hours("How long is your trip to school / work (one way)")

        self.prep_mins   = prep_h   * 60
        self.travel_mins = travel_h * 60

        self.profile["commute"] = {
            "prep_time_mins":   self.prep_mins,
            "travel_time_mins": self.travel_mins
        }

        ok(f"Got it! Getting ready: {prep_h}h  |  Travel: {travel_h}h each way")

    # ── SECTION 3 : Wake / Sleep & Free-time calculation ─────────────────────
    def _collect_sleep_wake(self):
        header("STEP 3 OF 5  —  When Do You Wake Up & Go to Sleep?")
        info("Now we know your school/work times and your commute,")
        info("so we can figure out exactly when your FREE time is each day.")
        info("(We'll also add a small 30-minute wind-down buffer after you get home.)\n")

        schedule = self._raw_schedule

        uniform_sleep = yes("Do you wake up and sleep at the SAME time Monday to Friday?")
        if uniform_sleep:
            wake  = get_time("What time do you wake up on weekdays")
            sleep = get_time("What time do you go to sleep on weekdays")
            for day in ["monday","tuesday","wednesday","thursday","friday"]:
                schedule[day]["wake_time"]  = wake
                schedule[day]["sleep_time"] = sleep
        else:
            for day in ["monday","tuesday","wednesday","thursday","friday"]:
                print(f"\n  {BOLD}{day.capitalize()}{RESET}")
                schedule[day]["wake_time"]  = get_time(f"  What time do you wake up")
                schedule[day]["sleep_time"] = get_time(f"  What time do you go to sleep")

        for day in ["saturday", "sunday"]:
            print(f"\n  {BOLD}{day.capitalize()}{RESET}")
            schedule[day]["wake_time"]  = get_time(f"  What time do you wake up")
            schedule[day]["sleep_time"] = get_time(f"  What time do you go to sleep")

        # ── Build final day blocks with free-slot calculation ──────────────
        final_schedule = {}
        for day, d in schedule.items():
            wake  = d["wake_time"]
            sleep = d["sleep_time"]

            if d["has_obligation"]:
                ws = d["work_start"]
                we = d["work_end"]
                free = compute_free_slots(wake, sleep, ws, we,
                                          self.prep_mins, self.travel_mins)
                final_schedule[day] = {
                    "wake_time":   wake,
                    "sleep_time":  sleep,
                    "work_start":  ws,
                    "work_end":    we,
                    "free_slots":  free
                }
            else:
                free = compute_free_slots(wake, sleep)
                final_schedule[day] = {
                    "wake_time":  wake,
                    "sleep_time": sleep,
                    "free_slots": free
                }

            ok(f"{day.capitalize():<12}  Your free time: {', '.join(final_schedule[day]['free_slots'])}")

        self.profile["weekly_schedule"] = final_schedule

    # ── SECTION 4 : Goals ────────────────────────────────────────────────────
    def _collect_goals(self):
        header("STEP 4 OF 5  —  What Do You Want to Achieve?")
        info("What's something you really want to get better at or finish?")
        info("It could be learning guitar, getting fit, studying for exams —")
        info("anything you want to make real progress on.")
        info("Tell us how many hours per week you can give to it.\n")

        while True:
            name = ask("What's your goal? (just press Enter when you're done adding goals)")
            if name == "":
                if not self.profile["goals"]:
                    warn("You need at least one goal — go ahead, add one!")
                    continue
                break

            weekly_h = get_hours(f"  How many hours per week do you want to spend on '{name}'")
            priority = get_int("  How important is this goal? (type 1 for most important, 2 for next, etc.)", min_val=1)

            self.profile["goals"].append({
                "name":          name,
                "weekly_hours":  weekly_h,
                "priority":      priority
            })
            ok(f"Added: {name}  ({weekly_h}h/week — priority #{priority})")

    # ── SECTION 5 : Hobbies & Fixed Commitments ──────────────────────────────
    def _collect_hobbies_and_rigid(self):
        header("STEP 5 OF 5  —  Hobbies & Regular Commitments")
        info("Almost done! Two more things:")
        info("  Hobbies = fun stuff you like doing, but timing is flexible.")
        info("            (LifeSync will find the best time for these.)")
        info("  Fixed spots = things that ALWAYS happen at a set time.")
        info("                (like Sunday church, a weekly gym class, etc.)\n")

        # Flexible hobbies
        while yes("Do you have a hobby or activity you'd like to make time for?"):
            name     = ask("  What's the activity?")
            weekly_h = get_hours(f"  How many hours per week for '{name}'")
            self.profile["hobbies"].append({
                "name":         name,
                "weekly_hours": weekly_h,
                "flexible":     True
            })
            ok(f"Added: {name}  — we'll find a great time slot for this!")

        # Rigid / fixed commitments
        while yes("Do you have something that happens at a FIXED time every week? (e.g. gym class, church, tuition)"):
            name  = ask("  What is it?")
            start = get_time("  What time does it start")
            end   = get_time("  What time does it end")
            days_raw = ask("  Which days does this happen? (e.g.  monday,sunday)")
            days = [d.strip().lower() for d in days_raw.split(",")]

            self.profile["rigid_blocks"].append({
                "name":       name,
                "start_time": start,
                "end_time":   end,
                "days":       days
            })
            ok(f"Locked in: {name}  {start} to {end}  every {', '.join(days)}")

    # ── VALIDATION ────────────────────────────────────────────────────────────
    def _validate(self):
        header("CHECKING EVERYTHING LOOKS GOOD...")
        errors = []

        for day, d in self.profile["weekly_schedule"].items():
            if "work_start" in d and "work_end" in d:
                ws = to_dt(d["work_start"])
                we = to_dt(d["work_end"])
                if we <= ws:
                    errors.append(f"{day.capitalize()}: the end time is before (or the same as) the start time — please check this!")

        for rb in self.profile["rigid_blocks"]:
            rs = to_dt(rb["start_time"])
            re_t = to_dt(rb["end_time"])
            if re_t <= rs:
                re_t += timedelta(days=1)

            for day in rb["days"]:
                if day not in self.profile["weekly_schedule"]:
                    continue
                d     = self.profile["weekly_schedule"][day]
                slots = d.get("free_slots", [])
                fits  = False

                for slot in slots:
                    if "→" not in slot:
                        continue
                    fs_str, fe_str = [s.strip() for s in slot.split("→")]
                    fs = to_dt(fs_str)
                    fe = to_dt(fe_str)
                    if fe <= fs:
                        fe += timedelta(days=1)
                    if fs <= rs and re_t <= fe:
                        fits = True
                        break

                if not fits:
                    errors.append(
                        f"'{rb['name']}' on {day.capitalize()} "
                        f"({rb['start_time']} to {rb['end_time']}) "
                        f"clashes with your free time windows: {slots}"
                    )

        if errors:
            print()
            for e in errors:
                error(e)
            print()
            warn("Looks like there are a few clashes above. You can re-run to fix them,")
            warn("or open user_profile.json and edit it directly if you know what to change.")
        else:
            ok("Everything checks out! No clashes found.")

    # ── ENTRY POINT ───────────────────────────────────────────────────────────
    def run(self):
        print(f"\n{BOLD}{CYAN}")
        print("  ╔══════════════════════════════════════════════╗")
        print("  ║        L I F E S Y N C   E N G I N E        ║")
        print("  ║           Let's build your schedule!         ║")
        print("  ╚══════════════════════════════════════════════╝")
        print(RESET)
        info("Hey! Welcome to LifeSync.")
        info("We're going to ask you 5 quick sets of questions")
        info("to understand your week — then we'll do all the planning for you.")
        info("It only takes about 3 minutes. Let's go!\n")

        self._collect_anchors()       # 1. What must you do?
        self._collect_commute()       # 2. How long to get there + get ready?
        self._collect_sleep_wake()    # 3. When do you wake/sleep? → free slots
        self._collect_goals()         # 4. What do you want to achieve?
        self._collect_hobbies_and_rigid()  # 5. What else is in your life?

        self._validate()

        output_path = "user_profile.json"
        with open(output_path, "w") as f:
            json.dump(self.profile, f, indent=4)

        header("YOU'RE ALL SET!")
        ok(f"Your profile has been saved to '{output_path}'")
        info("Next up: run planner.py and we'll build your personalised 2-week schedule!\n")


if __name__ == "__main__":
    app = LifeSyncEngine()
    app.run()