import json

from bs4 import BeautifulSoup
from gfm import markdown

from apistar import codecs
from apistar.types import Type


class _CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Type):
            return dict(obj)
        return json.JSONEncoder.default(self, obj)


def encode_json(data, indent=False):
    kwargs = {"ensure_ascii": False, "allow_nan": False, "cls": _CustomEncoder}
    if indent:
        kwargs.update({"indent": None, "separators": (",", ":")})
    else:
        kwargs.update({"indent": 4, "separators": (",", ": ")})
    return json.dumps(data, **kwargs).encode("utf-8")


def encode_jsonschema(validator, to_data_structure=False):
    codec = codecs.JSONSchemaCodec()
    return codec.encode(validator, to_data_structure=to_data_structure)


def markdown_paragraph(md: str) -> str:
    html = markdown(md)
    soup = BeautifulSoup(html, 'html5lib')
    return soup.prettify()


# class HTMLStripper(HTMLParser):
#     def __init__(self):
#         self.reset()
#         self.strict = False
#         self.convert_charrefs = True
#         self.fed = []
#
#     def handle_data(self, d):
#         self.fed.append(d)
#
#     def get_data(self):
#         return "".join(self.fed)


def strip_html_tags(html):
    # s = HTMLStripper()
    # s.feed(html)
    return html
