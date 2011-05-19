"""drafts.py
   Implements drafts behavior for dexterity types"""

import zope.interface
import zope.component

from Products.statusmessages.interfaces import IStatusMessage

from z3c.form import button

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.i18n import MessageFactory as _
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.browser.add import DefaultAddForm

from plone.z3cformbuttonoverrides.buttonoverrides import ButtonAndHandlerSubscriber

from plone.app.z3cformdrafts.interfaces import IDraftSaveBehavior, IDraftAutoSaveBehavior
from plone.app.drafts.interfaces import IDraftable
from plone.app.z3cformdrafts.fieldwidgets import FieldWidgets


class DexterityFieldWidgets(FieldWidgets):
    """Widget manager for IFieldWidget."""

    def __init__(self, form, request, content):
        fti = zope.component.queryUtility(IDexterityFTI, name=form.portal_type)

        # Don't allow autosave if IDraftAutoSaveBehavior is not enabled
        if 'plone.app.z3cformdrafts.interfaces.IDraftAutoSaveBehavior' in fti.behaviors:
            zope.interface.alsoProvides(request, IDraftAutoSaveBehavior)

        if 'plone.app.drafts.interfaces.IDraftable' in fti.behaviors:
            zope.interface.alsoProvides(request, IDraftable)

        super(DexterityFieldWidgets, self).__init__(form, request, content)


class AddSaveDraftButtonAndHandlerSubscriber(ButtonAndHandlerSubscriber, DefaultAddForm):
    """ Add a 'Draft' button and handler to DefaultAddForm to allow a draft
    to be saved manually.  The button will only be added if the content type
    supports plone.app.dexterity.interfaces.IDraftSavebehavior

    drafts.zcml adapts as follows:
        <subscriber
        for="plone.dexterity.browser.add.DefaultAddForm
             plone.z3cform.interfaces.IButtonOverrideEvent"
        handler=".drafts.AddSaveDraftButtonAndHandlerSubscriber"
        />
    """
    zope.interface.implements(IDraftSaveBehavior)

    position = 300

    def __init__(self, form, event):
        super(AddSaveDraftButtonAndHandlerSubscriber, self).__init__(form, event)
        fti = zope.component.queryUtility(IDexterityFTI, name=form.portal_type)
        if 'plone.app.z3cformdrafts.interfaces.IDraftSaveBehavior' in fti.behaviors:
            form.buttonsandhandlers[IDraftSaveBehavior] = self

    @button.buttonAndHandler(_(u'Draft'), name='draft')
    def buttonHandler(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Draft has been saved."), "info")
        view = '++add++%s' % self.portal_type
        redirectURL = "%s/%s" % (self.getContent().absolute_url(), view)
        self.request.response.redirect(redirectURL)

    def updateActions(self):
        self.form.actions["draft"].addClass("standalone")


class EditSaveDraftButtonAndHandlerSubscriber(ButtonAndHandlerSubscriber, DefaultEditForm):
    """ Add a 'Draft' button and handler to DefaultEditForm to allow a draft
    to be saved manually.  The button will only be added if the content type
    supports plone.app.dexterity.interfaces.IDraftSavebehavior

    drafts.zcml adapts as follows:
        <subscriber
        for="plone.dexterity.browser.edit.DefaultEditForm
             plone.z3cform.interfaces.IButtonOverrideEvent"
        handler=".drafts.AddSaveDraftButtonAndHandlerSubscriber"
        />
    """
    zope.interface.implements(IDraftSaveBehavior)

    position = 300

    def __init__(self, form, event):
        super(EditSaveDraftButtonAndHandlerSubscriber, self).__init__(form, event)
        fti = zope.component.queryUtility(IDexterityFTI, name=form.portal_type)
        if 'plone.app.z3cformdrafts.interfaces.IDraftSaveBehavior' in fti.behaviors:
            form.buttonsandhandlers[IDraftSaveBehavior] = self

    @button.buttonAndHandler(_(u'Draft'), name='draft')
    def buttonHandler(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Draft has been saved."), "info")
        view = 'edit'
        redirectURL = "%s/%s" % (self.getContent().absolute_url(), view)
        self.request.response.redirect(redirectURL)

    def updateActions(self):
        self.form.actions["draft"].addClass("standalone")
