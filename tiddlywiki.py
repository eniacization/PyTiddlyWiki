import re

from tiddler import Tiddler


class TiddlyWiki:

    RE_TITLE = re.compile('<title>(?P<title>[\w\W]*?) — '
                          '(?P<subtitle>[\w\W]*?)</title>')

    def __init__(self, title=None, subtitle=None, tiddlers=None):
        self.title = title
        self.subtitle = subtitle
        self.tiddlers = []
        if tiddlers is not None:
            self.add_tiddlers(tiddlers)

    def add_tiddler(self, tiddler):
        if tiddler not in self.tiddlers:
            self.tiddlers.append(tiddler)
            return True

        return False

    def add_tiddlers(self, it):
        for tiddler in it:
            self.add_tiddler(tiddler)

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

    def __contains__(self, tiddler):
        assert isinstance(tiddler, Tiddler)
        return tiddler in self.tiddlers

    @classmethod
    def parse_title(cls, buffer):
        match = re.search(cls.RE_TITLE, buffer)

        if match is not None:
            return match.group('title'), match.group('subtitle')
        return None, None

    @classmethod
    def parse_from_string(cls, buffer):
        """A TiddlyWiki factory
        Returns a TiddlyWiki instance containing all tiddlers found in string buffer
        """
        title, subtitle = cls.parse_title(buffer)
        tiddly_wiki = cls(title=title, subtitle=subtitle)

        for tiddler in Tiddler.finditer(buffer):
            tiddly_wiki.add_tiddler(tiddler)

        return tiddly_wiki

    @classmethod
    def parse_from_html(cls, html_file):
        """A TiddlyWiki factory
        Returns a TiddlyWiki instance containing all tiddlers found in html_file
        """
        with open(html_file, 'r') as html:
            buffer = html.read()

        return cls.parse_from_string(buffer)

    # TODO: implement
    @classmethod
    def open_in_browser(cls, tiddler_iterable):
        pass

    def apply(self, algorithm):
        return algorithm.evaluate(self)


if __name__ == "__main__":

    from algorithm import ExportToFile
    import time

    t0 = time.time()

    tw5 = TiddlyWiki.parse_from_html('./example/tw5.html')

    print(tw5.title)
    print(tw5.subtitle)

    for tiddler in tw5:
        print(tiddler.title)

    tw5.apply(ExportToFile('./tw5.pdf', '--toc'))

    print(str(time.time() - t0))
