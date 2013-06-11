// Объединить сортированные списки в сортированный список
define mergeSortedLists(List l1, List l2) {
define quickSort(List l) {
	
	if not l {
		return []
	}
	
	pivot = l[0]
	
	low = []
	high = []
	if len(l) > 1 {
		for x in l[1:len(l)] {
			if x < pivot {
				low = low + x
			} else {
				high = high + x
			}
		}
	}
	
	lesser = quickSort(low)	
	greater = quickSort(high)
	
	return lesser + [pivot] + greater	
}

	result = []
	
	while 1 {
		if not l1 {
			return result + l2
		} elif not l2 {
			return result + l1
		} else {
			if l1[0] < l2[0] {
				result = result + l1[0]
				--l1
			} else {
				result = result + l2[0]
				--l2
			}
		}
	}
	
	return result
}

list1 = [1, 3, 6, 8]
list2 = [2, 3, 5, 6, 9]
result = [1, 2, 3, 3, 5, 6, 6, 8, 9]

print result == mergeSortedLists(list1, list2)
