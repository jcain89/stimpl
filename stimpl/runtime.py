from typing import Any, Tuple, Optional

from stimpl.expression import *
from stimpl.types import *
from stimpl.errors import *

"""
Interpreter State
"""


class State(object):
    def __init__(self, variable_name: str, variable_value: Expr, variable_type: Type, next_state: 'State') -> None:
        self.variable_name = variable_name
        self.value = (variable_value, variable_type)
        self.next_state = next_state

    def copy(self) -> 'State':
        variable_value, variable_type = self.value
        return State(self.variable_name, variable_value, variable_type, self.next_state)

    def set_value(self, variable_name, variable_value, variable_type):
        return State(variable_name, variable_value, variable_type, self)

    #go through states and check if I match the variable name then return the value if thats true
    def get_value(self, variable_name) -> Any:
        if self.variable_name == variable_name:
            return self.value
        else:
            return self.next_state.get_value(variable_name)

    def __repr__(self) -> str:
        return f"{self.variable_name}: {self.value}, " + repr(self.next_state)


class EmptyState(State):
    def __init__(self):
        pass

    def copy(self) -> 'EmptyState':
        return EmptyState()

    def get_value(self, variable_name) -> None:
        return None

    def __repr__(self) -> str:
        return ""


"""
Main evaluation logic!
"""


def evaluate(expression: Expr, state: State) -> Tuple[Optional[Any], Type, State]:
    match expression:
        case Ren():
            return (None, Unit(), state)

        case IntLiteral(literal=l):
            return (l, Integer(), state)

        case FloatingPointLiteral(literal=l):
            return (l, FloatingPoint(), state)

        case StringLiteral(literal=l):
            return (l, String(), state)

        case BooleanLiteral(literal=l):
            return (l, Boolean(), state)

        case Print(to_print=to_print):
            printable_value, printable_type, new_state = evaluate(
                to_print, state)

            match printable_type:
                case Unit():
                    print("Unit")
                case _:
                    print(f"{printable_value}")

            return (printable_value, printable_type, new_state)

        #Case for sequence loops through and evaluates expressions
        case Sequence(exprs=exprs) | Program(exprs=exprs):
            if exprs == ():
                return (None, Unit(), None)
            for expr in exprs:
                expr_value, expr_type, state = evaluate(expr, state)
            return (expr_value, expr_type, state)

        case Variable(variable_name=variable_name):
            value = state.get_value(variable_name)
            if value == None:
                raise InterpSyntaxError(
                    f"Cannot read from {variable_name} before assignment.")
            variable_value, variable_type = value
            return (variable_value, variable_type, state)

        case Assign(variable=variable, value=value):

            value_result, value_type, new_state = evaluate(value, state)

            variable_from_state = new_state.get_value(variable.variable_name)
            _, variable_type = variable_from_state if variable_from_state else (
                None, None)

            if value_type != variable_type and variable_type != None:
                raise InterpTypeError(f"""Mismatched types for Assignment:
            Cannot assign {value_type} to {variable_type}""")

            new_state = new_state.set_value(
                variable.variable_name, value_result, value_type)
            return (value_result, value_type, new_state)

        #Case for adding only works on int floating point and string
        case Add(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_result + right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        #Case for subtraction only works on int and floating point
        case Subtract(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for subtract:
            Cannot subtract {left_type} to {right_type}""")
            match left_type:
                case Integer() | FloatingPoint():
                    result = left_result - right_result
                case _:
                    raise InterpTypeError(f"""Cannot subtract {left_type}s""")
            return (result, left_type, new_state)

        #Case for multiplication only works on ints and floating points
        case Multiply(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for multiply:
            Cannot multiply {left_type} to {right_type}""")
            match left_type:
                case Boolean() | Unit():
                    raise InterpTypeError(f"""Mismatched types for divide:
            Cannot divide {left_type} to {right_type}""")
                case Integer() | FloatingPoint():
                    result = left_result * right_result
                case _:
                    raise InterpTypeError(f"""Cannot multiply {left_type}s""")
            return (result, left_type, new_state)

        #Case for division only works on int and floating points but the division cases are slightly different
        case Divide(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)
            if right_result == 0:
                raise(InterpMathError())
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for divide:
            Cannot divide {left_type} to {right_type}""")
            match left_type:
                case Integer():
                    result = left_result // right_result
                case FloatingPoint():
                    result = left_result / right_result
                case _:
                    raise InterpTypeError(f"""Cannot divide {left_type}s""")
            return (result, left_type, new_state)

        #Case for ands only works on boolean types
        case And(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot and {left_type} to {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value and right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        #Case for Ors only works on boolean types
        case Or(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Or:
            Cannot or {left_type} to {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value | right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical or on non-boolean operands.")
            return (result, left_type, new_state)

        #Case for nots only works on boolean types
        case Not(expr=expr):
            expr_value, expr_type, expr_new_state = evaluate(expr, state)
            match expr_type:
                case Boolean():
                    result = not expr_value
                case _:
                    raise InterpTypeError(f"""Cannot not {expr_type}s""")
            return (result, expr_type, expr_new_state)


        #Case for Ifs only works on condition type booolean
        case If(condition=condition, true=true, false=false):
            condition_value, condition_type, new_state = evaluate(condition,state)
            match condition_type:
                case Boolean():
                    true_value, true_type, true_new_state = evaluate(true, new_state)
                    false_value, false_type, false_new_state = evaluate(false, new_state)
                    if condition_value == True:
                        return (true_value, true_type, true_new_state)
                    return (false_value, false_type, false_new_state)
                case _:
                    raise(InterpTypeError)

        #Case for Less Than only works on int, boolean, string, and floating points if unit its false
        case Lt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} to {right_type}""")
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value < right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")

            return (result, Boolean(), new_state)

        #Case for less than or equal to only works on int, boolean, string, floating points if unit its true
        case Lte(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Unit():
                    result = True
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value <= right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform <= on {left_type} type.")

            return (result, Boolean(), new_state)

        #Case for greater than only works on int, boolean, string, floating point, if unit its false
        case Gt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gt:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value > right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform > on {left_type} type.")

            return (result, Boolean(), new_state)
            
        #Case for Greater than or equal to only works on int, boolean, string, floating point, if unit its true
        case Gte(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gte:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value >= right_value
                case Unit():
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform >= on {left_type} type.")

            return (result, Boolean(), new_state)

        #Case for equals only works on int, boolean, string, floating point, if unit its true
        case Eq(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Ne:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value == right_value
                case Unit():
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform Ne on {left_type} type.")

            return (result, Boolean(), new_state)

        #Case for not equal to only works on int, boolean, string, floating point, if unit its false
        case Ne(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Ne:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value != right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform Ne on {left_type} type.")

            return (result, Boolean(), new_state)

        #Case for while only works when condition is of type boolean
        case While(condition=condition, body=body):
            value_condition, value_condition_type, new_state = evaluate(condition, state)
            match value_condition_type:
                case Boolean():
                    while value_condition:
                        new_value, new_value_type, new_state = evaluate(body, new_state)
                        value_condition, value_condition_type, new_state = evaluate(condition, new_state)
                case _:
                    raise InterpTypeError(f"Cannot perform while loop with non-boolean operand")
        
            return (False, Boolean(), new_state)
                            
                    

        case _:
            raise InterpSyntaxError("Unhandled!")
    pass


def run_stimpl(program, debug=False):
    state = EmptyState()
    program_value, program_type, program_state = evaluate(program, state)

    if debug:
        print(f"program: {program}")
        print(f"final_value: ({program_value}, {program_type})")
        print(f"final_state: {program_state}")

    return program_value, program_type, program_state
