import random


class SearchWikiMixin:

    def get_random_tiddler(self, *predicates):
        if predicates is None:
            available = self.tiddlers
        else:
            available = list(self.finditer(*predicates))
        return random.choice(available)

    def find_tiddler(self, *predicates):
        for tiddler in self:
            if all(p(tiddler) for p in predicates):
                return tiddler
        return None

    def finditer(self, *predicates):
        for tiddler in self:
            if all(p(tiddler) for p in predicates):
                yield tiddler