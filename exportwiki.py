import concurrent.futures

import os
import tempfile

import datetime
import webbrowser

import pypandoc
import tqdm


class ExportWikiMixin:

    __MAX_WORKERS = os.cpu_count()

    def __get_tiddlers(self, predicates):
        if predicates is not None:
            tiddlers = list(self.finditer(*predicates))
        else:
            tiddlers = list(self)
        return tiddlers

    def __get_safe_tiddlers(self, iterable_tiddlers, format):
        safe_tiddlers = []
        non_safe_tiddlers = []

        for tiddler in tqdm.tqdm(iterable_tiddlers):
            with tempfile.NamedTemporaryFile('w', suffix='.' + format) as fh:
                try:
                    tiddler.export_to_file(fh.name)
                except RuntimeError as error:
                    print(error)
                    non_safe_tiddlers.append(tiddler)
                else:
                    safe_tiddlers.append(tiddler)

        return safe_tiddlers, non_safe_tiddlers

    def __get_safe_tiddlers_multithread(self, iterable_tiddlers, format):
        workers = min(len(iterable_tiddlers), self.__MAX_WORKERS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor, \
                tempfile.NamedTemporaryFile('w', suffix='.' + format) as fh:
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

    def export_to_file(self, path, *extra_args, format=None, predicates=None, key=lambda t: t.created):
        if format is None:
            format = path.split('.')[-1]

        tiddlers = self.__get_tiddlers(predicates)

        if format in {'pdf'}:
            safe_tiddlers, non_safe_tiddlers = self.__get_safe_tiddlers_multithread(tiddlers, format)
        else:
            safe_tiddlers = tiddlers
            non_safe_tiddlers = []
        safe_tiddlers.sort(key=key)

        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as fh:
            title = '% {}\n' \
                    '% {}\n' \
                    '% {}\n\n'.format(self.title,
                                      self.subtitle,
                                      str(datetime.date.today()))
            fh.write(title)

            for tiddler in tqdm.tqdm(safe_tiddlers):
                if format in {'pdf'}:
                    encoding = 'latin-1'
                else:
                    encoding = 'utf-8'
                tiddler_md = tiddler.export(encoding=encoding)
                fh.write(tiddler_md)
                fh.write('\n\n---\n\n---\n\n')

        pypandoc.convert_file(fh.name,
                              format,
                              format='md',
                              outputfile=path,
                              extra_args=extra_args)

        if non_safe_tiddlers:
            msg = 'Could only export {} out of {} tiddlers.'
            print(msg.format(len(safe_tiddlers), len(tiddlers)))
            print("The following tiddlers raised a pandoc error:")
            for tiddler in non_safe_tiddlers:
                print("\t{}".format(tiddler.title))

    def open_in_browser(self, *extra_args, format='html', predicates=None, key=lambda t: t.created):

        tiddlers = self.__get_tiddlers(predicates)
        tiddlers.sort(key=key)
        with tempfile.NamedTemporaryFile('w', suffix='.'+format, delete=False) as fh:
            title = '% {}\n' \
                    '% {}\n' \
                    '% {}\n\n'.format(self.title,
                                      self.subtitle,
                                      str(datetime.date.today()))
            result = title

            for tiddler in tqdm.tqdm(tiddlers):
                if format in {'pdf'}:
                    encoding = 'latin-1'
                else:
                    encoding = 'utf-8'
                tiddler_md = tiddler.export(encoding=encoding)
                result += tiddler_md
                result += '\n\n---\n\n---\n\n'

            pypandoc.convert_text(result,
                                  format,
                                  format='md',
                                  outputfile=fh.name,
                                  extra_args=extra_args)
            #webbrowser.get(using='chrome').open('file://' + fh.name, new=1)
            webbrowser.get().open('file://' + fh.name, new=1)

