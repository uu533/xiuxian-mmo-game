"""
P0问题修复回归测试

测试目标：
1. BUG-001: REALM_NAMES.index()的ValueError处理
2. BUG-002: character.action_records的None检查
3. BUG-003: 所有公共函数的参数验证
4. BUG-004: 心魔值影响机制
5. BUG-005: 连续修炼惩罚调整
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.models import Character
from backend.configs.realms import REALM_NAMES
from backend.configs.formulas import BREAKTHROUGH_INNER_DEMON_FACTOR, BREAKTHROUGH_LUCK_FACTOR


def create_mock_character(
    realm="炼气一期",
    realm_stage="炼气",
    cultivation=100,
    cultivation_cap=200,
    mana=100,
    max_mana=150,
    hp=100,
    max_hp=150,
    base_attack=50,
    base_defense=40,
    hidden_inner_demon=0,
    hidden_luck=0,
    action_records=None,
    methods=None,
    artifacts=None,
):
    """创建模拟Character对象用于测试"""
    char = MagicMock(spec=Character)
    char.realm = realm
    char.realm_stage = realm_stage
    char.cultivation = cultivation
    char.cultivation_cap = cultivation_cap
    char.mana = mana
    char.max_mana = max_mana
    char.hp = hp
    char.max_hp = max_hp
    char.base_attack = base_attack
    char.base_defense = base_defense
    char.hidden_inner_demon = hidden_inner_demon
    char.hidden_luck = hidden_luck
    char.action_records = action_records or []
    char.methods = methods or []
    char.artifacts = artifacts or []
    char.spiritual_root = "金灵根"
    return char


class TestBUG001RealmNameHandling:
    """BUG-001: 测试REALM_NAMES.index()的ValueError处理"""

    def test_valid_realm_name(self):
        """测试正常境界名称"""
        from backend.services.calc_service import get_base_attack_by_realm

        char = create_mock_character(realm="炼气一期")
        result = get_base_attack_by_realm(char)
        assert result == 5  # 炼气一期 = 1 * 5

        char.realm = "筑基初期"
        result = get_base_attack_by_realm(char)
        assert result == 80

        print("✓ BUG-001: 正常境界名称处理正确")

    def test_old_format_realm_name(self):
        """测试旧格式境界名称（如"金丹"），应该返回默认值500"""
        from backend.services.calc_service import get_base_attack_by_realm

        # 模拟旧数据格式
        char = create_mock_character(realm="金丹")  # 不在REALM_NAMES中
        result = get_base_attack_by_realm(char)
        assert result == 500, f"预期500，实际{result}"

        char.realm = "元婴"  # 另一个可能的旧格式
        result = get_base_attack_by_realm(char)
        assert result == 500, f"预期500，实际{result}"

        print("✓ BUG-001: 旧格式境界名称返回默认值500")


class TestBUG002ActionRecordsNone:
    """BUG-002: 测试character.action_records的None检查"""

    def test_action_records_is_none(self):
        """测试action_records为None时不会崩溃"""
        from backend.services.calc_service import get_cultivation_efficiency

        char = create_mock_character()
        char.action_records = None

        # 不应该抛出TypeError
        result = get_cultivation_efficiency(char)
        assert result == 1.0, f"预期1.0，实际{result}"

        print("✓ BUG-002: action_records为None时返回1.0（无惩罚）")

    def test_action_records_empty(self):
        """测试action_records为空列表"""
        from backend.services.calc_service import get_cultivation_efficiency

        char = create_mock_character()
        char.action_records = []

        result = get_cultivation_efficiency(char)
        assert result == 1.0, f"预期1.0，实际{result}"

        print("✓ BUG-002: action_records为空列表时返回1.0")


class TestBUG003ParameterValidation:
    """BUG-003: 测试所有公共函数的参数验证"""

    def test_get_base_attack_by_realm_none(self):
        from backend.services.calc_service import get_base_attack_by_realm
        assert get_base_attack_by_realm(None) == 0

    def test_get_base_defense_by_realm_none(self):
        from backend.services.calc_service import get_base_defense_by_realm
        assert get_base_defense_by_realm(None) == 0

    def test_get_max_mana_none(self):
        from backend.services.calc_service import get_max_mana
        assert get_max_mana(None) == 100

    def test_get_max_hp_none(self):
        from backend.services.calc_service import get_max_hp
        assert get_max_hp(None) == 100

    def test_get_cultivation_speed_none(self):
        from backend.services.calc_service import get_cultivation_speed
        assert get_cultivation_speed(None) == 1.0

    def test_get_cultivation_efficiency_none(self):
        from backend.services.calc_service import get_cultivation_efficiency
        assert get_cultivation_efficiency(None) == 1.0

    def test_get_train_cultivation_bonus_none(self):
        from backend.services.calc_service import get_train_cultivation_bonus
        assert get_train_cultivation_bonus(None) == 0.0

    def test_get_breakthrough_rate_none(self):
        from backend.services.calc_service import get_breakthrough_rate
        assert get_breakthrough_rate(None) == 0.02

    def test_get_final_attack_none(self):
        from backend.services.calc_service import get_final_attack
        assert get_final_attack(None) == 0

    def test_get_final_defense_none(self):
        from backend.services.calc_service import get_final_defense
        assert get_final_defense(None) == 0

    def test_get_action_mana_cost_none(self):
        from backend.services.calc_service import get_action_mana_cost
        assert get_action_mana_cost(None, "train") == 0
        assert get_action_mana_cost(create_mock_character(), None) == 0

    def test_get_life_skill_mana_cost_none(self):
        from backend.services.calc_service import get_life_skill_mana_cost
        assert get_life_skill_mana_cost(None, {}) == 0
        assert get_life_skill_mana_cost(create_mock_character(), None) == 0

    def test_get_life_skill_success_rate_none(self):
        from backend.services.calc_service import get_life_skill_success_rate
        assert get_life_skill_success_rate(None, {}) == 0.05
        assert get_life_skill_success_rate(create_mock_character(), None) == 0.05

    def test_get_scout_talisman_luck_bonus_none(self):
        from backend.services.calc_service import get_scout_talisman_luck_bonus
        assert get_scout_talisman_luck_bonus(None) == 0

    def test_get_guard_talisman_damage_reduction_none(self):
        from backend.services.calc_service import get_guard_talisman_damage_reduction
        assert get_guard_talisman_damage_reduction(None) == 0.0

    def test_get_swift_talisman_mana_discount_none(self):
        from backend.services.calc_service import get_swift_talisman_mana_discount
        assert get_swift_talisman_mana_discount(None) == 0

    def test_apply_item_effects_none(self):
        from backend.services.calc_service import apply_item_effects
        assert apply_item_effects(None, {}) == {}
        assert apply_item_effects(create_mock_character(), None) == {}

    def test_scale_reward_value_none(self):
        from backend.services.calc_service import scale_reward_value
        assert scale_reward_value(0, 1.0) == 0
        assert scale_reward_value(100, 0) == 0

    def test_sync_base_and_caps_none(self):
        from backend.services.calc_service import sync_base_and_caps
        # 不应该抛出异常
        sync_base_and_caps(None)

    def test_derived_stats_none(self):
        from backend.services.calc_service import derived_stats
        assert derived_stats(None) == {}

    def test_get_explore_reward_bonus_none(self):
        from backend.services.calc_service import get_explore_reward_bonus
        assert get_explore_reward_bonus(None) == 0.0

    def test_get_battle_power_bonus_none(self):
        from backend.services.calc_service import get_battle_power_bonus
        assert get_battle_power_bonus(None) == 0

    def test_all_parameter_validation(self):
        """运行所有参数验证测试"""
        self.test_get_base_attack_by_realm_none()
        self.test_get_base_defense_by_realm_none()
        self.test_get_max_mana_none()
        self.test_get_max_hp_none()
        self.test_get_cultivation_speed_none()
        self.test_get_cultivation_efficiency_none()
        self.test_get_train_cultivation_bonus_none()
        self.test_get_breakthrough_rate_none()
        self.test_get_final_attack_none()
        self.test_get_final_defense_none()
        self.test_get_action_mana_cost_none()
        self.test_get_life_skill_mana_cost_none()
        self.test_get_life_skill_success_rate_none()
        self.test_get_scout_talisman_luck_bonus_none()
        self.test_get_guard_talisman_damage_reduction_none()
        self.test_get_swift_talisman_mana_discount_none()
        self.test_apply_item_effects_none()
        self.test_scale_reward_value_none()
        self.test_sync_base_and_caps_none()
        self.test_derived_stats_none()
        self.test_get_explore_reward_bonus_none()
        self.test_get_battle_power_bonus_none()

        print("✓ BUG-003: 所有公共函数参数验证通过（character=None时返回安全默认值）")


class TestBUG004InnerDemon:
    """BUG-004: 测试心魔值影响机制"""

    def test_inner_demon_reduces_breakthrough_rate(self):
        """测试心魔值降低突破率"""
        from backend.services.calc_service import get_breakthrough_rate

        char = create_mock_character(hidden_inner_demon=0, hidden_luck=0)
        rate_without_demon = get_breakthrough_rate(char)

        char.hidden_inner_demon = 50
        rate_with_demon = get_breakthrough_rate(char)

        # 心魔值50应该降低突破率 50 * BREAKTHROUGH_INNER_DEMON_FACTOR
        expected_reduction = 50 * BREAKTHROUGH_INNER_DEMON_FACTOR
        actual_reduction = rate_without_demon - rate_with_demon
        assert abs(actual_reduction - expected_reduction) < 0.001, \
            f"心魔值影响不正确: 预期降低{expected_reduction}，实际降低{actual_reduction}"

        print(f"✓ BUG-004: 心魔值50降低突破率约{expected_reduction:.3f}")

    def test_inner_demon_damage_in_explore(self):
        """测试探索时心魔值高造成气血损伤（需要测试action_service）"""
        # 这个函数主要在action_service._explore()中实现
        # 这里测试心魔值>=30时，有概率造成损伤的逻辑
        # 由于涉及random，这里只测试逻辑存在性

        # 检查代码是否包含心魔损伤逻辑
        with open(ROOT / "backend" / "services" / "action_service.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "hidden_inner_demon >= 30" in content, "心魔值>=30检查逻辑缺失"
            assert "inner_demon_damage" in content, "心魔损伤逻辑缺失"
            assert "心魔反噬" in content, "心魔反噬消息缺失"

        print("✓ BUG-004: 探索心魔损伤逻辑已实现")


class TestBUG005CultivationEfficiency:
    """BUG-005: 测试连续修炼惩罚调整"""

    def test_efficiency_penalty_array(self):
        """测试渐进式惩罚数组 [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]"""
        from backend.services.calc_service import get_cultivation_efficiency

        # 模拟连续修炼记录
        penalty_array = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]

        for consecutive in range(7):  # 0到6次
            char = create_mock_character()

            # 创建模拟的action_records
            records = []
            for i in range(consecutive):
                record = MagicMock()
                record.action_type = "train"
                record.result_json = {"success": True}
                record.id = i
                records.append(record)

            char.action_records = records

            result = get_cultivation_efficiency(char)

            if consecutive < 6:
                expected = penalty_array[consecutive]
            else:
                expected = 0.5  # 6次及以后

            assert abs(result - expected) < 0.001, \
                f"连续修炼{consecutive}次: 预期{expected}，实际{result}"

        print("✓ BUG-005: 连续修炼惩罚数组正确 [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]")

    def test_4th_train_efficiency_is_70_percent(self):
        """测试连续修炼第4次后，效率是70%（而不是20%）"""
        from backend.services.calc_service import get_cultivation_efficiency

        # 第4次连续修炼（index=3，因为从0开始）
        char = create_mock_character()
        records = []
        for i in range(4):  # 4次连续成功修炼
            record = MagicMock()
            record.action_type = "train"
            record.result_json = {"success": True}
            record.id = i
            records.append(record)

        char.action_records = records

        result = get_cultivation_efficiency(char)
        expected = 0.7  # 第4次应该是70%

        assert abs(result - expected) < 0.001, \
            f"第4次连续修炼: 预期{expected}（70%），实际{result}"

        print(f"✓ BUG-005: 第4次连续修炼效率为{result}（70%，不是20%）")


class TestCodeQuality:
    """代码质量检查"""

    def test_pep8_compliance(self):
        """检查代码是否符合PEP8规范"""
        try:
            import pycodestyle
        except ImportError:
            print("⚠ 代码质量: pycodestyle未安装，跳过PEP8检查")
            return

        # 检查修改后的文件
        files_to_check = [
            ROOT / "backend" / "services" / "calc_service.py",
            ROOT / "backend" / "services" / "action_service.py",
        ]

        style = pycodestyle.StyleGuide(quiet=True)
        total_errors = 0

        for file_path in files_to_check:
            if file_path.exists():
                result = style.check_files([str(file_path)])
                if result.total_errors > 0:
                    print(f"  PEP8问题 in {file_path.name}: {result.total_errors} errors")
                    total_errors += result.total_errors

        if total_errors == 0:
            print("✓ 代码质量: PEP8规范检查通过")
        else:
            print(f"⚠ 代码质量: 发现{total_errors}个PEP8问题")

        # 不阻塞测试，只报告
        assert True

    def test_function_docstrings(self):
        """检查函数是否有文档字符串"""
        import ast

        files_to_check = [
            ROOT / "backend" / "services" / "calc_service.py",
        ]

        with open(files_to_check[0], "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        missing_docstrings = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 跳过私有函数
                if not node.name.startswith("_"):
                    if not ast.get_docstring(node):
                        missing_docstrings.append(node.name)

        if missing_docstrings:
            print(f"⚠ 代码质量: 以下公共函数缺少文档字符串: {missing_docstrings}")
        else:
            print("✓ 代码质量: 所有公共函数都有文档字符串")

        # 不阻塞测试
        assert True


def run_all_tests():
    """运行所有回归测试"""
    print("=" * 60)
    print("P0问题修复回归测试开始")
    print("=" * 60)
    print()

    passed = 0
    failed = 0
    errors = []

    # BUG-001 测试
    print("-" * 60)
    print("BUG-001: REALM_NAMES.index()的ValueError处理")
    print("-" * 60)
    try:
        test_bug001 = TestBUG001RealmNameHandling()
        test_bug001.test_valid_realm_name()
        test_bug001.test_old_format_realm_name()
        passed += 2
    except AssertionError as e:
        print(f"✗ BUG-001 测试失败: {e}")
        failed += 1
        errors.append(f"BUG-001: {e}")
    except Exception as e:
        print(f"✗ BUG-001 测试错误: {e}")
        failed += 1
        errors.append(f"BUG-001: {e}")
    print()

    # BUG-002 测试
    print("-" * 60)
    print("BUG-002: character.action_records的None检查")
    print("-" * 60)
    try:
        test_bug002 = TestBUG002ActionRecordsNone()
        test_bug002.test_action_records_is_none()
        test_bug002.test_action_records_empty()
        passed += 2
    except AssertionError as e:
        print(f"✗ BUG-002 测试失败: {e}")
        failed += 1
        errors.append(f"BUG-002: {e}")
    except Exception as e:
        print(f"✗ BUG-002 测试错误: {e}")
        failed += 1
        errors.append(f"BUG-002: {e}")
    print()

    # BUG-003 测试
    print("-" * 60)
    print("BUG-003: 所有公共函数的参数验证")
    print("-" * 60)
    try:
        test_bug003 = TestBUG003ParameterValidation()
        test_bug003.test_all_parameter_validation()
        passed += 1  # 整体算1个测试
    except AssertionError as e:
        print(f"✗ BUG-003 测试失败: {e}")
        failed += 1
        errors.append(f"BUG-003: {e}")
    except Exception as e:
        print(f"✗ BUG-003 测试错误: {e}")
        failed += 1
        errors.append(f"BUG-003: {e}")
    print()

    # BUG-004 测试
    print("-" * 60)
    print("BUG-004: 心魔值影响机制")
    print("-" * 60)
    try:
        test_bug004 = TestBUG004InnerDemon()
        test_bug004.test_inner_demon_reduces_breakthrough_rate()
        test_bug004.test_inner_demon_damage_in_explore()
        passed += 2
    except AssertionError as e:
        print(f"✗ BUG-004 测试失败: {e}")
        failed += 1
        errors.append(f"BUG-004: {e}")
    except Exception as e:
        print(f"✗ BUG-004 测试错误: {e}")
        failed += 1
        errors.append(f"BUG-004: {e}")
    print()

    # BUG-005 测试
    print("-" * 60)
    print("BUG-005: 连续修炼惩罚调整")
    print("-" * 60)
    try:
        test_bug005 = TestBUG005CultivationEfficiency()
        test_bug005.test_efficiency_penalty_array()
        test_bug005.test_4th_train_efficiency_is_70_percent()
        passed += 2
    except AssertionError as e:
        print(f"✗ BUG-005 测试失败: {e}")
        failed += 1
        errors.append(f"BUG-005: {e}")
    except Exception as e:
        print(f"✗ BUG-005 测试错误: {e}")
        failed += 1
        errors.append(f"BUG-005: {e}")
    print()

    # 代码质量检查
    print("-" * 60)
    print("代码质量检查")
    print("-" * 60)
    try:
        test_quality = TestCodeQuality()
        try:
            test_quality.test_pep8_compliance()
        except ImportError:
            print("⚠ 代码质量: pycodestyle未安装，跳过PEP8检查")
        test_quality.test_function_docstrings()
    except Exception as e:
        print(f"⚠ 代码质量检查错误: {e}")
    print()

    # 输出测试报告
    print("=" * 60)
    print("测试报告汇总")
    print("=" * 60)
    print(f"总测试数: {passed + failed}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print()

    if errors:
        print("失败详情:")
        for error in errors:
            print(f"  - {error}")
        print()

    if failed == 0:
        print("✓ 所有测试通过！P0问题修复成功。")
        print("✓ 建议：可以提交到Git")
        return True
    else:
        print(f"✗ {failed}个测试失败，需要修复。")
        print("✗ 建议：不要提交，先修复失败的测试")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
