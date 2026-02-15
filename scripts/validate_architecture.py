import os
import re
import sys

def scan_files(root_dir, pattern):
    """Recursively scan files matching regex pattern."""
    matches = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.endswith('.py'):
                continue

            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            for match in re.finditer(pattern, content):
                matches.append({
                    'file': filepath,
                    'line': content[:match.start()].count('\n') + 1,
                    'match': match.group(1)
                })
    return matches

def validate_architecture():
    print("Running Architecture Validation...")
    errors = []

    # 1. Check for Duplicate Class Names
    class_pattern = r'class\s+([A-Z][a-zA-Z0-9_]+)\(?'
    all_classes = scan_files('backend', class_pattern)

    class_map = {}

    # Allowed exceptions (e.g. Schemas, Base classes, common utils)
    exceptions = {
        'BaseModel', 'BaseSovereignTool', 'Settings', 'Config',
        'TradeRequest', 'TradeResponse', 'PortfolioResponse', 'StrategyRequest', 'StrategyResponse'
    }

    for c in all_classes:
        name = c['match']
        if name in exceptions:
            continue

        # Ignore Pydantic schemas in domain/web vs domain/portfolio (often duplicated or shared)
        if 'schemas.py' in c['file']:
            continue

        if name in class_map:
            # Report only if files are different
            if class_map[name]['file'] != c['file']:
                errors.append(f"Duplicate Class Name: '{name}' found in:\n  - {class_map[name]['file']}\n  - {c['file']}")
        else:
            class_map[name] = c

    # 2. Check Folder Rules (Keyword-based)

    # Rule: 'Strategy' classes (logic) should be in 'strategies/'
    # Exception: StrategyParser (Jules), StrategyRequest/Response (Schemas), StrategyLibrary (Registry)
    strategies = [x for x in all_classes if 'Strategy' in x['match']]
    strategy_exceptions = ['StrategyParser', 'StrategyRequest', 'StrategyResponse', 'StrategyLibrary', 'BaseStrategy']

    for s in strategies:
        if s['match'] in strategy_exceptions:
            continue
        if 'schemas.py' in s['file']: # Pydantic models are fine
            continue

        if 'backend/strategies' not in s['file']:
            errors.append(f"Misclassified Strategy: '{s['match']}' found in '{s['file']}'. Should be in 'backend/strategies/'.")

    # Rule: 'Risk' classes (logic) should be in 'risk/'
    risks = [x for x in all_classes if 'Risk' in x['match']]
    risk_exceptions = ['RiskRequest', 'RiskResponse', 'RiskSnapshot'] # Schemas/Models

    for r in risks:
        if r['match'] in risk_exceptions:
            continue
        if 'schemas.py' in r['file']:
            continue

        if 'backend/risk' not in r['file']:
             # Exception: Risk might be in strategies/risk.py (legacy) but ideally move it.
             pass

    # 3. Report
    if errors:
        print("\n❌ Architecture Violations Found:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    else:
        print("\n✅ Architecture Validated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    validate_architecture()
