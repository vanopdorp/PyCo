#include <iostream>
#include <functional>
#include "library/value.hpp"
Value log_decorator(std::function<Value()> func) {
    std::cout << "Calling function..." << std::endl;
    func();  // Roep de originele functie aan via de functie pointer
    return Value();
}
Value say_hello(Value to_print) {
    print(to_print);
    return Value();
}
int main() {
    // Maak een lambda die say_hello aanroept met een Value argument
    auto func = []() {
        return say_hello(Value("hello"));  // Roep de functie aan met het juiste argument
    };

    // Geef de lambda door aan de decorator
    log_decorator(func);
    return 0;
}
