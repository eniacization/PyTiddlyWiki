import re

from datetime import datetime


class Tw5Mixin:

    @staticmethod
    def convert_tw5_to_md(text, latex_gif=False):
        """convert a tw5-flavored md text to a github-flavored md"""
        assert isinstance(text, str)

        def convert_list_symbols(match):
            match_string = match.group('list_symbols')

            # remove all spaces, tabs, etc.
            match_string = ''.join(match_string.split())

            # add indentation
            result = '  ' * (len(match_string) - 1)

            # add bullet or number
            if len(match_string) == 0:
                result = ''
            elif match_string[-1] == '*':
                result += '* ' # the ending space is important
            elif match_string[-1] == '#':
                result += '1. ' # the ending space is important

            return result

        def convert_heading(match):
            match_string = match.group('heading')

            # remove all spaces, tabs, etc.
            match_string = ''.join(match_string.split())

            return '#' * len(match_string) + ' '

        # convert links without reference
        text = re.sub('\[\[(?P<name>[.^\|]+?)\]\]',
                      '[\g<name>]',
                      text)

        # convert links with reference
        text = re.sub('\[\[(?P<name>[\w\W]+?)\|(?P<link>[\w\W]+?)\]\]',
                      '[\g<name>](\g<link>)',
                      text)

        # TODO: images are not converted to pdf correctly
        # convert images
        text = re.sub('\[[\s]*img(?P<options>[\w\W]*?)\[(?P<link>[\w\W]+?)\]\]',
                      '\![\g<options>](\g<link>)',
                      text)

        # convert list-symbols * and #
        text = re.sub('^(?P<list_symbols>[*#\t ]+)',
                      convert_list_symbols,
                      text,
                      flags=re.MULTILINE)

        # convert headings, i.e. change ! caption to # caption
        text = re.sub('^(?P<heading>[!\t ]+)',
                      convert_heading,
                      text,
                      flags=re.MULTILINE)

        # convert ''bold'' to **bold**
        text = re.sub('\'\'(?P<phrase>[\w\W]+?)\'\'',
                      '**\g<phrase>**',
                      text)

        # TODO: do not convert slashes in urls
        # convert //italic// to *italic*
        text = re.sub('//(?P<phrase>[\w\W]+?)//',
                      '*\g<phrase>*',
                      text)

        # convert &lt; to <
        text = re.sub(r'&lt;', r'<', text)

        # convert &gt; to >
        text = re.sub(r'&gt;', r'>', text)

        # remove single ~ in front of words
        text = re.sub('(?<=\s)~(?!~)', '', text)

        # convert block quote
        matches = list(re.finditer('^<<<(?P<quote>[\w\W]*?)<<<(?P<ref>[\w\W]*?)(?=\n)', text, flags=re.MULTILINE))
        while matches:
            match = matches.pop()
            quote = match.group('quote')
            quote = re.sub('\n', '\n> ', quote)
            text = text[:match.start()] + quote + match.group('ref') + text[match.end():]

        if latex_gif:
            # replace latex by gif image with codecogs.com
            text = re.sub('\$\$(?P<math>.+?)\$\$',
                          '![\g<math>](https://latex.codecogs.com/gif.latex?\g<math>)',
                          text)
        else:
            # convert $$ to $
            # TODO: drawback: inline formulas of the form 'some text $$ a^2 $$ some text' are not matched
            # TODO: two consecutive centered formula may lead to string '$$$$', which should not be converted
            text = re.sub('((?<!\n)\$\$|\$\$(?!\n))',
                          '$',
                          text)

        # TODO: convert tables

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
        '''gets a string of digits, e.g. 20180101201500.
        the first 14 digits are being interpreted as year+month+day+hour+minute+sec
        returns a datetime object.
        '''
        return datetime.strptime(date_string[:14], '%Y%m%d%H%M%S')