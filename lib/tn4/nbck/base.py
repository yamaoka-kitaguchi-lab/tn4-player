class Checker:
    def is_equal(self, s, t, **keys):
        for k in keys:
            return False if s[k] != t[k]
        return True

