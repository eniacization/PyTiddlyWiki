import abc
import concurrent.futures
import random
import tempfile

import datetime

import os
import pypandoc
import tqdm


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

# TODO: non-linear toc?
class ExportToFile:

    MAX_WORKERS = os.cpu_count()

    def __init__(self, path, *extra_args, format=None, predicates=None, key=None):
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
        self.extra_args = extra_args

    def _get_tiddlers(self, tiddly_wiki):
        if self.predicates is not None:
            tiddlers = list(tiddly_wiki.apply(FindAllTiddlers(*self.predicates)))
        else:
            tiddlers = list(tiddly_wiki)
        return tiddlers

    def _get_safe_tiddlers(self, iterable_tiddlers):
        safe_tiddlers = []
        non_safe_tiddlers = []

        for tiddler in tqdm.tqdm(iterable_tiddlers):
            with tempfile.NamedTemporaryFile('w', suffix='.'+self.format) as fh:
                try:
                    tiddler.export_to_file(fh.name)
                except RuntimeError as error:
                    print(error)
                    non_safe_tiddlers.append(tiddler)
                else:
                    safe_tiddlers.append(tiddler)

        return safe_tiddlers, non_safe_tiddlers

    def _get_safe_tiddlers_multithread(self, iterable_tiddlers):

        workers = min(len(iterable_tiddlers), self.MAX_WORKERS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor, \
                tempfile.NamedTemporaryFile('w', suffix='.'+self.format) as fh:
            future_to_tiddler = {}
            for tiddler in iterable_tiddlers:
                ftr = executor.submit(tiddler.export_to_file, fh.name)
                future_to_tiddler[ftr] = tiddler

            safe_tiddlers = []
            non_safe_tiddlers = []
            futures = concurrent.futures.as_completed(future_to_tiddler.keys())
            for future in tqdm.tqdm(futures, total=len(future_to_tiddler)):
                tiddler = future_to_tiddler[future]
                try:
                    future.result()
                except RuntimeError as error:
                    print(error)
                    non_safe_tiddlers.append(tiddler)
                else:
                    safe_tiddlers.append(tiddler)

        return safe_tiddlers, non_safe_tiddlers

    def evaluate(self, tiddly_wiki):

        tiddlers = self._get_tiddlers(tiddly_wiki)
        if self.format in {'pdf'}:
            safe_tiddlers, non_safe_tiddlers = self._get_safe_tiddlers_multithread(tiddlers)
        else:
            safe_tiddlers = tiddlers
            non_safe_tiddlers = []
        safe_tiddlers.sort(key=self.key)

        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as fh:
            title = '% {}\n' \
                    '% {}\n' \
                    '% {}\n\n'.format(tiddly_wiki.title,
                                      tiddly_wiki.subtitle,
                                      str(datetime.date.today()))
            fh.write(title)

            for tiddler in tqdm.tqdm(safe_tiddlers):
                if self.format in {'pdf'}:
                    encoding = 'latin-1'
                else:
                    encoding = 'utf-8'
                tiddler_md = tiddler.export(encoding=encoding)
                fh.write(tiddler_md)
                fh.write('\n\n---\n\n---\n\n')

        pypandoc.convert_file(fh.name,
                              self.format,
                              format='md',
                              outputfile=self.path,
                              extra_args=self.extra_args)

        if non_safe_tiddlers:
            msg = 'Could only export {} out of {} tiddlers.'
            print(msg.format(len(safe_tiddlers), len(tiddlers)))
            print("The following tiddlers raised a pandoc error:")
            for tiddler in non_safe_tiddlers:
                print("\t{}".format(tiddler.title))
