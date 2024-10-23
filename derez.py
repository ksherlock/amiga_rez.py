from amiga_rez import AmigaResource

from struct import unpack_from
import sys

Decode = {
	0x09: "\\t",
	0x0a: "\\n",
	0x0d: "\\r",
	0x92: "\\",
	0x34: "\\\"",
}


# splits into c-strings, retaining the 0x00
def split_cstr_list(m):


	count, = unpack_from(">H", m)

	m = m[2:]

	rv = []
	pos = 0
	for ix, c in enumerate(m):
		if c == 0:
			rv.append(m[pos:ix+1])
			pos = ix+1
	if pos != len(m): return None
	if count != len(rv): return None

	return rv

def format_str(data):

	rv = []


	l = 0
	buffer = []
	hardsplit = False
	softsplit = False
	for c in data:
		if c in Decode:
			buffer.append(Decode[c])
			l += 2
			hardsplit = c in (0x0a, 0x0d, 0x00)
			softsplit = c == 0x09
		elif c >= 0x20 and c <= 0x7e:
			buffer.append(chr(c))
			l += 1
			softsplit = c in b' ,.!?'
		else:
			buffer.append("\\${:02x}".format(c))
			l += 4

		if hardsplit or l >= 70 or (l >= 64 and softsplit):
			rv.append(''.join(buffer))
			buffer = []
			l = 0
			hardsplit = False
			softsplit = False

	if l>0:
		rv.append(''.join(buffer))

	return rv

def is_cstr(x):
	return len(x) > 0 and x[-1] == 0x00

def hexdump(data):
	l = len(data)
	for n in range(0, (l+15) // 16):
		dd = data[n*16:n*16+16]
		s = dd.hex(' ', -8)
		print('    $"',s,'"', sep='')


def dump(type, id, data):

	print("resource '{}' (${:x}) {{".format(type.decode('ascii'), id))

	if type == b'CStr':
		if (is_cstr(data)):
			txt = format_str(data[:-1])
			for x in txt:
				print('    "', x, '"',sep='')
		else:
			hexdump(data)
	elif type == b'CSt#':
		# n c-strings.
		tmp = split_cstr_list(data)
		# verify...
		if tmp and not all([is_cstr(x) for x in tmp]): tmp = None
		if tmp:
			l1 = len(tmp)-1
			# extra work since we also want to insert a , 
			for ix1, s1 in enumerate(tmp):
				strings = format_str(s1[:-1])
				l2 = len(strings)-1
				for ix2, s2 in enumerate(strings):
					comma = ''
					if ix2 == l2 and ix1 != l1: comma = ','
					print('    "', s2, '"', comma, sep='')
		else:
			hexdump(data)


	else:
		hexdump(data)


	print("}\n")



for arg in sys.argv[1:]:
	rf = AmigaResource(arg)

	for t in rf:
		for r in t:
			dump(t.type(), r.id(), r.data())

