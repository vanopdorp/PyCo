#include <iostream>
#include "library/value.hpp"
#include "library/range.hpp"
#include "library/booleans.hpp"
int main() {
    Value s = Value("Gur Mra bs Clguba, ol Gvz Crgref\n\nOrnhgvshy vf orggre guna htyl.\nRkcyvpvg vf orggre guna vzcyvpvg.\nFvzcyr vf orggre guna pbzcyrk.\nPbzcyrk vf orggre guna pbzcyvpngrq.\nSyng vf orggre guna arfgrq.\nFcnefr vf orggre guna qrafr.\nErnqnovyvgl pbhagf.\nFcrpvny pnfrf nera'g fcrpvny rabhtu gb oernx gur ehyrf.\nNygubhtu cenpgvpnyvgl orngf chevgl.\nReebef fubhyq arire cnff fvyragyl.\nHayrff rkcyvpvgyl fvyraprq.\nVa gur snpr bs nzovthvgl, ershfr gur grzcgngvba gb thrff.\nGurer fubhyq or bar-- naq cersrenoyl bayl bar --boivbhf jnl gb qb vg.\nNygubhtu gung jnl znl abg or boivbhf ng svefg hayrff lbh'er Qhgpu.\nAbj vf orggre guna arire.\nNygubhtu arire vf bsgra orggre guna *evtug* abj.\nVs gur vzcyrzragngvba vf uneq gb rkcynva, vg'f n onq vqrn.\nVs gur vzcyrzragngvba vf rnfl gb rkcynva, vg znl or n tbbq vqrn.\nAnzrfcnprf ner bar ubaxvat terng vqrn -- yrg'f qb zber bs gubfr!");
    Value d = Value(make_dict({}));
    for (Value c : iterate(Value(make_tuple({Value(65), Value(97)})))) {
    for (Value i : range(Value(0), Value(26), Value(1))) {
    dict_set(d, chr(add_builtin_func(i, c)), chr(add_builtin_func(mod_builtin_func(add_builtin_func(i, Value(13)), Value(26)), c)));
}
}   
    print("iteration succesfully");
    Value _tmp0 = Value(make_list({}));
    print(type(s));
    for (Value c : iterate(s)) {
        list_append(_tmp0, dict_get(d, c, c));
    }
    print(_tmp0);
    print(type(_tmp0));
    print(join_builtin_func(Value(""),_tmp0));
    return 0;
}