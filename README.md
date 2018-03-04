# PyTiddlyWiki

[TiddlyWiki](https://github.com/Jermolene/TiddlyWiki5) is a non-linear notebook
written in JavaScript and contained in a single html file.
__PyTiddlyWiki__ allows you to

* parse a standalone TiddlyWiki html file,
* filter and sort Tiddlers,
* export single Tiddlers to various formats,
such as (github flavored) markdown and pdf,
* export the whole TiddlyWiki to various formats,
such as md and pdf.

## How can PyTiddlyWiki be used?

Having the possibility to capture ideas and thoughts in a non-linear, '[rhizomatic](https://en.wikipedia.org/wiki/Rhizome_(philosophy))'
way is one of the amazing features of TiddlyWiki.
But sometimes a linear structure can also be helpful.
For example, think of the natural chronological order of a journal.
The linear nature of a book and the possibility to 'turn pages' is lost
to some extent in a wiki.
Exporting (parts of) a TiddlyWiki as a pdf with a book-like structure reinstates a
linear structure to your wiki.

The following use cases are part of [example.py](./example.py).

#### parse a TiddlyWiki

````python
from tiddlywiki import TiddlyWiki

tw5 = TiddlyWiki.parse_from_html('./example/tw5.html')
````

#### filter Tiddlers from a TiddlyWiki

````python
from algorithm import FindAllTiddlers

predicate = lambda t: 'journal' in t.tags
journal_tiddlers = list(tw5.apply(FindAllTiddlers(predicate)))
````

#### open Tiddler in browser

````python
for tiddler in journal_tiddlers:
    tiddler.open_in_browser()
````

#### export single Tiddler as pdf

````python
for tiddler in journal_tiddlers:
    tiddler.export_to_file('./example/' + tiddler.title + '.pdf')
````

#### export TiddlyWiki as pdf

````python
from algorithm import ExportToFile

algorithm = ExportToFile('./example/tw5_journal.pdf',
                         '--toc',
                         key=lambda t: t.created,
                         predicates=[predicate])
tw5.apply(algorithm)
```` 

## format specifiers

The export of a Tiddler or (parts of) a TiddlyWiki
is facilitated by the python wrapper
[pypandoc](https://github.com/bebraw/pypandoc/blob/master/README.md) for
[pandoc](https://github.com/jgm/pandoc).
You may use any valid pandoc format specifier when exporting, e.g.
```python
tiddler.export_to_file(format='markdown_github')
```

Valid pandoc (version 2.1.1) format specifiers include
```python
>>> for format in pypandoc.get_pandoc_formats[1]:
...    print(format)
...
asciidoc
beamer
commonmark
context
docbook
docbook4
docbook5
docx
dokuwiki
dzslides
epub
epub2
epub3
fb2
gfm
haddock
html
html4
html5
icml
jats
json
latex
man
markdown
markdown_github
markdown_mmd
markdown_phpextra
markdown_strict
mediawiki
ms
muse
native
odt
opendocument
opml
org
plain
pptx
revealjs
rst
rtf
s5
slideous
slidy
tei
texinfo
textile
zimwiki
```

## How to add functionality?

To add new functionality to PyTiddlyWiki you can subclass `Algorithm` in [algorithm.py](./algorithm.py).
Any subclass of `Algorithm` must implement
the abstract instance method `evaluate(self, tiddlywiki)`.
When an Algorithm instance `algorithm` is applied to a TiddlyWiki instance`tiddlywiki` via
```python
tiddlywiki.apply(algorithm)
```
the `evaluate` method of `algorithm` is called on `tiddlywiki`.

You may take a look at some of the Algorithm subclasses in [algorithm.py](./algorithm.py).