import re

from datetime import datetime


class Tw5Mixin:

    # TODO: improve readibility of this function
    @staticmethod
    def convert_tw5_to_md(text):
        """convert a tw5-flavored md text to a github-flavored md"""
        assert isinstance(text, str)

        def convert_list_symbols(match):
            match_string = match.group('list_symbols')
            # remove all spaces, tabs, etc.
            match_string = ''.join(match_string.split())
            # add indentation
            result = '  ' * (len(match_string) - 1)
            # add bullet or number
            if match_string[-1] == '*':
                result += '* ' # the ending space is important
            elif match_string[-1] == '#':
                result += '1. ' # the ending space is important
            return result

        def convert_heading(match):
            match_string = match.group('heading')
            # remove all spaces, tabs, etc.
            match_string = ''.join(match_string.split())
            return '#' * len(match_string) + ' '

        links = []
        def remove_links(text):
            def append_link(match):
                index = len(links)
                if match.group('link2') is None:
                    links.append(match.group('link1'))
                    return '[[{}|{}]]'.format(match.group('name'), index)
                else:
                    links.append(match.group('link2'))
                    return '[[{}]]'.format(index)

            text = re.sub('\[\[(?P<name>[\w\W]+?)\|(?P<link1>[\w\W]+?)\]\]|\[\[(?P<link2>[^\|]+?)\]\]',
                          append_link,
                          text)
            return text

        katex = []
        def remove_katex(text):
            def append_katex(match):
                index = len(katex)
                katex.append(match.group('katex'))
                return '$${}$$'.format(index)

            text = re.sub('\$\$(?P<katex>[\w\W]*?)\$\$',
                          append_katex,
                          text)
            return text

        def restore_links(text):
            def get_link(match):
                if match.group('index2') is None:
                    index = int(match.group('index1'))
                    return '[[{}|{}]]'.format(match.group('name'), links[index])
                else:
                    index = int(match.group('index2'))
                    return '[[{}]]'.format(links[index])

            text = re.sub('\[\[(?P<name>[\w\W]+?)\|(?P<index1>\d+?)\]\]|'
                          '\[\[(?P<index2>\d+?)\]\]',
                          get_link,
                          text)
            return text

        def restore_katex(text):
            def get_katex(match):
                index = int(match.group('index'))
                return '$${}$$'.format(katex[index])

            text = re.sub('\$\$(?P<index>\d*?)\$\$',
                          get_katex,
                          text)
            return text

        text = remove_katex(text)
        text = remove_links(text)

        # TODO: linked images on the web are not included correctly in pdf
        # convert images
        text = re.sub('\[[\s]*img(?P<options>[\w\W]*?)\[(?P<link>[\w\W]+?)\]\]',
                      '\![\g<options>](\g<link>)',
                      text)

        # convert list-symbols * and #
        text = re.sub('^(?P<list_symbols>[\t ]*[*#]+[*#\t ]*)',
                      convert_list_symbols,
                      text,
                      flags=re.MULTILINE)

        # convert headings, i.e. change ! caption to # caption
        text = re.sub('^(?P<heading>[\t ]*[!]+[!\t ]*)',
                      convert_heading,
                      text,
                      flags=re.MULTILINE)

        # TODO: do not convert '' in urls and katex code
        # convert ''bold'' to __bold__
        text = re.sub('\'\'(?P<phrase>[\w\W]+?)\'\'',
                      '__\g<phrase>__',
                      text)

        # TODO: do not convert slashes in urls and katex code
        # convert //italic// to _italic_
        text = re.sub('//(?P<phrase>[\w\W]+?)//',
                      '_\g<phrase>_',
                      text)

        # convert &lt; to <
        text = re.sub('&lt;', '<', text)

        # convert &gt; to >
        text = re.sub('&gt;', '>', text)

        # convert &amp; to &
        text = re.sub('&amp;', '&', text)

        # remove single ~ in front of words
        text = re.sub('(?<!~)~(?!~)', '', text, flags=re.MULTILINE)

        # convert block quote
        matches = list(re.finditer('^<<<[\t ]*(?P<quote>[\w\W]*?)<<<(?P<ref>[\w\W]*?)(?=\n)',
                                   text, flags=re.MULTILINE))
        while matches:
            match = matches.pop()
            quote = match.group('quote')
            quote = re.sub('\n', '\n> ', quote)
            quote = '> ' + quote
            ref = match.group('ref').strip()
            if ref:
                quote += '({})'.format(ref)

            text = text[:match.start()] + quote + text[match.end():]

        # TODO: convert tables
        # TODO: convert definitions
        # TODO: how to handle transclusions (in tiddlywiki.TiddlyWiki?)
        # TODO: how to handel links to other tiddlers?

        text = restore_katex(text)

        # convert $$ to $
        # TODO: drawback: inline formulas of the form 'some text $$ a^2 $$ some text' are not matched
        # TODO: two consecutive centered formula may lead to string '$$$$', which should not be converted
        text = re.sub('((?<!\n)\$\$|\$\$(?!\n|$))',
                      '$',
                      text)

        text = restore_links(text)

        # convert links without reference
        text = re.sub('\[\[(?P<link>[^\|]+?)\]\]',
                      '[\g<link>](\g<link>)',
                      text)

        # convert links with reference
        text = re.sub('\[\[(?P<name>[\w\W]+?)\|(?P<link>[\w\W]+?)\]\]',
                      '[\g<name>](\g<link>)',
                      text)

        return text

    @staticmethod
    def get_tag_list(tag_string):
        '''gets a string with tags, each tag is separated by a space.
        if a tag contains a space itself, it is enclosed by double square brackets,
        e.g. '[[tag with spaces]]'.
        returns a list of tags.
        '''
        assert isinstance(tag_string, str)

        RE_LINK = re.compile('\[\[(?P<link>.*?)\]\]')

        result = []
        m = re.search(RE_LINK, tag_string)
        while m:
            result.append(m.group('link'))
            s = m.start()
            e = m.end()
            tag_string = tag_string[:s] + tag_string[e:]
            m = re.search(RE_LINK, tag_string)

        result += tag_string.split()

        return result

    @staticmethod
    def string_to_date(date_string):
        '''gets a string of digits, e.g. '20180101201500'.
        the first 14 digits are being interpreted as year+month+day+hour+minute+sec
        returns a datetime object.
        '''
        return datetime.strptime(date_string[:14], '%Y%m%d%H%M%S')