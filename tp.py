class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return "Hello " + self.name

class Employee(Person):
    def __init__(self, name, role):
        super().__init__(name)
        self.role = role

    def describe(self):
        return self.name + " (" + self.role + ")"
    def greet(self):
        print("hello",self.name,"with role",self.role)
def add(a,b):
    return a + b

test = 7
uitkomst = add(3.14,test) - 17 * 4
print(uitkomst)
p = Person("Joep")
print(p.greet())

e = Employee("Piet", "Dev")
print(e.describe())

for teller in range(1000000):
    uitkomst += 3 - 4373 - teller