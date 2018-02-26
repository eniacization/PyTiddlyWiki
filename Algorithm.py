import abc
import random
import tempfile

import pypandoc
import tqdm as tqdm


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

# TODO: table of contents(, non-linear toc?)
class ExportToFile:

    def __init__(self, path, format=None, predicates=None, key=None):
        self.path = path
        if format is None:
            self.format = path.split('.')[-1]
        else:
            self.format = format
        self.predicates = predicates
        if key is None:
            self.key = lambda t: t.created
        else:
            self.key = key

    def evaluate(self, tiddly_wiki):

        if self.predicates is not None:
            tiddlers = list(tiddly_wiki.apply(FindAllTiddlers(*self.predicates)))
        else:
            tiddlers = list(tiddly_wiki)

        tiddlers.sort(key=self.key)
        safe_tiddlers = []
        non_safe_tiddlers = []

        for tiddler in tqdm.tqdm(tiddlers):
            with tempfile.NamedTemporaryFile('w', suffix='.'+self.format) as fh:
                try:
                    tiddler.export_to_file(fh.name)
                except RuntimeError as error:
                    print(error)
                    non_safe_tiddlers.append(tiddler)
                else:
                    safe_tiddlers.append(tiddler)

        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as fh:
            for tiddler in safe_tiddlers:
                tiddler_md = tiddler.export()
                fh.write(tiddler_md)
                fh.write('\n\n---\n\n---\n\n')

        pypandoc.convert_file(fh.name, self.format, format='md', outputfile=self.path)

        if non_safe_tiddlers:
            print("Could only export {} out of {} tiddlers.".format(len(safe_tiddlers), len(tiddlers)))
            print("The following tiddlers raised a pandoc error:")
            for tiddler in non_safe_tiddlers:
                print("\t{}".format(tiddler.title))
