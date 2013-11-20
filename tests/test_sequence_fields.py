from frostbite_wire.utils import integer_to_sequence_fields, SequenceFields

sf = SequenceFields(100, is_client=True, is_response=False)

def test_sequence_fields_type():
    assert sf.sequence_number == 100
    assert sf.is_client
    assert not sf.is_response
    assert sf.to_int() == 2147483748

def test_integer_conversion():
    recomputed_sf = integer_to_sequence_fields(sf.to_int())
    assert sf.sequence_number == recomputed_sf.sequence_number
    assert sf.is_client == recomputed_sf.is_client
    assert sf.is_response == recomputed_sf.is_response
