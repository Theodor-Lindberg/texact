Try it here
===========

Here you can try TeXact directly in your browser! Note that some
functionality is not exposed in the web interface. For example,
integration with ChkTeX, command-line arguments, and configuration
file options.

Keep in mind that TeXact does not ensure that the LaTeX code
compiles; that is the compiler's responsibility. However,
it will check for common mistakes in article writing.

.. raw:: html

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/stex/stex.min.js"></script>

    <div class="try-it">
        <p class="try-it-main-note" id="try-it-main-note" hidden>Note that this demo is running the latest version released on PyPi and not the latest development version.</p>
        <div class="try-it-toolbar">
            <label for="try-it-editor">example.tex</label>
            <span class="try-it-version" id="try-it-version">TeXact loading...</span>
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
