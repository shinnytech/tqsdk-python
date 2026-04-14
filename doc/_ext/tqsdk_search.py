# -*- coding: utf-8 -*-

import re

from sphinx.search.zh import SearchChinese


class TqSdkSearchChinese(SearchChinese):
    """Index both jieba tokens and whole text fragments for Chinese docs search."""

    lang = 'tqsdk_zh'
    # Reuse Sphinx's built-in English stemmer implementation for Latin tokens.
    # `js_stemmer_rawcode = 'english-stemmer.js'` expects `EnglishStemmer`.
    language_name = 'English'
    _phrase_re = re.compile(r'\w+', re.UNICODE)

    def split(self, input: str) -> list[str]:
        tokens = []
        tokens.extend(super().split(input))
        tokens.extend(self._phrase_re.findall(input))

        seen = set()
        results = []
        for token in tokens:
            token = token.strip()
            if not token or token in seen:
                continue
            seen.add(token)
            results.append(token)
        return results
