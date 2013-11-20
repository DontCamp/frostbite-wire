from ctypes import Structure, c_uint


def integer_to_sequence_fields(integer):
    # Mask off the is_client and is_response bits to get the sequence number
    sequence_number = integer &  ~((1 << 30) + (1 << 31))
    # Then inspect those bits directly to get the flag values
    is_response = integer >> 30 & 1
    is_client = integer >> 31 & 1
    return SequenceFields(sequence_number, is_response, is_client)


class SequenceFields(Structure):
    """Structure representing a frostbite packet's first 4 bytes

    bits 0-29 are the sequence number (30 bits wide),
    bits 30 and 31 are 0/1 flags

    """
    _fields_ = (
        ('sequence_number', c_uint, 30),
        ('is_response', c_uint, 1),
        ('is_client', c_uint, 1),
    )

    def to_int(self):
        integer = self.sequence_number
        integer += self.is_response << 30
        integer += self.is_client << 31
        return integer
