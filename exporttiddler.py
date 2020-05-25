import tempfile
import webbrowser

import pypandoc


class ExportTiddlerMixin:
    def export_header(self, format='md', encoding='utf-8'):
        '''export the tiddler head (containing title, creation date, and tags).
        format can be any valid pandoc format specifier.
        '''
        header = "# {}\n" \
                 "__created__: {}, " \
                 "__last modified__: {}\n\n" \
                 "__keywords__: {}"
        result = header.format(self.title, self.created, self.modified, self.tags)

        if encoding != 'utf-8':
            result = result.encode(encoding, errors='ignore').decode(encoding)

        return pypandoc.convert_text(result, format, format='md')


    def export_content(self, format='md', encoding='utf-8'):
        '''export the tiddler content.
        format can be any valid pandoc format specifier.
        first, the tiddler content is converted to github flavored markdown.
        then pypandoc is used to convert the md file to the desired format.
        '''
        if self.type_ == 'text/vnd.tiddlywiki':
            content = type(self).convert_tw5_to_md(self.content)
        elif self.type_ == 'text/html':
            content = pypandoc.convert_text(self.content, 'md', format='html')
        elif self.type_ == 'text/x-markdown':
            content = self.content
        else:
            content = self.content

        if encoding != 'utf-8':
            content = content.encode(encoding, errors='ignore').decode(encoding)

        return pypandoc.convert_text(content, format, format='md')


    def export(self, format='md', encoding='utf-8'):
        '''export the tiddler to a string.
        format can be any valid pandoc format specifier.
        '''
        result = self.export_header(encoding=encoding)
        result += '\n\n---\n\n'
        result += self.export_content(encoding=encoding)

        try:
            result = pypandoc.convert_text(result, format, format='md')
        except Exception as error:  # TODO: specify Exception
            print(error)
            result = None
        return result


    def export_to_file(self, path, format=None, encoding='utf-8'):
        '''export the tiddler to a file at dir <path>.
        format can be any valid pandoc format specifier.
        '''
        if format is None:
            format = path.split('.')[-1]
        # pandoc uses latex when converting to pdf.
        # unfortunately, the latex packet inputenc.sty doesn't use the utf-8 codec for unicode
        # (see: http://texdoc.net/texmf-dist/doc/latex/base/inputenc.pdf).
        # hence, some special characters can lead to runtime errors,
        # when pandocs tries to convert to latex.
        # to avoid these errors, the unicode string md is first encoded with a codec
        # (such as latin-1) that lacks these special characters and has less code points than utf-8.
        # (a list of codecs in python is https://docs.python.org/3.6/library/codecs.html#standard-encodings)
        # some code points associated to exotic characters
        # will be lost during this encoding (errors='ignore').
        # the (possibly trimmed) byte-string is then decoded back to unicode with the consequence
        # that all 'dangerous' characters are cut off.
        if format in {'pdf'}:
            encoding = 'latin-1'

        md = self.export(encoding=encoding)
        pypandoc.convert_text(md, format, format='md', outputfile=path)


    def open_in_browser(self, format='html'):
        with tempfile.NamedTemporaryFile('w', suffix='.' + format, delete=False) as fh:
            self.export_to_file(fh.name, format=format)
        #webbrowser.get(using='chrome').open('file://' + fh.name, new=1)
        webbrowser.get().open('file://' + fh.name, new=1)
