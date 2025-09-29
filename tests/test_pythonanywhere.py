""" unit tests for ae_pythonanywhere module package.

minimal testing because of the rate-limits on pythonanywhere.com (each endpoint has a 40 requests per minute rate limit,
apart from the send_input endpoint on consoles, which is 120 requests per minute - see
`https://help.pythonanywhere.com/pages/API`__ for more details).
"""
import os
import pytest
import requests

from conftest import skip_gitlab_ci
from unittest.mock import Mock, patch

from ae.base import PY_CACHE_FOLDER, PY_INIT, load_dotenvs, norm_name
from ae.shell import get_domain_user_variable, get_main_app
from ae.pythonanywhere import PythonanywhereApi


TEST_PROJECT_NAME = 'ae_pythonanywhere_tests'       #: package name used for integrity tests on web server

pkg0_ini_path = os.path.join(TEST_PROJECT_NAME, PY_INIT)
pkg0_version = '333.66.9'
pkg0_ini_content = f'""" test package doc string. """\n\n__version__ = \'{pkg0_version}\'\n'.encode()
pkg0_static_file = f'{TEST_PROJECT_NAME}/static/baseball.html'

pkg1_name = "test_pkg1"
pkg1_file_path = f'{pkg1_name}/namespace_mod.py'

pkg2_name = "test_pkg2"
sub_dir_path = f'{pkg2_name}/sub2'
sub_file_name = '.sub_file_name.z'
sub_file_path = f'{sub_dir_path}/{sub_file_name}'
mig_file_name = 'mig_fil.wxy'
mig_file_path = f'{sub_dir_path}/migrations/{mig_file_name}'
mig_pkg_paths = {sub_file_path, f'{sub_dir_path}/{PY_INIT}'}
pkg2_static_file = f'{pkg2_name}/static/a2.b'

static_ini_file = 'static/initial.ttt'
static_file_paths = {static_ini_file, pkg0_static_file, pkg2_static_file}

all_pkg_paths = {pkg0_ini_path, pkg1_file_path} | mig_pkg_paths

skipped_web_paths = {f'{PY_CACHE_FOLDER}/x.y', f'{pkg1_name}/{PY_CACHE_FOLDER}/y.Z',
                     mig_file_path,
                     'media/media_file.jjj', 'media_ini/med.ia',
                     pkg0_static_file}
skipped_lean_paths = {'not_deployed_root_file.xxx',
                      'db.sqlite', 'project.db',
                      'manage.py',
                      f'{pkg1_name}/fi1.po'}
all_file_paths = all_pkg_paths | skipped_web_paths | skipped_lean_paths | static_file_paths


@pytest.fixture(scope='class')
def connection():
    """ provide personal pythonanywhere remote web server for tests only running locally with personal credentials. """
    main_app = get_main_app()
    load_dotenvs(main_app)

    web_domain = "www.pythonanywhere.com"
    web_user = os.environ.get('PDV_AUTHOR')
    web_token = get_domain_user_variable(main_app, 'web_token', domain=web_domain, user=web_user)

    remote_connection = PythonanywhereApi(web_domain, web_user, web_token, TEST_PROJECT_NAME)

    yield remote_connection


@pytest.fixture(scope='class')
def con_pkg(connection):
    """ provide personal pythonanywhere remote web server connection plus test package for tests """
    del_fil = 'test0/sub4/del_file.txt'
    assert not connection.deploy_file(del_fil, b"deleted to test empty root folder")
    assert connection.error_message == ""
    assert not connection.delete_file_or_folder(del_fil)
    assert connection.error_message == ""

    for fil_pat in all_file_paths:
        assert not connection.deploy_file(fil_pat, b"content of " + fil_pat.encode())
        assert connection.error_message == ""
    # overwrite content of project's main package init file with project version
    assert not connection.deploy_file(pkg0_ini_path, pkg0_ini_content)
    assert connection.error_message == ""

    yield connection

    connection.delete_file_or_folder("")    # clean up: delete project root folder TEST_PROJECT_NAME on host


def test_pythonanywhere_declarations():
    """ test the module declarations (also for having at least one test case running on gitlab ci). """
    assert PythonanywhereApi

    assert norm_name(TEST_PROJECT_NAME) == TEST_PROJECT_NAME

    assert requests             # not-used-inspection-warning workaround, used for requests.Response.json() patching


@skip_gitlab_ci  # skip on gitlab because of missing remote repository user account token
class TestHostRunningOnlyLocally:
    def test_init_and_clean_up_from_last_failed_test_run(self, connection):
        assert connection.error_message == ""

        connection.delete_file_or_folder("")  # if last test run failed then wipe folder TEST_PROJECT_NAME on host

    def test_available_consoles(self, connection):
        connection.error_message = ""                       # clear con_pkg instance error from last test method

        consoles = connection.available_consoles()
        assert connection.error_message == ""
        assert isinstance(consoles, list)

    def test_deploy_file_and_deployed_file_content_and_deployed_version(self, con_pkg):
        con_pkg.error_message = ""                          # clear con_pkg instance error from last test method

        assert con_pkg.deployed_file_content(pkg0_ini_path) == pkg0_ini_content
        assert con_pkg.error_message == ""

        assert con_pkg.deployed_version() == pkg0_version
        assert con_pkg.error_message == ""

        inv_fil_path = "not/existing/file_path"
        assert con_pkg.deployed_file_content(inv_fil_path) is None
        assert inv_fil_path in con_pkg.error_message

        con_pkg.error_message = ""                          # clear con_pkg instance error

    def test_files_iterator_absolute_path(self, con_pkg):
        con_pkg.error_message = ""                          # clear con_pkg instance error from previous test method

        found_paths = list(con_pkg.files_iterator('*'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted(_ for _ in all_file_paths if '/' not in _)

        assert found_paths == list(con_pkg.files_iterator('/.'))
        assert found_paths == list(con_pkg.files_iterator('/*'))
        assert found_paths == list(con_pkg.files_iterator(''))

    def test_files_iterator_deeper(self, con_pkg):
        found_paths = list(con_pkg.files_iterator('**'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted(all_file_paths)

        found_paths = list(con_pkg.files_iterator('**/*'))
        assert con_pkg.error_message == ""
        assert found_paths
        assert sorted(found_paths) == sorted(all_file_paths)

        found_paths = list(con_pkg.files_iterator('*/**'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted(_ for _ in all_file_paths if '/' in _)

        found_paths = list(con_pkg.files_iterator(f'{pkg2_name}/**/*'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted(mig_pkg_paths | {mig_file_path, pkg2_static_file})

    def test_files_iterator_migrations(self, con_pkg):
        found_paths = list(con_pkg.files_iterator('**/migrations/' + mig_file_name))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == mig_file_path

        found_paths = list(con_pkg.files_iterator('*/**/migrations/*'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == mig_file_path

        found_paths = list(con_pkg.files_iterator('*/*/**/migrations/**/' + mig_file_name))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == mig_file_path

        found_paths = list(con_pkg.files_iterator('*/*/*/**/migrations/' + mig_file_name))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 0                        # not found because file mask is one level too deep

    def test_files_iterator_static(self, con_pkg):
        found_paths = list(con_pkg.files_iterator('static/**'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == static_ini_file

        found_paths = list(con_pkg.files_iterator('/static/*'))     # project root get interpreted as host root
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == static_ini_file

        found_paths = list(con_pkg.files_iterator('**/static/*'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted(static_file_paths)

        found_paths = list(con_pkg.files_iterator('*/**/static/*'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted((pkg0_static_file, pkg2_static_file))

        found_paths = list(con_pkg.files_iterator('*/static/*'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted((pkg0_static_file, pkg2_static_file))

        found_paths = list(con_pkg.files_iterator('*/*/**/static/*'))
        assert con_pkg.error_message == ""
        assert not found_paths                                      # too deep search mask

    def test_files_iterator_sub_package(self, con_pkg):
        found_paths = list(con_pkg.files_iterator('**/*/' + sub_file_name))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'{pkg2_name}/*/{sub_file_name}'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'{pkg2_name}/**/{sub_file_name}'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'{pkg2_name}/**/*/{sub_file_name}'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'{pkg2_name}/*/**/{sub_file_name}'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'**/*/{sub_file_name}'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'**/*ub2/{sub_file_name}'))     # *ub2 only matches sub2
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator(f'**/s?b2/{sub_file_name}'))     # s?b2 only matches sub2
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator('*/sub2/*'))
        assert con_pkg.error_message == ""
        assert sub_file_path in found_paths
        assert sorted(found_paths) == sorted({sub_file_path, os.path.join(sub_dir_path, PY_INIT)})

        found_paths = list(con_pkg.files_iterator('**/sub2/*'))
        assert con_pkg.error_message == ""
        assert sorted(found_paths) == sorted({sub_file_path, os.path.join(sub_dir_path, PY_INIT)})

        found_paths = list(con_pkg.files_iterator('*/sub2/*.z'))
        assert con_pkg.error_message == ""
        assert len(found_paths) == 1
        assert found_paths[0] == sub_file_path

        found_paths = list(con_pkg.files_iterator('*/*/sub2/*'))
        assert con_pkg.error_message == ""
        assert found_paths == []                                    # path_mask one level too deep

    def test_folder_items(self, con_pkg):
        con_pkg.error_message = ""                          # clear con_pkg instance error from last test method

        found_file_infos = con_pkg._folder_items('')
        assert not con_pkg.error_message
        assert len(found_file_infos) >= 1
        assert any(_['file_path'] == 'manage.py' for _ in found_file_infos)

        found_file_infos = con_pkg._folder_items(sub_dir_path)
        assert not con_pkg.error_message
        assert len(found_file_infos) >= 1
        assert any(_['file_path'] == sub_file_path for _ in found_file_infos)

        found_file_infos = con_pkg._folder_items(sub_file_path)
        assert con_pkg.error_message                        # _from_json()-exception get dir-list from file content
        assert found_file_infos is None
        con_pkg.error_message = ""                          # clear con_pkg instance error

        found_file_infos = con_pkg._folder_items(f'{pkg2_name}/*')
        assert found_file_infos is None                     # host api does NOT support wildcards
        assert not con_pkg.error_message                    # api returns 404:Not Found, so err gets NOT propagated

        found_file_infos = con_pkg._folder_items(f'*/sub2')
        assert found_file_infos is None                     # host api does NOT support wildcards
        assert not con_pkg.error_message                    # api returns 404:Not Found, so err gets NOT propagated

        # _folder_items() does not support file names, host api will erroneously fetch file content and throw json
        assert con_pkg._folder_items('manage.py') is None
        assert con_pkg.error_message                        # json() error will get propagated to caller
        con_pkg.error_message = ""                          # clear con_pkg instance error


@skip_gitlab_ci  # skip on gitlab because of missing remote repository user account token
class TestHostRunningOnlyLocallyWithPatchedSkipper:
    # with con_pkg.skip_enter_folder patched by deployed_code_file() or find_project_files()
    def test_deployed_code_files(self, con_pkg):
        con_pkg.error_message = ""                          # clear con_pkg instance error from last test method

        assert con_pkg.deployed_code_files({os.path.join(TEST_PROJECT_NAME, '**', '*.py')}) == {pkg0_ini_path}
        assert con_pkg.error_message == ""

        found_paths = con_pkg.deployed_code_files(['*/**/media*/*'])
        assert con_pkg.error_message == ""
        assert found_paths == set()                         # there are no deep folders with media*

        found_paths = con_pkg.deployed_code_files(['**/migrations/' + mig_file_name])
        assert con_pkg.error_message == ""
        assert found_paths == {mig_file_path}

        found_paths = con_pkg.deployed_code_files(['*/*/**/migrations/*'])
        assert con_pkg.error_message == ""
        assert found_paths == {mig_file_path}               # migrations folders are always deeper (not on project root)

        found_paths = con_pkg.deployed_code_files(['*/*/*/**/migrations/*'])
        assert con_pkg.error_message == ""
        assert found_paths == set()                         # .. but not that deep in the test project

        found_paths = con_pkg.deployed_code_files(['**/static/*'], skip_file_path=lambda fp: fp.startswith('static/'))
        assert con_pkg.error_message == ""
        assert found_paths == {pkg0_static_file, pkg2_static_file}  # static_ini_file  get excluded

        found_paths = con_pkg.deployed_code_files(['**/static/*'],
                                                  skip_file_path=lambda _: _.startswith(f'{TEST_PROJECT_NAME}/static/'))
        assert con_pkg.error_message == ""
        assert found_paths == {static_ini_file, pkg2_static_file}   # pkg0_static_file get excluded

    def test_find_project_files(self, con_pkg):
        con_pkg.error_message = ""                          # clear con_pkg instance error from previous test method

        found_paths = con_pkg.find_project_files()          # search files in the current working dir (project root)
        assert con_pkg.error_message == ""
        assert found_paths == set(_ for _ in all_file_paths if '/' not in _)

        assert found_paths == con_pkg.find_project_files('*')

        found_paths = con_pkg.find_project_files(f'{pkg2_name}/**/*')
        assert con_pkg.error_message == ""
        assert found_paths == mig_pkg_paths | {mig_file_path, pkg2_static_file}

        assert con_pkg.find_project_files("not_existing_pkg_root_file_name") == set()  # no test error
        assert con_pkg.error_message == ""
        assert isinstance(con_pkg.error_message, str)

        def _skippa1(_):
            return sub_file_name not in _
        found_paths = con_pkg.find_project_files('**/*', skip_file_path=_skippa1)
        assert con_pkg.error_message == ""
        assert found_paths == set()     # because the folders pkg2_name+sub_dir_path will be skipped; see next test case

        def _skippa2(_):
            return _ != f'{pkg2_name}/.' and _ != f'{sub_dir_path}/.' and sub_file_name not in _
        found_paths = con_pkg.find_project_files('**/*', skip_file_path=_skippa2)
        assert con_pkg.error_message == ""
        assert found_paths == {sub_file_path}

    def test_find_project_files_error(self, con_pkg):
        con_pkg.error_message = ""                          # clear con_pkg instance error from last test method

        tst_err_msg = "test error message"

        def _raise_json_err(_content_to_json):
            raise Exception(tst_err_msg)
        with patch('requests.Response.json', new=_raise_json_err):
            assert con_pkg.find_project_files('*') is None  # simulate broken response.content for coverage
        assert tst_err_msg in con_pkg.error_message

        con_pkg.error_message = ""                          # clear err to allow further con_pkg._request() calls

        # coverage: patch requests.api.request to patch requests.get, which is not patchable because it is set to the
        # method parameter of PythonanywhereApi._request(), to test error propagation from recursive
        # find_project_files() calls
        tst_err_msg = "tst err message"

        def _raise_requests_get_err(*_args, **_kwargs):
            if sub_dir_path in _args[1]:                    # _args[1] contains first requests.get argument (url)
                return Mock()                               # simulate error response
            else:
                return requests.request(*_args, **_kwargs)
        # with patch('requests.request', )                          doesn't work
        # even patch('ae.pythonanywhere.requests.api.get', )        doesn't work
        with patch('requests.api.request', new=_raise_requests_get_err):
            assert con_pkg.find_project_files('*/**') is None  # error from deeper recursion level get propagated
            assert con_pkg.find_project_files('**/*') is None  # error from deeper recursion level get propagated
        assert sub_dir_path in con_pkg.error_message

        con_pkg.error_message = ""                          # clear con_pkg instance error
