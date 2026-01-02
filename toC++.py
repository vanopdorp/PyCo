import ast

paths = {
    "/usr/lib/python3.11"
    "."
}


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
        # Ensure the temporary variable is initialized, even if it's just as an empty value

        print(self.output_stack)
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
                cpp = self.compile_stmt(stmt)
                # 🔑 eerst temps / helpers
                self.main_body.extend(self.output_stack)
                self.output_stack = []
                # 🔑 daarna de echte statement
                self.main_body.append(cpp)

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

        if isinstance(node, ast.Assign):
            if isinstance(node.targets[0], ast.Attribute):
                return self.compile_attr_assign(node)
            return self.compile_assign(node)
        if isinstance(node, ast.Try):
            # try block
            try_body = "\n".join("    " + self.compile_stmt(s) for s in node.body)

            cpp = "try {\n" + try_body + "\n}"

            # except handlers
            for handler in node.handlers:
                if handler.type is None:
                    # bare except
                    cpp += " catch (std::exception& e) {\n"
                else:
                    # except SomeError as e
                    exc_type, _ = self.compile_expr(handler.type)
                    name = handler.name or "e"
                    cpp += f" catch (std::exception& {name}) {{\n"

                handler_body = "\n".join("    " + self.compile_stmt(s) for s in handler.body)
                cpp += handler_body + "\n}"

            # else block
            if node.orelse:
                else_body = "\n".join("    " + self.compile_stmt(s) for s in node.orelse)
                cpp += f" /* else */ {{\n{else_body}\n}}"

            # finally block
            if node.finalbody:
                final_body = "\n".join("    " + self.compile_stmt(s) for s in node.finalbody)
                cpp += f" finally {{\n{final_body}\n}}"

            return cpp

        if isinstance(node, ast.Expr):
            return self.compile_expr(node.value)[0] + ";"
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript):
            return self.compile_subscript_assign(node)
        if isinstance(node, ast.Assert):
            test, _ = self.compile_expr(node.test)

            if node.msg is None:
                msg = '"Assertion failed"'
            else:
                msg, _ = self.compile_expr(node.msg)

            return f"if (!{test}.asBool()) throw std::runtime_error({msg}.asString());"

        if isinstance(node, ast.Break):
            return "break;"
        if isinstance(node, ast.Pass):
            return ";"
        if isinstance(node, ast.Raise):
            if node.exc is None:
                return 'raise_exception(Value("Exception"));"'
            exc, _ = self.compile_expr(node.exc)
            return f"raise_exception({exc});"

        if isinstance(node, ast.Continue):
            return "continue;"
        if isinstance(node,ast.Import):
            return ";"
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


            # Generic for-loop: for x in iterable
            iter_cpp, _ = self.compile_expr(node.iter)
            target = node.target.id
            body = "\n".join("    " + self.compile_stmt(s) for s in node.body)
            return f"for (Value {target} : iterate({iter_cpp})) {{\n{body}\n}}"

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

        # Dump in huidige scope
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
        if isinstance(node, ast.Attribute) and node.attr == "get":
            obj, _ = self.compile_expr(node.value)  # Het object (d)
            key, _ = self.compile_expr(node.args[0])  # Het sleutel argument (c)
            
            # Als er een tweede argument is, gebruik dat als de default waarde
            if len(node.args) > 1:
                default, _ = self.compile_expr(node.args[1])
                return f"dict_get({obj}, {key}, {default})", "Value"
            else:
                return f"dict_get({obj}, {key})", "Value"
        if isinstance(node, ast.Yield):
            raise NotImplementedError("yield is not supported yet")

        if isinstance(node, ast.GeneratorExp):
            # Gebruik dezelfde code als listcomp, maar maak een list
            temp = self.new_temp()
            lines = []

            # Maak lege lijst
            lines.append(f"Value {temp} = Value(make_list({{}}));")

            gen = node.generators[0]
            target = gen.target.id
            iter_cpp, _ = self.compile_expr(gen.iter)

            lines.append(f"for (Value {target} : iterate({iter_cpp})) {{")

            # if-filters
            for cond in gen.ifs:
                cond_cpp, _ = self.compile_expr(cond)
                lines.append(f"    if (!{cond_cpp}.asBool()) continue;")

            elt_cpp, _ = self.compile_expr(node.elt)
            lines.append(f"    list_append({temp}, {elt_cpp});")
            lines.append("}")

            # dump in output stack
            for line in lines:
                self.output_stack.append(line)

            return temp, "Value"

        # Constants
        if isinstance(node, ast.Constant):
            v = node.value

            # strings
            if isinstance(v, str):
                escaped = node.value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
                return f"Value(\"{escaped}\")", "Value"

            # ints / floats
            if isinstance(v, (int, float)):
                return f"Value({v})", "Value"

            # booleans
            if isinstance(v, bool):
                return f"Value({str(v).lower()})", "Value"   # true / false

            # None
            if v is None:
                return "Value()", "Value"

            # Ellipsis (...)
            if v is Ellipsis:
                return 'Value("Ellipsis")', "Value"

            # bytes
            if isinstance(v, bytes):
                s = v.decode("latin1")  # of utf-8
                return f'Value("{s}")', "Value"

            # complex numbers
            if isinstance(v, complex):
                return f"make_complex({v.real}, {v.imag})", "Value"

            raise NotImplementedError(f"Unsupported constant type: {type(v)}")

        if isinstance(node, ast.List):
            items = [self.compile_expr(item)[0] for item in node.elts]  # Compile each element
            return f"Value(make_list({{{', '.join(items)}}}))", "Value"
        if isinstance(node, ast.IfExp):
            test, _ = self.compile_expr(node.test)
            body, _ = self.compile_expr(node.body)
            orelse, _ = self.compile_expr(node.orelse)
            return f"({test}.asBool() ? {body} : {orelse})", "Value"
        if isinstance(node, ast.NamedExpr):
            # naam van de variabele
            target = node.target.id

            # compileer de rechterkant
            value_cpp, _ = self.compile_expr(node.value)

            # zorg dat de variabele bestaat in de huidige scope
            if target not in self.current_env:
                self.current_env[target] = "Value"
                decl = f"Value {target} = {value_cpp};"
            else:
                decl = f"{target} = {value_cpp};"

            # maak een tijdelijke naam
            temp = self.new_temp()

            # push de assignment in de output stack
            self.output_stack.append(decl)

            # return de waarde als expressie
            return target, "Value"
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(f'Value("{v.value}")')
                elif isinstance(v, ast.FormattedValue):
                    expr, _ = self.compile_expr(v.value)
                    parts.append(expr)
                else:
                    raise NotImplementedError(v)

            # concat alle stukken met jouw string-concat functie
            # ik neem aan dat jij add_builtin_func gebruikt voor strings
            expr = parts[0]
            for p in parts[1:]:
                expr = f"add_builtin_func({expr}, {p})"

            return expr, "Value"

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
            # verzamel alle stukken
            left = node.left
            ops = node.ops
            comps = node.comparators

            # compileer eerste vergelijking
            result_parts = []
            current_left, _ = self.compile_expr(left)

            for op, right_node in zip(ops, comps):
                right, _ = self.compile_expr(right_node)

                # bepaal operator
                if isinstance(op, ast.Lt):
                    expr = f"lt({current_left}, {right})"
                elif isinstance(op, ast.LtE):
                    expr = f"le({current_left}, {right})"
                elif isinstance(op, ast.Gt):
                    expr = f"gt({current_left}, {right})"
                elif isinstance(op, ast.GtE):
                    expr = f"ge({current_left}, {right})"
                elif isinstance(op, ast.Eq):
                    expr = f"eq({current_left}, {right})"
                elif isinstance(op, ast.NotEq):
                    expr = f"ne({current_left}, {right})"
                elif isinstance(op, ast.Is):
                    expr = f"is_op({current_left}, {right})"
                elif isinstance(op, ast.IsNot):
                    expr = f"not_op(is_op({current_left}, {right}))"
                elif isinstance(op, ast.In):
                    expr = f"in_op({current_left}, {right})"
                elif isinstance(op, ast.NotIn):
                    expr = f"not_op(in_op({current_left}, {right}))"
                else:
                    raise NotImplementedError(f"Comparison {op} not supported")

                result_parts.append(expr)

                # volgende vergelijking begint bij de rechterkant
                current_left = right

            # combineer alle vergelijkingen met AND
            final = result_parts[0]
            for part in result_parts[1:]:
                final = f"and_op({final}, {part})"

            return final, "Value"

        if isinstance(node, ast.Attribute):
            print(node.attr)
            if node.attr == "get":
                print("get")
                obj, _ = self.compile_expr(node.value)  # The dictionary
                key, _ = self.compile_expr(node.args[0])  # The key
                # The second argument of .get() is the default value
                if len(node.args) > 1:
                    default, _ = self.compile_expr(node.args[1])
                    return f"dict_get({obj}, {key}, {default})", "Value"
                else:
                    return f"dict_get({obj}, {key})", "Value"
            obj, _ = self.compile_expr(node.value)
            return f'{obj}.asObject()->fields["{node.attr}"]', "Value"

        if isinstance(node, ast.UnaryOp):
            # -x
            if isinstance(node.op, ast.USub):
                val, _ = self.compile_expr(node.operand)
                return f"neg_builtin_func({val})", "Value"

            # +x
            if isinstance(node.op, ast.UAdd):
                val, _ = self.compile_expr(node.operand)
                return val, "Value"   # unary + doet niets

            # not x
            if isinstance(node.op, ast.Not):
                val, _ = self.compile_expr(node.operand)
                return f"not_op({val})", "Value"

            # ~x  (bitwise invert)
            if isinstance(node.op, ast.Invert):
                val, _ = self.compile_expr(node.operand)
                return f"invert_builtin_func({val})", "Value"

            raise NotImplementedError(f"Unary operator {node.op} not supported")

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
            if isinstance(node.func, ast.Attribute) and node.func.attr == "join":
                # Get the delimiter (which is the first argument in the call)
                delimiter, _ = self.compile_expr(node.args[0])
                # Get the list of strings (the object that is calling join)
                obj, _ = self.compile_expr(node.func.value)

                # Generate C++ code equivalent to the Python str.join()
                return f"join_builtin_func({obj},{delimiter})", "Value"

            if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                obj, _ = self.compile_expr(node.func.value)
                key, _ = self.compile_expr(node.args[0])

                if len(node.args) > 1:
                    default, _ = self.compile_expr(node.args[1])
                    return f"dict_get({obj}, {key}, {default})", "Value"
                else:
                    return f"dict_get({obj}, {key})", "Value"

            # super() of super(Class, self)
            if isinstance(node.func, ast.Attribute):
                func = node.func

                # Check of het een super() call is
                if isinstance(func.value, ast.Call) and isinstance(func.value.func, ast.Name) and func.value.func.id == "super":

                    # super() zonder args → gebruik huidige class
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

                    # Methode naam
                    method = func.attr

                    # Compile arguments
                    args = [self.compile_expr(a)[0] for a in node.args]

                    # Bouw C++ call
                    if method != "__init__":
                        return f"{base}__{method}(self{''.join(', ' + a for a in args)})", "Value"
                    else:
                        return f"{base}{method}(self{''.join(', ' + a for a in args)})", "Value"

            # dynamic dispatch
            if isinstance(node.func, ast.Attribute):
                # compile object expression
                obj_cpp, _ = self.compile_expr(node.func.value)
                method = node.func.attr
                args = [self.compile_expr(a)[0] for a in node.args]

                # check dynamic dispatch only if object is a simple variable
                cls = None
                if isinstance(node.func.value, ast.Name):
                    varname = node.func.value.id
                    cls = self.current_var_classes.get(varname)

                # list.append special case
                if cls == "List" and method == "append":
                    return f"list_append({obj_cpp}, {args[0]})", "Value"

                # dynamic dispatch
                while cls:
                    if method in self.class_methods.get(cls, set()):
                        return f"{cls}__{method}({obj_cpp}{''.join(', ' + a for a in args)})", "Value"
                    cls = self.class_bases.get(cls)

                # fallback: direct attribute call
                return f"{obj_cpp}.asObject()->fields[\"{method}\"]({', '.join(args)})", "Value"

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
    code = open("randomtest.py").read()

    compiler = CppCompiler()
    cpp = compiler.compile(code)
    with open("test.cpp", "w") as f:
        f.write(cpp)
