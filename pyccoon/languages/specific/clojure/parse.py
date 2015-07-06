import sexpdata
from sexpdata import Symbol, Bracket, car, cdr

from picoparse import compose, satisfies, partial, \
    run_parser, seq, optional, many, many1, choice, \
    any_token, fail

# I already use regexps for the source anchors,
# so I better use them again.
import re
    

def normalize(sexp):
    if isinstance(sexp, Bracket):
        return normalize(sexp._val)
    elif isinstance(sexp, list):
        return map(normalize, sexp)
    else:
        return sexp


def sexpdumps(sexp):
    return sexpdata.dumps(sexp).replace(r'\.', '.')


def sexploads(sexp, norm=True):
    if norm:
        return normalize(sexpdata.loads(sexp))
    else:
        return sexpdata.loads(sexp)


def merge_dicts(dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def optional_combinations(parts):
    return itertools.product(*zip([[]] *len(parts), parts))


p = partial


def is_symbol(sexp):
    return isinstance(sexp, Symbol)


def is_keyword(sexp):
    return is_symbol(sexp) and sexp.value().startswith(':')


def sym(name):
    return p(satisfies,
             lambda sexp: is_symbol(sexp) and sexp.value() == name)

def kw(name):
    return sym(':' + name)


def is_list_of_symbols(sexp):
    return isinstance(sexp, list) and all(is_symbol(s) for s in sexp)


def names(symbs):
    return [symb.value() for symb in symbs]


def unpack(parser):
    token = satisfies(lambda x: isinstance(x, list))
    try:
        head, tail = run_parser(parser, token)
        return head
    except:
        fail()

symbol = p(satisfies, is_symbol)
keyword = p(satisfies, is_keyword)
list_of_symbols = p(satisfies, is_list_of_symbols)


def require_refer():
    
    def all_kw():
        kw('all')()
        return []
    
    kw('refer')()
    symbs = choice(all_kw, list_of_symbols)
    return names(symbs)


def require_alias():
    kw('as')()
    symb = symbol()
    return symb.value()


def require_flags():
    flag_kws = many(keyword)
    return names(flag_kws)


def require_directive():
    namespace = symbol().value()
    alias = optional(require_alias, None)
    refer_list = optional(require_refer, [])
    flags = optional(require_flags, [])
    
    if alias:
        alias_dict = {alias: namespace}
    else:
        alias_dict = dict()
    
    return {name: namespace for name in refer_list}, alias_dict


def require_single():
    require_dict = require_directive()
    return {}, {}


def require_multi():
    directives = many1(p(unpack, require_directive))
    refer_maps, alias_maps = zip(*directives)
    return merge_dicts(refer_maps), merge_dicts(alias_maps)


def require():
    kw('require')()
    refer_map, alias_map = choice(require_multi, require_single)
    return refer_map, alias_map


def require_macros():
    kw('require-macros')()
    refer_map, alias_map = choice(require_multi, require_single)
    return refer_map, alias_map

def only(namespace):
    kw('only')()
    symbs = list_of_symbols()
    return {name: namespace for name in names(symbs)}, {}


def exclude():
    kw('exclude')()
    symbs = list_of_symbols()
    return {}, {}


def all_():
    kw('all')()
    return {}, {}


def refer():
    kw('refer')()
    namespace = symbol().value()
    result = optional(p(choice, p(only, namespace), exclude, all_), ({}, {}))
    return refer_directive()


def refer_clojure():
    kw('refer-clojure')()
    result = optional(p(choice, p(only, 'clojure.core'), exclude, all_), ({}, {}))
    return result


def unrecognized_ns_directive():
    many(any_token)
    return {}, {}


def ns_directive():
    refer_map, alias_map = choice(require,
                                  require_macros,
                                  refer,
                                  refer_clojure,
                                  unrecognized_ns_directive)
    return refer_map, alias_map


def ns():
    sym('ns')()
    namespace = symbol().value()
    directives = many(p(unpack, ns_directive))
    many(any_token)
    refer_maps, alias_maps = zip(*directives)
    return merge_dicts(refer_maps), merge_dicts(alias_maps)


def extract_ns_info(s):
    s_ = '(' + s + ')'
    sexp = sexploads(s_)
    namespace, rest = run_parser(ns, sexp[0])
    return namespace

def split_full_name(full_name):
    try:
        ns, name = full_name.split('/', 1)
        assert ns and name
        return ns, name
    except:
        return None, full_name

# ## Local definitions

def get_local_defs(keyword_link_patterns, text):
    local_defs = []
    for pattern, formatter in keyword_link_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        names = [match.group('name') for match in matches]
        local_defs.extend(names)
    return local_defs
