"""drafts.py
   Implements drafts behavior for dexterity types"""

import zope.interface
import zope.component

from z3c.form import button
from z3c.form.form import AddForm, EditForm

from plone.dexterity.i18n import MessageFactory as _

#from plone.dexterity.browser.edit import DefaultEditForm
#from plone.dexterity.browser.add import DefaultAddForm

from plone.app.drafts.dexterity import discardDraftsOnCancel

from plone.z3cformbuttonoverrides.buttonoverrides import ButtonAndHandlerSubscriber

from plone.app.z3cformdrafts.interfaces import IDraftSubmitBehavior
from plone.app.z3cformdrafts.interfaces import IDraftCancelBehavior


class AddSubmitDraftButtonAndHandlerSubscriber(ButtonAndHandlerSubscriber, AddForm):
    """Overrides the current 'Save' button in DefaultAddForm to allow drafts
    to function properly only if the content type supports plone.app.drafts.IDraftable

    drafts.zcml adapts as follows:
        <subscriber
        for="plone.dexterity.browser.add.DefaultAddForm
             plone.z3cform.interfaces.IButtonOverrideEvent"
        handler=".drafts.AddSubmitDraftButtonAndHandlerSubscriber"
        />
    """
    zope.interface.implements(IDraftSubmitBehavior)

    position = 100

    def __init__(self, form, event):
        super(AddSubmitDraftButtonAndHandlerSubscriber, self).__init__(form, event)
        form.buttonsandhandlers[IDraftSubmitBehavior] = self

    @button.buttonAndHandler(_(u'Save'), name='save')
    def buttonHandler(self, action):
        # Execute original handler if it exists to provide compatibility
        # incase is a custom view
        originalButton = self.originalButtons.get('save', None)
        if originalButton is not None:
            originalHandler = self.originalHandlers.getHandler(originalButton)
            if originalHandler is not None:
                originalHandler(self, action)

        if self._finishedAdd:
            discardDraftsOnCancel(self.getContent(), None)

    def updateActions(self):
        self.form.actions["save"].addClass("context")


class AddCancelDraftButtonAndHandlerSubscriber(ButtonAndHandlerSubscriber, AddForm):
    """Overrides the current 'Cancel' button in DefaultAddForm to allow drafts
    to function properly only if the content type supports plone.app.drafts.IDraftable

    drafts.zcml adapts as follows:
        <subscriber
        for="plone.dexterity.browser.add.DefaultAddForm
             plone.z3cform.interfaces.IButtonOverrideEvent"
        handler=".drafts.AddCancelDraftButtonAndHandlerSubscriber"
        />
    """
    zope.interface.implements(IDraftCancelBehavior)

    position = 200

    def __init__(self, form, event):
        super(AddCancelDraftButtonAndHandlerSubscriber, self).__init__(form, event)
        form.buttonsandhandlers[IDraftCancelBehavior] = self

    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def buttonHandler(self, action):
        # Execute original handler if it exists to provide compatibility
        # incase is a custom view
        originalButton = self.originalButtons.get('cancel', None)
        if originalButton is not None:
            originalHandler = self.originalHandlers.getHandler(originalButton)
            if originalHandler is not None:
                originalHandler(self, action)

        discardDraftsOnCancel(self.getContent(), None)

    def updateActions(self):
        self.form.actions["cancel"].addClass("standalone")


class EditSubmitDraftButtonAndHandlerSubscriber(ButtonAndHandlerSubscriber, EditForm):
    """Overrides the current 'Save' button in DefaultEditForm to allow drafts
    to function properly only if the content type supports plone.app.drafts.IDraftable

    drafts.zcml adapts as follows:
        <subscriber
        for="plone.dexterity.browser.edit.DefaultEditForm
             plone.z3cform.interfaces.IButtonOverrideEvent"
        handler=".drafts.AddSubmitDraftButtonAndHandlerSubscriber"
        />
    """
    zope.interface.implements(IDraftSubmitBehavior)

    position = 100

    def __init__(self, form, event):
        super(EditSubmitDraftButtonAndHandlerSubscriber, self).__init__(form, event)
        form.buttonsandhandlers[IDraftSubmitBehavior] = self

    @button.buttonAndHandler(_(u'Save'), name='save')
    def buttonHandler(self, action):
        # Execute original handler if it exists to provide compatibility
        # incase is a custom view
        originalButton = self.originalButtons.get('save', None)
        if originalButton is not None:
            originalHandler = self.originalHandlers.getHandler(originalButton)
            if originalHandler is not None:
                originalHandler(self, action)

        discardDraftsOnCancel(self.getContent(), None)

    def updateActions(self):
        self.form.actions["save"].addClass("context")


class EditCancelDraftButtonAndHandlerSubscriber(ButtonAndHandlerSubscriber, EditForm):
    """Overrides the current 'Save' button in DefaultEditForm to allow drafts
    to function properly only if the content type supports plone.app.drafts.IDraftable

    drafts.zcml adapts as follows:
        <subscriber
        for="plone.dexterity.browser.edit.DefaultEditForm
             plone.z3cform.interfaces.IButtonOverrideEvent"
        handler=".drafts.AddCancelDraftButtonAndHandlerSubscriber"
        />
    """
    zope.interface.implements(IDraftCancelBehavior)

    position = 200

    def __init__(self, form, event):
        super(EditCancelDraftButtonAndHandlerSubscriber, self).__init__(form, event)
        form.buttonsandhandlers[IDraftCancelBehavior] = self

    @button.buttonAndHandler(_(u'Cancel'), name='cancel')
    def buttonHandler(self, action):
        # Execute original handler if it exists to provide compatibility
        # incase is a custom view
        originalButton = self.originalButtons.get('cancel', None)
        if originalButton is not None:
            originalHandler = self.originalHandlers.getHandler(originalButton)
            if originalHandler is not None:
                originalHandler(self, action)

        discardDraftsOnCancel(self.getContent(), None)

    def updateActions(self):
        self.form.actions["cancel"].addClass("standalone")
