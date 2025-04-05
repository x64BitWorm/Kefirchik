import unittest

loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.discover("tests", pattern="*_test.py"))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
