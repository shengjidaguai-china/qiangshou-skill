from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.writing = (ROOT / "references" / "writing.md").read_text(encoding="utf-8")
        cls.scenarios = (ROOT / "references" / "test-scenarios.md").read_text(
            encoding="utf-8"
        )
        cls.evolution = (ROOT / "references" / "self-evolution.md").read_text(
            encoding="utf-8"
        )

    def test_adaptive_orchestrator_uses_one_dominant_progression(self) -> None:
        for intent in ("项目故事", "观点实证"):
            self.assertIn(intent, self.skill)
            self.assertIn(intent, self.writing)
        for progression in ("事件变化", "认知变化", "决策变化", "实验变化", "人物关系变化"):
            self.assertIn(progression, self.skill + self.writing)
        self.assertIn("只是一种可选变体", self.skill)
        self.assertIn("不新增固定引擎", self.writing)

    def test_de_ai_review_is_delete_first_and_non_mechanical(self) -> None:
        combined = self.skill + self.writing
        self.assertIn("删除优先", combined)
        self.assertIn("先删不增加事实、因果、判断或人物变化的句子", combined)
        self.assertIn("不能设置机械删字比例", combined)
        self.assertIn("自然口语", combined)
        self.assertIn("author-voice.md", self.writing)

    def test_forward_scenarios_cover_structural_divergence_and_heavy_ai_draft(self) -> None:
        self.assertIn("三篇异构素材的自适应编排", self.scenarios)
        self.assertIn("唯一主导推进线", self.scenarios)
        self.assertIn("删除优先的去 AI 味审稿", self.scenarios)
        self.assertIn("不重新写一篇", self.scenarios)

    def test_single_article_structure_never_enters_long_term_memory(self) -> None:
        self.assertIn("单篇章节结构", self.evolution)
        self.assertIn("不能进入文字或视觉记忆", self.evolution)
        self.assertIn("不能晋升为固定引擎", self.evolution)

    def test_self_evolution_documents_persistent_commands(self) -> None:
        self.assertIn("source-id", self.evolution)
        self.assertIn("record --domain text", self.evolution)
        self.assertIn("author-voice-signals.json", self.evolution)


if __name__ == "__main__":
    unittest.main()
