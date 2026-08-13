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
        cls.readme = (ROOT / "references" / "github-readme.md").read_text(
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

    def test_readme_mode_is_bilingual_and_separate_from_wechat_workflow(self) -> None:
        combined = self.skill + self.readme + self.scenarios
        for term in ("README_EN.md", "一键切换", "README_SYNC"):
            self.assertIn(term, combined)
        self.assertIn("不要套用公众号长文", self.skill)
        self.assertIn("英文按英语开发者", combined)
        self.assertIn("validate_readme_pair.py", combined)

    def test_readme_professionalism_is_evidence_based(self) -> None:
        for term in ("先读仓库", "基线过滤", "快速开始", "许可证", "Star"):
            self.assertIn(term, self.readme)
        self.assertIn("4–8 个信息密度高", self.readme)
        self.assertIn("Stargazer 头像墙", self.readme)
        self.assertIn("项目名和一句话价值之后立即放首屏 Star", self.readme)
        self.assertIn("不逐句机翻", self.readme)

    def test_readme_source_available_license_is_precise(self) -> None:
        for term in (
            "source-available",
            "商业使用需事先取得商业授权",
            "不要将这种许可证标成 `Open Source`",
            "首页不展开许可证条款",
            "CONTRIBUTING.md",
            "贡献许可/CLA",
        ):
            self.assertIn(term, self.readme)

    def test_readme_license_type_is_never_assumed(self) -> None:
        for term in (
            "不得预设为非商业",
            "允许商业使用的开源许可证",
            "商业专有许可证",
            "仓库没有 `LICENSE`",
            "不生成许可证徽章",
            "不固定显示“非商业 License 徽章”",
        ):
            self.assertIn(term, self.readme)
        self.assertIn("不同许可证的 README 徽章", self.scenarios)


if __name__ == "__main__":
    unittest.main()
