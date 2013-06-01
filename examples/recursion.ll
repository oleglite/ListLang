i = 0
Element f() {
	global i
	i = i + 1
	print i
	if i < 5 {
		f()
	}
}

f()