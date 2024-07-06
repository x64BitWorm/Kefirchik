import math
import re
from queue import LifoQueue

opening_brackets = "([{<"
closing_brackets = ")]}>"
operation_priorities = {"+": 1, "*": 2, "\\": 3}

def get_operation_priorities(expr: str):
  bracket_depth = 0
  bracket_priority = 9
  res = {}

  for idx, c in enumerate(expr):
    if c in opening_brackets:
      bracket_depth += 1
    elif c in closing_brackets:
      bracket_depth -= 1
    elif c in operation_priorities.keys():
      res[idx] = operation_priorities[c] + bracket_depth * bracket_priority

  return res

def get_lowest_priority_index(priority_map):
  minn = (-1, math.inf)
  for k, v in priority_map.items():
    if v < minn[1] or (v == minn[1] and k > minn[0]) :
      minn = (k, v)
  return minn[0]

def get_split_index(expr: str):
  priorities = get_operation_priorities(expr)
  return get_lowest_priority_index(priorities)

def trim_expr(expr: str):
  while True:
    expr1 = re.sub(r"^\s*\((.*)\)\s*$", r"\1", expr).strip()
    if (expr1 == expr):
      return expr
    else:
      expr = expr1

def calculate_token(expr):
  if expr == 'x':
    return (0, 1)
  else:
    try:
      return (int(expr), 0)
    except ValueError:
      raise Exception("Value is neither x nor number.")

def calculate_operation(left_value, op, right_value):
  if op == '+':
    return (left_value[0] + right_value[0], left_value[1] + right_value[1])
  elif op == '*':
    if (left_value[1] != 0) and (right_value[1] != 0):
      raise Exception("Cannot multiply two variables x.")
    # (1 + x1) * (2 + x2) = 1 * 2   +    1 * x2 + 2 * x1
    return (left_value[0] * right_value[0], left_value[0] * right_value[1] + right_value[0] * left_value[1])
  elif op == '\\':
    if (left_value[1] != 0):
      raise Exception("Attempt of division by variable x.")
    if (left_value[0] == 0):
      raise Exception("Attempt of division by 0.")
    return (left_value[0] / right_value[0], left_value[1] / right_value[0])
  else:
    raise Exception("Unsupported operation encountered.")

def calculate(expr: str):
  split_index = get_split_index(expr)

  if split_index == -1:
    return calculate_token(trim_expr(expr))
  else:
    left_expr = trim_expr(expr[:split_index])
    right_expr = trim_expr(expr[split_index + 1:])

    left_value = calculate(left_expr)
    right_value = calculate(right_expr)
    op = expr[split_index]

    return calculate_operation(left_value, op, right_value)

def validate_brackets(expr: str):
  stack = LifoQueue()

  for c in expr:
    if (c in opening_brackets):
      stack.put(opening_brackets.index(c))
    elif (c in closing_brackets):
      if stack.empty() or closing_brackets.index(c) != stack.get():
        raise Exception("Invalid brackets consequence.")

  if not stack.empty():
    raise Exception("Invalid brackets consequence.")

def validate_expression(expr: str):
  validate_brackets(expr)

def parse_expression(expr: str):
  validate_expression(expr)
  return calculate(expr)

def calculate_spendings(expressions, total_sum):
  expressions_values = list(map(parse_expression, expressions))
  expressions_sum = [sum(i) for i in zip(*expressions_values)]
  # a * x + b = total_sum
  a_total = expressions_sum[1]
  b_total = expressions_sum[0]

  if a_total == 0:
    if total_sum == b_total:
      return [b for b, a in expressions_values]
    else:
      raise Exception("Shtani ne soshlis :(")
  
  x = (total_sum - b_total) / a_total
  
  if x < 0:
    raise Exception("Variable x cannot be less than 0.")

  return [a * x + b for b, a in expressions_values]
