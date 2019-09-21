from __future__ import absolute_import, division, print_function, unicode_literals

from collections import defaultdict
import inspect
import os
import re
import sys

from bs4 import BeautifulSoup
import requests

sys.path.append(os.path.join(sys.path[0], ".."))

import canvasapi  # noqa

DOCS_ROOT_URL = "https://canvas.instructure.com/doc/api"


def check_coverage():
    """
    Check endpoints for coverage
    """
    endpoints = get_endpoints()
    get_doc_links(endpoints)


def get_endpoints():
    """
    Traverse Canvas Swagger docs, getting a list of all endpoints.

    :returns: Dictionary where each key is a Canvas docs page
    :rtype: dict
    """
    swagger = requests.get(DOCS_ROOT_URL + "/api-docs.json")
    page_list = swagger.json().get("apis", [])

    endpoints = dict()

    for page_data in page_list:
        print(page_data["description"])
        page = requests.get(DOCS_ROOT_URL + '/' + page_data["path"])
        api_list = page.json().get("apis", [])
        endpoints[page_data["description"]] = {
            "page": page_data["path"],
            "endpoints": defaultdict(list),
        }
        for api in api_list:
            method = api["operations"][0]["method"]
            url = "/api" + convert_path_string(api["path"])
            summary = api["operations"][0]["summary"]
            # print(
            #     "\t{summary} {method} {url}".format(
            #         summary=summary, method=method, url=url
            #     )
            # )
            new_endpoint = {'method': method, 'path': url}
            # print(new_endpoint)
            endpoints[page_data["description"]]["endpoints"][summary].append(
                new_endpoint
            )

    return endpoints


def get_doc_links(endpoints):
    """
    Add documentation links to endpoints.

    :rtype: dict
    """
    response = requests.get(DOCS_ROOT_URL + "/all_resources.html")
    soup = BeautifulSoup(response.content, "html.parser")

    for group_name, group_details in endpoints.items():
        page = group_details['page'].replace('.json', '.html')

        method_docs = soup.find(
            "h2", {"data-subtopic": "API Token Scopes"}, class_="api_method_name"
        )

        for endpoint_description, endpoint_list in group_details['endpoints'].items():
            for endpoint in endpoint_list:
                endpoint['docs_url'] = DOCS_ROOT_URL + page + '#' + method_docs.attrs['name']

    return endpoints


def get_methods():
    """
    """
    for _, module in inspect.getmembers(canvasapi, inspect.ismodule):
        print(module.__name__)
        for class_name, theclass in inspect.getmembers(module, inspect.isclass):
            # Only process classes in this module
            if inspect.getmodule(theclass).__name__ != module.__name__:
                continue

            for func_name, func in inspect.getmembers(theclass, inspect.isfunction):
                # Only add function if it is part of this class.
                # Get function's class name from qualified name.
                print(func.__qualname__)
                call_lines = re.findall(
                    '`(POST|GET|PUT|PATCH|DELETE)([^<]*)<([^>]*)>`_',
                    inspect.getdoc(func)
                )
                import pdb; pdb.set_trace()

            # error_count += check_alphabetical(
            #     functions, theclass.__module__, theclass.__name__
            # )


def convert_path_string(path):
    """
    Convert the path string in the swagger JSON to match the pattern in
    the Canvas docs and our docstrings.

    Recursive call to replace multiple instances
    """
    match = re.search(r"{(.+?)}", path)

    if match is None:
        return path

    return convert_path_string(path.replace(match.group(0), ":" + match.group(1)))


if __name__ == "__main__":
    # check_coverage()
    get_methods()
    sys.exit(0)
