#!/usr/bin/env python3

class Calculator:
    def __init__(self, num1, num2):
        self.num1 = num1
        self.num2 = num2

    def add(self):
        return self.num1 + self.num2

    def subtract(self):
        return self.num1 - self.num2

    def multiply(self):
        return self.num1 * self.num2

    def divide(self):
        if self.num2 != 0:
            return self.num1 / self.num2
        else:
            return 'Error: Division by zero'

if __name__ == '__main__':
    num1 = float(input('Enter first number: '))
    num2 = float(input('Enter second number: '))
    operation = input('Enter operation (add, subtract, multiply, divide): ')

    calc = Calculator(num1, num2)
    if operation == 'add':
        print('Result:', calc.add())
    elif operation == 'subtract':
        print('Result:', calc.subtract())
    elif operation == 'multiply':
        print('Result:', calc.multiply())
    elif operation == 'divide':
        print('Result:', calc.divide())
    else:
        print('Invalid operation')