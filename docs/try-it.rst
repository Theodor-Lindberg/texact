Try it here
===========

Here you can try TeXact directly in your browser! The first run downloads
TeXact, so it may take a few seconds. Support for ChkTeX is
disabled in browser mode.

.. raw:: html

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/stex/stex.min.js"></script>

    <div class="try-it">
        <div class="try-it-toolbar">
            <label for="try-it-editor">example.tex</label>
            <button id="try-it-run" type="button">Run TeXact</button>
        </div>
        <textarea id="try-it-editor" spellcheck="false">
    \documentclass{article}
    \begin{document}

    In this work we should improve the asic design.
    See Section~\ref{sec:intro} for details.

    \label{sec:design}
    \end{document}
    </textarea>
        <div class="try-it-status" id="try-it-status" role="status">Ready to run</div>
        <div class="try-it-output" id="try-it-output" aria-live="polite">Run TeXact to see its output here.</div>
    </div>
