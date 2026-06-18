#!/usr/bin/env python3
"""
叙事系统简单验证脚本 — P0 需求

直接运行（无需 pytest）：
  python validate_narrative.py
"""

import sys
from pathlib import Path
import re

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from configs.events import EXPLORE_EVENTS
from configs.narrative_texts import TRAIN_NARRATIVES, get_train_narrative


def test_all_events_have_narrative_field():
    """所有事件都有 narrative 字段"""
    errors = []
    for event in EXPLORE_EVENTS:
        if "narrative" not in event:
            errors.append(f"事件 {event['code']} 缺少 narrative 字段")
    return errors


def test_narrative_field_is_non_empty_string():
    """narrative 字段是非空字符串"""
    errors = []
    for event in EXPLORE_EVENTS:
        narrative = event.get("narrative", "")
        if not isinstance(narrative, str):
            errors.append(f"事件 {event['code']} 的 narrative 字段不是字符串")
        elif len(narrative) == 0:
            errors.append(f"事件 {event['code']} 的 narrative 字段为空")
    return errors


def test_narrative_field_length():
    """narrative 字段字数在 80-160 之间（包含 \n）"""
    errors = []
    for event in EXPLORE_EVENTS:
        narrative = event.get("narrative", "")
        char_count = len(narrative)
        if not (80 <= char_count <= 160):
            errors.append(f"事件 {event['code']} 的 narrative 字段字数 {char_count} 不在 80-160 之间")
    return errors


def test_narrative_field_no_numeric_values():
    """narrative 字段不包含具体数值（如"+12"、"-5"）"""
    errors = []
    for event in EXPLORE_EVENTS:
        narrative = event.get("narrative", "")
        # 检查是否包含数字+符号的模式（如"+12"、"-5"）
        has_numeric = bool(re.search(r'[\+\-]\d+', narrative))
        if has_numeric:
            errors.append(f"事件 {event['code']} 的 narrative 字段包含具体数值")
    return errors


def test_train_narrative_pool_not_empty():
    """修炼叙事文本池不为空"""
    errors = []
    for realm, texts in TRAIN_NARRATIVES.items():
        if len(texts) == 0:
            errors.append(f"境界 {realm} 的修炼叙事文本池为空")
    return errors


def test_train_narrative_text_length():
    """修炼叙事文本字数在 60-120 之间"""
    errors = []
    for realm, texts in TRAIN_NARRATIVES.items():
        for i, text in enumerate(texts):
            char_count = len(text)
            if not (60 <= char_count <= 120):
                errors.append(f"境界 {realm} 的叙事文本[{i}] 字数 {char_count} 不在 60-120 之间")
    return errors


def test_get_train_narrative_returns_none_for_unknown_realm():
    """未知境界返回 None"""
    errors = []
    result = get_train_narrative("未知境界")
    if result is not None:
        errors.append(f"未知境界应该返回 None，但实际返回 {result}")
    return errors


def test_get_train_narrative_returns_valid_text():
    """已知境界返回有效文本"""
    errors = []
    for realm in TRAIN_NARRATIVES.keys():
        result = get_train_narrative(realm)
        if result is None:
            errors.append(f"境界 {realm} 应该返回叙事文本，但实际返回 None")
        elif not isinstance(result, str):
            errors.append(f"境界 {realm} 返回的叙事文本应该是字符串")
        elif len(result) == 0:
            errors.append(f"境界 {realm} 返回的叙事文本不应该为空")
    return errors


def main():
    """运行所有测试"""
    print("=" * 60)
    print("叙事系统验证")
    print("=" * 60)
    print()

    all_errors = []

    tests = [
        ("所有事件都有 narrative 字段", test_all_events_have_narrative_field),
        ("narrative 字段是非空字符串", test_narrative_field_is_non_empty_string),
        ("narrative 字段字数在 80-160 之间", test_narrative_field_length),
        ("narrative 字段不包含具体数值", test_narrative_field_no_numeric_values),
        ("修炼叙事文本池不为空", test_train_narrative_pool_not_empty),
        ("修炼叙事文本字数在 60-120 之间", test_train_narrative_text_length),
        ("未知境界返回 None", test_get_train_narrative_returns_none_for_unknown_realm),
        ("已知境界返回有效文本", test_get_train_narrative_returns_valid_text),
    ]

    for name, test_func in tests:
        print(f"运行测试: {name}...")
        errors = test_func()
        if errors:
            print(f"  ❌ 失败 ({len(errors)} 个错误)")
            for error in errors:
                print(f"    - {error}")
            all_errors.extend(errors)
        else:
            print("  ✅ 通过")
        print()

    print("=" * 60)
    if all_errors:
        print(f"总计: {len(all_errors)} 个错误")
        print("验证失败")
        sys.exit(1)
    else:
        print("所有测试通过")
        print("验证成功")
        sys.exit(0)


if __name__ == "__main__":
    main()
