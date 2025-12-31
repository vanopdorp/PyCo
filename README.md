# PyCo
a simple Python to C++ compiler

### source code is in branches !!!

## Versions:
- [x] 0.6: alpha version
- [x] 0.7: beta version
- [ ] 0.8: beta version  

## code snippet that he can compile
```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "Hello " + self.name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

    def speak(self):
        return "Woof " + self.name

dog = Dog("Rex", "Bulldog")
print(dog.speak())
```


## Searching for Developers

I am looking for developers who are interested in testing, providing feedback, and contributing to improving the code. My goal is to build a team of passionate developers to actively enhance and maintain this project. If you want to help make this project better, your contributions are welcome!
