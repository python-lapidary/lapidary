from lapidary.runtime import mime
from lapidary.runtime.http_consts import MIME_JSON


def test_find_mime():
    resolved = mime.find_mime([MIME_JSON], 'application/json; charset=utf-8')
    assert resolved == MIME_JSON
