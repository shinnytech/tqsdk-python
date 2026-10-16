"""Check files and fragments in a Sphinx HTML build without network access.

Usage: python doc/check_links.py build/doc
Run after the strict Sphinx build, which checks symbolic cross references.
"""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.anchors = set()
        self.links = []
        self.feed(path.read_text(encoding='utf-8'))
        self.close()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get('id'):
            self.anchors.add(attrs['id'])
        if tag == 'a':
            if attrs.get('name'):
                self.anchors.add(attrs['name'])
            if attrs.get('href'):
                self.links.append((self.getpos()[0], attrs['href']))


def check_links(directory):
    root = Path(directory).resolve()
    pages = {path.resolve(): Page(path) for path in sorted(root.rglob('*.html'))}
    if not pages or not (root / 'index.html').is_file():
        return 0, 0, ['No Sphinx HTML site found: ' + str(root)]
    errors = []
    checked = 0
    for source, page in pages.items():
        for line, href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            path = unquote(url.path)
            target = ((root / path.lstrip('/')) if path.startswith('/')
                      else (source.parent / path) if path else source).resolve()
            checked += 1
            prefix = f'{source.relative_to(root)}:{line}: {href}'
            if not target.is_relative_to(root):
                errors.append(prefix + ' (outside build directory)')
                continue
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                errors.append(prefix + ' (missing file)')
                continue
            fragment = unquote(url.fragment)
            if fragment and target.suffix == '.html':
                if target not in pages:
                    errors.append(prefix + ' (HTML target not scanned)')
                elif fragment not in pages[target].anchors:
                    errors.append(prefix + ' (missing fragment)')
    return len(pages), checked, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Sphinx HTML output directory')
    args = parser.parse_args()
    pages, links, errors = check_links(args.directory)
    for error in errors:
        print(error)
    print(f'{pages} HTML pages, {links} local links, {len(errors)} errors')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
