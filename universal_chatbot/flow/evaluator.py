"""Safe rule evaluator and variable templating for the Flow Engine.

Strictly avoids unsafe `eval()` or `exec()`.
Pure Python, zero framework dependencies.
"""

import ast
import operator
import re
from typing import Any, Dict, Optional


SAFE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

NAMED_OPERATORS = {
    "==": operator.eq,
    "=": operator.eq,
    "eq": operator.eq,
    "!=": operator.ne,
    "ne": operator.ne,
    "<": operator.lt,
    "lt": operator.lt,
    "<=": operator.le,
    "lte": operator.le,
    ">": operator.gt,
    "gt": operator.gt,
    ">=": operator.ge,
    "gte": operator.ge,
    "in": lambda a, b: a in b if b is not None else False,
    "not in": lambda a, b: a not in b if b is not None else True,
    "contains": lambda a, b: str(b).lower() in str(a).lower() if a is not None else False,
    "startswith": lambda a, b: str(a).lower().startswith(str(b).lower()) if a is not None else False,
    "endswith": lambda a, b: str(a).lower().endswith(str(b).lower()) if a is not None else False,
}


def interpolate_template(template: str, variables: Dict[str, Any]) -> str:
    """Safely replace `{var_name}` or `{{var_name}}` with its variable value."""
    if not template or not isinstance(template, str):
        return template or ""

    def _replace(match):
        var_name = match.group(1).strip()
        val = variables.get(var_name, "")
        return "" if val is None else str(val)

    # Replace {{var}} then {var}
    result = re.sub(r"\{\{([a-zA-Z0-9_\.]+)\}\}", _replace, template)
    result = re.sub(r"\{([a-zA-Z0-9_\.]+)\}", _replace, result)
    return result


class SafeConditionEvaluator:
    """Evaluates rule-based transition conditions against current variables."""

    @classmethod
    def evaluate(cls, condition: Any, variables: Dict[str, Any]) -> bool:
        """Evaluate a condition.

        Returns True if satisfied, False otherwise.
        None, empty string, or 'default' evaluate to True (unconditional).
        """
        if condition is None or condition == "" or condition == "default":
            return True

        if isinstance(condition, bool):
            return condition

        if isinstance(condition, dict):
            return cls._evaluate_dict(condition, variables)

        if isinstance(condition, str):
            condition = condition.strip()
            if not condition or condition.lower() == "default":
                return True
            return cls._evaluate_expression_string(condition, variables)

        return False

    @classmethod
    def _evaluate_dict(cls, rule: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        # Check compound conditions: all / any
        if "all" in rule and isinstance(rule["all"], list):
            return all(cls.evaluate(sub, variables) for sub in rule["all"])
        if "any" in rule and isinstance(rule["any"], list):
            return any(cls.evaluate(sub, variables) for sub in rule["any"])

        var_name = rule.get("variable")
        if not var_name:
            return True

        op_str = str(rule.get("operator", "==")).lower()
        target_val = rule.get("value")

        actual_val = variables.get(var_name)
        op_func = NAMED_OPERATORS.get(op_str)
        if not op_func:
            return False

        try:
            return bool(op_func(actual_val, target_val))
        except Exception:
            return False

    @classmethod
    def _evaluate_expression_string(cls, expr: str, variables: Dict[str, Any]) -> bool:
        try:
            tree = ast.parse(expr, mode="eval")
            return bool(cls._eval_node(tree.body, variables))
        except Exception:
            return False

    @classmethod
    def _eval_node(cls, node: ast.AST, variables: Dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return variables.get(node.id)
        elif isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, variables)
            for op, comparator in zip(node.ops, node.comparators):
                right = cls._eval_node(comparator, variables)
                op_func = SAFE_OPERATORS.get(type(op))
                if not op_func or not op_func(left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(cls._eval_node(val, variables) for val in node.values)
            elif isinstance(node.op, ast.Or):
                return any(cls._eval_node(val, variables) for val in node.values)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not cls._eval_node(node.operand, variables)
        elif isinstance(node, ast.List):
            return [cls._eval_node(elem, variables) for elem in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(cls._eval_node(elem, variables) for elem in node.elts)

        raise ValueError(f"Unsupported AST node in safe evaluation: {type(node)}")
