#pragma once
#include "value.hpp"

class RangeIterator {
public:
    RangeIterator(int current, int step, int end_value)
        : current(current), step(step), end_value(end_value) {}

    Value operator*() const {
        return Value(current);
    }

    RangeIterator& operator++() {
        current += step;
        return *this;
    }

    bool operator!=(const RangeIterator& other) const {
        return current < other.end_value;
    }

private:
    int current;
    int step;
    int end_value;
};

class Range {
public:
    Range(Value end)
        : start_value(0), end_value(end.asInt()), step_value(1) {}

    Range(Value start, Value end, Value step = Value(1))
        : start_value(start.asInt()), end_value(end.asInt()), step_value(step.asInt()) {}

    RangeIterator begin() const {
        return RangeIterator(start_value, step_value, end_value);
    }

    RangeIterator end() const {
        return RangeIterator(end_value, step_value, end_value);
    }

private:
    int start_value;
    int end_value;
    int step_value;
};

// Convenience wrappers
inline Range range(Value end) {
    return Range(end);
}

inline Range range(Value start, Value end, Value step = Value(1)) {
    return Range(start, end, step);
}
