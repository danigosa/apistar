import inspect
import re
import typing

from gfm import markdown

from apistar import http, types, validators
from apistar.document import Document, Field, Link, Response, Section
from apistar.utils import remove_markdown_paragraph, strip_html_tags
from apistar.validators import Validator


class Route:
    def __init__(
            self, url, method, handler,
            name=None, documented=True, standalone=False, encoding=None
    ):
        self.url = url
        self.method = method
        self.handler = handler
        self.name = name or handler.__name__
        self.documented = documented
        self.standalone = standalone
        self.encoding = encoding
        self.link = self.generate_link(url, method, handler, self.name)

    def generate_link(self, url, method, handler, name):
        fields = self.generate_fields(url, method, handler)
        if self.encoding is None and any([f.location == 'body' for f in fields]):
            _encoding = 'application/json'
        else:
            _encoding = self.encoding
        return Link(
            url=url,
            method=method,
            name=name,
            encoding=_encoding,
            fields=fields,
            response=self.generate_response(handler, _encoding),
            description=remove_markdown_paragraph(
                markdown(str(handler.__doc__))
            )
        )

    def generate_fields(self, url, method, handler):
        fields = []
        path_names = [
            item.strip('{}').lstrip('+') for item in re.findall('{[^}]*}', url)
        ]
        parameters = inspect.signature(handler).parameters
        for name, param in parameters.items():
            if name in path_names:
                if isinstance(param.annotation, Validator):
                    if param.annotation.description:
                        param.annotation.description = remove_markdown_paragraph(
                            markdown(param.annotation.description)
                        )
                    else:
                        param.annotation.description = remove_markdown_paragraph(
                            markdown("`{}`".format(param.annotation.__class__.__name__))
                        )
                    schema = param.annotation
                else:
                    if param.default is param.empty:
                        kwargs = {}
                    elif param.default is None:
                        kwargs = {'default': None}
                    else:
                        kwargs = {'default': param.default}
                    kwargs.update({'allow_null': False})
                    schema = {
                        param.empty: None,
                        int: validators.Integer(
                            description=remove_markdown_paragraph(markdown("`Integer`")),
                            **kwargs
                        ),
                        float: validators.Number(
                            description=remove_markdown_paragraph(markdown("`Number`")),
                            **kwargs
                        ),
                        str: validators.String(
                            description=remove_markdown_paragraph(markdown("`String`")),
                            **kwargs
                        ),
                    }[param.annotation]
                field = Field(name=name, location='path', schema=schema)
                fields.append(field)

            elif param.annotation in (param.empty, int, float, bool, str, http.QueryParam):
                if param.default is param.empty:
                    kwargs = {}
                elif param.default is None:
                    kwargs = {'default': None, 'allow_null': True}
                else:
                    kwargs = {'default': param.default}
                schema = {
                    param.empty: None,
                    int: validators.Integer(
                        description=remove_markdown_paragraph(markdown("`Integer`")),
                        **kwargs
                    ),
                    float: validators.Number(
                        description=remove_markdown_paragraph(markdown("`Number`")),
                        **kwargs
                    ),
                    bool: validators.Boolean(
                        description=remove_markdown_paragraph(markdown("`Boolean`")),
                        **kwargs
                    ),
                    str: validators.String(
                        description=remove_markdown_paragraph(markdown("`String`")),
                        **kwargs
                    ),
                    http.QueryParam: validators.String(
                        description=remove_markdown_paragraph(markdown("`String`")),
                        **kwargs
                    ),
                }[param.annotation]
                field = Field(
                    name=name, location='query', schema=schema
                )
                fields.append(field)
            elif isinstance(param.annotation, Validator):
                if param.annotation.description:
                    param.annotation.description = remove_markdown_paragraph(
                        markdown(param.annotation.description)
                    )
                else:
                    param.annotation.description = remove_markdown_paragraph(
                        markdown("`{}`".format(param.annotation.__class__.__name__))
                    )
                field = Field(
                    name=name, location='query', schema=param.annotation,
                    required=not param.annotation.allow_null
                )
                fields.append(field)
            elif issubclass(param.annotation, types.Type):
                if method in ('GET', 'DELETE'):
                    for _name, validator in param.annotation.validator.properties.items():
                        if validator.description:
                            validator.description = remove_markdown_paragraph(
                                markdown(validator.description)
                            )
                        else:
                            validator.description = remove_markdown_paragraph(
                                markdown("`{}`".format(validator.__class__.__name__))
                            )
                        field = Field(name=_name, location='query', schema=validator)
                        fields.append(field)
                else:
                    for _, validator in param.annotation.validator.properties.items():
                        if validator.description:
                            validator.description = remove_markdown_paragraph(
                                markdown(validator.description)
                            )
                        else:
                            validator.description = remove_markdown_paragraph(
                                markdown("`{}`".format(validator.__class__.__name__))
                            )
                    field = Field(
                        name=name, location='body',
                        schema=param.annotation.validator,
                        required=not param.annotation.validator.allow_null
                    )
                    fields.append(field)
        return fields

    def generate_response(self, handler, encoding):
        annotation = inspect.signature(handler).return_annotation
        annotation = self.coerce_generics(annotation)

        if not (issubclass(annotation, types.Type) or isinstance(annotation, validators.Validator)):
            return None

        return Response(encoding=encoding, status_code=200, schema=annotation)

    def coerce_generics(self, annotation):
        if (
                isinstance(annotation, type) and
                issubclass(annotation, typing.List) and
                getattr(annotation, '__args__', None) and
                issubclass(annotation.__args__[0], types.Type)
        ):
            return validators.Array(items=annotation.__args__[0])
        return annotation


class Include:
    def __init__(self, url, name, routes, documented=True):
        self.url = url
        self.name = name
        self.routes = routes
        self.documented = documented
        self.section = self.generate_section(routes, name)

    def generate_section(self, routes, name):
        content = self.generate_content(routes)
        return Section(name=name, content=content)

    def generate_content(self, routes):
        content = []
        for item in routes:
            if isinstance(item, Route):
                if item.link is not None:
                    content.append(item.link)
            elif isinstance(item, Section):
                if item.section is not None:
                    content.append(item.section)
        return content


def generate_document(routes):
    content = []
    for item in routes:
        if isinstance(item, Route) and item.documented:
            content.append(item.link)
        elif isinstance(item, Include) and item.documented:
            content.append(item.section)
            for link in item.section.get_links():
                link.url = item.url + link.url
    return Document(content=content)
