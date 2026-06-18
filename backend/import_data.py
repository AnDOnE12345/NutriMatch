"""Import supplements from ChatGPT JSON into the database."""
import json
import re
from backend.database import SessionLocal, engine, Base, ensure_database_schema
from backend.models import Supplement

Base.metadata.create_all(bind=engine)
ensure_database_schema()


def clean_url(url):
    """Fix markdown-formatted URLs like [text](url) -> url"""
    if not url:
        return url
    # Match markdown link pattern [text](url)
    match = re.search(r'\[.*?\]\((.*?)\)', url)
    if match:
        return match.group(1)
    # Also handle [url](url) pattern
    match = re.search(r'\[(https?://[^\]]+)\]', url)
    if match:
        return match.group(1)
    return url


def import_data():
    with open("data_from_chat_gpt.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # Clear existing supplements
        db.query(Supplement).delete()
        db.commit()
        print(f"Cleared existing supplements.")

        count = 0
        for item in data:
            supplement = Supplement(
                name=item["name"],
                brand=item.get("brand"),
                category=item["category"],
                ingredients=item.get("ingredients", []),
                dosage=item.get("dosage"),
                form=item.get("form"),
                serving_size=item.get("dosage"),
                price=item.get("price"),
                currency="EUR",
                shop_name=item.get("shop_name"),
                shop_url=clean_url(item.get("shop_url", "")),
                certifications=[c for c in [
                    "organic" if item.get("is_organic") else None,
                    "vegan" if item.get("is_vegan") else None,
                ] if c],
                allergens=item.get("allergens", []),
                is_vegan=item.get("is_vegan", False),
                is_organic=item.get("is_organic", False),
                evidence_level=item.get("evidence_level", "moderate"),
                description_de=item.get("description_de", ""),
                description_en=item.get("description_en", ""),
            )
            db.add(supplement)
            count += 1

        db.commit()
        print(f"Imported {count} supplements from ChatGPT data.")
    finally:
        db.close()


if __name__ == "__main__":
    import_data()
