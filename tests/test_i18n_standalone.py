"""
Standalone i18n translation coverage test for VidTanium
Tests translation files without requiring runtime dependencies
"""

import json
import sys
from pathlib import Path


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
    
    if not en_file.exists():
        print(f"✗ English translation file not found: {en_file}")
        return None, None
        
    if not zh_cn_file.exists():
        print(f"✗ Chinese translation file not found: {zh_cn_file}")
        return None, None
    
    print("✓ Translation files exist")
    return en_file, zh_cn_file


def test_translation_files_parseable(en_file, zh_cn_file):
    """Test that translation files are valid JSON"""
    try:
        en_data = load_translation_file(en_file)
        zh_cn_data = load_translation_file(zh_cn_file)
        
        if not isinstance(en_data, dict):
            print("✗ English translations not a dictionary")
            return None, None
            
        if not isinstance(zh_cn_data, dict):
            print("✗ Chinese translations not a dictionary")
            return None, None
        
        print("✓ Translation files are valid JSON")
        return en_data, zh_cn_data
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing error: {e}")
        return None, None
    except Exception as e:
        print(f"✗ Error loading files: {e}")
        return None, None


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


def test_no_empty_values(data, language):
    """Test that no translation values are empty"""
    def check_empty(obj, path=""):
        empty_keys = []
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, dict):
                empty_keys.extend(check_empty(value, current_path))
            elif isinstance(value, str):
                if not value.strip():
                    empty_keys.append(current_path)
        return empty_keys
    
    empty_keys = check_empty(data)
    if empty_keys:
        print(f"\n⚠ Empty translation values found in {language} ({len(empty_keys)}):")
        for key in empty_keys[:10]:
            print(f"  - {key}")
        if len(empty_keys) > 10:
            print(f"  ... and {len(empty_keys) - 10} more")
        return False
    
    print(f"✓ No empty values in {language} translations")
    return True


def test_new_component_keys_exist(en_data, zh_cn_data):
    """Test that new component translation keys exist"""
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
    
    missing_in_en = []
    missing_in_zh = []
    
    en_keys = get_all_keys(en_data)
    zh_keys = get_all_keys(zh_cn_data)
    
    for key in new_keys:
        if key not in en_keys:
            missing_in_en.append(key)
        if key not in zh_keys:
            missing_in_zh.append(key)
    
    success = True
    if missing_in_en:
        print(f"\n⚠ New component keys missing in English ({len(missing_in_en)}):")
        for key in missing_in_en:
            print(f"  - {key}")
        success = False
    
    if missing_in_zh:
        print(f"\n⚠ New component keys missing in Chinese ({len(missing_in_zh)}):")
        for key in missing_in_zh:
            print(f"  - {key}")
        success = False
    
    if success:
        print(f"✓ All {len(new_keys)} new component keys exist in both languages")
    
    return success


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
    print("VidTanium i18n Translation Coverage Test (Standalone)")
    print("="*60 + "\n")
    
    try:
        # Test 1: Files exist
        en_file, zh_cn_file = test_translation_files_exist()
        if not en_file or not zh_cn_file:
            return 1
        
        # Test 2: Files are parseable
        en_data, zh_cn_data = test_translation_files_parseable(en_file, zh_cn_file)
        if not en_data or not zh_cn_data:
            return 1
        
        # Test 3: Key parity
        parity_ok = test_translation_key_parity(en_data, zh_cn_data)
        
        # Test 4: No empty values
        empty_en_ok = test_no_empty_values(en_data, "English")
        empty_zh_ok = test_no_empty_values(zh_cn_data, "Chinese")
        
        # Test 5: New component keys
        new_keys_ok = test_new_component_keys_exist(en_data, zh_cn_data)
        
        # Generate coverage report
        generate_coverage_report(en_data, zh_cn_data)
        
        # Summary
        all_tests = [
            parity_ok,
            empty_en_ok,
            empty_zh_ok,
            new_keys_ok
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
