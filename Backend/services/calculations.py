import math
from queue import LifoQueue
import utils
from services.formatters import formatMoney
from models.dto.spendings_dto import SpendingType
from utils import BotException
import re

MONEY_ACCURACY = 5

opening_brackets = "([{<"
closing_brackets = ")]}>"
operation_priorities = {"-" : 1, "+": 1, "*": 2, "×": 2, "⋅": 2, "/": 3, "÷": 3}

class ExpressionContext:
  def __init__(self):
    self.total_sum: float | None = None

  def with_total_sum(self, total_sum: float) -> 'ExpressionContext':
    self.total_sum = total_sum
    return self

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

def find_brace_end(expr: str, fromPos: int) -> int:
  count = 1
  for i in range(fromPos, len(expr)):
    match expr[i]:
      case '(':
        count += 1
      case ')':
        count -= 1
        if count == 0:
          return i
  return -1

def trim_expr(expr: str):
  while len(expr) > 1 and expr[0] == '(' and expr[-1] == ')' and find_brace_end(expr, 1) == len(expr) - 1:
    expr = expr[1:-1]
  return expr

def calculate_token(expr, context: ExpressionContext):
  if expr == 'x':
    return (0, 1)
  elif expr == 's':
    if context.total_sum == None:
      raise Exception(f"Так нельзя использовать переменную s")
    return (context.total_sum, 0)
  else:
    try:
      time_match = re.match(r"^(\d?\d):(\d\d)$", expr)
      if time_match:
        return (float(time_match.group(1))*60+float(time_match.group(2)), 0)
      return (float(expr), 0)
    except ValueError:
      raise Exception(f"Значение должно быть числом, переменной или временем. Сейчас - '{expr}'")

def calculate_operation(left_value, op, right_value):
  if op == '+':
    return (left_value[0] + right_value[0], left_value[1] + right_value[1])
  elif op == '-':
    return (left_value[0] - right_value[0], left_value[1] - right_value[1])
  elif op in ('*', '×', '⋅'):
    if (left_value[1] != 0) and (right_value[1] != 0):
      raise Exception("Нельзя умножать x на x")
    # (1 + x1) * (2 + x2) = 1 * 2   +    1 * x2 + 2 * x1
    return (left_value[0] * right_value[0], left_value[0] * right_value[1] + right_value[0] * left_value[1])
  elif op in ('/', '÷', ':'):
    if (right_value[1] != 0):
      raise Exception("Попытка деления на x")
    if (right_value[0] == 0):
      raise Exception("Попытка деления на ноль")
    return (left_value[0] / right_value[0], left_value[1] / right_value[0])
  else:
    raise Exception(f"Неподдерживаемая операция '{op}'")

def calculate(expr: str, context: ExpressionContext):
  expr = trim_expr(expr)
  split_index = get_split_index(expr)

  if split_index == -1:
    return calculate_token(expr, context)
  else:
    left_expr = expr[:split_index]
    right_expr = expr[split_index + 1:]
    op = expr[split_index]

    if left_expr == '' and op == '-':
      left_expr = '0'

    left_value = calculate(left_expr, context)
    right_value = calculate(right_expr, context)

    return calculate_operation(left_value, op, right_value)

def validate_brackets(expr: str):
  stack = LifoQueue()

  for c in expr:
    if (c in opening_brackets):
      stack.put(opening_brackets.index(c))
    elif (c in closing_brackets):
      if stack.empty() or closing_brackets.index(c) != stack.get():
        raise Exception("Неверная последовательность скобок")

  if not stack.empty():
    raise Exception("Неверная последовательность скобок")

def validate_expression(expr: str):
  validate_brackets(expr)

def parse_expression(expr: str | float, context: ExpressionContext | None):
  expr = str(expr).lower().replace(' ', '').replace('х','x').replace(',','.')
  validate_expression(expr)
  return calculate(expr, context)

# Matches each expression with its calculated value
def calculate_spendings(expressions, total_sum) -> list[float]:
  context = ExpressionContext().with_total_sum(total_sum)
  try:
    expressions_values = list(map(lambda expr: parse_expression(expr, context), expressions))
  except Exception as e:
    raise utils.BotWrongInputException(f'Некорректная сумма у должника, правильный пример - <code>100 + x</code>\n<b>{str(e)}</b>')
  expressions_sum = [sum(i) for i in zip(*expressions_values)]
  # a * x + b = total_sum
  a_total = expressions_sum[1]
  b_total = expressions_sum[0]

  if a_total == 0:
    diff = total_sum - b_total
    if abs(diff) >= MONEY_ACCURACY * len(expressions):
      if diff > 0:
        raise BotException(f"Не сошлось: не хватает {formatMoney(diff)}")
      else:
        raise BotException(f"Не сошлось: лишние {formatMoney(-diff)}")
    return [b + diff / len(expressions) for b, a in expressions_values]

  x = (total_sum - b_total) / a_total

  return [a * x + b for b, a in expressions_values]

def get_spending_meta_info(expressions: list[str], total_sum: float) -> tuple[SpendingType, float, float | None]:
  context = ExpressionContext().with_total_sum(total_sum)
  expressions_values = list(map(lambda expr: parse_expression(expr, context), expressions))
  expressions_sum = [sum(i) for i in zip(*expressions_values)]
  # a * x + b = total_sum
  a_total = expressions_sum[1]
  b_total = expressions_sum[0]
  x_value: float | None = None
  if a_total != 0.0:
    x_value = (total_sum - b_total) / a_total
  spendingType = SpendingType.SIMPLE if a_total == 0.0 else SpendingType.RELATIVE
  currentAmount = 0.0
  if spendingType == SpendingType.SIMPLE:
    currentAmount = b_total
  return (spendingType, total_sum - currentAmount, x_value)
