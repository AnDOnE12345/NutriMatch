import unittest
from unittest.mock import AsyncMock, patch

from backend.seed_data import SAMPLE_SUPPLEMENTS
from backend.services.chat_service import (
    SUPPLEMENT_KNOWLEDGE,
    generate_chat_reply,
    grounded_intake_reply,
    select_knowledge_entries,
)


class SupplementKnowledgeTests(unittest.IsolatedAsyncioTestCase):
    def test_every_catalog_ingredient_is_covered_once(self):
        catalog_keys = {
            ingredient
            for product in SAMPLE_SUPPLEMENTS
            for ingredient in product.get("ingredients", [])
        }
        mapped_keys = [
            ingredient
            for entry in SUPPLEMENT_KNOWLEDGE["entries"]
            for ingredient in entry["ingredient_keys"]
        ]
        self.assertEqual(catalog_keys, set(mapped_keys))
        self.assertEqual(len(mapped_keys), len(set(mapped_keys)))

    def test_alias_retrieval_supports_catalog_and_russian_names(self):
        self.assertEqual(select_knowledge_entries("Wann Magnesium einnehmen?")[0]["id"], "magnesium")
        self.assertEqual(select_knowledge_entries("Когда принимать витамин D?")[0]["id"], "vitamin_d")

    def test_intake_reply_contains_curated_sources(self):
        reply = grounded_intake_reply("Soll ich Eisen vor oder nach dem Essen einnehmen?")
        self.assertIn("Am besten nüchtern", reply)
        self.assertIn("https://www.nhs.uk/", reply)

    def test_unverified_timing_is_explicit(self):
        reply = grounded_intake_reply("Wann soll ich L-Theanin einnehmen?")
        self.assertIn("kein ausreichend verifiziertes", reply)

    async def test_intake_question_never_calls_model_provider(self):
        with patch(
            "backend.services.chat_service._call_ollama",
            new=AsyncMock(side_effect=AssertionError("LLM must not be called")),
        ) as model_call:
            reply = await generate_chat_reply(
                "local",
                "Kann ich Magnesium morgens mit Essen einnehmen?",
                [],
                [],
            )
        self.assertIn("Magnesium", reply)
        model_call.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
