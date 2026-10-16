"""Resolve implementation names emitted by Python's type annotations."""

from sphinx.ext.intersphinx import missing_reference


# CPython exposes these classes under implementation modules in signatures;
# the Python inventory documents them under their public import paths.
TYPE_ALIASES = {
    '_asyncio.Task': 'asyncio.Task',
    'asyncio.events.AbstractEventLoop': 'asyncio.AbstractEventLoop',
    'asyncio.streams.StreamWriter': 'asyncio.StreamWriter',
}


def resolve_type_alias(app, env, node, contnode):
    if node.get('refdomain') != 'py':
        return None
    # Forward annotations are emitted as class references, even for this
    # documented union alias. Resolve it as data without altering SDK types.
    if node.get('reftarget') in {'UnionTradeable', 'tqsdk.api.UnionTradeable'}:
        return env.domains['py'].resolve_xref(
            env, node['refdoc'], app.builder, 'data',
            'tqsdk.api.UnionTradeable', node, contnode,
        )
    target = TYPE_ALIASES.get(node.get('reftarget'))
    if target is None:
        return None
    reference = node.copy()
    reference['reftarget'] = target
    return missing_reference(app, env, reference, contnode)


def setup(app):
    app.connect('missing-reference', resolve_type_alias)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
