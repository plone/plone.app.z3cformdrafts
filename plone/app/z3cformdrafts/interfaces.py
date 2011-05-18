"""drafts.py
   Implements drafts behavior for dexterity types"""

import zope.interface

from plone.app.drafts.interfaces import IDraft, IDrafting
from plone.z3cformbuttonoverrides.interfaces import IButtonAndHandlerSubscriber


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


class IDraftSaveBehavior(IButtonAndHandlerSubscriber):
    """Marker interfac to enable custom 'save draft' button and handler override
    This is set by an opt-in behavior statement
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


#class IDictDraftProxy(zope.interface.Interface):
#    """Marker interface for the draft proxy where the proxy contains dict
#    context.
#    """
