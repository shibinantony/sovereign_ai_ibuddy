from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.db import ConversationNotFoundError, ConversationStore


class ConversationStoreTests(unittest.TestCase):
    def test_history_survives_repository_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "persistent.db"
            first = ConversationStore(database)
            conversation = first.create_conversation()
            first.add_message(conversation["id"], "user", "A title derived from this prompt")
            first.add_message(
                conversation["id"],
                "assistant",
                "Stored answer.",
                [
                    {
                        "title": "Source",
                        "url": "https://example.com",
                        "snippet": "",
                        "domain": "example.com",
                    }
                ],
            )

            reopened = ConversationStore(database)
            detail = reopened.get_conversation(conversation["id"])

            self.assertEqual(detail["title"], "A title derived from this prompt")
            self.assertEqual(detail["message_count"], 2)
            self.assertEqual(detail["messages"][1]["content"], "Stored answer.")
            self.assertEqual(detail["messages"][1]["sources"][0]["title"], "Source")
            self.assertEqual(
                reopened.context_messages(conversation["id"], limit=1),
                [],
            )
            self.assertEqual(
                reopened.context_messages(conversation["id"], limit=2),
                [
                    {"role": "user", "content": "A title derived from this prompt"},
                    {"role": "assistant", "content": "Stored answer."},
                ],
            )

    def test_delete_cascades_messages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ConversationStore(Path(directory) / "cascade.db")
            conversation = store.create_conversation("Disposable")
            store.add_message(conversation["id"], "user", "hello")

            store.delete_conversation(conversation["id"])

            with self.assertRaises(ConversationNotFoundError):
                store.get_conversation(conversation["id"])


if __name__ == "__main__":
    unittest.main()
