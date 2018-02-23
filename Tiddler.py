import re
import reprlib
import tempfile
import webbrowser

from Tw5Mixin import Tw5Mixin
import pypandoc


class Tiddler(Tw5Mixin):

    def __init__(self, content, title=None, tags=None, created=None, modified=None,
                 type='text/vnd.tiddlywiki', **kwargs):
        self.content = content
        self.title = title
        self.tags = [] if tags is None else tags
        self.created = created
        self.modified = modified
        self.type_ = type
        self.__dict__.update(kwargs)

    @classmethod
    def finditer(cls, buffer):

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
                pass

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

    def export_content(self, format='md'):
        '''export the tiddler content.
        format is any valid pandoc format specifier.
        first, the tiddler content is converted to github flavored markdown.
        then pypandoc is used to convert the md file to the desired format.
        '''
        if self.type_ == 'text/vnd.tiddlywiki':
            content = type(self).convert_tw5_to_md(self.content)
        else:
            content = self.content

        return pypandoc.convert_text(content, 'md', format=format)

    def export(self):
        '''the tiddler is exported to a markdown string'''

        result = '# ' + self.title + '\n\n'
        result += self.export_content()
        return result

    def open_in_browser(self):

        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as fh:
            md = self.export()
            fh.write(md)

        webbrowser.get(using='chrome').open('file://' + fh.name, new = 1)


