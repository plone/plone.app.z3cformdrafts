"""drafts.py
   Implements drafts behavior for dexterity types"""

import zope.interface

from plone.app.drafts.interfaces import IDraft, IDrafting
from plone.z3cformbuttonoverrides.interfaces import IButtonAndHandlerSubscriber


class IZ3cFormDraft(zope.interface.Interface):
    """IDraftBehavior used to merge request and draft data back into request.
    """

    form = zope.interface.Attribute(
        u'Form that was passed in.')

    request = zope.interface.Attribute(
        u'Request object.')

    formDataNotToSave = zope.interface.Attribute(
        u'Dictionary of items not to save on draft, but will be added back to request.')

    draftRequestForm = zope.interface.Attribute(
        u'A copy of the requested form that is stored on draft.')

    draft = zope.interface.Attribute(
        u'plone.app.drafts draft object.')

    isKssValidation = zope.interface.Attribute(
        u'Boolean indicator indicating if kss validation is actively providing the request.')

    def __init__(form, request):
        """Draft behavior is instantiated using attributes passed to it."""

    def setupDraftRequest():
        """Sets up the request to make it work with drafting."""

    def restoreRequest():
        """Restores draft to its original state before drafting was applied
        incase there were drafting errors and we need to revert."""

    def updateRequest(key, value):
        """Update the request.form and .other with supplied value pairs
        """

    def getDraft(content, request, portal_type):
        """Tries to get or set the draft for form content object."""

    def mergeDraftWithRequest():
        """Loop through all the widgets to an set values for newRequestForm so
        it can be used to replace existing request.form."""

    def setRequestFormValues(widget, temporaryRequestForm=False):
        """Sets request.form value either from the widget.value or
        directly from the draft."""

    def saveDraft():
        """Saves a copy of the newly created newRequestForm in the draft
           Returns True if successful."""

    def markRequest():
        """Mark request with hints on what form view created
        the draft so we can adapt it and such
        """

    def update():
        """Updates request.form with data from draft."""


#Custom Behavior Button Marker Interfaces
class IDraftAutoSaveBehavior(zope.interface.Interface):
    """Marker interfac to enable autosave of draft if kss ajax validation
    is enabled.  The default is not to auto save.
    Note: This is set by an opt-in behavior statement.
    """


class IDraftSubmitBehavior(IButtonAndHandlerSubscriber):
    """Marker interface to enable custom submit button and handler override
    This is automatically set when creating a draft
    """


class IDraftCancelBehavior(IButtonAndHandlerSubscriber):
    """Marker interface to enable custom cancel button and handler override
    This is automatically set when creating a draft
    """


class IZ3cDraft(IDraft):
    """Marker interface to indicate a z3c.form draft is present
    """


class IZ3cDrafting(IDrafting):
    """Marker interface to indicate a z3c.form draft is currently being
    created; but is not yet complete.
    """


class IDraftableField(zope.interface.Interface):
    """Marker interface to indicate a field is draftable.
    """


class IZ3cFormDataContext(zope.interface.Interface):
    """Indirection to help determine where draft forms store their data.

    This is a multi-adapter on ``(context, request, form)``. The context and
    request are the same as ``form.context`` and ``form.request``, but these
    discriminators allow the data context to be customised depending on
    the context or request.

    The default implementation simply returns ``form.context``.
    """
