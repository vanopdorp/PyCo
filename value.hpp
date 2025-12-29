#pragma once
#include <string>
#include <variant>
#include <iostream>
#include <unordered_map>
#include <memory>
#include <cmath>
#include <stdexcept>
#include <vector>
#include <charconv>
#include <functional>
std::string format_double(double d) {
    char buf[64];
    auto [ptr, ec] = std::to_chars(buf, buf + sizeof(buf),
                                   d, std::chars_format::general);
    return std::string(buf, ptr);
}


// ------------------------------------------------------------
// Forward declarations
// ------------------------------------------------------------
class Value;
struct Object;
struct List;
struct Tuple;
struct Dict;
inline Value eq(const Value& a, const Value& b);
bool has_builtin_method(const std::string& name);
Value call_builtin_method(const std::string& name, Value self);

std::unordered_map<std::string, std::function<Value(Value)>> builtin_methods;

// ------------------------------------------------------------
// List
// ------------------------------------------------------------
struct List {
    std::vector<Value> items;

    List() = default;
    List(std::initializer_list<Value> init) : items(init) {}
};

// ------------------------------------------------------------
// Tuple
// ------------------------------------------------------------
struct Tuple {
    std::vector<Value> items;

    Tuple() = default;
    Tuple(std::initializer_list<Value> init) : items(init) {}
};

// ------------------------------------------------------------
// Object
// ------------------------------------------------------------
struct Object {
    std::string type_name = "";   // <-- toevoegen!
    std::unordered_map<std::string, Value> fields;
};


// ------------------------------------------------------------
// Value type
// ------------------------------------------------------------
class Value {
public:
    using Variant = std::variant<
        std::monostate,
        int,
        double,
        bool,
        std::string,
        std::shared_ptr<Object>,
        std::shared_ptr<List>,
        std::shared_ptr<Tuple>,
        std::shared_ptr<Dict>
    >;

    Variant data;

    // Constructors
    Value() : data(std::monostate{}) {}
    Value(int v) : data(v) {}
    Value(double v) : data(v) {}
    Value(bool v) : data(v) {}
    Value(const std::string& v) : data(v) {}
    Value(const char* v) : data(std::string(v)) {}
    Value(std::shared_ptr<Object> obj) : data(obj) {}
    Value(std::shared_ptr<List> list) : data(list) {}
    Value(std::shared_ptr<Tuple> tup) : data(tup) {}
    Value(std::shared_ptr<Dict> dict) : data(dict) {}

    // Type checks
    bool isNull()   const { return std::holds_alternative<std::monostate>(data); }
    bool isInt()    const { return std::holds_alternative<int>(data); }
    bool isDouble() const { return std::holds_alternative<double>(data); }
    bool isBool()   const { return std::holds_alternative<bool>(data); }
    bool isString() const { return std::holds_alternative<std::string>(data); }
    bool isObject() const { return std::holds_alternative<std::shared_ptr<Object>>(data); }
    bool isList()   const { return std::holds_alternative<std::shared_ptr<List>>(data); }
    bool isTuple()  const { return std::holds_alternative<std::shared_ptr<Tuple>>(data); }
    bool isDict()   const { return std::holds_alternative<std::shared_ptr<Dict>>(data); }

    // Accessors
    int asInt() const {
        if (isInt()) return std::get<int>(data);
        if (isDouble()) return (int)std::get<double>(data);
        throw std::runtime_error("Value is not int");
    }
    std::string toString() const;
    double asDouble() const {
        if (isDouble()) return std::get<double>(data);
        if (isInt()) return (double)std::get<int>(data);
        throw std::runtime_error("Value is not double");
    }

    bool asBool() const {
        if (isBool()) return std::get<bool>(data);
        throw std::runtime_error("Value is not bool");
    }

    std::string asString() const {
        if (isString()) return std::get<std::string>(data);
        throw std::runtime_error("Value is not string");
    }

    std::shared_ptr<Object> asObject() const {
        if (isObject()) return std::get<std::shared_ptr<Object>>(data);
        throw std::runtime_error("Value is not object");
    }

    std::shared_ptr<List> asList() const {
        if (isList()) return std::get<std::shared_ptr<List>>(data);
        throw std::runtime_error("Value is not list");
    }

    std::shared_ptr<Tuple> asTuple() const {
        if (isTuple()) return std::get<std::shared_ptr<Tuple>>(data);
        throw std::runtime_error("Value is not tuple");
    }

    std::shared_ptr<Dict> asDict() const {
        if (isDict()) return std::get<std::shared_ptr<Dict>>(data);
        throw std::runtime_error("Value is not dict");
    }

    // ------------------------------------------------------------
    // Python-style toString()
    // ------------------------------------------------------------
    std::string str() const {
        if (isObject()) {
            auto obj = asObject();

            // 1. Kijk of er een C++ functie bestaat met naam ClassName__str__
            if (obj->type_name != "" && has_builtin_method(obj->type_name + "__str__")) {
                Value result = call_builtin_method(obj->type_name + "__str__", *this);
                return result.asString();
            }

            // 2. Anders fallback naar repr()
            return repr();
        }

        return toString();
    }
    std::string repr() const {
        if (isObject()) {
            auto obj = asObject();

            if (obj->type_name != "" && has_builtin_method(obj->type_name + "__repr__")) {
                Value result = call_builtin_method(obj->type_name + "__repr__", *this);
                return result.asString();
            }

            return "<object>";
        }

        return toString();
    }


};
bool has_builtin_method(const std::string& name) {
    return builtin_methods.count(name);
}

Value call_builtin_method(const std::string& name, Value self) {
    return builtin_methods[name](self);
}

// ------------------------------------------------------------
// Dict
// ------------------------------------------------------------
struct Dict {
    std::vector<std::pair<Value, Value>> entries;

    // Voeg een key-value paar toe
    void add(const Value& key, const Value& value) {
        for (auto& entry : entries) {
            if (eq(entry.first, key).asBool()) {  // Gebruik de eq functie
                entry.second = value;  // Als de sleutel al bestaat, update de waarde
                return;
            }
        }
        entries.push_back(std::make_pair(key, value));  // Voeg een nieuw paar toe
    }

    // Verkrijg waarde voor een bepaalde sleutel
    Value get(const Value& key) const {
        for (const auto& entry : entries) {
            if (eq(entry.first, key).asBool()) {  // Gebruik de eq functie
                return entry.second;
            }
        }
        throw std::runtime_error("Key not found in Dict");
    }

    // Controleer of een sleutel bestaat
    bool contains(const Value& key) const {
        for (const auto& entry : entries) {
            if (eq(entry.first, key).asBool()) {  // Gebruik de eq functie
                return true;
            }
        }
        return false;
    }

    // Verwijder een sleutel-waarde paar
    void remove(const Value& key) {
        auto it = entries.begin();
        while (it != entries.end()) {
            if (eq(it->first, key).asBool()) {  // Gebruik de eq functie
                entries.erase(it);
                return;
            }
            ++it;
        }
        throw std::runtime_error("Key not found in Dict");
    }

    // Verkrijg de grootte van de dict
    size_t size() const {
        return entries.size();
    }

    // Print de inhoud van de dict
    void print() const {
        for (const auto& entry : entries) {
            std::cout << entry.first.toString() << ": " << entry.second.toString() << std::endl;
        }
    }
};


// ------------------------------------------------------------
// MODULE 2 — Python‑style operators
// ------------------------------------------------------------

// ------------------------------------------------------------
// Helper: Python truthiness
// ------------------------------------------------------------
inline bool py_truth(const Value& v) {
    if (v.isBool()) return v.asBool();
    if (v.isInt()) return v.asInt() != 0;
    if (v.isDouble()) return v.asDouble() != 0.0;
    if (v.isString()) return !v.asString().empty();
    if (v.isList()) return !v.asList()->items.empty();
    if (v.isTuple()) return !v.asTuple()->items.empty();
    if (v.isDict()) return !v.asDict()->entries.empty();
    return false; // None → False
}

// ------------------------------------------------------------
// Arithmetic
// ------------------------------------------------------------

// Python-style addition
inline Value add_builtin_func(const Value& a, const Value& b) {
    // string + string
    if (a.isString() && b.isString())
        return Value(a.asString() + b.asString());

    // string + non-string → TypeError in Python
    if (a.isString() || b.isString())
        throw std::runtime_error("TypeError: can only concatenate str to str");

    // numeric
    return Value(a.asDouble() + b.asDouble());
}

inline Value sub_builtin_func(const Value& a, const Value& b) {
    return Value(a.asDouble() - b.asDouble());
}

inline Value mul_builtin_func(const Value& a, const Value& b) {
    // string * int
    if (a.isString() && b.isInt()) {
        std::string out;
        for (int i = 0; i < b.asInt(); i++) out += a.asString();
        return Value(out);
    }
    if (b.isString() && a.isInt()) {
        std::string out;
        for (int i = 0; i < a.asInt(); i++) out += b.asString();
        return Value(out);
    }

    return Value(a.asDouble() * b.asDouble());
}

inline Value div_builtin_func(const Value& a, const Value& b) {
    return Value(a.asDouble() / b.asDouble());
}

// Python-style floor division
inline Value floor_div_builtin_func(const Value& a, const Value& b) {
    double x = a.asDouble();
    double y = b.asDouble();
    return Value(std::floor(x / y));
}

// Python-style modulo
inline Value mod_builtin_func(const Value& a, const Value& b) {
    double x = a.asDouble();
    double y = b.asDouble();
    double result = x - std::floor(x / y) * y;
    return Value(result);
}

// Power
inline Value pow_builtin_func(const Value& a, const Value& b) {
    return Value(std::pow(a.asDouble(), b.asDouble()));
}

// Negation
inline Value neg_builtin_func(const Value& a) {
    return Value(-a.asDouble());
}

// ------------------------------------------------------------
// Boolean operators (Python truthiness)
// ------------------------------------------------------------
inline Value not_op(const Value& v) {
    return Value(!py_truth(v));
}

inline Value and_op(const Value& a, const Value& b) {
    return Value(py_truth(a) && py_truth(b));
}

inline Value or_op(const Value& a, const Value& b) {
    return Value(py_truth(a) || py_truth(b));
}

// ------------------------------------------------------------
// Comparisons
// ------------------------------------------------------------

// Python-style <
inline Value lt(const Value& a, const Value& b) {
    if (a.isDouble() || b.isDouble()) return Value(a.asDouble() < b.asDouble());
    if (a.isInt() || b.isInt()) return Value(a.asDouble() < b.asDouble());
    if (a.isString() && b.isString()) return Value(a.asString() < b.asString());
    throw std::runtime_error("TypeError: unsupported operand types for <");
}

inline Value le(const Value& a, const Value& b) {
    if (a.isDouble() || b.isDouble()) return Value(a.asDouble() <= b.asDouble());
    if (a.isInt() || b.isInt()) return Value(a.asDouble() <= b.asDouble());
    if (a.isString() && b.isString()) return Value(a.asString() <= b.asString());
    throw std::runtime_error("TypeError: unsupported operand types for <=");
}

inline Value gt(const Value& a, const Value& b) {
    if (a.isDouble() || b.isDouble()) return Value(a.asDouble() > b.asDouble());
    if (a.isInt() || b.isInt()) return Value(a.asDouble() > b.asDouble());
    if (a.isString() && b.isString()) return Value(a.asString() > b.asString());
    throw std::runtime_error("TypeError: unsupported operand types for >");
}

inline Value ge(const Value& a, const Value& b) {
    if (a.isDouble() || b.isDouble()) return Value(a.asDouble() >= b.asDouble());
    if (a.isInt() || b.isInt()) return Value(a.asDouble() >= b.asDouble());
    if (a.isString() && b.isString()) return Value(a.asString() >= b.asString());
    throw std::runtime_error("TypeError: unsupported operand types for >=");
}

// Python-style equality
inline Value eq(const Value& a, const Value& b) {
    if (a.isInt() && b.isInt()) return Value(a.asInt() == b.asInt());
    if (a.isDouble() && b.isDouble()) return Value(a.asDouble() == b.asDouble());
    if ((a.isInt() && b.isDouble()) || (a.isDouble() && b.isInt()))
        return Value(a.asDouble() == b.asDouble());
    if (a.isBool() && b.isBool()) return Value(a.asBool() == b.asBool());
    if (a.isString() && b.isString()) return Value(a.asString() == b.asString());

    // tuple equality
    if (a.isTuple() && b.isTuple()) {
        auto ta = a.asTuple();
        auto tb = b.asTuple();
        if (ta->items.size() != tb->items.size()) return Value(false);
        for (size_t i = 0; i < ta->items.size(); i++) {
            if (!eq(ta->items[i], tb->items[i]).asBool())
                return Value(false);
        }
        return Value(true);
    }

    // list equality
    if (a.isList() && b.isList()) {
        auto la = a.asList();
        auto lb = b.asList();
        if (la->items.size() != lb->items.size()) return Value(false);
        for (size_t i = 0; i < la->items.size(); i++) {
            if (!eq(la->items[i], lb->items[i]).asBool())
                return Value(false);
        }
        return Value(true);
    }

    // dict equality
    if (a.isDict() && b.isDict()) {
        auto da = a.asDict();
        auto db = b.asDict();
        if (da->entries.size() != db->entries.size()) return Value(false);

        for (auto& pa : da->entries) {
            bool found = false;
            for (auto& pb : db->entries) {
                if (eq(pa.first, pb.first).asBool()) {
                    if (!eq(pa.second, pb.second).asBool())
                        return Value(false);
                    found = true;
                    break;
                }
            }
            if (!found) return Value(false);
        }
        return Value(true);
    }

    return Value(false);
}

inline Value ne(const Value& a, const Value& b) {
    return Value(!eq(a, b).asBool());
}
// ------------------------------------------------------------
// MODULE 3 — Python‑style list operations
// ------------------------------------------------------------

// Helper: normalize Python negative index
inline int normalize_index(int index, int size) {
    if (index < 0) index += size;
    return index;
}

inline Value make_dict(std::initializer_list<std::pair<Value, Value>> items) {
    Dict dict;  // Maak een lege Dict
    for (const auto& item : items) {
        dict.add(item.first, item.second);  // Voeg elk paar toe aan de dict
    }
    return Value(std::make_shared<Dict>(dict));  // Retourneer een Value met een gedeelde pointer naar de Dict
}
Value dict_get(Value& dictVal, const Value& key) {
    // Probeer te casten naar een Dict, als het geen Dict is, maak een nieuwe
    std::shared_ptr<Dict> dict;
    
    try {
        dict = dictVal.asDict();  // Probeer de Value als een Dict te behandelen
    } catch (const std::runtime_error&) {
        // Als de Value geen Dict is, maak dan een nieuwe Dict aan
        dict = std::make_shared<Dict>();
        dictVal = Value(dict);  // Zet de nieuwe Dict terug in de Value
    }
    
    // Zoek de sleutel in de Dict
    for (const auto& entry : dict->entries) {
        if (eq(entry.first, key).asBool()) {  // Vergelijk de sleutel
            return entry.second;  // Geef de waarde van de sleutel terug
        }
    }
    
    throw std::runtime_error("Key not found in Dict");
}
// ------------------------------------------------------------
// list_len
// ------------------------------------------------------------
inline Value list_len(const Value& listVal) {
    auto list = listVal.asList();
    return Value((int)list->items.size());
}

// ------------------------------------------------------------
// list_get (supports negative indexing)
// ------------------------------------------------------------
inline Value list_get(const Value& listVal, const Value& indexVal) {
    auto list = listVal.asList();
    int size = (int)list->items.size();
    int index = indexVal.asInt();

    if (index < 0)
        index = size + index;

    if (index < 0 || index >= size)
        throw std::runtime_error("IndexError: list index out of range");

    return list->items[index];
}

// ------------------------------------------------------------
// list_set (supports negative indexing)
// ------------------------------------------------------------
inline void list_set(Value& listVal, const Value& indexVal, const Value& value) {
    auto list = listVal.asList();
    int size = (int)list->items.size();
    int index = indexVal.asInt();

    // inline normalize_index
    if (index < 0)
        index = size + index;

    if (index < 0 || index >= size)
        throw std::runtime_error("IndexError: list assignment index out of range");

    list->items[index] = value;
}


// ------------------------------------------------------------
// list_append
// ------------------------------------------------------------
inline void list_append(Value& listVal, const Value& item) {
    auto list = listVal.asList();
    list->items.push_back(item);
}

// ------------------------------------------------------------
// list_slice (Python slicing)
// ------------------------------------------------------------
// slice arguments: start, stop, step (all optional)
inline Value list_slice(const Value& listVal, int start, int stop, int step = 1) {
    auto list = listVal.asList();
    int size = (int)list->items.size();

    if (step == 0)
        throw std::runtime_error("ValueError: slice step cannot be zero");

    // Normalize start
    if (start < 0) start += size;
    if (start < 0) start = 0;
    if (start > size) start = size;

    // Normalize stop
    if (stop < 0) stop += size;
    if (stop < 0) stop = 0;
    if (stop > size) stop = size;

    auto result = std::make_shared<List>();

    if (step > 0) {
        for (int i = start; i < stop; i += step)
            result->items.push_back(list->items[i]);
    } else {
        for (int i = start; i > stop; i += step)
            result->items.push_back(list->items[i]);
    }

    return Value(result);
}

// ------------------------------------------------------------
// make_list
// ------------------------------------------------------------
inline Value make_list(std::initializer_list<Value> items) {
    return Value(std::make_shared<List>(items));
}
// ------------------------------------------------------------
// MODULE 5 — Utility functions
// ------------------------------------------------------------

// print(...) like Python print
inline void print(const Value& v) {
    std::cout << v.str() << std::endl;
}

template<typename... Args>
inline void print(const Value& first, const Args&... rest) {
    std::cout << first.str() << " ";
    print(rest...);
}


// iterate(list) → vector<Value>
inline std::vector<Value> iterate(const Value& v) {
    return v.asList()->items;
}

// type(x) → Python type name
inline Value type(const Value& v) {
    if (v.isNull())   return Value("NoneType");
    if (v.isInt())    return Value("int");
    if (v.isDouble()) return Value("float");
    if (v.isBool())   return Value("bool");
    if (v.isString()) return Value("str");
    if (v.isList())   return Value("list");
    if (v.isTuple())  return Value("tuple");
    if (v.isDict())   return Value("dict");
    if (v.isObject()) return Value("object");
    return Value("unknown");
}
inline void dict_set(Value& dictVal, const Value& key, const Value& value) {
    std::shared_ptr<Dict> dict;

    // Probeer te casten naar Dict
    try {
        dict = dictVal.asDict();
    } catch (const std::runtime_error&) {
        // Als het geen dict is → maak een nieuwe
        dict = std::make_shared<Dict>();
        dictVal = Value(dict);
    }

    // Bestaat de key al?
    for (auto& entry : dict->entries) {
        if (eq(entry.first, key).asBool()) {
            entry.second = value;  // update
            return;
        }
    }

    // Nieuwe key toevoegen
    dict->entries.push_back(std::make_pair(key, value));
}
 std::string Value::toString() const {
        if (isNull()) return "None";
        if (isInt()) return std::to_string(asInt());
        if (isDouble()) return format_double(asDouble());
        if (isBool()) return asBool() ? "True" : "False";
        if (isString()) return asString();
        if (isObject()) return "<object>";

        if (isList()) {
            auto list = asList();
            std::string out = "[";
            for (size_t i = 0; i < list->items.size(); ++i) {
                out += list->items[i].toString();
                if (i + 1 < list->items.size()) out += ", ";
            }
            out += "]";
            return out;
        }

        if (isTuple()) {
            auto tup = asTuple();
            std::string out = "(";
            for (size_t i = 0; i < tup->items.size(); ++i) {
                out += tup->items[i].toString();
                if (i + 1 < tup->items.size()) out += ", ";
            }
            if (tup->items.size() == 1) out += ",";
            out += ")";
            return out;
        }

        if (isDict()) {
            auto dict = asDict();
            std::string out = "{";
            for (size_t i = 0; i < dict->entries.size(); ++i) {
                out += dict->entries[i].first.toString();
                out += ": ";
                out += dict->entries[i].second.toString();
                if (i + 1 < dict->entries.size()) out += ", ";
            }
            out += "}";
            return out;
        }

        return "<unknown>";
    }
inline Value tuple_get(const Value& tupleVal, const Value& indexVal) {
    auto tuple = tupleVal.asTuple();  // Ensure the Value is a Tuple
    int size = (int)tuple->items.size();  // Get the size of the tuple
    int index = indexVal.asInt();  // Get the index value

    // Normalize negative index
    if (index < 0) {
        index += size;
    }

    // Check for out-of-bounds index
    if (index < 0 || index >= size) {
        throw std::runtime_error("IndexError: tuple index out of range");
    }

    // Return the item at the specified index
    return tuple->items[index];
}
inline Value make_tuple(std::initializer_list<Value> items) {
    // Create a new Tuple object initialized with the given items
    auto tuple = std::make_shared<Tuple>(items);

    // Return a Value containing the Tuple
    return Value(tuple);
}
