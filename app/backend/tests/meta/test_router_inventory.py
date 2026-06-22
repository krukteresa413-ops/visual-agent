import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "main.py"
BASELINE = Path(__file__).with_name("router_baseline.json")


def _registered_routers() -> set[str]:
    tree = ast.parse(MAIN.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Attribute) and fn.attr == "include_router"):
            continue
        if node.args and isinstance(node.args[0], ast.Name):
            names.add(node.args[0].id)
    return names


def test_registered_routers_match_snapshot():
    expected = set(json.loads(BASELINE.read_text(encoding="utf-8")))
    assert _registered_routers() == expected
