clean:
	find . -name '*.pyc' -exec rm {} \;

web:
	./rw webservice frontend/{html,static} /static
