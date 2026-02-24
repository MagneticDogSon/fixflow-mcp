import sys
import os
import re
import yaml

def validate_kb_card(file_path):
    """
    Validates a Knowledge Base (KB) card markdown file against strict quality rules.
    """
    print(f"🔍 Validating: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    # 1. Check YAML Frontmatter
    yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not yaml_match:
        print("❌ Error: Missing YAML frontmatter (--- ... ---)")
        return False

    try:
        metadata = yaml.safe_load(yaml_match.group(1))
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
        return False

    # 2. Check Required Metadata Fields
    required_fields = ['kb_id', 'category', 'platform', 'criticality']
    missing_fields = [f for f in required_fields if f not in metadata]
    if missing_fields:
        print(f"❌ Error: Missing metadata fields: {', '.join(missing_fields)}")
        return False

    # 3. Check KB_ID Format (Simple Regex)
    kb_id = metadata.get('kb_id', '')
    if not re.match(r'^[A-Z]+_[A-Z]+_\d+$', kb_id):
        print(f"❌ Error: Invalid KB_ID format '{kb_id}'. Expected format like WIN_TERM_001")
        return False

    # 4. Check Required Sections
    required_sections = [
        r'#\s+',                   # Title
        r'##\s+🔍\s+This Is Your Problem If:',
        r'##\s+✅\s+SOLUTION\s+\(copy-paste\)',
        r'##\s+✔️\s+Verification'
    ]
    
    for pattern in required_sections:
        if not re.search(pattern, content):
            print(f"❌ Error: Missing required section matching pattern: '{pattern}'")
            return False

    # 5. Check Content Length (Spam protection)
    if len(content) < 200:
        print("❌ Error: Content too short (potential spam/stub). Minimum 200 chars.")
        return False

    if "TBD" in content or "TODO" in content:
        print("⚠️ Warning: File contains placeholders (TBD/TODO). Please review.")
        # We allow this but warn

    print("✅ Validation PASSED. File is ready for upload.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_kb_card.py <path_to_md_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    is_valid = validate_kb_card(file_path)
    
    if is_valid:
        sys.exit(0)
    else:
        sys.exit(1)
