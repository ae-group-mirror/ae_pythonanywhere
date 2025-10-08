# THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.project_tpls v0.3.58
""" setup of ae namespace module portion pythonanywhere: PythonAnywhere Web API Client. """
# noinspection PyUnresolvedReferences
import sys
print(f"SetUp {__name__=} {sys.executable=} {sys.argv=} {sys.path=}")

# noinspection PyUnresolvedReferences
import setuptools

setup_kwargs = {
    'author': 'AndiEcker',
    'author_email': 'aecker2@gmail.com',
    'classifiers': [       'Development Status :: 3 - Alpha', 'Natural Language :: English', 'Operating System :: OS Independent',
        'Programming Language :: Python', 'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9', 'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed'],
    'description': 'ae namespace module portion pythonanywhere: PythonAnywhere Web API Client',
    'extras_require': {       'dev': [       'aedev_project_tpls', 'ae_ae', 'anybadge', 'coverage-badge', 'aedev_project_manager', 'flake8',
                       'mypy', 'pylint', 'pytest', 'pytest-cov', 'pytest-django', 'typing', 'types-setuptools'],
        'docs': [],
        'tests': [       'anybadge', 'coverage-badge', 'aedev_project_manager', 'flake8', 'mypy', 'pylint', 'pytest',
                         'pytest-cov', 'pytest-django', 'typing', 'types-setuptools']},
    'install_requires': ['requests', 'types-requests', 'ae_base', 'ae_paths', 'ae_dev_ops'],
    'keywords': ['configuration', 'development', 'environment', 'productivity'],
    'license': 'GPL-3.0-or-later',
    'long_description': ('<!-- THIS FILE IS EXCLUSIVELY MAINTAINED by the project ae.ae v0.3.100 -->\n'
 '<!-- THIS FILE IS EXCLUSIVELY MAINTAINED by the project aedev.namespace_root_tpls v0.3.21 -->\n'
 '# pythonanywhere 0.3.2\n'
 '\n'
 '[![GitLab develop](https://img.shields.io/gitlab/pipeline/ae-group/ae_pythonanywhere/develop?logo=python)](\n'
 '    https://gitlab.com/ae-group/ae_pythonanywhere)\n'
 '[![LatestPyPIrelease](\n'
 '    https://img.shields.io/gitlab/pipeline/ae-group/ae_pythonanywhere/release0.3.2?logo=python)](\n'
 '    https://gitlab.com/ae-group/ae_pythonanywhere/-/tree/release0.3.2)\n'
 '[![PyPIVersions](https://img.shields.io/pypi/v/ae_pythonanywhere)](\n'
 '    https://pypi.org/project/ae-pythonanywhere/#history)\n'
 '\n'
 '>ae namespace module portion pythonanywhere: PythonAnywhere Web API Client.\n'
 '\n'
 '[![Coverage](https://ae-group.gitlab.io/ae_pythonanywhere/coverage.svg)](\n'
 '    https://ae-group.gitlab.io/ae_pythonanywhere/coverage/index.html)\n'
 '[![MyPyPrecision](https://ae-group.gitlab.io/ae_pythonanywhere/mypy.svg)](\n'
 '    https://ae-group.gitlab.io/ae_pythonanywhere/lineprecision.txt)\n'
 '[![PyLintScore](https://ae-group.gitlab.io/ae_pythonanywhere/pylint.svg)](\n'
 '    https://ae-group.gitlab.io/ae_pythonanywhere/pylint.log)\n'
 '\n'
 '[![PyPIImplementation](https://img.shields.io/pypi/implementation/ae_pythonanywhere)](\n'
 '    https://gitlab.com/ae-group/ae_pythonanywhere/)\n'
 '[![PyPIPyVersions](https://img.shields.io/pypi/pyversions/ae_pythonanywhere)](\n'
 '    https://gitlab.com/ae-group/ae_pythonanywhere/)\n'
 '[![PyPIWheel](https://img.shields.io/pypi/wheel/ae_pythonanywhere)](\n'
 '    https://gitlab.com/ae-group/ae_pythonanywhere/)\n'
 '[![PyPIFormat](https://img.shields.io/pypi/format/ae_pythonanywhere)](\n'
 '    https://pypi.org/project/ae-pythonanywhere/)\n'
 '[![PyPILicense](https://img.shields.io/pypi/l/ae_pythonanywhere)](\n'
 '    https://gitlab.com/ae-group/ae_pythonanywhere/-/blob/develop/LICENSE.md)\n'
 '[![PyPIStatus](https://img.shields.io/pypi/status/ae_pythonanywhere)](\n'
 '    https://libraries.io/pypi/ae-pythonanywhere)\n'
 '[![PyPIDownloads](https://img.shields.io/pypi/dm/ae_pythonanywhere)](\n'
 '    https://pypi.org/project/ae-pythonanywhere/#files)\n'
 '\n'
 '\n'
 '## installation\n'
 '\n'
 '\n'
 'execute the following command to install the\n'
 'ae.pythonanywhere module\n'
 'in the currently active virtual environment:\n'
 ' \n'
 '```shell script\n'
 'pip install ae-pythonanywhere\n'
 '```\n'
 '\n'
 'if you want to contribute to this portion then first fork\n'
 '[the ae_pythonanywhere repository at GitLab](\n'
 'https://gitlab.com/ae-group/ae_pythonanywhere "ae.pythonanywhere code repository").\n'
 'after that pull it to your machine and finally execute the\n'
 'following command in the root folder of this repository\n'
 '(ae_pythonanywhere):\n'
 '\n'
 '```shell script\n'
 'pip install -e .[dev]\n'
 '```\n'
 '\n'
 'the last command will install this module portion, along with the tools you need\n'
 'to develop and run tests or to extend the portion documentation. to contribute only to the unit tests or to the\n'
 'documentation of this portion, replace the setup extras key `dev` in the above command with `tests` or `docs`\n'
 'respectively.\n'
 '\n'
 'more detailed explanations on how to contribute to this project\n'
 '[are available here](\n'
 'https://gitlab.com/ae-group/ae_pythonanywhere/-/blob/develop/CONTRIBUTING.rst)\n'
 '\n'
 '\n'
 '## namespace portion documentation\n'
 '\n'
 'information on the features and usage of this portion are available at\n'
 '[ReadTheDocs](\n'
 'https://ae.readthedocs.io/en/latest/_autosummary/ae.pythonanywhere.html\n'
 '"ae_pythonanywhere documentation").\n'),
    'long_description_content_type': 'text/markdown',
    'name': 'ae_pythonanywhere',
    'package_data': {'': []},
    'packages': ['ae'],
    'project_urls': {       'Bug Tracker': 'https://gitlab.com/ae-group/ae_pythonanywhere/-/issues',
        'Documentation': 'https://ae.readthedocs.io/en/latest/_autosummary/ae.pythonanywhere.html',
        'Repository': 'https://gitlab.com/ae-group/ae_pythonanywhere',
        'Source': 'https://ae.readthedocs.io/en/latest/_modules/ae/pythonanywhere.html'},
    'python_requires': '>=3.9',
    'url': 'https://gitlab.com/ae-group/ae_pythonanywhere',
    'version': '0.3.2',
    'zip_safe': True,
}

if __name__ == "__main__":
    setuptools.setup(**setup_kwargs)
    pass
