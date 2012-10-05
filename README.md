# TikZ for Markdown

An extension to [Python-Markdown](http://packages.python.org/Markdown/) to convert blocks of [TikZ-code](http://www.ctan.org/pkg/pgf) to inline SVG images using `mk4ht` (which should be part of your TeX distribution).

Just insert a block (i.e. surrounded by new lines) of raw LaTeX/TikZ code into your document:

    Normal Markdown...
    Here is a tree:
    
    \begin{tikzpicture}
      \draw[thick, level distance=3em] node{Root}
        child{ node{Child} }
        child{ node{Child} [sibling distance=3cm]
          child{ node{Grandchild} }
          child{ node{Grandchild} } };
    \end{tikzpicture}
    
    Using the *Lindenmayer* library:
    
    \usetikzlibrary{lindenmayersystems}
    \begin{tikzpicture}
      \draw[rotate=90]
        lindenmayer system[l-system={
          rule set={F -> FF-[-F+F]+[+F-F]},
          axiom=F, order=4,
          step=2pt, randomize step percent=25,
          angle=30, randomize angle percent=5}];
    \end{tikzpicture}
    
    More Markdown.

The compilation results are cached for each picture, the downside is that you can't use definitions between pictures (but you can use TeX `\input` command).

When `TikzMarkdown.py` is executed standalone, it watches the current directory for changes to Markdown documents and compiles them automatically, taking advantage of the caching.
