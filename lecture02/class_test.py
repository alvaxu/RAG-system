"""
-*- coding: utf-8 -*-
class_test.py -
Author：Administrator
Date:2025-04-05
"""


class student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def study(self):
        if self.age < 18:
            print("study middle school")
        else:
            print("study college")


if __name__ == '__main__':
    stud1 = student("xu1", 19)
    stud2 = student("xu2", 14)
    stud1.study()
    stud2.study()
