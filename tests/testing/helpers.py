import unittest


def run_contract(case_class):
    """Run a test case class in isolation and return its ``unittest.TestResult``."""
    result = unittest.TestResult()
    unittest.defaultTestLoader.loadTestsFromTestCase(case_class).run(result)
    return result


def failed_test_names(result):
    """Names of the test methods that failed or errored, sub-test failures included."""
    return {str(test).split(" ")[0] for test, _ in [*result.failures, *result.errors]}
