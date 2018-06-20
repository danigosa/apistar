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


def markdown_paragraph(md: str, description=False) -> str:
    if md is None or md == "None":
        return ""
    print(f"Markdown: ({type(md)}){md}")
    md = markdown(md)
    if description:
        html = "<div class=\"description\">" + md + "</div>"
    else:
        html = md
    print(f"After md html: {html}")
    return html


def strip_html_tags(html) -> str:
    print(f"Before stripping: {html}")
    soup = BeautifulSoup(html)
    print(f"After stripping: {html}")
    return soup.get_text()
