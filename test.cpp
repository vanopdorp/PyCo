#include <iostream>
#include "value.hpp"
#include "range.hpp"
#include "booleans.hpp"
#include "builtin.hpp"
Value Person__init__(Value self, Value name) {
    self.asObject()->fields["name"] = name;
    return Value();
}
Value Person__greet(Value self) {
    return add_builtin_func(Value("Hello "), self.asObject()->fields["name"]);
}
Value Person__new__(Value cls_obj) {
    auto obj = std::make_shared<Object>();
    return Value(obj);
}
Value Person__repr__(Value self) {
    return Value("<Person object>");
}
Value Person(Value name) {
    auto obj = std::make_shared<Object>();
    obj->type_name = "Person";
    Value self(obj);
    Person__init__(self, name);
    return self;
}
Value Employee__init__(Value self, Value name, Value role) {
    Person__init__(self, name);
    self.asObject()->fields["role"] = role;
    return Value();
}
Value Employee____str__(Value self) {
    return Value("an employee");
}
Value Employee__describe(Value self) {
    return add_builtin_func(add_builtin_func(add_builtin_func(self.asObject()->fields["name"], Value(" (")), self.asObject()->fields["role"]), Value(")"));
}
Value Employee__greet(Value self) {
    print(Value("hello"), self.asObject()->fields["name"], Value("with role"), self.asObject()->fields["role"]);
    return Value();
}
Value Employee__new__(Value cls_obj) {
    auto obj = std::make_shared<Object>();
    return Value(obj);
}
Value Employee__repr__(Value self) {
    return Value("<Employee object>");
}
Value Employee(Value name, Value role) {
    auto obj = std::make_shared<Object>();
    obj->type_name = "Employee";
    Value self(obj);
    Employee__init__(self, name, role);
    return self;
}
Value add(Value a, Value b) {
    return add_builtin_func(a, b);
}
Value do_anything(Value a) {
    Value _tmp0 = Value(make_list({}));
    for (Value val : iterate(a)) {
        if (!eq(mod_builtin_func(val, Value(2)), Value(0)).asBool()) continue;
        list_append(_tmp0, val);
    }
    return _tmp0;
}
int main() {
    builtin_methods["Employee__str__"] = Employee____str__;
    builtin_methods["Employee__repr__"] = Employee__repr__;
    builtin_methods["Employee__new"] = Employee__new__;
    builtin_methods["Person__repr__"] = Person__repr__;
    builtin_methods["Person__new"] = Person__new__;
    Value test = Value(7);
    Value uitkomst = sub_builtin_func(add(Value(3.14), test), mul_builtin_func(Value(17), Value(4)));
    print(mod_builtin_func(uitkomst, Value(2.5)));
    Value p = Person(Value("Joep"));
    print(Person__greet(p));
    Value e = Employee(Value("Piet"), Value("Dev"));
    print(Employee__describe(e));
    for (Value teller : range(Value(0), Value(1000000), Value(1))) {
    uitkomst = add_builtin_func(uitkomst, sub_builtin_func(sub_builtin_func(Value(3), Value(4373)), teller));
}
    Value f = Value(True);
    Value g = Value(False);
    if (or_op(and_op(not_op(lt(Value(1), Value(3))), f), g).asBool()) {
    print(Value("da's raar"));
} else {
    print(Value("klinkt logisch"));
}
    Value lst = Value(make_list({Value(1), Value(2), Value(3), Value("4")}));
    list_append(lst, Value(5.0));
    print(list_get(lst, Value(0)));
    print(lst);
    print(type(list_get(lst, Value(3))));
    Value d = Value(make_dict({{ Value("a"), Value(10) }, { Value(20), Value("b") }, { Value(True), Value(3.14) }}));
    print(dict_get(d, Value(True)));
    dict_set(d, Value(True), Value(3.14159));
    print(dict_get(d, Value(True)));
    Value res = do_anything(Value(make_list({Value(1), Value(2), Value(3), Value(4), Value(5)})));
    print(res);
    list_set(res, neg_builtin_func(Value(1)), Value(3));
    print(res);
    Value t = Value(make_tuple({Value(1), Value(2), Value(3)}));
    print(t);
    auto _tmp1 = t;
Value x = tuple_get(_tmp1, Value(0));
Value y = tuple_get(_tmp1, Value(1));
Value z = tuple_get(_tmp1, Value(2));
    print(z);
    print(type(z));
    print(e);
    print(p);
    return 0;
}