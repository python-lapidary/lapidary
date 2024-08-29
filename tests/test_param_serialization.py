from lapidary.runtime.model.param_serialization import FormExplode, SimpleMultimap, SimpleString

# simple no-explode, multimap version


def test_simple_multimap_string():
    assert SimpleMultimap.serialize_scalar('name', 'value') == [('name', 'value')]


def test_simple_multimap_scalar_none():
    assert list(SimpleMultimap.serialize_scalar('name', None)) == []


def test_simple_multimap_none():
    assert list(SimpleMultimap.serialize('name', None)) == []


def test_simple_multimap_int():
    assert SimpleMultimap.serialize_scalar('name', 1) == [('name', '1')]


def test_simple_multimap_list():
    assert SimpleMultimap.serialize_array('name', ['value', 1]) == [('name', 'value,1')]


def test_simple_multimap_object():
    assert SimpleMultimap.serialize_object('name', {'key1': 'value', 'key2': 1}) == [('name', 'key1,value,key2,1')]


def test_deser_simple_multimap_str():
    assert SimpleMultimap.deserialize_scalar('value', str) == 'value'


def test_deser_simple_multimap_str_generic():
    assert SimpleMultimap.deserialize('value', str) == 'value'


def test_deser_simple_multimap_array():
    assert SimpleMultimap.deserialize_array('value1,value2', list[str]) == ['value1', 'value2']


def test_deser_simple_multimap_array_generic():
    assert SimpleMultimap.deserialize('value1,value2', list[str]) == ['value1', 'value2']


def test_deser_simple_multimap_object():
    assert SimpleMultimap.deserialize_object('name1,value1,name2,value2', dict[str, str]) == {'name1': 'value1', 'name2': 'value2'}


def test_deser_simple_multimap_object_generic():
    assert SimpleMultimap.deserialize('name1,value1,name2,value2', dict[str, str]) == {'name1': 'value1', 'name2': 'value2'}


# simple no-explode, string version


def test_simple_string_string():
    assert SimpleString.serialize_scalar('name', 'value') == 'value'


def test_simple_string_int():
    assert SimpleString.serialize_scalar('name', 1) == '1'


def test_simple_string_list():
    assert SimpleString.serialize_array('name', ['value', 1]) == 'value,1'


def test_simple_string_object():
    assert SimpleString.serialize_object('name', {'key1': 'value', 'key2': 1}) == 'key1,value,key2,1'


# form explode (multimap only)


def test_form_explode_string():
    assert FormExplode.serialize_scalar('name', 'value') == [('name', 'value')]


def test_form_explode_int():
    assert FormExplode.serialize_scalar('name', 1) == [('name', '1')]


def test_form_explode_list():
    assert list(FormExplode.serialize_array('name', ['value', 1])) == [('name', 'value'), ('name', '1')]


def test_form_explode_object():
    assert list(FormExplode.serialize_object('name', {'key1': 'value', 'key2': 1})) == [('key1', 'value'), ('key2', '1')]
