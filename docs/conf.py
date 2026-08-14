import os

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

extensions = ["myst_parser", "sphinx_multiversion"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
myst_heading_anchors = 3

templates_path = ["_templates"]
exclude_patterns = []

smv_remote_whitelist = r"^origin$"
smv_branch_whitelist = r"^main$"
smv_tag_whitelist = os.environ.get(
    "SMV_TAG_WHITELIST",
    r"^v\d+\.\d+\.\d+$",
)
smv_released_pattern = r"^refs/tags/v\d+\.\d+\.\d+$"
smv_outputdir_format = "{ref.name}"
smv_prefer_remote_refs = True


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css", "try-it.css"]  # For scaling the logo over ToC
html_js_files = ["try-it.js"]
html_favicon = "_static/texact.ico"
html_logo = "_static/texactlogo.svg"
html_sidebars = {
    "**": [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "versions.html",
        "sidebar/navigation.html",
        "sidebar/scroll-end.html",
        "sidebar/variant-selector.html",
    ]
}
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
