"""
Test i18n translation coverage for VidTanium GUI
Verifies that all translation keys are properly defined in both EN and ZH_CN
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from gui.utils.i18n import I18nManager
except ImportError:
    # Try alternative import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "i18n", 
        Path(__file__).parent.parent / "src" / "gui" / "utils" / "i18n.py"
    )
    i18n_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(i18n_module)
    I18nManager = i18n_module.I18nManager

# Create manager singleton
_manager = None

def get_i18n_manager():
    global _manager
    if _manager is None:
        _manager = I18nManager()
    return _manager

def tr(key, **kwargs):
    return get_i18n_manager().tr(key, **kwargs)


def load_translation_file(filepath):
    """Load translation JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_keys(data, prefix=''):
    """Recursively get all translation keys from nested dictionary"""
    keys = set()
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(get_all_keys(value, full_key))
        else:
            keys.add(full_key)
    return keys


def test_translation_files_exist():
    """Test that translation files exist"""
    project_root = Path(__file__).parent.parent
    locales_dir = project_root / "src" / "locales"
    
    en_file = locales_dir / "en.json"
    zh_cn_file = locales_dir / "zh_CN.json"
    
    assert en_file.exists(), f"English translation file not found: {en_file}"
    assert zh_cn_file.exists(), f"Chinese translation file not found: {zh_cn_file}"
    
    print("✓ Translation files exist")
    return en_file, zh_cn_file


def test_translation_files_parseable(en_file, zh_cn_file):
    """Test that translation files are valid JSON"""
    en_data = load_translation_file(en_file)
    zh_cn_data = load_translation_file(zh_cn_file)
    
    assert isinstance(en_data, dict), "English translations not a dictionary"
    assert isinstance(zh_cn_data, dict), "Chinese translations not a dictionary"
    
    print("✓ Translation files are valid JSON")
    return en_data, zh_cn_data


def test_translation_key_parity(en_data, zh_cn_data):
    """Test that both language files have the same keys"""
    en_keys = get_all_keys(en_data)
    zh_cn_keys = get_all_keys(zh_cn_data)
    
    # Find missing keys
    missing_in_zh = en_keys - zh_cn_keys
    missing_in_en = zh_cn_keys - en_keys
    
    if missing_in_zh:
        print(f"\n⚠ Keys missing in Chinese translations ({len(missing_in_zh)}):")
        for key in sorted(missing_in_zh)[:10]:  # Show first 10
            print(f"  - {key}")
        if len(missing_in_zh) > 10:
            print(f"  ... and {len(missing_in_zh) - 10} more")
    
    if missing_in_en:
        print(f"\n⚠ Keys missing in English translations ({len(missing_in_en)}):")
        for key in sorted(missing_in_en)[:10]:  # Show first 10
            print(f"  - {key}")
        if len(missing_in_en) > 10:
            print(f"  ... and {len(missing_in_en) - 10} more")
    
    if not missing_in_zh and not missing_in_en:
        print("✓ Translation key parity verified - all keys present in both languages")
        return True
    
    return len(missing_in_zh) == 0 and len(missing_in_en) == 0


def test_i18n_manager_initialization():
    """Test i18n manager initialization"""
    try:
        manager = get_i18n_manager()
        assert manager is not None, "i18n manager is None"
        assert manager.is_initialized(), "i18n manager not properly initialized"
        print("✓ i18n manager initializes correctly")
        return True
    except Exception as e:
        print(f"✗ i18n manager initialization failed: {e}")
        return False


def test_translation_retrieval():
    """Test translation retrieval with fallback"""
    manager = get_i18n_manager()
    
    # Test key that exists
    result = tr("app.title")
    assert result, "Failed to retrieve existing translation"
    print(f"✓ Translation retrieval works: app.title = '{result}'")
    
    # Test key that doesn't exist (should fallback)
    result = tr("nonexistent.key")
    assert result == "Key", "Fallback mechanism not working properly"
    print(f"✓ Fallback mechanism works for missing keys")
    
    return True


def test_new_component_translations():
    """Test that new component translations are available"""
    new_keys = [
        "analytics.title",
        "analytics.eta_title",
        "bulk_ops.title",
        "bulk_ops.select_all",
        "error_dialog.title",
        "error_dialog.retry",
        "progress.downloading",
        "tooltip.show_details",
        "history.title"
    ]
    
    missing = []
    for key in new_keys:
        result = tr(key)
        # If result is the last part of the key capitalized, it's missing
        expected_fallback = key.split('.')[-1].replace('_', ' ').title()
        if result == expected_fallback:
            missing.append(key)
    
    if missing:
        print(f"\n⚠ New component translations not found ({len(missing)}):")
        for key in missing:
            print(f"  - {key}")
        return False
    
    print(f"✓ All {len(new_keys)} new component translations are available")
    return True


def test_translation_formatting():
    """Test translation with parameter substitution"""
    # Test parameter substitution
    result = tr("dialogs.task_created_message", name="Test Task")
    assert "Test Task" in result, "Parameter substitution not working"
    print(f"✓ Parameter substitution works")
    
    return True


def generate_coverage_report(en_data, zh_cn_data):
    """Generate coverage statistics"""
    en_keys = get_all_keys(en_data)
    zh_cn_keys = get_all_keys(zh_cn_data)
    
    total_keys = len(en_keys | zh_cn_keys)
    common_keys = len(en_keys & zh_cn_keys)
    coverage = (common_keys / total_keys * 100) if total_keys > 0 else 0
    
    print("\n" + "="*60)
    print("Translation Coverage Report")
    print("="*60)
    print(f"Total unique keys:         {total_keys}")
    print(f"Keys in English:           {len(en_keys)}")
    print(f"Keys in Chinese:           {len(zh_cn_keys)}")
    print(f"Keys in both:              {common_keys}")
    print(f"Coverage:                  {coverage:.2f}%")
    print("="*60)
    
    # Category breakdown
    categories = {}
    for key in en_keys:
        category = key.split('.')[0]
        categories[category] = categories.get(category, 0) + 1
    
    print("\nKeys by Category:")
    for category, count in sorted(categories.items()):
        print(f"  {category:30s} {count:4d} keys")
    print("="*60)


def main():
    """Run all i18n tests"""
    print("\n" + "="*60)
    print("VidTanium i18n Translation Coverage Test")
    print("="*60 + "\n")
    
    try:
        # Test 1: Files exist
        en_file, zh_cn_file = test_translation_files_exist()
        
        # Test 2: Files are parseable
        en_data, zh_cn_data = test_translation_files_parseable(en_file, zh_cn_file)
        
        # Test 3: Key parity
        parity_ok = test_translation_key_parity(en_data, zh_cn_data)
        
        # Test 4: i18n manager
        manager_ok = test_i18n_manager_initialization()
        
        # Test 5: Translation retrieval
        retrieval_ok = test_translation_retrieval()
        
        # Test 6: New component translations
        new_components_ok = test_new_component_translations()
        
        # Test 7: Formatting
        formatting_ok = test_translation_formatting()
        
        # Generate coverage report
        generate_coverage_report(en_data, zh_cn_data)
        
        # Summary
        all_tests = [
            parity_ok,
            manager_ok,
            retrieval_ok,
            new_components_ok,
            formatting_ok
        ]
        
        passed = sum(all_tests)
        total = len(all_tests)
        
        print(f"\nTest Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("✓ All i18n tests passed successfully!")
            return 0
        else:
            print("⚠ Some i18n tests failed. Please review the output above.")
            return 1
            
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
