"""
PythonAnywhere Web API Client
=============================

this portion provides the class :class:`PythonanywhereApip . an instance of this class are used as a
client to interact with the PythonAnywhere web server API, which gives you access on web servers like
``www.pythonanywhere.com`` and ``eu.pythonanywhere.com``, for managing and inspecting deployed project files.

initialize an API client with connection details for a specific project passed as arguments to the class
constructor::

* the :paramref:`~PythonanywhereApi.web_domain` argument expects the used remote web host domain address
  (e.g., ``eu.pythonanywhere.com``).
* the remote connection username in the :paramref:`~PythonanywhereApi.web_user` argument, and
* the personal user credential token string in :paramref:`~PythonanywhereApi.web_token`.
* the :paramref:`~PythonanywhereApi.project_name` argument gets the name of the web project package,
  which is also used as the sub-folder name, situated underneath of the remote user's home directory.

the :meth:`~PythonanywhereApi.find_project_files` method of a client instance searches for files within
the deployed project directory. this method is designed to overcome the PythonAnywhere API limit of 1000
files per request by recursively calling the API on subdirectories (see `API: File Storage`_).
its arguments are::

* :paramref:`~PythonanywhereApi.path_mask`: the file mask including relative path to the package project root to
  be searched. passing an empty string (the default) returns all files in the project root directory.
* :paramref:`~PythonanywhereApi.collector`: file collector callable (see the class :class:`~ae.paths.Collector`).
* :paramref:`~PythonanywhereApi.skip_file_path`: selector callable that accepts a file/folder path (relative to the
  project root) and returns ``True`` to exclude it from the search result. calls for folders have a ``/.`` suffix.

the :meth:`~PythonanywhereApi.find_project_files` method returns a :class:`set` of file paths relative to the
project root, or ``None`` if an error occurred.


usage examples
--------------

the following examples demonstrate key functionality, including how to initialize
the :class:`PythonanywhereApi` and list deployed files/folders, excluding common
temporary directories::

    from ae.paths import Collector
    from ae.pythonanywhere import PythonanywhereApi

    # 1. initialize the API client
    WEB_DOMAIN = 'www.pythonanywhere.com'
    WEB_USER = 'YourUsername'
    WEB_TOKEN = 'your-secret-token'
    PROJECT_NAME = 'your_django_project'
    api = PythonanywhereApi(WEB_DOMAIN, WEB_USER, WEB_TOKEN, PROJECT_NAME)

    # 2. declare a function to skip e.g. hidden files/folders or common cache, venv and temp files
    def skip_temp_files(path: str) -> bool:
        if path.startswith(('.', '/.')):  # skips hidden files and folders
            return True
        if '__pycache__' in path or '.venv' in path:
            return True
        return False

    # 3. find all project files, excluding temp directories
    all_files = api.find_project_files(path_mask="**/*", skip_file_path=skip_temp_files)

    if api.error_message:
        print(f"Error fetching files: {api.error_message}")
    elif all_files:
        print(f"Found {len(all_files)} files:")
        print("\n".join(sorted(list(all_files))))
    else:
        print("No files found or project directory is empty.")


more useful methods
-------------------

the most useful methods of the :class:`PythonanywhereAPI` class are (check the source code for more):~

* :meth:`~PythonanywhereAPI.deployed_file_content`: determine the file content of a file, deployed to the web server.
* :meth:`~PythonanywhereAPI.deployed_version`: determine the version of the deployed django project package.
* :meth:`~PythonanywhereAPI.deploy_file`: add or update a project file to the web server.
* :meth:`~PythonanywhereAPI.delete_file_or_folder`: delete a file or folder on the web server.

..hint::
    PythonAnywhere File Storage API documents: `https://help.pythonanywhere.com/pages/API/`__

.. hint::
    a similar package can be found at `https://gitlab.com/texperience/pythonanywhereapiclient`_.
"""
import os
import time

from fnmatch import fnmatchcase
from functools import partial
from typing import Any, Callable, Container, Iterable, Optional, Union, cast

import requests

from ae.base import PY_INIT, ErrorMsgMixin                                                  # type: ignore
from ae.paths import Collector, CollYieldItems, SearcherRetType, coll_items                 # type: ignore
from ae.dev_ops import code_version                                                         # type: ignore


__version__ = '0.3.2'


class PythonanywhereApi(ErrorMsgMixin):    # pylint: disable=too-many-instance-attributes
    """ remote host api to a project package on the web hosts eu.pythonanywhere.com and pythonanywhere.com. """
    error_message: str

    def __init__(self, web_domain: str, web_user: str, web_token: str, project_name: str):
        """ initialize web host api and the deployed project package name.

        :param web_domain:      remote web host domain (including subdomains).
        :param web_user:        remote connection username.
        :param web_token:       personal user credential token string on remote host.
        :param project_name:    name of the web project package (and of the sub-folder in the web users home directory).
        """
        super().__init__()

        self.base_url = f"https://{web_domain}/api/v0/user/{web_user}/"
        self.consoles_url_part = "consoles/"
        self.protocol_headers = {'Authorization': f"Token {web_token}"}

        # self.web_domain = web_domain
        self.web_user = web_user
        # self.web_token = web_token

        self.project_name = self._project_name = project_name
        self.skip_enter_folder = lambda item_info: False

    @property
    def project_name(self) -> str:
        """ project main package name string property.

        :getter:                return the currently connected/configured project package name of the web host server.
        :setter:                set/change the currently connected/configured project name of the web host server.
        """
        return self._project_name

    @project_name.setter
    def project_name(self, project_name: str):
        self.pkg_files_url_part = f"files/path/home/{self.web_user}/{project_name}/"
        self._project_name = project_name

    def _folder_items(self, folder_path: str) -> Optional[list[dict[str, str]]]:
        """ determine the files in the specified folder path.

        :param folder_path:     the remote path of the folder to search in.
        :return:                list of found files or None if an error occurred (check self.error_message for error
                                details). each list item contains a dict with the item 'file_path` to keep the absolute
                                path of the found file, and a 'type' item with the file type (like returned by the
                                Pythonanywhere API).
        """
        url_path = self.pkg_files_url_part
        if folder_path:
            url_path += folder_path + '/'

        response = self._request(url_path, f"fetching files in folder {folder_path}")
        if not self.error_message:
            found_file_infos = cast(Optional[dict[str, dict[str, Any]]], self._from_json(response))
            if found_file_infos is not None:        # == not self.error_message:
                return [{'file_path': os.path.join(folder_path, _name), 'type': _info['type']}
                        for _name, _info in found_file_infos.items()]

        if response.status_code == 404:
            self.error_message = ""         # if folder not exists, do not propagate 404:Not Found errors

        return None

    def _from_json(self, response: requests.Response) -> Optional[Union[list[dict[str, Any]],
                                                                        dict[str, dict[str, Any]],
                                                                        dict[str, str]]]:
        """ convert json in response to python type (list/dict).

        :param response:        response from requests to convert into python data type.
        :return:                list|dict of dictionaries|str converted from the response content or None on error.
        """
        try:
            return response.json()
        except Exception as exc:  # pylint: disable=broad-exception-caught # requests.exceptions.JSONDecodeError
            self.error_message = f"{exc} in response.json() call on response content '{response.content!r}'"
            return None

    def _prepare_collector(self, skipper: Callable[[str], bool]) -> Callable[[str], CollYieldItems]:
        """ prepare the file collector.

        :param skipper:         callback receiving a string argument with the file path and returning a boolean
                                True if the file has to be excluded from the file search result.
        :return:                callable receiving a string argument with the file path and returning an Iterable
                                of tuples, to be used as the :paramref:`~ae.paths.Collector.item_collector` argument
                                of the file/folder :class:`~ae.paths.Collector` class.
        """
        def _sel(file_path: str):
            return not skipper(file_path)

        def _det(file_path: str):
            return os.path.splitext(file_path)[1]

        self.skip_enter_folder = skipper

        return partial(coll_items, searcher=self.files_iterator, selector=_sel, type_detector=_det)

    def _request(self, url_path: str, task: str, method: Callable = requests.get, success_codes: Container = (200, 201),
                 **request_kwargs) -> requests.Response:
        """ send a https request specified via the :paramref:`~_request.method` argument and return the response.

        :param url_path:        sub url path to send request to.
        :param task:            string describing the task to archive (used to compile an error message).
        :param method:          requests method (get, post, push, delete, patch, ...).
        :param success_codes:   container of response.status_code success codes.
        :param request_kwargs:  additional request method arguments.
        :return:                request response. if on error occurred then the instance string attribute
                                :attr:`.error_message` contains an error message. if the caller is not checking for
                                errors and not resetting the error message string, then this function will accumulate
                                further errors to :attr:`.error_message`, separated by two new line characters.
        """
        method_call_err_msg = f"requests '{method}' method call failed"
        response = requests.Response()
        response.reason = method_call_err_msg
        response.status_code = 489  # hopefully not clashing with real client error (400...499)
        while True:
            try:
                response = method(f"{self.base_url}{url_path}", headers=self.protocol_headers, **request_kwargs)
                if response.status_code != 429:     # too many requests per minute against host api
                    response.raise_for_status()
                    break
            except (requests.HTTPError, Exception) as ex:   # pylint: disable=broad-exception-caught
                self.error_message = method_call_err_msg + f" (exception={ex})"
                break
            time.sleep(12)

        if response.status_code in success_codes:
            self.error_message = ""
        else:
            self.error_message = (f"request error '{response.status_code}:{response.reason}'"
                                  f" {task} via '{self.base_url}{url_path}'")

        return response

    def available_consoles(self) -> list[dict[str, Any]]:
        """ determine the available consoles.

        :return:                list of available console dictionaries or empty list if an error occurred.
        """
        response = self._request(self.consoles_url_part, "get list of consoles")
        if not self.error_message:
            consoles = self._from_json(response)
            if consoles:
                return cast(list[dict[str, Any]], consoles)
        return []

    def console_execute(self, con_id: int, command: str) -> str:
        """ execute command on server console

        :param con_id:          console id.
        :param command:         command to execute.
        :return:                console output.

        .. note:
            unfortunately the consoles send_input endpoint is not working without a user interaction in a browser;
            post method error 412: "Console not yet started. please load it (or its iframe) in a browser first".
        """
        self._request(f"{self.consoles_url_part}{con_id}/send_input/", f"exec console command '{command}'",
                      method=requests.post, data={'input': command})
        if not self.error_message:
            response = self._request(f"{self.consoles_url_part}{con_id}/get_latest_output/", "get output of command")
            if not self.error_message:
                output = self._from_json(response)
                if isinstance(output, dict) and 'output' in output and isinstance(output['output'], str):
                    # noinspection PyTypeChecker
                    return output['output']
        return ""

    def deployed_code_files(self, path_masks: Iterable[str], skip_file_path: Callable[[str], bool] = lambda _: False
                            ) -> Optional[set[str]]:
        """ determine all deployed code files of given package name deployed to the pythonanywhere server.

        :param path_masks:      root package paths with glob wildcards to collect deployed code files from.
        :param skip_file_path:  called for each found file/folder with the path_mask relative to the package root folder
                                as argument, returning True to exclude the specified item from the returned result set.
                                calls of a folder have a prefix of a slash character followed by a dot (`"/."`) and
                                help to minimize the number of calls against the web server api.
        :return:                set of file paths of the package deployed on the web, relative to the project root
                                or None if an error occurred.
        """
        collector = Collector(item_collector=self._prepare_collector(skip_file_path))
        for item_mask in path_masks:
            if self.find_project_files(item_mask, collector=collector, skip_file_path=skip_file_path) is None:
                return None
        return set(collector.files)

    def deployed_file_content(self, file_path: str) -> Optional[bytes]:
        """ determine the file content of a file deployed to a web server.

        :param file_path:       path of a deployed file relative to the project root.
        :return:                file content as bytes or None if error occurred (check self.error_message).
        """
        response = self._request(self.pkg_files_url_part + file_path, "fetching file content")
        if self.error_message:
            return None
        return response.content

    def deployed_version(self) -> str:
        """ determine the version of a deployed django project package.

        :return:                version string of the package deployed to the web host/server
                                or empty string if package version file or version-in-file not found.
        """
        init_file_content = self.deployed_file_content(os.path.join(self.project_name, PY_INIT))
        return "" if init_file_content is None else code_version(init_file_content)

    def deploy_file(self, file_path: str, file_content: bytes) -> str:
        """ add or update a project file to the web server.

        :param file_path:       path relative to the project root of the file to be deployed (added or updated).
        :param file_content:    file content to deploy/upload.
        :return:                error message if update/add failed else on success an empty string.
        """
        self._request(self.pkg_files_url_part + file_path, f"deploy file '{file_path}'", method=requests.post,
                      files={'content': file_content})
        return self.error_message

    def delete_file_or_folder(self, file_path: str) -> str:
        """ delete a file or folder on the web server.

        :param file_path:       path relative to the project root of the file to be deleted.
        :return:                error message if deletion failed else on success an empty string.
        """
        self._request(self.pkg_files_url_part + file_path, f"deleting file {file_path}", method=requests.delete,
                      success_codes=(204, ))
        return self.error_message

    def files_iterator(self, path_mask: str, level_index: int = 0) -> SearcherRetType:
        """ find files matching the path mask string passed as the :paramref:`~files_iterator.path_mask` argument.

        :param path_mask:       file path pattern/mask with optional wildcards. passing an empty string will return
                                the files of the project/package root directory, as well as passing '.' or '*'.
                                also absolute path masks will be relative to the project root directory. file path mask
                                matches are case-sensitive (done with the function :func:`fnmatch.fnmatchcase`).
        :param level_index:     folder level depth in :paramref:`passed file path mask <files_iterator.path_mask>`
                                to start searching (only specified in recursive call).
        :return:                iterator/generator yielding dicts. each dict has a `file_path` key containing the
                                path string of the found file relative to the project root folder and a `type` key
                                containing the string `'directory'` or `'file'`.
        """
        if path_mask.startswith('/'):
            path_mask = path_mask[1:]
        if path_mask in ('', '.') or path_mask.endswith('/.'):
            path_mask = path_mask[:-1] + '*'    # ae_paths.normalize() is converting empty mask string into '-'
        mask_parts = path_mask.split('/')
        level_count = len(mask_parts)

        while level_index < level_count and '*' not in mask_parts[level_index] and '?' not in mask_parts[level_index]:
            level_index += 1
        if level_index == level_count:          # no wildcards found
            match_index = level_count - 1
            deep_search = False
            file_pattern = mask_parts[-1]
        else:
            match_index = level_index
            deep_search = mask_parts[level_index] == '**'
            if deep_search:
                level_index += 1
            file_pattern = mask_parts[level_index] if level_index < level_count else '*'

        file_infos = self._folder_items('/'.join(mask_parts[:match_index]))
        for file_info in file_infos or ():
            item_path, is_folder = file_info['file_path'], file_info['type'] == 'directory'
            item_name = os.path.basename(item_path)
            matched = fnmatchcase(item_name, file_pattern)
            assert not matched or item_path == '/'.join(mask_parts[:match_index] + [item_name])

            if matched and not is_folder and level_index + 1 >= level_count:
                yield item_path

            elif (matched or deep_search) and is_folder and match_index + int(matched) - int(deep_search) < level_count:
                if not self.skip_enter_folder(item_path + '/.'):
                    deep_parts = (mask_parts[:match_index] + [item_name]     # == file_path == only-folders-path
                                  + (['**'] if deep_search and (not matched or file_pattern in ('*', '**')) else [])
                                  + mask_parts[level_index + int(matched):])
                    yield from self.files_iterator('/'.join(deep_parts), level_index=match_index + 1)

    def find_project_files(self, path_mask: str = '',
                           skip_file_path: Callable[[str], bool] = lambda _: False,
                           collector: Optional[Collector] = None,
                           ) -> Optional[set[str]]:
        """ determine the server files matching the glob pattern provided in :paramref:`~find_project_files.path_mask`.

        not using the files tree api endpoints/function (files/tree/?path=/home/{self.web_user}/{project_name})
        because their response is limited to 1000 files
        (see https://help.pythonanywhere.com/pages/API#apiv0userusernamefilestreepathpath) and e.g. kairos has more
        than 5300 files in its package folder (mainly for django filer and the static files).

        :param path_mask:       file mask including relative path to the package project root to be searched.
                                passing an empty string (the default) returns all files in the package root directory.
        :param skip_file_path:  called for each found file/folder with the path_mask relative to the package root folder
                                as argument, returning True to exclude the specified item from the returned result set.
                                calls of a folder have a prefix of a slash character followed by a dot (`"/."`) and
                                help to minimize the number of calls against the web server api.
        :param collector:       file collector callable.
        :return:                set of file paths of the package deployed on the web, relative to the project root
                                or None if an error occurred. all files underneath a
        """
        if not collector:
            collector = Collector(item_collector=self._prepare_collector(skip_file_path))

        collector.collect(path_mask)
        return None if self.error_message else set(collector.files)
