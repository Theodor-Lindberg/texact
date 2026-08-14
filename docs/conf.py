# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "TeXact"
copyright = "2026, Theodor Lindberg"
author = "Theodor Lindberg"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_heading_anchors = 3

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"] # For scaling the logo over ToC
html_favicon = "_static/texact.ico"
html_logo = "_static/texactlogo.svg"
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#ff6442",
        "color-brand-content": "#ff6442",
        "color-brand-visited": "#d1a221",
    },
    "dark_css_variables": {
        "color-brand-primary": "#ff6442 ",
        "color-brand-content": "#ff6442",
        "color-brand-visited": "#d1a221",
    },
}


def setup(app):
    import m2r2

    m2r2._IS_SPHINX = True
    app.add_config_value("no_underscore_emphasis", False, "env")
    app.add_config_value("m2r_parse_relative_links", False, "env")
    app.add_config_value("m2r_anonymous_references", False, "env")
    app.add_config_value("m2r_disable_inline_math", False, "env")
    app.add_config_value("m2r_use_mermaid", False, "env")
    app.add_directive("mdinclude", m2r2.MdInclude)
