"""
叙事系统测试 — P0 需求

校验：
1. events.py 的所有事件都有 narrative 字段
2. narrative 字段格式正确（非空字符串，字数在 80-160 之间）
3. narrative_texts.py 的叙事文本格式正确
4. action_service.py 返回格式正确（集成测试）
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from configs.events import EXPLORE_EVENTS
from configs.narrative_texts import TRAIN_NARRATIVES, get_train_narrative


class TestEventsNarrative:
    """测试 events.py 的 narrative 字段"""

    def test_all_events_have_narrative_field(self):
        """所有事件都有 narrative 字段"""
        for event in EXPLORE_EVENTS:
            assert "narrative" in event, f"事件 {event['code']} 缺少 narrative 字段"

    def test_narrative_field_is_non_empty_string(self):
        """narrative 字段是非空字符串"""
        for event in EXPLORE_EVENTS:
            narrative = event.get("narrative", "")
            assert isinstance(narrative, str), f"事件 {event['code']} 的 narrative 字段不是字符串"
            assert len(narrative) > 0, f"事件 {event['code']} 的 narrative 字段为空"

    def test_narrative_field_length(self):
        """narrative 字段字数在 80-160 之间（包含 \n）"""
        for event in EXPLORE_EVENTS:
            narrative = event.get("narrative", "")
            # 计算中文字符数（\n 算一个字符）
            char_count = len(narrative)
            assert 80 <= char_count <= 160, f"事件 {event['code']} 的 narrative 字段字数 {char_count} 不在 80-160 之间"

    def test_narrative_field_no_numeric_values(self):
        """narrative 字段不包含具体数值（如"攻击+12"）"""
        import re
        for event in EXPLORE_EVENTS:
            narrative = event.get("narrative", "")
            # 检查是否包含数字+符号的模式（如"+12"、"-5"）
            has_numeric = bool(re.search(r'[\+\-]\d+', narrative))
            assert not has_numeric, f"事件 {event['code']} 的 narrative 字段包含具体数值"


class TestNarrativeTexts:
    """测试 narrative_texts.py 的叙事文本"""

    def test_train_narrative_pool_not_empty(self):
        """修炼叙事文本池不为空"""
        for realm, texts in TRAIN_NARRATIVES.items():
            assert len(texts) > 0, f"境界 {realm} 的修炼叙事文本池为空"

    def test_train_narrative_text_length(self):
        """修炼叙事文本字数在 60-120 之间"""
        for realm, texts in TRAIN_NARRATIVES.items():
            for text in texts:
                char_count = len(text)
                assert 60 <= char_count <= 120, f"境界 {realm} 的叙事文本字数 {char_count} 不在 60-120 之间"

    def test_get_train_narrative_returns_none_for_unknown_realm(self):
        """未知境界返回 None"""
        result = get_train_narrative("未知境界")
        assert result is None, f"未知境界应该返回 None，但实际返回 {result}"

    def test_get_train_narrative_returns_valid_text(self):
        """已知境界返回有效文本"""
        for realm in TRAIN_NARRATIVES.keys():
            result = get_train_narrative(realm)
            assert result is not None, f"境界 {realm} 应该返回叙事文本，但实际返回 None"
            assert isinstance(result, str), f"境界 {realm} 返回的叙事文本应该是字符串"
            assert len(result) > 0, f"境界 {realm} 返回的叙事文本不应该为空"


class TestActionServiceNarrative:
    """测试 action_service.py 返回 narrative 字段（需要数据库，暂时跳过）"""

    @pytest.mark.skip(reason="需要数据库，暂时跳过")
    def test_train_returns_narrative(self):
        """_train() 30% 概率返回 narrative 字段"""
        pass

    @pytest.mark.skip(reason="需要数据库，暂时跳过")
    def test_explore_returns_narrative(self):
        """_explore() 返回 narrative 字段（从事件读取）"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
