package listlang.objects;

import java.util.LinkedList;

public class List {
	
	private LinkedList<Integer> mList = new LinkedList<Integer>();
	
	public List() {
	}
	
	public void print() {		
		String str = "";
		if(!mList.isEmpty()) {
			str = mList.get(0).toString();
			for(int i = 1; i < mList.size(); i++) {
				str += ", " + mList.get(i).toString();
			}
		}
		System.out.print("[" + str + "]");
	}
	
	public List clone() {
		return new List(this.getLinkedList());
	}
	
	@SuppressWarnings("unchecked")
	public List(LinkedList<Integer> linkedList) {
		mList = (LinkedList<Integer>) linkedList.clone();
	}
	
	public LinkedList<Integer> getLinkedList() {
		return mList;
	}
	
	public void addFirst(int n) {
		mList.addFirst(new Integer(n));
	}
	
	public void addLast(int n) {
		mList.addLast(new Integer(n));
	}
	
	public void del(int i) {
		mList.remove(i);
	}
	
	public boolean boolean_value() {
		return !mList.isEmpty();
	}
	
	public int to_int() {
		return boolean_value() ? 1 : 0;
	}
	
	// expressions
	
	public int get(int i) {
		return mList.get(i).intValue();
	}
	
	public int len() {
		return mList.size();
	}

	public int equal(List second) {
		if(second.getLinkedList().equals(mList)) {
			return 1;
		} else {
			return 0;
		}
	}
	
	public List add(List second) {
		List resList = this.clone();
		for(int i = 0; i < second.len(); i++) {
			resList.addLast(second.get(i));
		}
		return resList;
	}

	public List pre_incr() {
		addFirst(0);
		return this;
	}

	public List pre_decr() {
		del(0);
		return this;
	}

	public List post_incr() {
		addLast(0);
		return this;
	}

	public List post_decr() {
		del(len() - 1);
		return this;
	}
}
