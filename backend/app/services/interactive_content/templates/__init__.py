"""
Question template generators for each game type.

Usage:
    from app.services.interactive_content.templates import TEMPLATE_REGISTRY
    generators = TEMPLATE_REGISTRY["counting"]
    question = generators["count_objects"](level=2)
"""

from . import counting, addition_sub, shapes_space, patterns

TEMPLATE_REGISTRY = {
    "counting": counting.GENERATORS,
    "addition_sub": addition_sub.GENERATORS,
    "shapes_space": shapes_space.GENERATORS,
    "patterns": patterns.GENERATORS,
}
