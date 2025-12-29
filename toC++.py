import ast

binop_map = {
    ast.Add: "add_builtin_func",
    ast.Sub: "sub_builtin_func",
    ast.Mult: "mul_builtin_func",
    ast.Div: "div_builtin_func",
    ast.FloorDiv: "floor_div_builtin_func",
    ast.Mod: "mod_builtin_func",
    ast.Pow: "pow_builtin_func",
    ast.LShift: "lshift_builtin_func",
    ast.RShift: "rshift_builtin_func",
    ast.BitOr: "bit_or_builtin_func",
    ast.BitAnd: "bit_and_builtin_func",
    ast.BitXor: "bit_xor_builtin_func"
}

class CppCompiler(ast.NodeVisitor):
    def __init__(self):
        self.global_env = {}
        self.current_env = None
        self.functions = []
        self.main_body = []
        self.output_stack = []  

        self.current_var_classes = {}
        self.class_bases = {}
        self.class_methods = {}
        self.current_class = None
    def new_temp(self): 
        if not hasattr(self, "_temp_counter"): 
            self._temp_counter = 0 
        name = f"_tmp{self._temp_counter}" 
        self._temp_counter += 1 
        return name
    def compile(self, code: str) -> str:
        tree = ast.parse(code)

        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef):
                self.visit(stmt)
            elif isinstance(stmt, ast.FunctionDef):
                self.visit_FunctionDef(stmt)

        self.current_env = self.global_env
        self.current_var_classes = {}

        for stmt in tree.body:
            if not isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
                self.main_body.append(self.compile_stmt(stmt))

        return self.generate_cpp()


    def visit_FunctionDef(self, node: ast.FunctionDef):
        name = node.name
        params = [a.arg for a in node.args.args]

        old_env = self.current_env
        old_stack = self.output_stack
        self.current_env = {p: "Value" for p in params}
        self.output_stack = []

        body = []
        for s in node.body:
            cpp = self.compile_stmt(s)
            body.extend(self.output_stack)
            self.output_stack = []
            body.append(cpp)
        print(body)
        if not any(b.strip().startswith("return") for b in body):
            body.append("return Value();")

        cpp = [f"Value {name}({', '.join('Value ' + p for p in params)}) {{"] + \
            ["    " + b for b in body] + ["}"]

        self.functions.append("\n".join(cpp))

        self.current_env = old_env
        self.output_stack = old_stack



    def visit_ClassDef(self, node: ast.ClassDef):
        cls = node.name
        self.class_methods[cls] = set()

        if node.bases:
            base = node.bases[0]
            if isinstance(base, ast.Name):
                self.class_bases[cls] = base.id

        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                self.class_methods[cls].add(stmt.name)
                self.compile_method(cls, stmt)
        default_dunders = {
            "__new__": [
                f"Value {cls}__new__(Value cls_obj) {{",
                "    auto obj = std::make_shared<Object>();",
                "    return Value(obj);",
                "}"
            ],
            "__repr__": [
                f"Value {cls}__repr__(Value self) {{",
                f"    return Value(\"<{cls} object>\");",
                "}"
            ],
        }

        for name, body in default_dunders.items():
            if name not in self.class_methods[cls]:
                self.functions.append("\n".join(body))
                self.class_methods[cls].add(name)
        self.main_body.insert(0,f'builtin_methods["{cls}__new"] = {cls}__new__;')
        self.main_body.insert(0,f'builtin_methods["{cls}__repr__"] = {cls}__repr__;')
        if "__str__" in self.class_methods[cls]:
            self.main_body.insert(0,f'builtin_methods["{cls}__str__"] = {cls}____str__;')
        if "__init__" in self.class_methods[cls]:
            init = next(m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == "__init__")
            params = [a.arg for a in init.args.args][1:]  # skip self
            cpp = [
                f"Value {cls}({', '.join('Value ' + p for p in params)}) {{",
                "    auto obj = std::make_shared<Object>();",
                f'    obj->type_name = "{cls}";',
                "    Value self(obj);",
                f"    {cls}__init__(self{''.join(', ' + p for p in params)});",
                "    return self;",
                "}"
            ]
            self.functions.append("\n".join(cpp))
    def compile_dict_assign(self, node):
        target = node.targets[0]
        obj, _ = self.compile_expr(target.value)
        key, _ = self.compile_expr(target.slice)
        val, _ = self.compile_expr(node.value)

        return f"{obj}.asObject()->fields.set({key}, {val});"

    def compile_method(self, cls, node: ast.FunctionDef):
        old_env = self.current_env
        old_vars = self.current_var_classes
        old_class = self.current_class
        old_stack = self.output_stack

        self.current_env = {}
        self.current_var_classes = {}
        self.current_class = cls
        self.output_stack = []

        params = [a.arg for a in node.args.args]
        for p in params:
            self.current_env[p] = "Value"
        if params:
            self.current_var_classes[params[0]] = cls

        body = []
        for s in node.body:
            cpp = self.compile_stmt(s)
            body.extend(self.output_stack)
            self.output_stack = []
            body.append(cpp)

        if not any(b.strip().startswith("return") for b in body):
            body.append("return Value();")

        if node.name == "__init__":
            header = f"Value {cls}__init__({', '.join('Value ' + p for p in params)}) {{"
        else:
            header = f"Value {cls}__{node.name}({', '.join('Value ' + p for p in params)}) {{"

        self.functions.append("\n".join([header] + ["    " + b for b in body] + ["}"]))

        self.current_env = old_env
        self.current_var_classes = old_vars
        self.current_class = old_class
        self.output_stack = old_stack

    def compile_if(self, node: ast.If):
        cond, _ = self.compile_expr(node.test)
        cond = f"{cond}.asBool()"  
        body = "\n".join("    " + self.compile_stmt(s) for s in node.body)
        cpp = f"if ({cond}) {{\n{body}\n}}"


        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                # elif
                elif_node = orelse[0]
                cond, _ = self.compile_expr(elif_node.test)
                cond = f"{cond}.asBool()" 
                body = "\n".join("    " + self.compile_stmt(s) for s in elif_node.body)
                cpp += f" else if ({cond}) {{\n{body}\n}}"
                orelse = elif_node.orelse
            else:
                # else
                body = "\n".join("    " + self.compile_stmt(s) for s in orelse)
                cpp += f" else {{\n{body}\n}}"
                break

        return cpp
    def emit(self, line):
        if self.output_stack is not None:
            self.output_stack.append(line)
        else:
            self.main_body.append(line)
    def compile_subscript_assign(self, node):
        target = node.targets[0]
        obj, _ = self.compile_expr(target.value)
        index, _ = self.compile_expr(target.slice)
        val, _ = self.compile_expr(node.value)

        obj_name = target.value.id if isinstance(target.value, ast.Name) else None
        var_type = self.current_var_classes.get(obj_name)

        if var_type == "Dict":
            return f"dict_set({obj}, {index}, {val});"

        return f"list_set({obj}, {index}, {val});"

    def compile_stmt(self, node):
        self.output_stack = []
        if isinstance(node, ast.Assign):
            if isinstance(node.targets[0], ast.Attribute):
                return self.compile_attr_assign(node)
            return self.compile_assign(node)

        if isinstance(node, ast.Expr):
            return self.compile_expr(node.value)[0] + ";"
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript):
            return self.compile_subscript_assign(node)

        if isinstance(node, ast.Break):
            return "break;"
        if isinstance(node, ast.Pass):
            return ";"

        if isinstance(node, ast.Continue):
            return "continue;"

        if isinstance(node, ast.Return):
            return f"return {self.compile_expr(node.value)[0]};"
        if isinstance(node, ast.If):
            return self.compile_if(node)
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                args = [self.compile_expr(a)[0] for a in node.iter.args]
                target = node.target.id
                # range(start)
                if len(args) == 1:
                    start = "Value(0)"
                    end = args[0]
                    step = "Value(1)"

                # range(start, end)
                elif len(args) == 2:
                    start = args[0]
                    end = args[1]
                    step = "Value(1)"

                # range(start, end, step)
                elif len(args) == 3:
                    start = args[0]
                    end = args[1]
                    step = args[2]


                body = "\n".join("    " + self.compile_stmt(s) for s in node.body)
                return f"for (Value {target} : range({start}, {end}, {step})) {{\n{body}\n}}"


            raise NotImplementedError("Only for-loops over range() supported")
        if isinstance(node, ast.AugAssign):
            target = node.target.id
            op_type = type(node.op)
            op_func = binop_map.get(op_type)
            if op_func is None:
                raise NotImplementedError(f"Operator {op_type} not supported in AugAssign")
            value, _ = self.compile_expr(node.value)
            return f"{target} = {op_func}({target}, {value});"
        if isinstance(node, ast.While):
            cond, _ = self.compile_expr(node.test)
            cond = f"{cond}.asBool()"
            body = "\n".join("    " + self.compile_stmt(s) for s in node.body)
            return f"while ({cond}) {{\n{body}\n}}"
        if isinstance(node,ast.FunctionDef):
            return self.visit_NestedFunctionDef(node)
        raise NotImplementedError(f"not implemented: {node}")
    def visit_NestedFunctionDef(self, node: ast.FunctionDef):
            name = node.name
            params = [a.arg for a in node.args.args]

            old_env = self.current_env
            old_stack = self.output_stack
            self.current_env = {p: "Value" for p in params}
            self.output_stack = []

            body = []
            for s in node.body:
                cpp = self.compile_stmt(s)
                body.extend(self.output_stack)
                self.output_stack = []
                body.append(cpp)
            print(body)
            try:
                if not any(b.strip().startswith("return") for b in body):
                    body.append("return Value();")
            except Exception:
                body.append("return Value();")
            cpp = [f"auto {name} = [&]({', '.join('Value ' + p for p in params)}) {{"] + \
                ["    " + b for b in body] + ["};"]


            self.current_env = old_env
            self.output_stack = old_stack
            return "".join(cpp)
    def compile_assign(self, node):
        if isinstance(node.targets[0], ast.Subscript):
            return self.compile_subscript_assign(node)


        expr, _ = self.compile_expr(node.value)
        if isinstance(node.targets[0], ast.Tuple):
            target_elts = node.targets[0].elts
            value_expr, _ = self.compile_expr(node.value)
            temp = self.new_temp()

            lines = [f"auto {temp} = {value_expr};"]

            for i, elt in enumerate(target_elts):
                name = elt.id
                if name not in self.current_env:
                    self.current_env[name] = "Value"
                    lines.append(f"Value {name} = tuple_get({temp}, Value({i}));")
                else:
                    lines.append(f"{name} = tuple_get({temp}, Value({i}));")

            return "\n".join(lines)
        name = node.targets[0].id
        # Track the type of the variable
        if isinstance(node.value, ast.List):  # Handling assignment of list
            self.current_var_classes[name] = "List"
        if isinstance(node.value, ast.Dict):
            self.current_var_classes[name] = "Dict"


        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            self.current_var_classes[name] = node.value.func.id

        if name not in self.current_env:
            self.current_env[name] = "Value"
            return f"Value {name} = {expr};"
        return f"{name} = {expr};"

    def compile_listcomp(self, node: ast.ListComp):
        temp = self.new_temp()
        lines = []

        # Maak lijst
        lines.append(f"Value {temp} = Value(make_list({{}}));")

        gen = node.generators[0]
        target = gen.target.id
        iter_cpp, _ = self.compile_expr(gen.iter)

        lines.append(f"for (Value {target} : iterate({iter_cpp})) {{")

        for cond in gen.ifs:
            cond_cpp, _ = self.compile_expr(cond)
            lines.append(f"    if (!{cond_cpp}.asBool()) continue;")

        elt_cpp, _ = self.compile_expr(node.elt)
        lines.append(f"    list_append({temp}, {elt_cpp});")
        lines.append("}")

        # Dump in the scope
        for line in lines:
            self.output_stack.append(line)

        return temp, "Value"

    def compile_attr_assign(self, node):
        obj, _ = self.compile_expr(node.targets[0].value)
        val, _ = self.compile_expr(node.value)
        return f'{obj}.asObject()->fields["{node.targets[0].attr}"] = {val};'

    # ---------------------------------------------------------
    # Expressions
    # ---------------------------------------------------------
    def compile_expr(self, node):
        # Constants
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return f'Value("{node.value}")', "Value"
            if isinstance(node.value, (int, float)):
                return f"Value({node.value})", "Value"
            if isinstance(node.value, list):  # Handle list literals
                items = [self.compile_expr(item)[0] for item in node.value]
                return f"Value(make_list({{ {', '.join(items)} }}))", "Value"
            if node.value is None:
                return "Value()", "Value"
        if isinstance(node, ast.List):
            items = [self.compile_expr(item)[0] for item in node.elts]  # Compile each element
            return f"Value(make_list({{{', '.join(items)}}}))", "Value"
        if isinstance(node, ast.Subscript):
            obj_name = node.value.id if isinstance(node.value, ast.Name) else None
            obj, _ = self.compile_expr(node.value)
            index, _ = self.compile_expr(node.slice)

            # Check type
            if obj_name and self.current_var_classes.get(obj_name) == "Dict":
                return f"dict_get({obj}, {index})", "Value"
            if isinstance(node.slice, ast.Slice):
                obj, _ = self.compile_expr(node.value)

                lower = "Value(0)" if node.slice.lower is None else self.compile_expr(node.slice.lower)[0]
                upper = f"{obj}.asList()->size()" if node.slice.upper is None else self.compile_expr(node.slice.upper)[0]
                step  = "Value(1)" if node.slice.step is None else self.compile_expr(node.slice.step)[0]

                return f"list_slice({obj}, {lower}, {upper}, {step})", "Value"
            # Default: list
            return f"list_get({obj}, {index})", "Value"
        if isinstance(node, ast.ListComp):
            return self.compile_listcomp(node)
        if isinstance(node, ast.Tuple):
            items = [self.compile_expr(e)[0] for e in node.elts]
            return f"Value(make_tuple({{{', '.join(items)}}}))", "Value"


        if isinstance(node, ast.Dict):
            items = []
            for k, v in zip(node.keys, node.values):
                key_cpp, _ = self.compile_expr(k)
                val_cpp, _ = self.compile_expr(v)
                items.append(f"{{ {key_cpp}, {val_cpp} }}")

            return f"Value(make_dict({{{', '.join(items)}}}))", "Value"

        if isinstance(node, ast.Name):
            return node.id, "Value"
        # Comparisons (zoals <, >, ==, !=)
        if isinstance(node, ast.Compare):
            left, _ = self.compile_expr(node.left)
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise NotImplementedError("Only single comparisons supported")
            right, _ = self.compile_expr(node.comparators[0])
            op = node.ops[0]
            if isinstance(op, ast.Lt):
                return f"lt({left}, {right})", "Value"
            if isinstance(op, ast.LtE):
                return f"le({left}, {right})", "Value"
            if isinstance(op, ast.Gt):
                return f"gt({left}, {right})", "Value"
            if isinstance(op, ast.GtE):
                return f"ge({left}, {right})", "Value"
            if isinstance(op, ast.Eq):
                return f"eq({left}, {right})", "Value"
            if isinstance(op, ast.NotEq):
                return f"ne({left}, {right})", "Value"
            raise NotImplementedError(f"Comparison {op} not supported")
        if isinstance(node, ast.Attribute):
            obj, _ = self.compile_expr(node.value)
            return f'{obj}.asObject()->fields["{node.attr}"]', "Value"

        # Unary operators
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):  # -x
                val, _ = self.compile_expr(node.operand)
                return f"neg_builtin_func({val})", "Value"
            if isinstance(node.op, ast.Not):  # not x
                val, _ = self.compile_expr(node.operand)
                return f"not_op({val})", "Value"  
        if isinstance(node, ast.BoolOp):
            values = [self.compile_expr(v)[0] for v in node.values]
            if isinstance(node.op, ast.And):
                # a and b and c -> and_op(a, and_op(b, c))
                expr = values[0]
                for v in values[1:]:
                    expr = f"and_op({expr}, {v})"
                return expr, "Value"
            if isinstance(node.op, ast.Or):
                expr = values[0]
                for v in values[1:]:
                    expr = f"or_op({expr}, {v})"
                return expr, "Value"


        # Calls
        if isinstance(node, ast.Call):
            # super() or super(Class, self)
            if isinstance(node.func, ast.Attribute):
                func = node.func

                # Check of it a super() call is
                if isinstance(func.value, ast.Call) and isinstance(func.value.func, ast.Name) and func.value.func.id == "super":

                    if len(func.value.args) == 0:
                        base = self.class_bases.get(self.current_class)
                        if base is None:
                            raise NotImplementedError("super() called but class has no base class")

                    # super(Base, self)
                    elif len(func.value.args) == 2:
                        base_node = func.value.args[0]
                        if isinstance(base_node, ast.Name):
                            base = base_node.id
                        else:
                            raise NotImplementedError("Unsupported super() base class expression")

                    else:
                        raise NotImplementedError("super() with unexpected arguments")

                    # Method name
                    method = func.attr

                    # Compile arguments
                    args = [self.compile_expr(a)[0] for a in node.args]

                    # Build C++ calls
                    if method != "__init__":
                        return f"{base}__{method}(self{''.join(', ' + a for a in args)})", "Value"
                    else:
                        return f"{base}{method}(self{''.join(', ' + a for a in args)})", "Value"

            # dynamic dispatch
            if isinstance(node.func, ast.Attribute):
                obj = node.func.value.id
                method = node.func.attr
                args = [self.compile_expr(a)[0] for a in node.args]
                cls = self.current_var_classes[obj]
                if self.current_var_classes.get(obj) == "List" and method == "append":
                    arg = self.compile_expr(node.args[0])[0] 
                    return f"list_append({obj}, {arg})", "Value"

                while cls:
                    if method in self.class_methods.get(cls, set()):
                        return f"{cls}__{method}({obj}{''.join(', ' + a for a in args)})", "Value"
                    cls = self.class_bases.get(cls)
                raise NotImplementedError(f"Method {method} not found")

            # normal function call
            func_name = node.func.id
            args = [self.compile_expr(a)[0] for a in node.args]
            return f"{func_name}({', '.join(args)})", "Value"


        if isinstance(node, ast.BinOp):
            l, _ = self.compile_expr(node.left)
            r, _ = self.compile_expr(node.right)
            op_func = binop_map[type(node.op)]
            return f"{op_func}({l}, {r})", "Value"

        raise NotImplementedError(node)

    def generate_cpp(self):
        out = ['#include <iostream>', '#include "library/value.hpp"', '#include "library/range.hpp"','#include "library/booleans.hpp"']
        out += self.functions
        out.append("int main() {")
        out += ["    " + l for l in self.main_body]
        out.append("    return 0;")
        out.append("}")
        return "\n".join(out)

if __name__ == "__main__":
    code = """
class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return "Hello " + self.name

class Employee(Person):
    def __init__(self, name, role):
        super().__init__(name)
        self.role = role
    def __str__(self):
        return "an employee"
    def describe(self):
        return self.name + " (" + self.role + ")"
    def greet(self):
        print("hello",self.name,"with role",self.role)
def add(a,b):
    return a + b
def do_anything(a):
    return [val for val in a if val % 2 == 0]
test = 7
uitkomst = add(3.14,test) - 17 * 4
print(uitkomst % 2.5)
p = Person("Joep")
print(p.greet())

e = Employee("Piet", "Dev")
print(e.describe())

for teller in range(1000000):
    uitkomst += 3 - 4373 - teller


lst = [1, 2, 3,"4"]
lst.append(5.0)
print(lst[0])
print(lst)
print(type(lst[3]))
d = {"a": 10, 20: "b", True: 3.14}
print(d[True])
d[True] = 3.14159
print(d[True])
res = do_anything([1, 2, 3, 4, 5])
print(res)
res[-1] = 3
print(res)
t = (1,2,3)
print(t)
x,y,z = t
print(z)
print(type(z))
print(e)
print(p)
a = 3
a -= 1.47
print(a)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
print(fib(40))
def dosom():
    def indo():
        print("this is a nested func")
        def indodo():
            print("this is a nested func in a nested func")
        indodo()
    indo()
dosom()
def pass_it_on(x=[]):
    def do_something():
        print(x)
    do_something()
pass_it_on("hello")
pass_it_on(1)
pass_it_on(True)
pass_it_on(None)
pass_it_on(False)


    """

    compiler = CppCompiler()
    cpp = compiler.compile(code)
    print(cpp)
    with open("test.cpp", "w") as f:
        f.write(cpp)
