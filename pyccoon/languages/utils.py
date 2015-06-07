class Section(dict):

    """ Helper class that includes some frequently used routines """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

        if not self.get('line'):
            self['line'] = 1

    def has_code(self):
        """ Check if there is some code """
        return bool(self["code_text"].strip())

    def has_docs(self):
        """ Check if there are some docs """
        return bool(self["docs_text"].strip())

    def __missing__(self, key):
        """ Emulate `collections.defaultdict` behavior """
        return ''

    def copy(self):
        return Section(**dict((k, v) for (k, v) in self.items()))


# ## Parsing strategy


class ParsingStrategy(list):

    """ Helper class that handles a list of methods and allows to insert item before or after \
        some specific item. """

    def __init__(self, *args):
        """ Initialize from an arbitrary sequence of arguments """
        for arg in args:
            self.append(arg)

    def index(self, name):
        """ Return the index of a method which name is `name` or raise an exception. """
        index = next((i for i, x in enumerate(self) if x.__name__ == name), None)
        if not index:
            raise Exception("Step '{0}' not found in the strategy: {1}".format(name, self))

        return index

    def insert_before(self, key, method):
        """ Insert a `method` before an item with a name `key` """
        self.insert(self.index(key), method)

    def insert_after(self, key, method):
        """ Insert a `method` after an item with a name `key` """
        self.insert(self.index(key) + 1, method)

    def delete(self, key):
        """ Remove the item with a name `key` """
        self.pop(self.index(key))


def iterate_sections(start=1, increment=1):
    """
    Helper decorator to iterate through the `sections` while altering them.

    :param start: Section index to start with.
    :param increment: Index increment. Use `-1` to iterate backwards.
    """
    def wrap(f):
        def wrapped_f(self, sections):
            i = start
            while i < len(sections) and i > -1:
                new_i = f(self, sections, i)
                i = new_i if new_i else i + increment

            return sections

        wrapped_f.__name__ = f.__name__
        return wrapped_f

    return wrap


def split_section_by_regex(section, regex, meta=None):
    """ Helper method that splits a section into parts using the `regex` matching against\
        the section code """
    if not section.has_code():
        return [section]

    sections = []
    start = 0
    for match in regex.finditer(section["code_text"]):
        code = section["code_text"][start:match.start()]
        if code.strip():
            sections.append(Section(code_text=code))
        sections.append(Section(docs_text=match.group(1), meta=meta))
        start = match.end()

    remains = section["code_text"][start:].strip('\n')
    if remains.strip():
        sections.append(Section(code_text=remains))

    return sections


def split_code_by_pos(i, pos, sections):
    code = sections[i]["code_text"]
    section_1 = sections[i].copy()
    section_1['code_text'] = code[:pos]
    section_2 = sections[i].copy()
    section_2['docs_text'] = ""
    section_2['code_text'] = code[pos:]

    sections[i:i+1] = [section_1, section_2]
    return sections
