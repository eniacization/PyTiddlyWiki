import re
import reprlib

from convertstrings import ConvertStringsMixin
from exporttiddler import ExportTiddlerMixin


class Tiddler(ConvertStringsMixin, ExportTiddlerMixin):

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


if __name__ == "__main__":

    tiddler_string = r"""
<div created="20180108222550419" modified="20180111174922056" tags="[[multi word tag]] tag2 tag3" title="just a test" tmap.id="8b72e085-396b-4145-92aa-6793964cedad">
<pre>!This is a test tiddler.

* nested
** bullet
* points
*# point 1
*# point 2

# enumeration
# one
# two
# hashtag sign # is used on twitter and instagram

''bold'' //italic//

~CamelCase ~CamelCase ~~strike through~~

&lt;&lt;&lt; This is a very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long quote
on many lines 

by a &lt;&lt;&lt; wise man

separation bar
---
without blank lines before or after

&quot;&quot;&quot;
multi
line
environment
&quot;&quot;&quot;

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