import unittest
from Testing import ZopeTestCase as ztc
from plone.app.z3cformdrafts.tests.base import Z3cformdraftsFunctionalTestCase

doc_tests = (
    )
functional_tests = (
    'drafts.txt',
    )

def test_suite():
    return unittest.TestSuite(
        [ztc.FunctionalDocFileSuite(
            'tests/%s' % f, package='plone.app.z3cformdrafts',
            test_class=Z3cformdraftsFunctionalTestCase)
            for f in functional_tests] + 
        [ztc.ZopeDocFileSuite(
            'tests/%s' % f, package='plone.app.z3cformdrafts',
            test_class=Z3cformdraftsFunctionalTestCase)
            for f in doc_tests],
        )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
