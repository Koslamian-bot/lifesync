"""
LifeSync — Planner Engine  (planner.py)
----------------------------------------
Reads user_profile.json produced by engine.py, asks a few quick questions,
then calls Gemini 2.5 Flash with a bulletproof prompt to generate a
personalised, constraint-safe 2-week plan as structured JSON.

Dependencies:
    pip install google-genai pydantic python-dotenv
"""

import json
import os
import re
import textwrap
from datetime import date, timedelta
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
#  Terminal UI helpers
# ─────────────────────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
WHITE   = "\033[97m"
MAGENTA = "\033[95m"

def header(text):
    width = 62
    print(f"\n{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{CYAN}{'─' * width}{RESET}")

def info(text):   print(f"  {DIM}{WHITE}{text}{RESET}")
def ok(text):     print(f"  {GREEN}✓  {text}{RESET}")
def warn(text):   print(f"  {YELLOW}⚠  {text}{RESET}")
def error(text):  print(f"  {RED}✗  {text}{RESET}")
def ask(text):    return input(f"  {CYAN}▸{RESET} {text} ").strip()
def label(text):  print(f"  {BOLD}{MAGENTA}{text}{RESET}")

def yes(prompt):
    while True:
        val = ask(f"{prompt} (Y/N)").lower()
        if val in ("y", "n"):
            return val == "y"
        error("Just type  Y  for yes  or  N  for no")

def get_int(prompt, min_val=1, max_val=999):
    while True:
        val = ask(f"{prompt}:")
        if val.isdigit() and min_val <= int(val) <= max_val:
            return int(val)
        error(f"Please type a whole number between {min_val} and {max_val}")


# ─────────────────────────────────────────────────────────────────────────────
#  Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class ExerciseItem(BaseModel):
    name:        str            # e.g. "Barbell Back Squat"
    sets:        Optional[int]  # e.g. 4
    reps:        Optional[str]  # e.g. "8-10" or "to failure"
    duration:    Optional[str]  # e.g. "30 sec" — used for holds/cardio
    notes:       Optional[str]  # form tip or technique cue


class PracticeItem(BaseModel):
    name:        str            # e.g. "G Major Scale — two octaves"
    duration:    str            # e.g. "5 min"
    technique:   Optional[str]  # e.g. "use a metronome at 60bpm"


class TaskBlock(BaseModel):
    time_start:   str
    time_end:     str
    task_name:    str
    category:     str           # goal | hobby | rigid | rest | self-care
    goal_ref:     Optional[str]
    notes:        str
    # Populated only for workout tasks (category=goal, physique goal)
    exercises:    Optional[list[ExerciseItem]]
    # Populated only for music practice tasks
    practice:     Optional[list[PracticeItem]]


class DayPlan(BaseModel):
    date:         str           # "YYYY-MM-DD"  — provided by Python, not AI
    day_name:     str           # "Tuesday"     — provided by Python, not AI
    week_number:  int           # 1 or 2        — provided by Python, not AI
    tasks:        list[TaskBlock]
    day_summary:  str


class WeeklyMilestone(BaseModel):
    goal_name:     str
    week_1_target: str
    week_2_target: str


class TwoWeekPlan(BaseModel):
    plan_title:     str
    sprint_start:   str
    sprint_end:     str
    milestones:     list[WeeklyMilestone]
    daily_plans:    list[DayPlan]
    general_advice: str


# ─────────────────────────────────────────────────────────────────────────────
#  Date spine — pre-compute all 14 dates with correct day names
#  This is the fix for the "wrong day name" bug: Python calculates
#  the real day name from the date so the AI never has to guess.
# ─────────────────────────────────────────────────────────────────────────────

def build_date_spine(start: date) -> list[dict]:
    """Returns a list of 14 dicts: {date, day_name, week_number, weekday_lower}"""
    spine = []
    for i in range(14):
        d = start + timedelta(days=i)
        spine.append({
            "date":          d.isoformat(),
            "day_name":      d.strftime("%A"),          # real calendar day
            "week_number":   1 if i < 7 else 2,
            "weekday_lower": d.strftime("%A").lower()   # for schedule lookup
        })
    return spine


# ─────────────────────────────────────────────────────────────────────────────
#  Profile loader + display
# ─────────────────────────────────────────────────────────────────────────────

def load_profile(path="user_profile.json") -> dict:
    if not os.path.exists(path):
        error(f"Could not find '{path}'. Please run engine.py first!")
        exit(1)
    with open(path) as f:
        return json.load(f)


def display_profile_summary(profile: dict):
    header("YOUR PROFILE  —  Quick Summary")
    sched = profile.get("weekly_schedule", {})
    for day, d in sched.items():
        slots    = d.get("free_slots", [])
        has_work = "work_start" in d
        tag = f"  work {d['work_start']}-{d['work_end']}" if has_work else "  free day"
        info(f"  {day.capitalize():<12}{tag:<28}  Free: {', '.join(slots)}")
    print()
    for g in profile.get("goals", []):
        info(f"  🎯  {g['name']}  —  {g['weekly_hours']}h/week  (priority #{g['priority']})")
    for h in profile.get("hobbies", []):
        info(f"  🎨  {h['name']}  —  {h['weekly_hours']}h/week  (flexible)")
    for r in profile.get("rigid_blocks", []):
        info(f"  📌  {r['name']}  {r['start_time']}-{r['end_time']}  every {', '.join(r['days'])}")


# ─────────────────────────────────────────────────────────────────────────────
#  User input — sprint setup
# ─────────────────────────────────────────────────────────────────────────────

def collect_sprint_config(profile: dict) -> dict:
    header("LET'S SET UP YOUR 2-WEEK PLAN")
    info("We'll ask you a few quick things to personalise your schedule.\n")

    info("When do you want to START this plan?")
    info("  Press Enter to start from TODAY, or type a date like  2026-04-14\n")
    while True:
        raw = ask("Start date")
        if raw == "":
            start_date = date.today()
            break
        try:
            start_date = date.fromisoformat(raw)
            break
        except ValueError:
            error("Use the format  YYYY-MM-DD  e.g.  2026-04-14")

    end_date = start_date + timedelta(days=13)
    # Show user the real day names so they can verify
    ok(f"Sprint: {start_date} ({start_date.strftime('%A')})  to  {end_date} ({end_date.strftime('%A')})  — 14 days")

    goals = profile.get("goals", [])
    if not goals:
        error("No goals found in your profile. Please re-run engine.py.")
        exit(1)

    print()
    info("Here are your goals:")
    for i, g in enumerate(goals, 1):
        label(f"    {i}. {g['name']}  ({g['weekly_hours']}h/week, priority #{g['priority']})")

    print()
    if len(goals) == 1:
        selected_goals = goals
        ok(f"Only one goal found — we'll focus on: {goals[0]['name']}")
    else:
        info("Do you want to work on ALL your goals this sprint, or just focus on one?")
        if yes("Work on ALL goals this sprint?"):
            selected_goals = goals
            ok("Great! We'll balance all your goals across the 2 weeks.")
        else:
            idx = get_int(
                f"Which goal to focus on? (type a number 1-{len(goals)})",
                min_val=1, max_val=len(goals)
            )
            selected_goals = [goals[idx - 1]]
            ok(f"Focusing on: {selected_goals[0]['name']}")

    print()
    info("When do you feel most focused and energetic?")
    info("  1 = Mornings (I'm a morning person!)")
    info("  2 = Evenings (I come alive at night)")
    info("  3 = Both are fine — no preference\n")
    energy_pref = {1: "morning", 2: "evening", 3: "no preference"}[
        get_int("Pick 1, 2, or 3", min_val=1, max_val=3)
    ]
    ok(f"Got it — hardest tasks go in your {energy_pref} windows.")

    print()
    info("How long do you like to work in one sitting before a break?")
    info("  1 = Short bursts  (25-30 mins, then a break)")
    info("  2 = Medium chunks (45-60 mins)")
    info("  3 = Long sessions (90+ mins, I like to go deep)\n")
    session_pref = {
        1: "short (25-30 min sessions)",
        2: "medium (45-60 min sessions)",
        3: "long (90+ min sessions)"
    }[get_int("Pick 1, 2, or 3", min_val=1, max_val=3)]
    ok(f"Sessions will be: {session_pref}")

    print()
    info("Anything else we should know? (upcoming exam, holiday, feeling burnt out...)")
    extra_context = ask("Tell us anything (or just press Enter to skip)")

    return {
        "start_date":     str(start_date),
        "end_date":       str(end_date),
        "selected_goals": selected_goals,
        "energy_pref":    energy_pref,
        "session_pref":   session_pref,
        "extra_context":  extra_context or "None provided."
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Prompt builder
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt(profile: dict, config: dict, date_spine: list[dict]) -> str:

    sched    = profile.get("weekly_schedule", {})
    commute  = profile.get("commute", {})
    prep_h   = commute.get("prep_time_mins",  0) / 60
    travel_h = commute.get("travel_time_mins", 0) / 60

    # Schedule block — one line per day
    day_lines = []
    for day, d in sched.items():
        free = ", ".join(d.get("free_slots", ["none"]))
        if "work_start" in d:
            day_lines.append(
                f"{day[:3].upper()}: LOCKED {d['work_start']}-{d['work_end']} | free: {free}"
            )
        else:
            day_lines.append(f"{day[:3].upper()}: no obligation | free: {free}")
    schedule_block = "\n".join(day_lines)

    # Date spine — tell AI EXACTLY what date/day each slot is
    # This is the core fix: AI never guesses day names
    spine_lines = []
    for s in date_spine:
        # Look up free slots for this actual calendar day
        weekday = s["weekday_lower"]
        day_data = sched.get(weekday, {})
        free = ", ".join(day_data.get("free_slots", ["none"]))
        locked = ""
        if "work_start" in day_data:
            locked = f" | LOCKED {day_data['work_start']}-{day_data['work_end']}"
        spine_lines.append(
            f"  Day {date_spine.index(s)+1:>2}: {s['date']}  {s['day_name']:<10} (Week {s['week_number']}){locked} | free: {free}"
        )
    spine_block = "\n".join(spine_lines)

    rigid_lines = [
        f"  {r['name']} {r['start_time']}-{r['end_time']} on {','.join(r['days'])}"
        for r in profile.get("rigid_blocks", [])
    ]
    rigid_block = "\n".join(rigid_lines) or "  None."

    goals_block = "\n".join(
        f"  [{g['priority']}] {g['name']} — {g['weekly_hours']}h/week"
        for g in config["selected_goals"]
    )

    hobby_lines = [
        f"  {h['name']} — {h['weekly_hours']}h/week (flexible)"
        for h in profile.get("hobbies", [])
    ]
    hobbies_block = "\n".join(hobby_lines) or "  None."

    prompt = f"""You are LifeSync, a personal life-planning AI. Generate a detailed, specific, realistic 2-week daily plan as JSON.

════════════════════════════════════════
HARD RULES — ABSOLUTE, NO EXCEPTIONS
════════════════════════════════════════
1. NEVER place tasks inside LOCKED windows (work/school).
2. ALL task times must fall strictly within the free windows for that specific date.
3. Rigid blocks are pre-placed. Include them as category "rigid". Do not move or overlap them.
4. No tasks outside wake/sleep bounds.
5. Times must be exact HH:MM strings only. Never write "07:00-08:00" as a string value.
6. Every day must include at least one "rest" block (min 15 min, category "rest").

════════════════════════════════════════
DATE SPINE — USE THESE EXACT VALUES
════════════════════════════════════════
The date and day_name for each DayPlan are already decided below.
You MUST copy them exactly — do NOT invent or change day names.
{spine_block}

════════════════════════════════════════
WEEKLY SCHEDULE PATTERN
════════════════════════════════════════
prep={prep_h:.1f}h commute={travel_h:.1f}h (already factored into free windows above)
{schedule_block}

════════════════════════════════════════
FIXED COMMITMENTS (category=rigid, pre-placed)
════════════════════════════════════════
{rigid_block}

════════════════════════════════════════
GOALS
════════════════════════════════════════
{goals_block}

════════════════════════════════════════
HOBBIES
════════════════════════════════════════
{hobbies_block}

════════════════════════════════════════
SPRINT INFO
════════════════════════════════════════
Start: {config["start_date"]}  End: {config["end_date"]}  (14 days)
Energy peak: {config["energy_pref"]} — hardest tasks go here
Session length: {config["session_pref"]}
Extra context: {config["extra_context"]}

════════════════════════════════════════
SPECIFICITY RULES — VERY IMPORTANT
════════════════════════════════════════

FOR PHYSIQUE / WORKOUT TASKS:
- task_name must name the session type e.g. "Lower Body Strength" or "Cardio: HIIT"
- Populate the "exercises" list with 4-6 specific exercises per session
- Each exercise needs: name, sets (int), reps (string e.g. "8-12"), and a form tip in notes
- For cardio: use duration instead of sets/reps e.g. duration="20 min at moderate pace"
- Vary exercise selection across days (don't repeat same workout two days in a row)
- Week 1 = slightly lower volume. Week 2 = increase sets or reps by one step.
- Example exercises for lower body: Barbell Back Squat, Romanian Deadlift, Leg Press,
  Bulgarian Split Squat, Leg Curl, Standing Calf Raise
- Example exercises for upper body: Bench Press, Bent-Over Row, Overhead Press,
  Pull-Up/Lat Pulldown, Dumbbell Curl, Tricep Dip
- Example exercises for core: Plank, Dead Bug, Hollow Hold, Cable Crunch, Russian Twist

FOR MUSIC PRACTICE TASKS:
- task_name must be specific e.g. "Guitar: G-C-D Chord Transitions" not just "Practice"
- Populate the "practice" list with 3-5 specific drills
- Each drill needs: name (specific exercise), duration (e.g. "5 min"), and a technique cue
- Week 1 = fundamentals (scales, basic chords, finger exercises)
- Week 2 = applied (song sections, tempo work, performing from memory)
- Example drills: "C Major Scale — one octave, both hands", "G to C chord switch x20",
  "Fingerpicking pattern #1", "Sight-read 4 bars of [song]"

FOR ALL TASKS:
- task_name must be specific, never generic like "Workout" or "Practice" alone
- notes = one sentence WHY this task is at this exact time
- day_summary = one warm motivating sentence for the whole day
- Leave exercises=null and practice=null for non-workout/non-music tasks

════════════════════════════════════════
PLANNING APPROACH
════════════════════════════════════════
- Week 1: build the habit, moderate load. Week 2: step up intensity/complexity.
- Vary the type of session each day (no two identical days back to back).
- Realistic > perfect. Light day is better than burnout.
- milestones: one clear measurable target per goal for end of Week 1 and Week 2.
- general_advice: 2-3 sentences of honest, practical coaching.

Output ONLY a valid JSON object. No explanation. No markdown fences. No extra text."""

    return prompt


# ─────────────────────────────────────────────────────────────────────────────
#  Gemini call — with full fallback + diagnostics
# ─────────────────────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> TwoWeekPlan:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        error("GEMINI_API_KEY not found.")
        error("Create a .env file in this folder and add:")
        error("    GEMINI_API_KEY=your_key_here")
        exit(1)

    client = genai.Client(api_key=api_key)

    info("Sending your profile to Gemini 2.5 Flash...")
    info("This usually takes 20-40 seconds (more detail = more time). Hang tight!\n")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TwoWeekPlan,
            temperature=0.4,
            max_output_tokens=65535,
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
    )

    # Diagnostic
    if response.candidates:
        finish = str(response.candidates[0].finish_reason)
        if finish not in ("FinishReason.STOP", "STOP", "1"):
            warn(f"Gemini stopped early — finish_reason: {finish}")
            if "MAX_TOKENS" in finish:
                warn("Output too long. Try focusing on fewer goals.")
            elif "SAFETY" in finish:
                warn("Response was blocked by a safety filter.")

    if response.parsed:
        return response.parsed

    # Fallback: manual parse
    raw = ""
    try:
        raw = response.text.strip()
    except Exception:
        pass

    if not raw:
        error("Gemini returned no content at all.")
        error("Possible reasons:")
        error("  - free_slots in user_profile.json may be empty")
        error("  - Temporary API issue — try running again")
        exit(1)

    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)

    try:
        data = json.loads(raw)
        return TwoWeekPlan(**data)
    except Exception as parse_err:
        error(f"Could not parse Gemini response: {parse_err}")
        error("Raw response saved to gemini_raw_response.txt for inspection.")
        with open("gemini_raw_response.txt", "w") as f:
            f.write(raw)
        exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  Post-process: fix day_name and week_number from the date spine
#  Even if AI drifts on day names, we correct them here from Python's calendar
# ─────────────────────────────────────────────────────────────────────────────

def apply_date_spine(plan: TwoWeekPlan, spine: list[dict]) -> TwoWeekPlan:
    spine_by_date = {s["date"]: s for s in spine}
    corrected_days = []
    for dp in plan.daily_plans:
        if dp.date in spine_by_date:
            s = spine_by_date[dp.date]
            corrected_days.append(DayPlan(
                date        = dp.date,
                day_name    = s["day_name"],       # always correct from Python
                week_number = s["week_number"],    # always correct from Python
                tasks       = dp.tasks,
                day_summary = dp.day_summary
            ))
        else:
            corrected_days.append(dp)

    return TwoWeekPlan(
        plan_title    = plan.plan_title,
        sprint_start  = plan.sprint_start,
        sprint_end    = plan.sprint_end,
        milestones    = plan.milestones,
        daily_plans   = corrected_days,
        general_advice= plan.general_advice
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Pretty-print
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "goal":      GREEN,
    "hobby":     MAGENTA,
    "rigid":     YELLOW,
    "rest":      CYAN,
    "self-care": DIM + WHITE,
}
CATEGORY_ICONS = {
    "goal":      "🎯",
    "hobby":     "🎨",
    "rigid":     "📌",
    "rest":      "☕",
    "self-care": "🌿",
}

def print_plan(plan: TwoWeekPlan):
    header(f"YOUR 2-WEEK PLAN  —  {plan.plan_title}")
    info(f"  Sprint: {plan.sprint_start}  to  {plan.sprint_end}\n")

    print(f"  {BOLD}{WHITE}MILESTONES{RESET}")
    for m in plan.milestones:
        print(f"\n  {CYAN}{m.goal_name}{RESET}")
        print(f"    Week 1 → {m.week_1_target}")
        print(f"    Week 2 → {m.week_2_target}")
    print()

    current_week = 0
    for day in plan.daily_plans:
        if day.week_number != current_week:
            current_week = day.week_number
            print(f"\n  {BOLD}{CYAN}{'━' * 58}{RESET}")
            print(f"  {BOLD}{CYAN}  WEEK {current_week}{RESET}")
            print(f"  {BOLD}{CYAN}{'━' * 58}{RESET}")

        print(f"\n  {BOLD}{WHITE}{day.day_name.upper()}  {day.date}{RESET}")
        print(f"  {DIM}{WHITE}  {day.day_summary}{RESET}")

        if not day.tasks:
            info("    (rest day — no tasks scheduled)")
            continue

        for t in day.tasks:
            color    = CATEGORY_COLORS.get(t.category, WHITE)
            icon     = CATEGORY_ICONS.get(t.category, "•")
            goal_tag = f"  [{t.goal_ref}]" if t.goal_ref else ""
            print(
                f"\n    {BOLD}{t.time_start}-{t.time_end}{RESET}  "
                f"{color}{icon} {t.task_name}{RESET}"
                f"{DIM}{WHITE}{goal_tag}{RESET}"
            )
            if t.notes:
                print(f"    {DIM}↳ {t.notes}{RESET}")

            # Print exercises for workout tasks
            if t.exercises:
                print(f"    {YELLOW}Exercises:{RESET}")
                for ex in t.exercises:
                    sets_reps = ""
                    if ex.sets and ex.reps:
                        sets_reps = f"{ex.sets} sets × {ex.reps} reps"
                    elif ex.duration:
                        sets_reps = ex.duration
                    tip = f"  — {ex.notes}" if ex.notes else ""
                    print(f"      {GREEN}• {ex.name}{RESET}  {DIM}{sets_reps}{tip}{RESET}")

            # Print practice drills for music tasks
            if t.practice:
                print(f"    {YELLOW}Drills:{RESET}")
                for pr in t.practice:
                    tech = f"  — {pr.technique}" if pr.technique else ""
                    print(f"      {MAGENTA}♪ {pr.name}{RESET}  {DIM}({pr.duration}){tech}{RESET}")

    print()
    header("COACH'S ADVICE")
    for line in textwrap.wrap(plan.general_advice, width=60):
        info(line)
    print()


# ─────────────────────────────────────────────────────────────────────────────
#  Save outputs
# ─────────────────────────────────────────────────────────────────────────────

def save_outputs(plan: TwoWeekPlan):
    json_path = "two_week_plan.json"
    with open(json_path, "w") as f:
        json.dump(plan.model_dump(), f, indent=4)
    ok(f"Full plan saved to '{json_path}'")

    txt_path = "two_week_plan.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"LifeSync — {plan.plan_title}\n")
        f.write(f"Sprint: {plan.sprint_start} to {plan.sprint_end}\n\n")

        f.write("MILESTONES\n")
        for m in plan.milestones:
            f.write(f"  {m.goal_name}\n")
            f.write(f"    Week 1: {m.week_1_target}\n")
            f.write(f"    Week 2: {m.week_2_target}\n")
        f.write("\n")

        current_week = 0
        for day in plan.daily_plans:
            if day.week_number != current_week:
                current_week = day.week_number
                f.write(f"\n{'='*52}\nWEEK {current_week}\n{'='*52}\n")
            f.write(f"\n{day.day_name.upper()}  {day.date}\n")
            f.write(f"  {day.day_summary}\n")
            for t in day.tasks:
                f.write(f"\n  {t.time_start}-{t.time_end}  [{t.category.upper()}]  {t.task_name}\n")
                if t.notes:
                    f.write(f"    -> {t.notes}\n")
                if t.exercises:
                    f.write(f"    Exercises:\n")
                    for ex in t.exercises:
                        sets_reps = ""
                        if ex.sets and ex.reps:
                            sets_reps = f"{ex.sets}x{ex.reps}"
                        elif ex.duration:
                            sets_reps = ex.duration
                        tip = f" | {ex.notes}" if ex.notes else ""
                        f.write(f"      • {ex.name}  {sets_reps}{tip}\n")
                if t.practice:
                    f.write(f"    Drills:\n")
                    for pr in t.practice:
                        tech = f" | {pr.technique}" if pr.technique else ""
                        f.write(f"      ♪ {pr.name}  ({pr.duration}){tech}\n")

        f.write(f"\n\nCOACH'S ADVICE\n{plan.general_advice}\n")

    ok(f"Readable summary saved to '{txt_path}'")


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{CYAN}")
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║      L I F E S Y N C   P L A N N E R        ║")
    print("  ║        Your 2-Week Sprint Builder            ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(RESET)
    info("Welcome back! Let's turn your profile into an actual plan.")
    info("This will only take about 2 minutes of questions, then Gemini")
    info("does the heavy lifting and builds your full 2-week schedule.\n")

    profile = load_profile("user_profile.json")
    display_profile_summary(profile)

    if not yes("\nDoes this profile look right to you?"):
        warn("Please re-run engine.py to update your profile, then come back here.")
        exit(0)

    config     = collect_sprint_config(profile)
    date_spine = build_date_spine(date.fromisoformat(config["start_date"]))

    header("BUILDING YOUR PLAN WITH GEMINI AI...")
    prompt = build_prompt(profile, config, date_spine)

    try:
        plan = call_gemini(prompt)
    except Exception as e:
        error(f"Something went wrong with the AI call: {e}")
        error("Check your GEMINI_API_KEY and internet connection, then try again.")
        exit(1)

    if not plan:
        error("Gemini returned an empty plan. Please try again.")
        exit(1)

    # Always correct day names from Python's calendar — never trust the AI for this
    plan = apply_date_spine(plan, date_spine)

    ok("Plan generated successfully!\n")
    print_plan(plan)
    save_outputs(plan)

    header("ALL DONE!")
    ok("Your 2-week plan is ready.")
    info("Next step: Google Calendar integration to push this to your calendar.")
    info("Or open  two_week_plan.txt  for a clean readable version anytime.\n")


if __name__ == "__main__":
    main()