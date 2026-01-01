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
### that compiles to
```C++
#include <iostream>
#include "library/value.hpp"
#include "library/range.hpp"
#include "library/booleans.hpp"
Value Animal__init__(Value self, Value name) {
    self.asObject()->fields["name"] = name;
    return Value();
}
Value Animal__speak(Value self) {
    return add_builtin_func(Value("Hello "), self.asObject()->fields["name"]);
}
Value Animal__new__(Value cls_obj) {
    auto obj = std::make_shared<Object>();
    return Value(obj);
}
Value Animal__repr__(Value self) {
    return Value("<Animal object>");
}
Value Animal(Value name) {
    auto obj = std::make_shared<Object>();
    obj->type_name = "Animal";
    Value self(obj);
    Animal__init__(self, name);
    return self;
}
Value Dog__init__(Value self, Value name, Value breed) {
    Animal__init__(self, name);
    self.asObject()->fields["breed"] = breed;
    return Value();
}
Value Dog__speak(Value self) {
    return add_builtin_func(Value("Woof "), self.asObject()->fields["name"]);
}
Value Dog__new__(Value cls_obj) {
    auto obj = std::make_shared<Object>();
    return Value(obj);
}
Value Dog__repr__(Value self) {
    return Value("<Dog object>");
}
Value Dog(Value name, Value breed) {
    auto obj = std::make_shared<Object>();
    obj->type_name = "Dog";
    Value self(obj);
    Dog__init__(self, name, breed);
    return self;
}
int main() {
    builtin_methods["Dog__repr__"] = Dog__repr__;
    builtin_methods["Dog__new"] = Dog__new__;
    builtin_methods["Animal__repr__"] = Animal__repr__;
    builtin_methods["Animal__new"] = Animal__new__;
    Value dog = Dog(Value("Rex"), Value("Bulldog"));
    print(Dog__speak(dog));
    return 0;
}
```


## Searching for Developers

I am looking for developers who are interested in testing, providing feedback, and contributing to improving the code. My goal is to build a team of passionate developers to actively enhance and maintain this project. If you want to help make this project better, your contributions are welcome!
