from Testing.ZopeTestCase import app, close, installProduct, installPackage
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.layer import PloneSite
from zope.app.component.hooks import setSite, setHooks
from transaction import commit

# BBB Zope 2.12
try:
    from Zope2.App import zcml
    from OFS import metaconfigure
    zcml # pyflakes
    metaconfigure
except ImportError:
    from Products.Five import zcml
    from Products.Five import fiveconfigure as metaconfigure

class Z3cformdraftsLayer(PloneSite):
    
    @classmethod
    def setUp(cls):
        metaconfigure.debug_mode = True
        import plone.app.dexterity
        import plone.app.z3cformdrafts
        import plone.app.drafts
        zcml.load_config('meta.zcml', plone.app.dexterity)
        zcml.load_config('configure.zcml', plone.app.dexterity)
        zcml.load_config('configure.zcml', plone.app.z3cformdrafts)
        metaconfigure.debug_mode = False

        # import the default profile
        root = app()
        portal = root.plone
        setHooks()
        setSite(portal)
        tool = getToolByName(portal, 'portal_setup')
        profile = 'profile-plone.app.dexterity:default'
        tool.runAllImportStepsFromProfile(profile, purge_old=False)
        profile = 'profile-plone.app.z3cformdrafts:default'
        tool.runAllImportStepsFromProfile(profile, purge_old=False)
        setSite(None)
        # and commit the changes
        commit()
        close(root)

    @classmethod
    def tearDown(cls):
        pass
