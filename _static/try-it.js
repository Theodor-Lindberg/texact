(function () {
  "use strict";

  const root = document.querySelector(".try-it");
  if (!root || typeof CodeMirror === "undefined") {
    return;
  }

  const editor = CodeMirror.fromTextArea(
    document.querySelector("#try-it-editor"),
    {
      lineNumbers: true,
      lineWrapping: true,
      mode: "stex",
      viewportMargin: Infinity,
    },
  );
  const output = document.querySelector("#try-it-output");
  const runButton = document.querySelector("#try-it-run");
  const status = document.querySelector("#try-it-status");
  const versionLabel = document.querySelector("#try-it-version");
  let pyodidePromise;

  function loadTexact() {
    if (!pyodidePromise) {
      pyodidePromise = (async function () {
        const { loadPyodide } = await import(
          "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs"
        );
        const pyodide = await loadPyodide();
        status.textContent = "Loading TeXact dependencies...";
        await pyodide.loadPackage("pillow");
        await pyodide.loadPackage("micropip");
        await pyodide.runPythonAsync(`
import micropip
await micropip.install("texact")
        `);
        const version = await pyodide.runPythonAsync(
          "from texact import get_version\nget_version()",
        );
        versionLabel.textContent = `TeXact v${version}`;
        return pyodide;
      })().catch(function (error) {
        pyodidePromise = undefined;
        versionLabel.textContent = "TeXact unavailable";
        throw error;
      });
    }
    return pyodidePromise;
  }

  function appendSafeHtml(node, parent) {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) {
        parent.appendChild(document.createTextNode(child.nodeValue));
        continue;
      }
      if (child.nodeType !== Node.ELEMENT_NODE) {
        continue;
      }
      if (child.localName === "br") {
        parent.appendChild(document.createElement("br"));
        continue;
      }
      if (child.localName === "span") {
        const style = child.getAttribute("style") || "";
        if (/^color:\s*#(?:008000|800000|808000)\s*;?$/i.test(style)) {
          const span = document.createElement("span");
          span.style.color = style.split(":", 2)[1].replace(";", "").trim();
          appendSafeHtml(child, span);
          parent.appendChild(span);
          continue;
        }
      }
      appendSafeHtml(child, parent);
    }
  }

  function showTexactOutput(html) {
    html = html.replace(/<br>\r?\n/g, "<br>");
    const parsed = new DOMParser().parseFromString(
      `<div>${html}</div>`,
      "text/html",
    );
    output.replaceChildren();
    appendSafeHtml(parsed.body.firstElementChild, output);
  }

  async function runTexact() {
    runButton.disabled = true;
    status.textContent = "Loading TeXact...";
    output.textContent = "";

    try {
      const pyodide = await loadTexact();
      pyodide.FS.writeFile("example.tex", editor.getValue());
      status.textContent = "Running TeXact...";
      const result = await pyodide.runPythonAsync(`
import contextlib
import io
import json
import sys
from texact import main

sys.argv = ["texact", "--no-chktex", "--html-style", "example.tex"]
stdout = io.StringIO()
stderr = io.StringIO()
exit_code = 0
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    try:
        main()
    except SystemExit as error:
        exit_code = error.code if isinstance(error.code, int) else 1

json.dumps({"output": stdout.getvalue() + stderr.getvalue(), "exit_code": exit_code})
      `);
      const parsed = JSON.parse(result);
      showTexactOutput(parsed.output || "No output.");
      status.textContent = parsed.exit_code === 0
        ? "Finished without errors"
        : "Finished with findings";
    } catch (error) {
      output.textContent = String(error);
      status.textContent = "Unable to run TeXact";
    } finally {
      runButton.disabled = false;
    }
  }

  runButton.addEventListener("click", runTexact);
  status.textContent = "Loading TeXact...";
  loadTexact().then(
    function () {
      if (!runButton.disabled) {
        status.textContent = "Ready to run";
      }
    },
    function () {
      if (!runButton.disabled) {
        status.textContent = "Unable to load TeXact";
      }
    },
  );
})();