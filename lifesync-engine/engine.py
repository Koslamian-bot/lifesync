import os
import json
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

# --- 1. SCHEMAS ---
class EnergyCurve(BaseModel):
    morning: str 
    afternoon: str
    evening: str

class LifestyleStructure(BaseModel):
    wake_time: str
    sleep_time: str
    work_hours: list[str]
    energy_curve: EnergyCurve
    free_slots: list[str]
    habits: list[str]
    constraints: list[str]
    goals: list[str]

# --- 2. API SETUP ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("🚨 ERROR: GEMINI_API_KEY is missing!")
    exit(1)

client = genai.Client(api_key=api_key)

# --- 3. CLI MENU HELPER ---
def ask_mcq(question, options, allow_multiple=False):
    """Handles the terminal UI for asking multiple choice questions cleanly."""
    print(f"\n{question}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print(f"  {len(options) + 1}. Other (type your own)")
    
    while True:
        hint = "(comma-separated numbers)" if allow_multiple else "(select one number)"
        ans = input(f"\n> Your choice {hint}: ")
        
        selected = []
        parts = [p.strip() for p in ans.split(',')] if allow_multiple else [ans.strip()]
        
        try:
            for p in parts:
                idx = int(p) - 1
                if 0 <= idx < len(options):
                    selected.append(options[idx])
                elif idx == len(options):
                    custom = input("  👉 Type your custom answer: ")
                    selected.append(custom)
                else:
                    raise ValueError
            return selected if allow_multiple else selected[0]
        except ValueError:
            print("❌ Invalid input, please enter the correct number(s).")

# --- 4. THE ONBOARDING FLOW ---
def run_interactive_onboarding():
    print("\n🧠 Welcome to LifeSync AI — Let's structure your lifestyle.")
    print("---------------------------------------------------------")
    
    data = {}
    
    # Phase 1: Basic Schedule
    data["wake_time"] = ask_mcq("PHASE 1: What is your typical Wake Time?", 
                                ["05:00-06:00", "06:00-07:00", "07:00-08:00", "08:00-09:00"])
    
    data["sleep_time"] = ask_mcq("What is your typical Sleep Time?", 
                                 ["21:00-22:00", "22:00-23:00", "23:00-00:00", "00:00-01:00"])

    # Phase 2: Work/Study
    data["work_hours"] = ask_mcq("PHASE 2: Select your typical work/study time blocks", 
                                 ["06:00-09:00", "09:00-13:00", "13:00-17:00", "17:00-21:00"], allow_multiple=True)

    # Phase 3: Energy
    print("\nPHASE 3: ENERGY PROFILE")
    energy_opts = ["high", "medium", "low"]
    data["energy_morning"] = ask_mcq("Morning energy level?", energy_opts)
    data["energy_afternoon"] = ask_mcq("Afternoon energy level?", energy_opts)
    data["energy_evening"] = ask_mcq("Evening energy level?", energy_opts)

    # Phase 4: Free Time
    data["free_slots"] = ask_mcq("PHASE 4: When are you usually free?", 
                                 ["Early morning", "Afternoon", "Evening", "Late night"], allow_multiple=True)

    # Phase 5: Habits
    data["habits"] = ask_mcq("PHASE 5: What activities are regularly part of your life?", 
                             ["Gym / Exercise", "Coding / Learning", "Reading", "Gaming", "Social Media", "Meditation", "Watching content"], allow_multiple=True)

    # Phase 6: Constraints
    data["constraints"] = ask_mcq("PHASE 6: What limits or controls your schedule?", 
                                  ["College", "Job", "Commute", "Family responsibilities", "Health issues"], allow_multiple=True)

    # Phase 7: Goals
    data["goals"] = ask_mcq("PHASE 7: What are your current goals?", 
                            ["Career growth", "Skill building", "Fitness", "Financial independence", "Better routine / discipline", "Mental health"], allow_multiple=True)

    # Phase 8: Narrative
    print("\nPHASE 8: NARRATIVE INPUT (VERY IMPORTANT)")
    print("Now give me a quick walkthrough of your life:")
    print("1. What does a typical weekday look like from wake to sleep?")
    print("2. What does your weekend usually look like?")
    narrative = input("\n> ")

    return data, narrative

# --- 5. GEMINI MERGE & FORMAT LOGIC ---
def finalize_profile(structured_data, narrative):
    print("\n⏳ LifeSync Engine is compiling your master profile...")
    
    prompt = f"""
    You are the LifeSync AI data compiler. 
    
    Step 1: Review the rigid data the user provided via the onboarding quiz:
    {json.dumps(structured_data, indent=2)}
    
    Step 2: Review their casual narrative context:
    "{narrative}"
    
    Step 3: Merge these together and output strictly into the required JSON schema.
    
    CRITICAL RULES:
    1. Convert ALL times to 24-hour format (e.g., "07:00", "23:00").
    2. Time ranges must be clean (e.g., "09:00-13:00").
    3. Energy values must ONLY be "high", "medium", or "low".
    4. If the narrative adds context that modifies the quiz answers, trust the narrative.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.0, 
                "response_mime_type": "application/json",
                "response_schema": LifestyleStructure,
            }
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

# --- MAIN RUNNER ---
if __name__ == "__main__":
    quiz_data, user_narrative = run_interactive_onboarding()
    final_json = finalize_profile(quiz_data, user_narrative)
    
    print("\n✅ PROFILE COMPLETE. SYSTEM-READY OUTPUT:\n")
    print(json.dumps(final_json, indent=2))