import abc
import random


class Algorithm(abc.ABC):

    @abc.abstractmethod
    def evaluate(self, tiddl_wiki):
        '''called by TiddlyWiki.apply and implements the visitor pattern'''


class GetRandomTiddler(Algorithm):

    def __init__(self, *predicates):
        self.predicates = predicates

    def evaluate(self, tiddl_wiki):
        if self.predicates is None:
            available = tiddl_wiki.tiddlers
        else:
            available = list(tiddl_wiki.apply(FindAllTiddlers(*self.predicates)))

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
        for tiddler in tiddly_wiki:
            if all(p(tiddler) for p in self.predicates):
                yield tiddler