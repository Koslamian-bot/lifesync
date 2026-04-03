import json
import os
from dotenv import load_dotenv
from google import genai
from datetime import datetime, timedelta

# def is_weekend(day_index):
#     # assuming Day 1 = today
#     today = datetime.today()
#     current_day = today + timedelta(days=day_index)
#     return current_day.weekday() >= 5  # 5=Sat, 6=Sun

def generate_day_context(days, start_date):
    context = []

    for i in range(days):
        current_day = start_date + timedelta(days=i)
        day_name = current_day.strftime("%A")
        is_weekend = current_day.weekday() >= 5

        context.append({
            "day_number": i + 1,
            "day_name": day_name,
            "type": "Weekend" if is_weekend else "Weekday"
        })

    return context
# --- LOAD ENV ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Missing API Key")
    exit(1)

client = genai.Client(api_key=api_key)

# --- LOAD PROFILE ---
def load_profile():
    try:
        with open("profile.json", "r") as f:
            return json.load(f)
    except:
        print("❌ profile.json not found. Run Engine 1 first.")
        exit(1)

# --- USER INPUT ---
def get_inputs(profile):
    print("\n🚀 LifeSync Planning Engine")
    print("--------------------------------")

    print("\n🎯 Your Goals:")
    for i, g in enumerate(profile["goals"], 1):
        print(f"{i}. {g}")

    goal = profile["goals"][int(input("\nSelect goal: ")) - 1]

    duration_days = int(input("📅 Enter duration (in days): "))
    start_date_input = input("📅 Enter start date (YYYY-MM-DD) or press Enter for today: ")

    if start_date_input:
        start_date = datetime.strptime(start_date_input, "%Y-%m-%d")
    else:
        start_date = datetime.today()

    return goal, duration_days, start_date


# --- AI PLANNER ---
def generate_plan(profile, goal, days, day_context):
    print("\n🧠 Generating your personalized life plan...\n")

    prompt = f"""
You are LifeSync AI — an advanced lifestyle-aware planning system.

DAY STRUCTURE:
{json.dumps(day_context, indent=2)}

USER PROFILE:
{json.dumps(profile, indent=2)}

GOAL:
{goal}

DURATION:
{days} days

IMPORTANT CONTEXT:
- Work hours: {profile.get("work_hours")}
- Free slots: {profile.get("free_slots")}
- Energy curve:
  Morning: {profile.get("energy_curve", {}).get("morning")}
  Afternoon: {profile.get("energy_curve", {}).get("afternoon")}
  Evening: {profile.get("energy_curve", {}).get("evening")}

TASK:
Create a HIGHLY PERSONALIZED daily plan.

STRICT RULES:

1. Each day must have MULTIPLE time blocks (2–4 sessions per day)
2. DO NOT use a fixed time for all days
3. Adapt schedule based on:
   - Weekdays (more constrained)
   - Weekends (more flexible, more sessions)
4. Use FREE SLOTS intelligently
5. NEVER overlap with WORK HOURS
6. Match ENERGY:
   - High → deep work / learning
   - Medium → practice
   - Low → revision / light tasks
7. Vary timings across days (avoid repetition)
8. Include breaks where needed
9. Gradually increase difficulty over days
10. Make weekend days more productive but balanced

OUTPUT FORMAT (TEXT ONLY):

DAY 1 (Weekday):
- Time → Task
- Time → Task

DAY 6 (Weekend):
- Time → Task
- Time → Task
- Time → Task

Make it realistic, adaptive, and human-friendly.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"temperature": 0.5}
    )

    return response.text

# --- MAIN ---
def run():
    profile = load_profile()
    goal, days, start_date = get_inputs(profile)
    day_context = generate_day_context(days, start_date)

    plan = generate_plan(profile, goal, days, day_context)

    if not plan:
        print("❌ Failed to generate plan.")
        return

    print("\n✅ YOUR LIFE PLAN:\n")
    print(plan)

    with open("plan.txt", "w", encoding="utf-8") as f:
        f.write(plan)

    print("\n💾 Plan saved as plan.txt")
# --- RUN ---
if __name__ == "__main__":
    run()