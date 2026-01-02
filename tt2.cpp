#include <iostream>
#include <functional>
#include "library/value.hpp"
Value log_decorator(Value func) {
    print("Calling function");
    func();
    return Value();
}
Value say_hello_without(Value to_print) {
    print(to_print);
    return Value();
}
int main() {
    auto say_hello1 = []() {
        return say_hello_without(Value("hello")); 
    };

    log_decorator(Value(std::function<Value()>(say_hello1)));
    auto say_hello2 = []() {
        return say_hello_without(Value(3)); 
    };
    log_decorator(Value(std::function<Value()>(say_hello2)));
    return 0;
}
