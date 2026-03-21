"""Quick test: scan currently open programs and print what was found."""
import sys
sys.path.insert(0, r"e:\0_Python\pyWorkspace")

from pyworkspace.sheets import get_open_windows_deep

apps = get_open_windows_deep()
print(f"\n{'='*80}")
print(f"  Found {len(apps)} programs currently open on your desktop")
print(f"{'='*80}\n")

for i, app in enumerate(apps, 1):
    print(f"[{i}] {app['name']}")
    print(f"    Path : {app['path']}")
    print(f"    Args : {app['args'] or '(none)'}")
    print(f"    CWD  : {app['cwd']}")
    print(f"    Titles: {app['titles']}")
    print(f"    Files : {app['open_files'] or '(none detected)'}")
    print()
