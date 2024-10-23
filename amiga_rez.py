import io
from struct import unpack, unpack_from
from bisect import bisect_left

__all__ = ['AmigaResource']


class ResourceType:
	__slots__ = '_type', '_children'

	def __init__(self, type, children):
		self._type = type
		# self._parent = parent
		self._children = children

	def type(self): return self._type
	def resource_type(self): return self._type


	def LoadResource(self, rID):

		i = bisect_left(self._children, rId)
		if i == len(self._children): return None
		r = self._children[i]
		if r._id != id: return None

		return r



	def __iter__(self):
		return self._children.__iter__()

	def __len__(self):
		return len(self._children)

	def __getitem__(self, index):
		return self._children[index]

	@staticmethod
	def _key(other):
		if type(other) == bytes: return other
		if type(other) == str: return other.encode('ascii')
		if type(other) == ResourceType: return other._type
		return None

	def __lt__(self, other):
		a = self._type ; b = self.key(other)
		if b == None: return super().__lt__(other)
		return a < b

	def __gt__(self, other):
		a = self._type ; b = self.key(other)
		if b == None: return super().__gt__(other)
		return a > b

	def __eq__(self, other):
		a = self._type ; b = self.key(other)
		if b == None: return super().__eq__(other)
		return a == b


class Resource:
	__slots__ = '_id', '_data'

	def __init__(self, id, data):
		self._id = id
		self._data = data

	def data(self): return self._data
	def id(self): return self._id
	def resource_id(self): return self._id

	def __bytes__(self):
		return bytes(self._data)

	def __len__(self):
		return len(self._data)

	def __getitem__(self, index):
		return self._data[index]

	@staticmethod
	def _key(other):
		if type(other) == int: return other
		if type(other) == Resource: return other._id
		return None

	def __lt__(self, other):
		a = self._id; b = self._key(other)
		if b == None: return super().__lt__(other)
		return a < b

	def __gt__(self, other):
		a = self._id; b = self._key(other)
		if b == None: return super().__gt__(other)
		return a > b

	def __eq__(self, other):
		a = self._id; b = self._key(other)
		if b == None: return super().__eq__(other)
		return a == b


class AmigaResource:
	"""docstring for AmigaResource"""
	__slots__ = '_types', 

	def __init__(self, file):
		data = None
		with io.open(file, "rb") as f:
			data = f.read()

		m = memoryview(data)

		flags, offset1, offset2 = unpack_from(">III", data, offset = 0)
		if flags != 0x00000100: raise Exception("bad flag")

		# 
		offset = offset1 + 0x1c
		type_count,  = unpack_from(">H", data, offset=offset)
		type_count += 1

		tt = []

		offset += 2
		resource_count = 0
		for n in range(0, type_count):
			type, count, pos = unpack_from(">4sHH", data, offset=offset) ; offset += 8
			count += 1
			resource_count += count

			tt.append( (type, count) )



		types = []
		for (type, count) in tt:
			children = []

			for n in range(0, count):
				# 12 bytes, 3rd word unknown
				rid, _, addr, _ = unpack_from(">HHII", data, offset=offset) ; offset += 12
				addr &= 0x00ffffff # high byte flags?
				addr += 256

				rlen, = unpack_from(">I", data, addr)

				addr += 4
				children.append(
					Resource(rid, m[addr:addr+rlen])
				)

			children.sort(key=lambda x: x.resource_id())
			types.append(
				ResourceType(type, children)
			)
		types.sort(key=lambda x: x.resource_type())
		self._types = types


	def LoadResource(self, rType, rId):
		if type(rType) == str:
			rType = type.encode('ascii')
		i = bisect_left(self._types, rType)
		if i == len(self._types): return None
		t = self._types[i]
		if t._type != rType: return None

		return t.LoadResource(rID)


	def __len__(self):
		"""Returns number of resource types"""
		return len(self._types)

	def __iter__(self):
		return iter(self._types)


	def __getitem__(self, index):
		if type(index) == int: return self._types[index]
		if type(index) == str: index = index.encode('ascii')
		if type(index) != bytes: raise TypeError('index must be integer, string, or bytes')

		rType = index
		i = bisect_left(self._types, rType)
		if i == len(self._types): return None
		t = self._types[i]
		if t._type != rType: return None
		return t



