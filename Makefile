.PHONY: test
test: test.interfaces

.PHONY: test.interfaces
test.interfaces:
	#python3 -m unittest ./lib/tn4/netbox/test_interfaces.py || true
	python3 ./lib/tn4/netbox/test_interfaces.py || true
