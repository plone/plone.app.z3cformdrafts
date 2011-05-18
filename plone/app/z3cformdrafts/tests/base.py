from Products.PloneTestCase import PloneTestCase as ptc
from plone.app.z3cformdrafts.tests.layer import Z3cformdraftsLayer

ptc.setupPloneSite()

class Z3cformdraftsTestCase(ptc.PloneTestCase):
    layer = Z3cformdraftsLayer

class Z3cformdraftsFunctionalTestCase(ptc.FunctionalTestCase):
    layer = Z3cformdraftsLayer
