# TODO: implement export_tiddler in TiddlyWiki, in order to handle transclusions

from Tiddler import Tiddler


class TiddlyWiki:

    def __init__(self):
        self.tiddlers = []

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
    def parse_from_string(cls, buffer):
        """A TiddlyWiki factory
        Returns a TiddlyWiki instance containing all tiddlers found in string buffer

        """
        tiddly_wiki = cls()

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

    def apply(self, algorithm):
        return algorithm.evaluate(self)
