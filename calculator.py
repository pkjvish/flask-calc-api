import math


class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    def power(self, a: float, b: float) -> float:
        return math.pow(a, b)

    def sqrt(self, a: float) -> float:
        if a < 0:
            raise ValueError("Cannot compute sqrt of negative number")
        return math.sqrt(a)