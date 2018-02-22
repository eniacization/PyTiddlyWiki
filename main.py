#TODO: write a converter: tw5-markdown to github-markdown.
#TODO: add latex to github-markdown with external gifs
#TODO: write argparse interface
#TODO: better time format for created and modified

import abc
import random
import re

import pypandoc

RE_LINK = re.compile('\[\[(?P<link>.*?)\]\]')

# is the order always the same? some parameters (e.g. color, type) are optional
# TODO: better read in option string first, and then find keywords in this string
RE_TIDDLER = re.compile('<div '
                        '(color=\"(?P<color>\w+?)\" |)'
                        '[\w\W]*?'
                        'created=\"(?P<created>\d+)\" '
                        'modified=\"(?P<modified>\d+)\" '
                        'tags=\"(?P<tags>[^\n]*?)\" '
                        'title=\"(?P<title>[^\n]*?)\" '
                        'tmap.id=\"[^\n]*?\"'
                        '[\w\W]*?'
                        '(type=\"(?P<type>\w+?)\"|)'
                        '[\w\W]*?'
                        '>\n'
                        '<pre>'
                        '(?P<content>[\w\W]*?)</pre>\n'
                        '</div>')


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


    # TODO: convert links without alias first

    # convert links
    text = re.sub('\[\[(?P<name>[\w\W]+?)\|(?P<link>[\w\W]+?)\]\]',
                  '[\g<name>](\g<link>)',
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

    # change ''bold'' to **bold**
    text = re.sub('\'\'(?P<phrase>[\w\W]+?)\'\'',
                  '**\g<phrase>**',
                  text)

    # change //italic// to *italic*
    text = re.sub('//(?P<phrase>[\w\W]+?)//',
                  '*\g<phrase>*',
                  text)

    return text


class Tiddler:

    #TODO: tags should be None or a list of tags
    def __init__(self, title, content, tags=None, created=None, modified=None):
        self.title = title
        self.content = content
        self.tag_list = [] if tags is None else type(self).get_tag_list(tags)
        self.created = created
        self.modified = modified
        self.links = self.find_links()

    @classmethod
    def parse_from_html(cls, html_file, title):
        """A Tiddler factory
        If html_file contains a tiddler with name title, a Tiddler instance of this tiddler is returned.
        If html_file does not contain a tiddler with name title, None is returned.

        """
        with open(html_file) as html:
            buffer = html.read()

        for match in re.finditer(RE_TIDDLER, buffer):
            if match.group('title') == title:
                content = match.group('content')
                tags = match.group('tags')
                created = match.group('created')
                modified = match.group('modified')

                return cls(title, content, tags=tags, created=created, modfied=modified)

        return None

    @staticmethod
    def get_tag_list(tags):
        assert isinstance(tags, str)
        result = []
        m = re.search(RE_LINK, tags)
        while m:
            result.append(m.group('link'))
            s = m.start()
            e = m.end()
            tags = tags[:s] + tags[e:]
            m = re.search(RE_LINK, tags)

        result += tags.split()

        return result


    def find_links(self):
        result = []
        for m in re.finditer(RE_LINK, self.content):
            link = m.group('link')
            if '|' in link:
                link = link.split('|')[1]
            result.append(link)

        return result

    def __str__(self):
        result = (self.title + '\n' +
                  '\ttags: ' + str(self.tag_list) + '\n' +
                  '\tcreated: ' + self.created + ', '
                  '\tmodified: ' + self.modified + '\n'
                  '\t' + self.content[:10] + '...' + self.content[-10:])

        return result

    def export_content(self, format=None):
        if format is None:
            format = 'md'
        # TODO: check type
        content = convert_tw5_to_md(self.content)
        return pypandoc.convert_text(content, 'md', format=format)

    def export(self):
        result = '# ' + self.title + '\n\n'
        result += self.export_content()
        return result


class TiddlyWiki:

    def __init__(self):
        self.tiddlers = []

    def add_tiddler(self, tiddler):
        if tiddler in self.tiddlers:
            return False

        self.tiddlers.append(tiddler)
        return True

    def remove_tiddler(self, tiddler):
        if tiddler in self.tiddlers:
            self.tiddlers.remove(tiddler)
            return True

        return False

    def __iter__(self):
        return (tiddler for tiddler in self.tiddlers)

    def __len__(self):
        return len(self.tiddlers)

    def __getitem__(self, item):
        return self.tiddlers[item]

    def __contains__(self, item):
        assert isinstance(item, Tiddler)
        return item in self.tiddlers

    @classmethod
    def parse_from_html(cls, html_file):
        """A TiddlyWiki factory
        Returns a TiddlyWiki instance containing all tiddlers found in html_file

        """
        with open(html_file) as html:
            buffer = html.read()

        tiddly_wiki = cls()

        for match in re.finditer(RE_TIDDLER, buffer):
            title = match.group('title')
            content = match.group('content')
            tags = match.group('tags')
            created = match.group('created')
            modified = match.group('modified')

            tiddler = Tiddler(title, content, tags=tags, created=created, modified=modified)
            tiddly_wiki.add_tiddler(tiddler)

        return tiddly_wiki

    # TODO: instead of tiddly_wiki.apply_Algorithm(get_random_tiddler), i want to be able to use get_random_tiddler(tiddly_wiki)
    def apply_algorithm(self, algorithm):
        return algorithm.evaluate(self)


class Algorithm(abc.ABC):

    @abc.abstractmethod
    def evaluate(self, tiddl_wiki):
        pass


class GetRandomTiddler(Algorithm):

    def __init__(self, *filter):
        self.filter = filter

    def evaluate(self, tiddl_wiki):
        if self.filter is None:
            available = tiddl_wiki.tiddlers
        else:
            available = tiddl_wiki.apply_algorithm(FindAllTiddlers(*self.filter))

        return random.choice(available)


class FindTiddler(Algorithm):

    def __init__(self, *predicates):
        self.predicates = predicates

    def evaluate(self, tiddly_wiki):
        for tiddler in tiddly_wiki:
            if all(p(tiddler) for p in self.predicates):
                return tiddler

        return None


class FindAllTiddlers(Algorithm):

    def __init__(self, *predicates):
        self.predicates = predicates

    def evaluate(self, tiddly_wiki):
        result = []
        for tiddler in tiddly_wiki:
            if all(p(tiddler) for p in self.predicates):
                result.append(tiddler)

        return result


if __name__ == "__main__":

    tw5 = TiddlyWiki.parse_from_html('/Users/admin/Documents/TiddlyWiki/notebook.html')

    def exclude_tags(tiddler):
        exclusion = ['journal', 'music', 'proceedings', 'movies', 'photography', 'literature']
        return all(tag not in tiddler.tag_list for tag in exclusion)

    def include_tags(tiddler):
        inclusion = ['notes', 'PhD', 'question', 'physics', 'mathematics', 'interesting things', 'computer']
        return any(tag in tiddler.tag_list for tag in inclusion)

    predicates = [exclude_tags,
                  include_tags,
                  lambda tiddler: not tiddler.title.endswith('Manuel')]

    t = tw5.apply_algorithm(GetRandomTiddler(*predicates))
    print(t.export())

    liste = tw5.apply_algorithm(FindAllTiddlers(*predicates))
    print(len(liste))
