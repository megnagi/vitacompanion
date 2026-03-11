"""
Seed script: inserts global wellness knowledge documents into rag_documents.
Run from the project root: python seed_rag.py
"""
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import text
from db import AsyncSessionLocal
from services.rag_service import insert_document


# ─── Documents to seed ───────────────────────────────────────────

DOCUMENTS = [
    {
        "title": "Nutrition Guidelines for Adults 50+",
        "category": "nutrition",
        "content": (
            "Adults over 50 have higher protein needs than younger adults to preserve muscle mass "
            "and prevent sarcopenia. Target 1.2 to 1.6 grams of protein per kilogram of body weight "
            "per day, distributed across meals. Calcium intake should reach 1200mg/day (women) and "
            "1000mg/day (men) to support bone density; prioritise dairy, fortified plant milks, "
            "leafy greens, and almonds. Vitamin D (800-2000 IU/day) is critical for calcium "
            "absorption and immune function — many adults 50+ are deficient. Aim for 25-30g of "
            "dietary fibre daily from vegetables, legumes, and whole grains to support gut health "
            "and cholesterol. Hydration needs increase with age as thirst signals diminish; target "
            "at least 2 litres of water per day. Minimise ultra-processed foods, refined sugars, "
            "and excess sodium. The Mediterranean diet (olive oil, fish, legumes, vegetables, "
            "whole grains, moderate dairy) is strongly evidence-backed for cardiovascular health "
            "and longevity in this age group. For muscle synthesis, spread protein intake evenly "
            "and include a protein-rich meal or snack within 1-2 hours of strength training."
        ),
    },
    {
        "title": "Caloric Guidelines by Goal for Adults 50+",
        "category": "nutrition",
        "content": (
            "Caloric needs decline with age due to reduced muscle mass and slower metabolism. "
            "Baseline estimates for adults 50+ (adjust for actual activity): sedentary women "
            "1600-1800 kcal, sedentary men 2000-2200 kcal; active women 1800-2200 kcal, "
            "active men 2400-2800 kcal. For weight loss, apply a deficit of 300-500 kcal/day "
            "— avoid aggressive cuts that accelerate muscle loss. Never go below 1200 kcal/day "
            "for women or 1400 kcal/day for men without medical supervision. For muscle gain, "
            "a modest surplus of 150-300 kcal/day is sufficient; larger surpluses primarily "
            "add fat in this age group. For maintenance, match intake to Total Daily Energy "
            "Expenditure (TDEE). Activity level multipliers: sedentary x1.2, light x1.375, "
            "moderate x1.55, active x1.725, very active x1.9. Prioritise protein and "
            "micronutrient density over total calories — at a deficit, nutrient quality matters "
            "more than ever. Weekly weigh-ins at the same time of day are more reliable than "
            "daily measurements for tracking trends."
        ),
    },
    {
        "title": "Exercise Guidelines for Adults 50+",
        "category": "training",
        "content": (
            "WHO and ACSM guidelines for adults 50+ recommend at least 150 minutes of "
            "moderate-intensity aerobic activity per week (or 75 minutes vigorous), spread "
            "across at least 3 days. Strength training should occur at least 2 times per week, "
            "targeting all major muscle groups; resistance training is the primary tool against "
            "age-related muscle and bone loss. Balance and flexibility training (yoga, tai chi, "
            "stretching) should be incorporated at least 2-3 times per week to reduce fall risk. "
            "Allow 48 hours of recovery between strength sessions targeting the same muscle group. "
            "Signs of overtraining in older adults include persistent fatigue lasting more than "
            "48 hours, declining performance, increased resting heart rate, disrupted sleep, and "
            "mood changes. Joint-friendly alternatives: swimming and water aerobics for high-impact "
            "substitutes, resistance bands instead of heavy free weights for joint issues, cycling "
            "or elliptical instead of running for knee problems, seated or wall exercises for "
            "balance limitations. Progress volume and intensity gradually — no more than 10% "
            "increase per week. Rest days are not optional; they are where adaptation occurs."
        ),
    },
    {
        "title": "Heart Rate Zones for Adults 50+",
        "category": "training",
        "content": (
            "Estimated maximum heart rate (MHR) formula: 220 minus age. For a 60-year-old, "
            "MHR = 160 bpm. Heart rate zones based on percentage of MHR: "
            "Zone 1 (50-60%) — very light, warm-up and recovery, conversational pace; "
            "Zone 2 (60-70%) — fat-burning zone, sustainable aerobic base, ideal for longer "
            "sessions and metabolic health; "
            "Zone 3 (70-80%) — aerobic zone, moderate intensity, improves cardiovascular "
            "fitness, harder to hold a full conversation; "
            "Zone 4 (80-90%) — threshold zone, hard effort, interval training; "
            "Zone 5 (90-100%) — maximum effort, only for short bursts, not recommended for "
            "daily use in adults 50+. "
            "For adults 50+, the majority of cardio (70-80% of sessions) should be in zones 2-3. "
            "Zone 2 training is particularly valuable for metabolic health, fat oxidation, and "
            "cardiovascular longevity. "
            "Warning signs requiring immediate exercise cessation: HR exceeding 90% MHR with "
            "no return to baseline after 2-3 minutes of rest, chest tightness, dizziness, "
            "shortness of breath disproportionate to effort, or heart palpitations."
        ),
    },
    {
        "title": "Safety Rules and Physical Red Flags",
        "category": "safety",
        "content": (
            "Absolute stop conditions — cease exercise immediately and seek medical attention: "
            "chest pain, pressure, or tightness; pain radiating to the arm, jaw, or neck; "
            "sudden severe shortness of breath at rest or disproportionate to activity level; "
            "dizziness, lightheadedness, or fainting; sudden severe headache; visual disturbances. "
            "Sharp joint pain (stabbing, localised, sudden) is a warning signal — stop the "
            "aggravating movement immediately. Distinguish from normal muscle soreness (DOMS), "
            "which is diffuse, develops 24-48 hours after exercise, and resolves within 72 hours. "
            "Medication interactions: beta-blockers blunt HR response — HR zones are less reliable; "
            "diuretics increase dehydration risk; statins may increase muscle soreness. "
            "Signs of hypoglycemia during exercise (especially for diabetic users): shakiness, "
            "sudden sweating, confusion, weakness — stop activity, consume fast-acting carbs. "
            "Recommend seeing a physician before starting a new program if: no exercise for 6+ "
            "months, known cardiovascular disease, diabetes, hypertension, or recent surgery. "
            "Never prescribe or advise on medication changes — always defer to the user's doctor."
        ),
    },
    {
        "title": "Emotional Wellbeing and Mental Health Guidelines",
        "category": "safety",
        "content": (
            "Wellness coaching for adults 50+ must account for emotional and psychological health "
            "alongside physical metrics. Warning signs of depression: persistent low mood for 2+ "
            "weeks, loss of interest in previously enjoyed activities, changes in appetite or "
            "sleep, fatigue, feelings of worthlessness, difficulty concentrating, or withdrawal "
            "from social contact. Anxiety signs: excessive worry, restlessness, physical tension, "
            "avoidance behaviours. When a user expresses emotional distress: acknowledge first "
            "without immediately pivoting to solutions; validate their feelings; avoid toxic "
            "positivity ('just stay positive!'). Setbacks and plateaus are normal parts of any "
            "wellness journey — respond with normalisation and curiosity, not pressure or shame. "
            "Suggest professional help (therapist, psychologist, GP) gently when: distress is "
            "persistent, affects daily functioning, involves hopelessness or self-harm ideation, "
            "or is beyond the scope of wellness coaching. Never diagnose. Never minimise. "
            "Grief and major life transitions (retirement, loss of a spouse, health diagnoses) "
            "are common triggers in this age group and require extra empathy and patience. "
            "Physical activity itself is a strong evidence-based intervention for mild-to-moderate "
            "depression and anxiety — frame movement as mood support when appropriate."
        ),
    },
]


# ─── Seed logic ──────────────────────────────────────────────────

async def document_exists(session, title: str) -> bool:
    result = await session.execute(
        text("SELECT id FROM rag_documents WHERE metadata->>'title' = :title LIMIT 1"),
        {"title": title},
    )
    return result.fetchone() is not None


async def seed():
    print("Starting RAG seed...\n")

    async with AsyncSessionLocal() as session:
        for doc in DOCUMENTS:
            title = doc["title"]

            if await document_exists(session, title):
                print(f"  [SKIP] '{title}' already exists.")
                continue

            print(f"  [INSERT] '{title}' ({doc['category']}) — embedding...", end=" ", flush=True)
            await insert_document(
                db=session,
                title=title,
                content=doc["content"],
                category=doc["category"],
                user_id=None,
            )
            await session.commit()
            print("done.")

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
