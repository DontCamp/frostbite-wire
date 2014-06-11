from struct import pack, pack_into, unpack_from


class Packet(object):
    # _buffer holds this Packet's state, pre-seed it with dummy values
    # to simplify altering the state later
    _buffer = bytearray(pack('12s', '\x00' * 12))

    def __init__(self, sequence_number, is_response=False, is_client=True, words=''):
        self.sequence_number = sequence_number
        self.is_response = is_response
        self.is_client = is_client
        self.words = words

    @classmethod
    def from_buffer(cls, buf):
        # Since the entire state of a Packet is in its _buffer,
        # create an uninitialized instance with _new_ and inject the
        # passed-in buffer
        instance = cls.__new__(cls)
        instance._buffer = buf
        return instance

    def to_buffer(self):
        return self._buffer

    def __len__(self):
        return self._size

    @property
    def _sequence(self):
        return int(unpack_from('I', self._buffer, 0)[0])

    @_sequence.setter
    def _sequence(self, seq_num_with_flags):
        pack_into('I', self._buffer, 0, seq_num_with_flags)

    @property
    def sequence_number(self):
        # Sequence number is the int value of the first four bytes
        # with the is response/is_client bits masked off
        return self._sequence & ~((self.is_response << 30) + (self.is_client << 31))

    @sequence_number.setter
    def sequence_number(self, seq_num):
        # Opposite of the getter, add the flag bits back onto the sequence number int
        # Woe be unto those that use ints bigger than 32 bits for their sequence numbers
        self._sequence = seq_num | ((self.is_response << 30) + (self.is_client << 31))

    @property
    def is_response(self):
        return self._get_bit_truthiness(30)

    @is_response.setter
    def is_response(self, is_response):
        self._set_bit(is_response, 30)

    @property
    def is_client(self):
        return self._get_bit_truthiness(31)

    @is_client.setter
    def is_client(self, is_client):
        self._set_bit(is_client, 31)

    @property
    def size(self):
        # Public getter for size, but no public setter
        return self._size

    @property
    def _size(self):
        return int(unpack_from('I', self._buffer, 4)[0])

    @_size.setter
    def _size(self, size):
        pack_into('I', self._buffer, 4, int(size))

    @property
    def num_words(self):
        return int(unpack_from('I', self._buffer, 8)[0])

    @property
    def words(self):
        words = list()
        seen_words, num_words = 0, self.num_words
        # Start the word pointer after the int32 flags (byte 12),
        # and advance the pointer as appropriate for each step
        word_pointer = 12
        while seen_words < num_words:
            word_len = int(unpack_from('I', self._buffer, word_pointer)[0])
            word_pointer += 4
            word = unpack_from('%ds' % word_len, self._buffer, word_pointer)[0]
            word_pointer += word_len
            # TODO: AssertionError here should be replaced with a more
            # specific exception class
            assert unpack_from('s', self._buffer, word_pointer)[0] == '\x00'
            word_pointer += 1
            words.append(word)
            seen_words += 1

        return words

    @words.setter
    def words(self, words):
        if isinstance(words, basestring):
            words = words.split()
        num_words = len(words)
        pack_into('I', self._buffer, 8, num_words)

        words_buf = bytearray()
        for word in words:
            word_len = len(word)
            words_buf.extend(pack('I%dsb' % word_len, word_len, word, 0))

        # Strip off any old words that may have been in the buffer
        # and append the new words buffer to it
        self._buffer = self._buffer[:12] + words_buf
        self._size = len(self._buffer)

    def _set_bit(self, truthy, bit_offset):
        int_bit = 1 << bit_offset
        if truthy:
            self._sequence |= int_bit
        else:
            self._sequence &= ~int_bit

    def _get_bit_truthiness(self, bit_offset):
        return bool(self._sequence & (1 << bit_offset))
