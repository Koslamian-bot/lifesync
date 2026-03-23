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

# --- 3. EXTRACTION LOGIC ---
def structure_lifestyle(user_input: str):
    prompt = f"""
    Extract the daily routine into the required schema. 
    
    CRITICAL RULES:
    1. Do NOT guess missing data. If wake time, sleep time, or energy levels are not explicitly mentioned, output "MISSING" for that exact field.
    2. ALL times MUST be converted to 24-hour format (e.g., "07:00", "23:00").
    3. Time ranges must be clean (e.g., "08:30-16:00"). Do not include text inside the time fields.
    4. Energy levels must be strictly one of: "high", "medium", "low", or "MISSING".
    
    User Input: "{user_input}"
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

def check_missing_fields(data):
    """Returns a list of keys that the LLM marked as MISSING."""
    missing = []
    if data.get("wake_time") == "MISSING": missing.append("Wake Time")
    if data.get("sleep_time") == "MISSING": missing.append("Sleep Time")
    
    ec = data.get("energy_curve", {})
    if "MISSING" in [ec.get("morning"), ec.get("afternoon"), ec.get("evening")]:
        missing.append("Energy Levels (Morning/Afternoon/Evening)")
        
    return missing

# --- 4. THE "QUIZ" SLOT-FILLING LOOP ---
def interactive_ingestion_loop():
    print("\n🧠 LifeSync AI — Lifestyle Structuring Engine")
    print("---------------------------------------------")
    
    # Step 1: Get the initial story
    story = input("\nDescribe your daily routine (or target routine):\n> ")
    
    # Step 2: First Pass Extraction
    print("\n⏳ Analyzing routine...")
    raw_profile = structure_lifestyle(story)
    
    if "error" in raw_profile:
        print(f"❌ Critical Failure: {raw_profile['error']}")
        exit(1)

    # Step 3: Check what is missing
    missing_fields = check_missing_fields(raw_profile)

    # Step 4: The Quiz (Slot Filling)
    if missing_fields:
        print("\n⚠️ I need a few more quick details to complete your profile:")
        addendum = "\n\nUser clarified the following missing details:\n"
        
        for field in missing_fields:
            # Ask one specific question at a time
            answer = input(f"  👉 What is your {field}? ")
            addendum += f"- {field}: {answer}\n"
            
        # Step 5: Final LLM Pass with the complete picture
        print("\n⏳ Finalizing profile...")
        final_story = story + addendum
        final_profile = structure_lifestyle(final_story)
        return final_profile
        
    # If nothing was missing the first time, just return it
    return raw_profile

# --- 5. MAIN ---
if __name__ == "__main__":
    final_profile = interactive_ingestion_loop()
    
    print("\n✅ PROFILE COMPLETE. SYSTEM-READY OUTPUT:\n")
    print(json.dumps(final_profile, indent=2))