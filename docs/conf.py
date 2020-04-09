project = 'KubePortal'
copyright = '2019, Peter Tröger'
author = 'Peter Tröger'
release = 'v0.3.7'
extensions = [
	'sphinx_issues'
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
master_doc = 'index'

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