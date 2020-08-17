project = 'KubePortal'
copyright = '2019, Peter Tröger'
author = 'Peter Tröger'
release = 'v0.3.14'
extensions = [
	'sphinx_issues',
    'sphinx.ext.autosectionlabel'	
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = "sphinx_rtd_theme"
master_doc = 'index'

autosectionlabel_prefix_document = False

issues_github_path = 'troeger/kubeportal'

html_theme_options = {
    'display_version': True,
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}