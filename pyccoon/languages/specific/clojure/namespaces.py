import os

crossclj_template = \
  "https://crossclj.info/{link_type}/{package}/" + \
  "{version}/{namespace}{suffix}.html#_{name}"

local_template = \
  "{path}.{ext}.html#_{name}"


def target_on_crossclj(root, source, namespace, params, name):
    if isinstance(params, str):
        package = params
        link_type = 'doc'
        version = 'latest'
        suffix = ''
    else:
        package = params.get('package')
        if not package:
            return None
        link_type = (params.get('source') and 'ns') or 'doc'
        version = params.get('version', 'latest')
        suffix = (params.get('is-cljs') and '.cljs') or ''
    
    return crossclj_template.format(link_type=link_type,
                                    package=package,
                                    version=version,
                                    namespace=namespace,
                                    name=name,
                                    suffix=suffix)


def local_target(root, source, namespace, params, name):
    path = params.get('path', None)
    if path is None:
        return None
    
    namespace_ = "/".join(namespace.split('.')[1:])

    abs_target_path = os.path.join(root, path, namespace_)
    abs_source_path = os.path.join(root, os.path.dirname(source))
    
    rel_path = os.path.relpath(abs_target_path, abs_source_path)
    ext = params.get('extension', 'clj')

    return local_template.format(path=rel_path,
                                 ext=ext,
                                 name=name)
    
target_methods = {
    'crossclj': target_on_crossclj,
    'local': local_target
}


def get_by_prefix(d, namespace):
    matches = [(ns, info) for ns, info in d.iteritems()
                          if namespace.startswith(ns + '.') or ns == namespace]
    if matches:
        best_ns, best_info = max(matches, key=lambda item: len(item[0]))
        return best_info
    else:
        return None


def target(root, source, namespaces, namespace, name):
    info = get_by_prefix(namespaces, namespace)
    if info:
        if isinstance(info, str):
            return target_on_crossclj(root, source, namespace, info, name)
        else:
            method = info.get('method')
            if method in target_methods:
                return target_methods[method](root, source, namespace, info, name)
            else:
                return target_on_crossclj(root, source, namespace, info, name)
    else:
        return None
