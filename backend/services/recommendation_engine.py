"""
Recommendation Engine for personalized supplement suggestions.
Combines questionnaire data, health tracking data, and supplement database
to generate personalized recommendations.
"""

from sqlalchemy.orm import Session
from backend.models import User, QuestionnaireResponse, HealthData, Supplement, Recommendation


# Human-readable nutrient names
NUTRIENT_NAMES = {
    "vitamin_b12": "Vitamin B12",
    "iron": "Eisen",
    "coq10": "Coenzym Q10",
    "magnesium": "Magnesium",
    "vitamin_d": "Vitamin D",
    "melatonin": "Melatonin",
    "l_theanine": "L-Theanin",
    "valerian": "Baldrian",
    "zinc": "Zink",
    "vitamin_c": "Vitamin C",
    "elderberry": "Holunder",
    "echinacea": "Echinacea",
    "protein": "Protein",
    "creatine": "Kreatin",
    "bcaa": "BCAA",
    "green_tea_extract": "Grüntee-Extrakt",
    "cla": "CLA",
    "l_carnitine": "L-Carnitin",
    "chromium": "Chrom",
    "fiber": "Ballaststoffe",
    "biotin": "Biotin",
    "collagen": "Kollagen",
    "vitamin_e": "Vitamin E",
    "omega3": "Omega-3",
    "probiotics": "Probiotika",
    "digestive_enzymes": "Verdauungsenzyme",
    "ginger": "Ingwer",
    "peppermint": "Pfefferminze",
    "ashwagandha": "Ashwagandha",
    "rhodiola": "Rhodiola",
    "b_complex": "Vitamin B-Komplex",
    "ginkgo": "Ginkgo",
    "lion_mane": "Löwenmähne (Lion's Mane)",
    "caffeine": "Koffein",
    "b_vitamins": "B-Vitamine",
    "glucosamine": "Glucosamin",
    "chondroitin": "Chondroitin",
    "turmeric": "Kurkuma",
    "electrolytes": "Elektrolyte",
    "potassium": "Kalium",
    "calcium": "Calcium",
}

GOAL_NAMES = {
    "energy": "Energie",
    "sleep": "Schlaf",
    "immunity": "Immunsystem",
    "muscle": "Muskelaufbau",
    "weight_loss": "Gewichtsabnahme",
    "skin_hair": "Haut & Haare",
    "digestion": "Verdauung",
    "stress": "Stressabbau",
    "focus": "Konzentration",
    "joints": "Gelenke",
}

DIET_NAMES = {
    "omnivore": "Mischkost",
    "vegetarian": "vegetarische Ernährung",
    "vegan": "vegane Ernährung",
    "pescatarian": "pescetarische Ernährung",
    "keto": "Keto-Diät",
    "paleo": "Paleo-Diät",
}

ACTIVITY_NAMES = {
    "sedentary": "sitzend",
    "light": "leicht aktiv",
    "moderate": "moderat aktiv",
    "active": "aktiv",
    "very_active": "sehr aktiv",
}


def _readable_nutrients(nutrients: list) -> str:
    """Convert nutrient IDs to human-readable names."""
    return ", ".join(NUTRIENT_NAMES.get(n, n.replace('_', ' ').title()) for n in nutrients)


# Mapping: health goals -> relevant supplement categories and specific nutrients
GOAL_SUPPLEMENT_MAP = {
    "energy": {
        "nutrients": ["vitamin_b12", "iron", "coq10", "magnesium", "vitamin_d"],
        "categories": ["vitamin", "mineral"],
    },
    "sleep": {
        "nutrients": ["magnesium", "melatonin", "l_theanine", "valerian", "zinc"],
        "categories": ["mineral", "herbal"],
    },
    "immunity": {
        "nutrients": ["vitamin_c", "vitamin_d", "zinc", "elderberry", "echinacea"],
        "categories": ["vitamin", "mineral", "herbal"],
    },
    "muscle": {
        "nutrients": ["protein", "creatine", "bcaa", "vitamin_d", "magnesium"],
        "categories": ["amino_acid", "mineral"],
    },
    "weight_loss": {
        "nutrients": ["green_tea_extract", "cla", "l_carnitine", "chromium", "fiber"],
        "categories": ["herbal", "mineral"],
    },
    "skin_hair": {
        "nutrients": ["biotin", "collagen", "vitamin_e", "zinc", "omega3"],
        "categories": ["vitamin", "mineral", "omega"],
    },
    "digestion": {
        "nutrients": ["probiotics", "fiber", "digestive_enzymes", "ginger", "peppermint"],
        "categories": ["probiotic", "herbal"],
    },
    "stress": {
        "nutrients": ["ashwagandha", "rhodiola", "magnesium", "b_complex", "l_theanine"],
        "categories": ["herbal", "vitamin", "mineral"],
    },
    "focus": {
        "nutrients": ["omega3", "ginkgo", "lion_mane", "caffeine", "b_vitamins"],
        "categories": ["omega", "herbal", "vitamin"],
    },
    "joints": {
        "nutrients": ["glucosamine", "chondroitin", "omega3", "turmeric", "collagen"],
        "categories": ["omega", "herbal"],
    },
}

# Nutrients commonly needed based on diet type
DIET_DEFICIENCY_MAP = {
    "vegan": ["vitamin_b12", "iron", "omega3", "vitamin_d", "zinc", "calcium"],
    "vegetarian": ["vitamin_b12", "iron", "omega3", "vitamin_d"],
    "keto": ["magnesium", "potassium", "fiber", "vitamin_c"],
    "paleo": ["calcium", "vitamin_d"],
    "pescatarian": ["vitamin_b12", "iron"],
    "omnivore": ["vitamin_d", "magnesium"],
}

# Activity level adjustments
ACTIVITY_ADJUSTMENTS = {
    "very_active": ["magnesium", "electrolytes", "protein", "bcaa", "iron"],
    "active": ["magnesium", "protein", "vitamin_d"],
    "moderate": ["vitamin_d", "magnesium"],
    "light": ["vitamin_d"],
    "sedentary": ["vitamin_d", "omega3"],
}


def _score_supplement(supplement: Supplement, needed_nutrients: list, preferences: dict) -> float:
    """Score a supplement based on how well it matches user needs."""
    score = 0.0

    # Check ingredient match
    if supplement.ingredients:
        for nutrient in needed_nutrients:
            for ingredient in supplement.ingredients:
                if nutrient.lower() in str(ingredient).lower():
                    score += 10.0
                    break

    # Preference matching
    if preferences.get("prefer_organic") and supplement.is_organic:
        score += 3.0
    if preferences.get("is_vegan") and supplement.is_vegan:
        score += 5.0

    # Form preference
    if preferences.get("preferred_form") and supplement.form == preferences["preferred_form"]:
        score += 2.0

    # Budget check
    budget = preferences.get("budget_monthly")
    if budget and supplement.price:
        if supplement.price <= budget * 0.3:  # Supplement should be max 30% of budget
            score += 2.0
        elif supplement.price > budget * 0.5:
            score -= 3.0

    # Evidence level bonus
    evidence_scores = {"strong": 5.0, "moderate": 3.0, "emerging": 1.0, "limited": 0.0}
    if supplement.evidence_level:
        score += evidence_scores.get(supplement.evidence_level, 0)

    # Allergen check - disqualify if contains user allergens
    user_allergies = preferences.get("allergies", [])
    if supplement.allergens and user_allergies:
        for allergen in supplement.allergens:
            if allergen in user_allergies:
                return -100.0  # Disqualify

    return score


def generate_recommendations(user: User, db: Session) -> Recommendation:
    """Generate personalized supplement recommendations for a user."""

    # Get questionnaire data
    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.user_id == user.id
    ).first()

    if not questionnaire:
        # Return basic recommendation without questionnaire
        recommendation = Recommendation(
            user_id=user.id,
            supplements=[],
            reasoning={"message": "Please complete the questionnaire for personalized recommendations"},
            score=0.0,
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)
        return recommendation

    # Build list of needed nutrients
    needed_nutrients = set()
    reasoning = {}

    # 1. Goals-based nutrients
    goals = questionnaire.goals or []
    for goal in goals:
        if goal in GOAL_SUPPLEMENT_MAP:
            nutrients = GOAL_SUPPLEMENT_MAP[goal]["nutrients"]
            needed_nutrients.update(nutrients)
            goal_name = GOAL_NAMES.get(goal, goal)
            reasoning[goal] = f"Ziel «{goal_name}»: empfohlen werden {_readable_nutrients(nutrients)}"

    # 2. Diet-based deficiencies
    diet = questionnaire.diet_type or "omnivore"
    if diet in DIET_DEFICIENCY_MAP:
        diet_nutrients = DIET_DEFICIENCY_MAP[diet]
        needed_nutrients.update(diet_nutrients)
        diet_name = DIET_NAMES.get(diet, diet)
        reasoning["diet"] = f"Bei {diet_name} können fehlen: {_readable_nutrients(diet_nutrients)}"

    # 3. Activity level adjustments
    activity = questionnaire.activity_level or "moderate"
    if activity in ACTIVITY_ADJUSTMENTS:
        activity_nutrients = ACTIVITY_ADJUSTMENTS[activity]
        needed_nutrients.update(activity_nutrients)
        activity_name = ACTIVITY_NAMES.get(activity, activity)
        reasoning["activity"] = f"Aktivitätslevel «{activity_name}»: empfohlen {_readable_nutrients(activity_nutrients)}"

    # 4. Health data integration (sleep, stress)
    health_data = db.query(HealthData).filter(
        HealthData.user_id == user.id
    ).order_by(HealthData.recorded_at.desc()).limit(30).all()

    for entry in health_data:
        if entry.data_type == "sleep" and entry.value:
            avg_sleep = entry.value.get("hours", 7)
            if avg_sleep < 6:
                needed_nutrients.update(["magnesium", "melatonin", "l_theanine"])
                reasoning["sleep_data"] = "Low sleep detected: adding sleep support supplements"

    # Build preferences dict
    preferences = {
        "prefer_organic": questionnaire.prefer_organic,
        "is_vegan": questionnaire.diet_type == "vegan",
        "preferred_form": questionnaire.preferred_form,
        "budget_monthly": questionnaire.budget_monthly,
        "allergies": questionnaire.allergies or [],
    }

    # Score all supplements
    all_supplements = db.query(Supplement).all()
    scored = []
    for supp in all_supplements:
        score = _score_supplement(supp, list(needed_nutrients), preferences)
        if score > 0:
            scored.append((supp, score))

    # Sort by score and take top recommendations
    scored.sort(key=lambda x: x[1], reverse=True)
    top_supplements = scored[:8]

    # Normalize score to 0-100 percentage
    max_possible_score = 35.0  # approximate max from ingredient match + bonuses

    # Build recommendation
    supplement_list = [
        {
            "id": supp.id,
            "name": supp.name,
            "brand": supp.brand,
            "score": round(min(100, score / max_possible_score * 100), 1),
            "price": supp.price,
            "category": supp.category,
        }
        for supp, score in top_supplements
    ]

    overall_score = min(100, (sum(s[1] for s in top_supplements) / max(len(top_supplements), 1)) / max_possible_score * 100)

    recommendation = Recommendation(
        user_id=user.id,
        supplements=supplement_list,
        reasoning=reasoning,
        score=round(overall_score, 1),
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation
