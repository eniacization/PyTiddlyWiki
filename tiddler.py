import re
import reprlib
import tempfile
import webbrowser

from tw5mixin import Tw5Mixin
import pypandoc


class Tiddler(Tw5Mixin):

    RE_TIDDLER = re.compile('<div'
                            '(?P<options>[\w\W]*?)'
                            '>\n'
                            '<pre>'
                            '(?P<content>[\w\W]*?)</pre>\n'
                            '</div>')

    RE_OPTION = re.compile('\s+(?P<key>\w+?)=\"(?P<value>[\w\W]*?)\"')

    def __init__(self, content, title=None, tags=None, created=None, modified=None,
                 type='text/vnd.tiddlywiki', **kwargs):
        """besides standard attributes (title, tags, created, modified, type_)
        an arbitrary number of kwargs is added to the Tiddler namespace __dict__.
        """
        self.content = content
        self.title = title
        self.tags = [] if tags is None else tags
        self.created = created
        self.modified = modified
        self.type_ = type
        self.__dict__.update(kwargs)

    @classmethod
    def finditer(cls, buffer):
        """generator function, yielding Tiddler instances found in buffer.
        The Tiddler initiator is invoked with the kwargs of all options found in buffer.
        """
        for match in re.finditer(cls.RE_TIDDLER, buffer):
            options = match.group('options')
            content = match.group('content')

            attr = {}
            for match in re.finditer(cls.RE_OPTION, options):
                key = match.group('key')
                value = match.group('value')
                attr[key] = value

            try:
                attr['tags'] = cls.get_tag_list(attr['tags'])
            except KeyError:
                pass

            try:
                attr['modified'] = cls.string_to_date(attr['modified'])
            except KeyError:
                pass

            try:
                attr['created'] = cls.string_to_date(attr['created'])
            except KeyError:
                continue  # don't include tiddlers without creation tag

            try:
                if attr['title'].startswith('$:/'):
                    continue  # don't include tiddlers, whose title start with '$:/'
            except KeyError:
                continue  # don't include tiddlers without title

            yield cls(content, **attr)

    @classmethod
    def parse_from_string(cls, buffer):
        """A Tiddler factory
        If buffer contains a tiddler, a Tiddler instance of the first tiddler is returned.
        If buffer does not contain any tiddler, None is returned.
        """
        try:
            return next(cls.finditer(buffer))
        except StopIteration:
            return None

    def __str__(self):
        result = (self.title + '\n' +
                  '\ttags: ' + str(self.tags) + '\n' +
                  '\tcreated: ' + str(self.created) + ', '
                  '\tmodified: ' + str(self.modified) + '\n'
                  '\t' + reprlib.repr(self.content))

        return result

    def __repr__(self):
        attr = {key: value for key, value in self.__dict__.items()
                if not key.startswith('__') and key not in {'content'}}

        attr_string = ', '.join('{}={}'.format(key, reprlib.repr(value))
                                for key, value in attr.items())

        result = 'Tiddler({}, {})'.format(reprlib.repr(self.content), attr_string)

        return result

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
        except Exception as error: # TODO: specify Exception
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
        with tempfile.NamedTemporaryFile('w', suffix='.'+format, delete=False) as fh:
            self.export_to_file(fh.name, format=format)
        webbrowser.get(using='chrome').open('file://' + fh.name, new = 1)


if __name__ == "__main__":

    tiddler_string = r"""
<div created="20180108222550419" modified="20180111174922056" tags="[[multi word tag]] tag2 tag3" title="just a test" tmap.id="8b72e085-396b-4145-92aa-6793964cedad">
<pre>!This is a test tiddler.

* nested
** bullet
* points

# enumeration
# one
# two

''bold'' //italic//

~CamelCase ~CamelCase ~~strike through~~

&lt;&lt;&lt; This is a very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long quote
on many lines

by a &lt;&lt;&lt; wise man

in line math formula $$a^2+b^2=c^2$$. this is the [[pythagorean theorem|https://en.wikipedia.org/wiki/Pythagorean_theorem]].
second derivative: $$f''(x) + g''(x)$$. [[https://en.wikipedia.org/wiki/Pythagorean_theorem]].

a formula ''within a bold text region $$a^2$$''.

latex equation:
$$
a^2+b^2=c^2.
$$</pre>
</div>"""

    tiddler = Tiddler.parse_from_string(tiddler_string)
    print(tiddler)

    tiddler.open_in_browser('md')
    tiddler.open_in_browser('markdown_github')
    tiddler.open_in_browser('html')