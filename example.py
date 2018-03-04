from tiddlywiki import TiddlyWiki
from algorithm import FindAllTiddlers, ExportToFile, OpenInBrowser

tw5 = TiddlyWiki.parse_from_html('./example/tw5.html')

predicate = lambda t: 'journal' in t.tags
journal_tiddlers = list(tw5.apply(FindAllTiddlers(predicate)))

for tiddler in journal_tiddlers:
    tiddler.open_in_browser()

for tiddler in journal_tiddlers:
    tiddler.export_to_file('./example/' + tiddler.title + '.pdf')

export_journal = ExportToFile('./example/tw5_journal.pdf',
                              '--toc',
                              key=lambda t: t.created,
                              predicates=[predicate])
tw5.apply(export_journal)

open_journals_in_browser = OpenInBrowser('--toc',
                                         key=lambda t: t.created,
                                         predicates=[predicate])
tw5.apply(open_journals_in_browser)