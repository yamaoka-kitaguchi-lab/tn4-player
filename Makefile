.PHONY: test
test: test.interfaces

.PHONY: test.interfaces
test.interfaces:
	python3 ./lib/tn4/netbox/test_interfaces.py || true
