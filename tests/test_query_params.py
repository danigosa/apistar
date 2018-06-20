import test

import pytest

from apistar import App, ASyncApp, Route, validators
from apistar.types import Type
from apistar.validators import Boolean, Integer, Number, String

md_description = """
_Some_ **formatted** `description`

#### Pending:

- [x] Finish my changes
- [x] Push my commits to GitHub
- [ ] Open a pull request

#### Ordered list:

1. Everything
1. in
1. order

#### Unordered list:

*  Some inline `Code`
*  Some _previewed_ code in list:
   <pre class="highlight">
   while True:
        print('This is taking forever')</pre>

#### Some outer code:

<pre class="highlight">print("Hellow world!")</pre>

"""


class Sometype(Type):
    a = validators.String(description=md_description)
    b = Integer(allow_null=True)
    f = Number()
    c = Boolean()


def get_do_nothing(
    p: Integer(allow_null=False, description="`Integer` **path** parameter"),
    a,
    s: str,
    f: float,
    n: Number(),
    b: Boolean(),
    d: String(description="This is **not required** _parameter_", allow_null=True),
) -> validators.String:
    """_Modest_ **formatted** `documentation` <hr>"""
    return f"I did: {p}|{a}|{s}|{f}|{n}|{b}|{d}"


def post_do_nothing(
    p: int,
    a,
    b: Boolean(description="Just gimme a **true** _or_ **false**"),
    i: Integer(description="**Query** _parameter_"),
    d: String(allow_null=True),
    data: Sometype,
) -> validators.String:
    """
_Some_ **formatted** `documentation` using [Apistar](https://github.com/encode/apistar)

For GET doc go to [get_test](#get_test)

![Lets go](https://pic.chinesefontdesign.com/uploads/2016/08/chinesefontdesign.com_2016-08-19_17-58-43.gif)

### Pending:

- [x] Finish my changes
- [ ] Push my commits to GitHub
- [ ] Open a pull request

### Ordered list:

1. Everything
1. in
1. order

### Unordered list:

*  Some inline `Code`
*  Some _previewed_ code in list:
   <pre class="highlight">
   while True:
        print('This is taking forever')</pre>


### Some outer code:

<pre class="highlight">print("Hellow world!")</pre>

<hr>
    """
    return f"I did: {p}|{a}|{b}|{d}|{i}|{dict(data)}"


routes = [
    Route(
        "/{p}",
        name="post_test",
        method="POST",
        handler=post_do_nothing,
        documented=True,
        encoding="some/encoding",
    ),
    Route(
        "/{p}",
        name="get_test",
        method="GET",
        handler=get_do_nothing,
        documented=True,
        encoding="some/encoding",
    ),
]

app = App(routes=routes)


@pytest.fixture(scope="module", params=["wsgi", "asgi"])
def client(request):
    if request.param == "asgi":
        app = ASyncApp(routes=routes)
    else:
        app = App(routes=routes)
    return test.TestClient(app)


# Good
def test_get_ok(client):
    response = client.get("/1?a=2&b=true&s=s&i=4&f=1.0&n=2.0")
    assert response.status_code == 200
    assert response.content == b"I did: None|2|s|1.0|2.0|True|None"


def test_post_ok(client):
    response = client.post(
        "/1?a=2&b=true&s=s&i=4&f=1.0", json={"a": "a", "b": 1, "f": 2.0, "c": True}
    )
    assert response.status_code == 200
    assert (
        response.content
        == b"I did: 1|2|True|None|4|{'a': 'a', 'b': 1, 'f': 2.0, 'c': True}"
    )


# Bad
def test_get_nok(client):
    response = client.get("/1?a=2&b=true&s=s&i=4&f=1.0")
    assert response.status_code == 400
    assert response.content == b'{"n":"The \\"n\\" field is required."}'


def test_post_nok(client):
    response = client.post(
        "/1?a=2&b=true&s=s&f=1.0&n=2.0", json={"a": "a", "b": 1, "f": 2.0, "c": True}
    )
    assert response.status_code == 400
    assert response.content == b'{"i":"The \\"i\\" field is required."}'
