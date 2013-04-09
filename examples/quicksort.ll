List quickSort(List l) {
	// Разделить список l на два содрежащих элементы меньше pivot и больше, pivot не должен находиться в l 
	List divide(List l, Element pivot, List low, List high) {
		if empty l {
			return [low, high]
		} elif l[0] < pivot {
			return divide(l[1:], pivot, low + l[0], high)
		} else {
			return divide(l[1:], pivot, low, high + l[0])
		}
	}
	
	if empty l {
		return l
	} else {
		pivot = l[0]
		equals = List(pivot) * count(l, pivot)
		l = l / pivot
		parts = divide(l, pivot, List(), List())
		return quickSort(parts[0]) + equals + quickSort(parts[1])
	}
}

l = [6, 4, 8, 8, 1, 4, 6, 3, 5, 1]

print quickSort(l) == [1, 2, 3, 3, 5, 6, 6, 8, 9]
