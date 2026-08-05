from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "self_evolution.py"
SPEC = importlib.util.spec_from_file_location("self_evolution", SCRIPT)
assert SPEC and SPEC.loader
self_evolution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(self_evolution)


class RevisionAttributionTests(unittest.TestCase):
    def test_distinguishes_all_sources_and_excludes_unchanged(self) -> None:
        draft = "保留\n删除我\n共同锚点\n旧句表达\n末尾"
        final = "保留\n共同锚点\n新句表达\n末尾\n新增"
        changes = self_evolution.classify_revision(draft, final)
        kinds = {change["kind"] for change in changes}
        self.assertEqual({"unchanged", "deleted", "rewritten", "added"}, kinds)
        for change in changes:
            if change["kind"] == "unchanged":
                self.assertEqual("assistant", change["attribution"])
                self.assertFalse(change["learning_eligible"])
            else:
                self.assertEqual("user", change["attribution"])
                self.assertTrue(change["learning_eligible"])

    def test_mixed_replace_block_is_split(self) -> None:
        changes = self_evolution.classify_revision(
            "保留\n删除句\n旧写法内容\n结尾",
            "保留\n新写法内容\n用户新增\n结尾",
        )
        kinds = [change["kind"] for change in changes]
        self.assertIn("deleted", kinds)
        self.assertIn("rewritten", kinds)
        self.assertIn("added", kinds)

    def test_formatting_headings_and_images_are_not_user_writing(self) -> None:
        changes = self_evolution.classify_revision(
            "正文原样",
            "## 新增导航\n\n**正文原样**\n\n![图](new.png)",
            "text",
        )
        self.assertEqual(["unchanged"], [change["kind"] for change in changes])

    def test_source_id_is_stable_across_layout_only_changes(self) -> None:
        baseline = self_evolution.source_id_for_final("正文原样", "text")
        formatted = self_evolution.source_id_for_final(
            "## 新导航\n\n**正文原样**\n\n![图](new.png)", "text"
        )
        self.assertEqual(baseline, formatted)


class PromotionTests(unittest.TestCase):
    def test_inferred_rule_needs_two_distinct_finals(self) -> None:
        state = self_evolution.new_state()
        self_evolution.record_preference(
            state, key="shorter-lists", rule="不制造冗长列表", source_id="final-a"
        )
        self.assertEqual("pending", state["rules"]["shorter-lists"]["status"])
        self_evolution.record_preference(
            state, key="shorter-lists", rule="不制造冗长列表", source_id="final-a"
        )
        self.assertEqual("pending", state["rules"]["shorter-lists"]["status"])
        self_evolution.record_preference(
            state, key="shorter-lists", rule="不制造冗长列表", source_id="final-b"
        )
        self.assertEqual("effective", state["rules"]["shorter-lists"]["status"])

    def test_latest_explicit_instruction_overrides_and_blocks_inference(self) -> None:
        state = self_evolution.new_state()
        self_evolution.record_preference(
            state, key="lists", rule="尽量不用列表", source_id="final-a"
        )
        self_evolution.record_preference(
            state,
            key="lists",
            rule="列表可用于真实步骤",
            source_id="explicit-new",
            explicit=True,
        )
        result = self_evolution.record_preference(
            state, key="lists", rule="尽量不用列表", source_id="final-b"
        )
        self.assertEqual("ignored", result["status"])
        self.assertEqual("列表可用于真实步骤", state["rules"]["lists"]["rule"])

    def test_only_explicit_rule_can_supersede_another_key(self) -> None:
        state = self_evolution.new_state()
        self_evolution.record_preference(
            state, key="old-tone", rule="旧规则", source_id="explicit-old", explicit=True
        )
        with self.assertRaises(ValueError):
            self_evolution.record_preference(
                state,
                key="new-tone",
                rule="推断规则",
                source_id="final-a",
                supersedes=["old-tone"],
            )
        self_evolution.record_preference(
            state,
            key="new-tone",
            rule="最新明确规则",
            source_id="explicit-new",
            explicit=True,
            supersedes=["old-tone"],
        )
        self.assertNotIn("old-tone", state["rules"])
        self.assertIn("new-tone", state["rules"])

    def test_record_cli_persists_ledger_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "signals.json"
            memory_file = Path(directory) / "memory.md"
            base = [
                "python3",
                str(SCRIPT),
                "record",
                "--domain",
                "text",
                "--key",
                "concise-lists",
                "--rule",
                "列表只用于真实步骤",
                "--state-file",
                str(state_file),
                "--memory-file",
                str(memory_file),
            ]
            subprocess.run(base + ["--source-id", "final-a"], check=True, capture_output=True)
            subprocess.run(base + ["--source-id", "final-b"], check=True, capture_output=True)
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual("effective", state["rules"]["concise-lists"]["status"])
            self.assertIn("列表只用于真实步骤", memory_file.read_text(encoding="utf-8"))


class TriggerTests(unittest.TestCase):
    def test_visuals_and_copyable_html_trigger_final(self) -> None:
        self.assertTrue(self_evolution.is_final_delivery({"visuals", "wechat_copyable_html"}))
        self.assertFalse(self_evolution.is_final_delivery({"wechat_copyable_html"}))
        self.assertTrue(self_evolution.is_final_delivery(set(), explicit_final=True))


if __name__ == "__main__":
    unittest.main()
