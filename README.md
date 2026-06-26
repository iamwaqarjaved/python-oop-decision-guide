# Python OOP Decision Guide

> When should you write a class? When should you write a function? This guide answers that.

Python is multi-paradigm — you can write entire applications without ever defining a class,
and many real Python projects do. Knowing *when* classes earn their complexity is one of the
most important judgments a Python developer makes.

## Contents

| File | Description |
|---|---|
| `oop_decision_guide.md` | The full 12-section decision guide |
| `oop_right_examples.py` | 4 worked examples where OOP is clearly right |
| `procedural_right_examples.py` | 4 worked examples where procedural is clearly cleaner |
| `it_depends_examples.py` | 2 worked examples where context drives the decision |

## Topics Covered

- Decision criteria: when classes pay off vs. when they don't
- `@dataclass` — when it replaces `__init__`, when it doesn't
- Encapsulation in Python: the single-underscore convention and why `__name` mangling is almost never appropriate
- Inheritance vs. composition: the modern Python community preference
- Anti-pattern register: Java-in-Python tendencies to avoid

## Running the Examples

Each companion file is self-contained with a `__main__` block:

\```bash
python oop_right_examples.py
python procedural_right_examples.py
python it_depends_examples.py
\```

No dependencies beyond the Python standard library.

## Module

This guide is produced as part of **Module 7: OOP in Python** coursework at Atlantis University.

## License

MIT