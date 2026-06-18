"""
Meal Planner Service.
Generates daily meal plans based on user profile (TDEE, goals, diet, allergies).
Uses pre-generated meal database from meals_data.json.
"""
import json
import os
import random
import re
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session
from backend.models import QuestionnaireResponse


DATA_PATH = Path(__file__).resolve().parent.parent.parent / "meals_data.json"

_meals_db = None


def _load_meals():
    global _meals_db
    if _meals_db is None:
        if DATA_PATH.exists():
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                _meals_db = json.load(f)
        else:
            _meals_db = {"breakfast": [], "lunch": [], "dinner": []}
    return _meals_db


def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Mifflin-St Jeor equation."""
    if gender == "female":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.3,
    "moderate": 1.4,
    "active": 1.5,
    "very_active": 1.65,
}

ACTIVITY_DESCRIPTIONS = {
    "sedentary": {
        "de": "wenig Bewegung, vorwiegend sitzend",
        "en": "little movement, mostly seated",
    },
    "light": {
        "de": "leichte Alltagsbewegung oder 1-2 Trainings pro Woche",
        "en": "light daily movement or 1-2 workouts per week",
    },
    "moderate": {
        "de": "regelmaessige Bewegung oder 3-4 Trainings pro Woche",
        "en": "regular movement or 3-4 workouts per week",
    },
    "active": {
        "de": "viel Bewegung oder 4-5 Trainings pro Woche",
        "en": "high movement or 4-5 workouts per week",
    },
    "very_active": {
        "de": "koerperliche Arbeit oder fast taegliches intensives Training",
        "en": "physical work or almost daily intense training",
    },
}

GOAL_CALORIE_ADJUSTMENTS = {
    "weight_loss": -300,
    "muscle": +200,
}


def calculate_tdee(questionnaire: QuestionnaireResponse) -> int:
    """Calculate Total Daily Energy Expenditure."""
    return calculate_calorie_estimate(questionnaire)["target_calories"]


def calculate_calorie_estimate(questionnaire: QuestionnaireResponse) -> dict:
    """Calculate calorie target and expose the inputs for UI/debugging."""
    weight = questionnaire.weight_kg or 70
    height = questionnaire.height_cm or 170
    age = questionnaire.age or 30
    gender = questionnaire.gender or "male"
    activity = questionnaire.activity_level or "moderate"

    bmr = calculate_bmr(gender, weight, height, age)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity, ACTIVITY_MULTIPLIERS["moderate"])
    maintenance_calories = bmr * multiplier

    goal_adjustment = 0
    goals = questionnaire.goals or []
    for goal in goals:
        if goal in GOAL_CALORIE_ADJUSTMENTS:
            goal_adjustment += GOAL_CALORIE_ADJUSTMENTS[goal]

    target_calories = maintenance_calories + goal_adjustment

    return {
        "bmr": round(bmr),
        "activity_level": activity,
        "activity_multiplier": multiplier,
        "activity_description_de": ACTIVITY_DESCRIPTIONS.get(activity, {}).get("de", ""),
        "activity_description_en": ACTIVITY_DESCRIPTIONS.get(activity, {}).get("en", ""),
        "maintenance_calories": round(maintenance_calories),
        "goal_adjustment": goal_adjustment,
        "target_calories": round(target_calories),
    }


# Target macro split as percentage of daily calories
MACRO_TARGETS = {
    "protein_pct": 25,
    "carbs_pct": 50,
    "fat_pct": 25,
}

# Daily recommended nutrients (simplified, in mg or mcg as noted)
DAILY_NUTRIENT_TARGETS = {
    "vitamin_d": {"amount": 20, "unit": "mcg", "label_de": "Vitamin D", "label_en": "Vitamin D"},
    "vitamin_c": {"amount": 100, "unit": "mg", "label_de": "Vitamin C", "label_en": "Vitamin C"},
    "vitamin_b12": {"amount": 4, "unit": "mcg", "label_de": "Vitamin B12", "label_en": "Vitamin B12"},
    "calcium": {"amount": 1000, "unit": "mg", "label_de": "Calcium", "label_en": "Calcium"},
    "magnesium": {"amount": 400, "unit": "mg", "label_de": "Magnesium", "label_en": "Magnesium"},
    "iron": {"amount": 14, "unit": "mg", "label_de": "Eisen", "label_en": "Iron"},
    "zinc": {"amount": 10, "unit": "mg", "label_de": "Zink", "label_en": "Zinc"},
    "omega3": {"amount": 250, "unit": "mg", "label_de": "Omega-3", "label_en": "Omega-3"},
    "fiber": {"amount": 30, "unit": "g", "label_de": "Ballaststoffe", "label_en": "Fiber"},
    "potassium": {"amount": 3500, "unit": "mg", "label_de": "Kalium", "label_en": "Potassium"},
}


INGREDIENT_PORTIONS = {
    "Haferflocken": (60, "g"),
    "Blaubeeren": (100, "g"),
    "Walnuesse": (25, "g"),
    "Walnüsse": (25, "g"),
    "Naturtofu": (160, "g"),
    "Spinat": (80, "g"),
    "Tomaten": (150, "g"),
    "Apfel": (150, "g"),
    "Mandeln": (25, "g"),
    "Chiasamen": (20, "g"),
    "Griechischer Joghurt": (200, "g"),
    "Himbeeren": (100, "g"),
    "Mango": (120, "g"),
    "Kokosdrink": (200, "ml"),
    "Kokosmilch": (120, "ml"),
    "Eier": (2, "Stk"),
    "Ei": (1, "Stk"),
    "Feta": (60, "g"),
    "Kraeuter": (10, "g"),
    "Kräuter": (10, "g"),
    "Vollkornbrot": (90, "g"),
    "Huettenkaese": (150, "g"),
    "Hüttenkäse": (150, "g"),
    "Radieschen": (80, "g"),
    "Vollkorntoast": (90, "g"),
    "Avocado": (80, "g"),
    "Gurke": (100, "g"),
    "Raeucherlachs": (80, "g"),
    "Räucherlachs": (80, "g"),
    "Banane": (120, "g"),
    "Orange": (150, "g"),
    "Hirse": (70, "g"),
    "Birne": (150, "g"),
    "Gruenkohl": (80, "g"),
    "Grünkohl": (80, "g"),
    "Leinsamen": (15, "g"),
    "Kiwi": (100, "g"),
    "Kefir": (250, "ml"),
    "Haferkleie": (40, "g"),
    "Kokosjoghurt": (180, "g"),
    "Heidelbeeren": (100, "g"),
    "Joghurt": (180, "g"),
    "Pfirsich": (150, "g"),
    "Roggenbrot": (90, "g"),
    "Raeucherforelle": (90, "g"),
    "Räucherforelle": (90, "g"),
    "Karotten": (120, "g"),
    "Sellerie": (80, "g"),
    "Putenbrust": (150, "g"),
    "Gruene Bohnen": (140, "g"),
    "Grüne Bohnen": (140, "g"),
    "Couscous": (75, "g"),
    "Falafel": (120, "g"),
    "Bulgur": (75, "g"),
    "Hummus": (70, "g"),
    "Vollkornnudeln": (90, "g"),
    "Brokkoli": (180, "g"),
    "Haehnchenbrust": (150, "g"),
    "Hähnchenbrust": (150, "g"),
    "Naturreis": (80, "g"),
    "Paprika": (150, "g"),
    "Lachs": (140, "g"),
    "Sushireis": (90, "g"),
    "Edamame": (100, "g"),
    "Linsen": (90, "g"),
    "Kartoffeln": (250, "g"),
    "Kabeljau": (160, "g"),
    "Zucchini": (180, "g"),
    "Champignons": (150, "g"),
    "Quinoa": (75, "g"),
    "Kichererbsen": (140, "g"),
    "Suesskartoffel": (220, "g"),
    "Süßkartoffel": (220, "g"),
    "Rindfleisch": (150, "g"),
    "Blumenkohl": (220, "g"),
    "Spätzle": (180, "g"),
    "Bergkaese": (50, "g"),
    "Bergkäse": (50, "g"),
    "Zwiebeln": (80, "g"),
    "Aubergine": (180, "g"),
    "Mozzarella": (100, "g"),
    "Weizennudeln": (90, "g"),
    "Thunfisch": (120, "g"),
    "Roemersalat": (120, "g"),
    "Römersalat": (120, "g"),
    "Parmesan": (25, "g"),
    "Garnelen": (160, "g"),
    "Pak Choi": (150, "g"),
    "Miso": (20, "g"),
    "Rote Linsen": (90, "g"),
    "Halloumi": (100, "g"),
    "Erbsen": (120, "g"),
    "Spargel": (160, "g"),
    "Vollkornspaghetti": (90, "g"),
    "Weiße Bohnen": (140, "g"),
    "Weisse Bohnen": (140, "g"),
    "Petersilie": (10, "g"),
    "Putenhackfleisch": (150, "g"),
    "Oliven": (40, "g"),
    "Kidneybohnen": (140, "g"),
    "Tempeh": (150, "g"),
    "Forelle": (150, "g"),
    "Dill": (8, "g"),
    "Cheddar": (40, "g"),
    "Sahne": (60, "ml"),
    "Seitan": (160, "g"),
    "Lammfleisch": (150, "g"),
    "Kuerbiskerne": (25, "g"),
    "Kürbiskerne": (25, "g"),
    "Beeren": (120, "g"),
    "Reis": (80, "g"),
    "Zitrone": (0.5, "Stk"),
    "Olivenoel": (10, "ml"),
    "Olivenöl": (10, "ml"),
    "Sesamoel": (6, "ml"),
    "Sesamöl": (6, "ml"),
    "Salz": (1, "g"),
    "Pfeffer": (1, "g"),
    "Knoblauch": (1, "Stk"),
    "Zitronensaft": (15, "ml"),
    "Essig": (10, "ml"),
    "Sojasauce": (15, "ml"),
    "Paprikapulver": (2, "g"),
    "Kreuzkuemmel": (2, "g"),
    "Kreuzkümmel": (2, "g"),
    "Zimt": (2, "g"),
    "Ahornsirup": (10, "ml"),
}

INGREDIENT_EN_NAMES = {
    "Olivenoel": "Olive oil",
    "Olivenöl": "Olive oil",
    "Sesamoel": "Sesame oil",
    "Sesamöl": "Sesame oil",
    "Salz": "Salt",
    "Pfeffer": "Pepper",
    "Knoblauch": "Garlic",
    "Zitronensaft": "Lemon juice",
    "Essig": "Vinegar",
    "Sojasauce": "Soy sauce",
    "Paprikapulver": "Paprika powder",
    "Kreuzkuemmel": "Cumin",
    "Kreuzkümmel": "Cumin",
    "Zimt": "Cinnamon",
    "Ahornsirup": "Maple syrup",
    "Ei": "Egg",
    "Eier": "Eggs",
}

PANTRY_INGREDIENTS = {
    "Olivenoel", "Olivenöl", "Sesamoel", "Sesamöl", "Salz", "Pfeffer",
    "Knoblauch", "Zitronensaft", "Essig", "Sojasauce", "Paprikapulver",
    "Kreuzkuemmel", "Kreuzkümmel", "Zimt", "Ahornsirup",
}


def _filter_meals(meals: list, diet_type: str, allergies: list) -> list:
    """Filter meals by diet and allergies."""
    filtered = []
    for meal in meals:
        # Diet filter
        meal_diets = meal.get("suitable_for", [])
        if diet_type and diet_type != "omnivore":
            if diet_type not in meal_diets:
                continue

        # Allergy filter
        meal_allergens = meal.get("allergens", [])
        if any(a in meal_allergens for a in allergies):
            continue

        filtered.append(meal)
    return filtered


def _pick_meal(meals: list, target_cal: float, used_ids: set) -> dict | None:
    """Pick a meal close to target calories, avoiding repeats."""
    candidates = [m for m in meals if m.get("id") not in used_ids]
    if not candidates:
        candidates = meals  # fallback: allow repeats

    # Sort by calorie closeness
    candidates.sort(key=lambda m: abs(m.get("calories", 0) - target_cal))
    # Pick from top 5 randomly for variety
    top = candidates[:5]
    if not top:
        return None

    # Use date as seed for daily consistency
    today_seed = date.today().toordinal()
    rng = random.Random(today_seed + hash(str(target_cal)))
    choice = rng.choice(top)
    return choice


def _clean_image_url(url: str | None) -> str | None:
    """Normalize image URLs imported from markdown-like generated data."""
    if not url:
        return None

    url = str(url).strip()
    markdown_match = re.search(r"\]\((https?://[^)]+)\)", url)
    if markdown_match:
        return markdown_match.group(1)

    bracketed_match = re.search(r"https?://[^\]\s)]+", url)
    if bracketed_match:
        return bracketed_match.group(0)

    return url.strip("[]() ")


def _scale_nutrients(nutrients: dict, serving_factor: float) -> dict:
    return {
        nutrient: round(amount * serving_factor, 1)
        for nutrient, amount in (nutrients or {}).items()
    }


def _format_amount(amount: float, unit: str) -> float | int:
    if unit == "Stk":
        rounded = round(amount * 2) / 2
        return int(rounded) if rounded.is_integer() else rounded

    if unit == "g" and amount <= 5:
        rounded = round(amount, 1)
        return int(rounded) if rounded.is_integer() else rounded

    step = 5
    rounded = round(amount / step) * step
    return max(step, int(rounded))


def _normalize_ingredient_name(name: str) -> str:
    return (
        str(name)
        .lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def _ingredient_detail(name_de: str, name_en: str | None, serving_factor: float) -> dict:
    base_amount, unit = INGREDIENT_PORTIONS.get(name_de, (100, "g"))
    return {
        "name_de": name_de,
        "name_en": name_en or INGREDIENT_EN_NAMES.get(name_de, name_de),
        "amount": _format_amount(base_amount * serving_factor, unit),
        "unit": unit,
    }


def _append_ingredient(
    details: list[dict],
    seen: set[str],
    name_de: str,
    serving_factor: float,
    name_en: str | None = None,
) -> None:
    normalized = _normalize_ingredient_name(name_de)
    if normalized in seen:
        return

    details.append(_ingredient_detail(name_de, name_en, serving_factor))
    seen.add(normalized)


def _add_named_ingredients(meal: dict, details: list[dict], seen: set[str], serving_factor: float) -> None:
    text = " ".join([
        meal.get("name_de") or "",
        meal.get("name") or "",
    ])
    normalized_text = _normalize_ingredient_name(text)

    candidates = [
        ingredient for ingredient in INGREDIENT_PORTIONS
        if ingredient not in PANTRY_INGREDIENTS
    ]
    for ingredient in sorted(candidates, key=len, reverse=True):
        normalized = _normalize_ingredient_name(ingredient)
        if normalized in normalized_text:
            if any(normalized in seen_name or seen_name in normalized for seen_name in seen):
                continue
            _append_ingredient(
                details,
                seen,
                ingredient,
                serving_factor,
                INGREDIENT_EN_NAMES.get(ingredient),
            )


def _recipe_extra_ingredients(meal: dict) -> list[str]:
    text = _normalize_ingredient_name(" ".join([
        meal.get("name_de") or "",
        meal.get("name") or "",
        " ".join(meal.get("ingredients_de") or meal.get("ingredients") or []),
    ]))
    extras = []

    sweet_terms = ["hafer", "porridge", "joghurt", "pudding", "beeren", "mango", "pfirsich"]
    savory_terms = [
        "lachs", "forelle", "kabeljau", "haehnchen", "pute", "rind", "tempeh",
        "tofu", "bowl", "salat", "chili", "curry", "nudeln", "reis", "quinoa",
        "kartoffel", "gemuese", "brokkoli", "bohnen", "linsen", "kichererbsen",
    ]

    if any(term in text for term in savory_terms):
        extras.extend(["Olivenöl", "Salz", "Pfeffer"])

    if any(term in text for term in ["lachs", "forelle", "kabeljau", "salat", "avocado"]):
        extras.append("Zitronensaft")

    if any(term in text for term in ["sushi", "asiatisch", "tofu", "tempeh", "pak choi", "miso"]):
        extras.extend(["Sojasauce", "Sesamöl"])

    if any(term in text for term in ["chili", "curry", "linsen", "bohnen", "kichererbsen"]):
        extras.extend(["Knoblauch", "Paprikapulver", "Kreuzkümmel"])

    if any(term in text for term in ["nudeln", "spaghetti", "tomaten", "champignons", "zucchini"]):
        extras.append("Knoblauch")

    if any(term in text for term in sweet_terms):
        extras.append("Zimt")
        if "vegan" not in (meal.get("suitable_for") or []):
            extras.append("Ahornsirup")

    return extras


def _build_ingredient_details(meal: dict, serving_factor: float) -> list[dict]:
    ingredients_de = meal.get("ingredients_de") or meal.get("ingredients") or []
    ingredients_en = meal.get("ingredients_en") or meal.get("ingredients") or []
    details = []
    seen = set()

    for index, ingredient_de in enumerate(ingredients_de):
        ingredient_en = (
            ingredients_en[index]
            if index < len(ingredients_en)
            else ingredient_de
        )
        _append_ingredient(details, seen, ingredient_de, serving_factor, ingredient_en)

    _add_named_ingredients(meal, details, seen, serving_factor)

    for ingredient in _recipe_extra_ingredients(meal):
        _append_ingredient(
            details,
            seen,
            ingredient,
            serving_factor,
            INGREDIENT_EN_NAMES.get(ingredient),
        )

    return details


def _get_serving_factor(target_calories: int, base_total_calories: int) -> float:
    if base_total_calories <= 0:
        return 1.0

    ratio = target_calories / base_total_calories
    if 0.9 <= ratio <= 1.1:
        return 1.0

    return round(min(max(ratio, 0.75), 1.5), 2)


def _prepare_meal(meal: dict | None, target_cal: float, serving_factor: float = 1.0) -> dict:
    if not meal:
        return {
            "target_cal": round(target_cal),
            "nutrient_coverage": {},
        }

    prepared = dict(meal)
    prepared["image_url"] = _clean_image_url(prepared.get("image_url"))
    prepared["base_calories"] = prepared.get("calories", 0)
    prepared["serving_factor"] = serving_factor
    prepared["calories"] = round(prepared.get("calories", 0) * serving_factor)
    prepared["protein"] = round(prepared.get("protein", 0) * serving_factor, 1)
    prepared["carbs"] = round(prepared.get("carbs", 0) * serving_factor, 1)
    prepared["fat"] = round(prepared.get("fat", 0) * serving_factor, 1)
    prepared["nutrients"] = _scale_nutrients(prepared.get("nutrients", {}), serving_factor)
    prepared["ingredient_details"] = _build_ingredient_details(prepared, serving_factor)
    prepared["target_cal"] = round(target_cal)
    return prepared


def generate_meal_plan(questionnaire: QuestionnaireResponse) -> dict:
    """Generate a daily meal plan for the user."""
    meals_db = _load_meals()

    calorie_estimate = calculate_calorie_estimate(questionnaire)
    tdee = calorie_estimate["target_calories"]
    diet_type = questionnaire.diet_type or "omnivore"
    allergies = questionnaire.allergies or []

    # Calorie distribution: breakfast 25%, lunch 40%, dinner 35%
    cal_breakfast = tdee * 0.25
    cal_lunch = tdee * 0.40
    cal_dinner = tdee * 0.35

    used_ids = set()

    # Filter meals
    breakfasts = _filter_meals(meals_db.get("breakfast", []), diet_type, allergies)
    lunches = _filter_meals(meals_db.get("lunch", []), diet_type, allergies)
    dinners = _filter_meals(meals_db.get("dinner", []), diet_type, allergies)

    breakfast = _pick_meal(breakfasts, cal_breakfast, used_ids)
    if breakfast:
        used_ids.add(breakfast.get("id"))
    lunch = _pick_meal(lunches, cal_lunch, used_ids)
    if lunch:
        used_ids.add(lunch.get("id"))
    dinner = _pick_meal(dinners, cal_dinner, used_ids)

    base_total_calories = sum(
        m.get("calories", 0)
        for m in [breakfast, lunch, dinner]
        if m
    )
    serving_factor = _get_serving_factor(tdee, base_total_calories)

    breakfast_data = _prepare_meal(breakfast, cal_breakfast, serving_factor)
    lunch_data = _prepare_meal(lunch, cal_lunch, serving_factor)
    dinner_data = _prepare_meal(dinner, cal_dinner, serving_factor)

    # Calculate total daily nutrients
    total_nutrients = {}
    for meal in [breakfast_data, lunch_data, dinner_data]:
        if not meal:
            continue
        for nutrient, amount in meal.get("nutrients", {}).items():
            total_nutrients[nutrient] = total_nutrients.get(nutrient, 0) + amount

    # Calculate coverage percentages
    nutrient_coverage = {}
    for nutrient, target_info in DAILY_NUTRIENT_TARGETS.items():
        actual = total_nutrients.get(nutrient, 0)
        target = target_info["amount"]
        pct = round(min(100, actual / target * 100)) if target > 0 else 0
        nutrient_coverage[nutrient] = {
            "actual": round(actual, 1),
            "target": target,
            "unit": target_info["unit"],
            "percent": pct,
            "label_de": target_info["label_de"],
            "label_en": target_info["label_en"],
        }

    # Calculate per-meal coverage
    def meal_coverage(meal):
        if not meal:
            return {}
        coverage = {}
        for nutrient, target_info in DAILY_NUTRIENT_TARGETS.items():
            actual = meal.get("nutrients", {}).get(nutrient, 0)
            target = target_info["amount"]
            raw_pct = round(actual / target * 100) if target > 0 else 0
            pct = min(100, raw_pct)
            if pct > 0:
                coverage[nutrient] = {
                    "actual": round(actual, 1),
                    "target": target,
                    "unit": target_info["unit"],
                    "percent": pct,
                    "raw_percent": raw_pct,
                    "label_de": target_info["label_de"],
                    "label_en": target_info["label_en"],
                }
        return coverage

    # Identify deficiencies (< 60% coverage) → supplement opportunity
    deficiencies = []
    for nutrient, info in nutrient_coverage.items():
        if info["percent"] < 60:
            deficiencies.append({
                "nutrient": nutrient,
                "coverage_percent": info["percent"],
                "label_de": info["label_de"],
                "label_en": info["label_en"],
            })

    total_calories = sum(
        m.get("calories", 0)
        for m in [breakfast_data, lunch_data, dinner_data]
        if m
    )

    calorie_gap = total_calories - tdee
    calorie_coverage_percent = round(total_calories / tdee * 100) if tdee else 0

    breakfast_data["nutrient_coverage"] = meal_coverage(breakfast_data)
    lunch_data["nutrient_coverage"] = meal_coverage(lunch_data)
    dinner_data["nutrient_coverage"] = meal_coverage(dinner_data)

    return {
        "date": date.today().isoformat(),
        "tdee": tdee,
        "calorie_estimate": calorie_estimate,
        "base_total_calories": base_total_calories,
        "total_calories": total_calories,
        "calorie_gap": calorie_gap,
        "calorie_coverage_percent": calorie_coverage_percent,
        "serving_factor": serving_factor,
        "meals": {
            "breakfast": breakfast_data,
            "lunch": lunch_data,
            "dinner": dinner_data,
        },
        "daily_nutrient_coverage": nutrient_coverage,
        "deficiencies": deficiencies,
    }
