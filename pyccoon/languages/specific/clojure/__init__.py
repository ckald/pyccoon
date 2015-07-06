import xml.etree.ElementTree as etree
import yaml
import os

with open(os.path.join(os.path.dirname(__file__), 'data/namespaces.yaml')) as f:
    DEFAULT_NAMESPACES = yaml.safe_load(f.read())

from parse import extract_ns_info, split_full_name, get_local_defs
from namespaces import target


def hyperlink_source(root, source, anchor_prefix, namespaces,
                     default_namespaces, local_defs,
                     alias_map, refer_map, highlighted_source):
    try:
        tree = etree.fromstring(highlighted_source)
        for span in tree.iter('span'):
            # Pygments renders the tokens we are interested in inside
            # <span> tags, so we are only interested in their content.
            if span.text:
                full_name = span.text.strip()
                namespace_, name = split_full_name(full_name)
                if namespace_:
                    namespace = alias_map.get(namespace_) or namespace_
                else:
                    namespace = refer_map.get(name)

                if namespace:
                    href = target(root, source, namespaces, namespace, name)
                    if href is None:
                        href = target(root, source, default_namespaces, namespace, name)
                elif name in local_defs:
                    href = '#{anchor_prefix}{name}'.format(anchor_prefix=anchor_prefix,
                                                           name=name)
                else:
                    href = None

                if href:
                    a = etree.Element('a')
                    a.set('href', href)
                    a.set('class', 'hidden')
                    a.text = span.text
                    # We are changing the tree as we traverse it, by adding <a> elements.
                    # This is not a problem because we only visit <span> elements.
                    span.text = ''
                    span.append(a)
            
        return etree.tostring(tree)
    
    except:
        return highlighted_source


class LinkSourceData(object):
    namespaces = dict()
    default_namespaces = DEFAULT_NAMESPACES
    local_defs = []
    alias_map = {}
    refer_map = {}


def link_source_post(self, sections):
    for i, section in enumerate(sections):
        sections[i]['code_html'] = \
            hyperlink_source(self.root,
                             self.source,
                             self.anchor_prefix,
                             self.link_source.namespaces,
                             self.link_source.default_namespaces,
                             self.link_source.local_defs,
                             self.link_source.alias_map,
                             self.link_source.refer_map,
                             sections[i]['code_html'])


def link_source_pre(self, sections):
    code_text = "\n".join([section['code_text'] for section in sections])
    try:
        refer_map, alias_map = extract_ns_info(code_text)
        self.link_source.namespaces =  self.parent.config.get('language-specific')\
                                                         .get('clojure')\
                                                         .get('namespaces')
        self.link_source.alias_map = alias_map
        self.link_source.refer_map = refer_map
        self.link_source.local_defs = get_local_defs(self.keyword_link_patterns,
                                                     code_text)
    except:
        self.link_source.namespaces = dict()
        self.link_source.alias_map = dict()
        self.link_source.refer_map = dict()
        self.link_source.local_defs = dict()
