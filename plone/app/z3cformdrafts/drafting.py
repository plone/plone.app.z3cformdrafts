"""Z3cFormDrafts FieldWidgits Implementation
"""
__docformat__ = "reStructuredText"
import zope.component
import zope.interface
import zope.location
import zope.schema.interfaces

from z3c.form import interfaces, util, error
from z3c.form.error import MultipleErrors
from z3c.form.widget import AfterWidgetUpdateEvent

import z3c.form.field

import re

from types import InstanceType

import zope.interface
import zope.component
from zope.annotation.interfaces import IAnnotations

from z3c.form import interfaces
from z3c.form.interfaces import NO_VALUE

from plone.z3cform.interfaces import IWidgetInputConverter

from plone.app.z3cformdrafts.interfaces import IZ3cDraft, IZ3cDrafting
from plone.app.drafts.dexterity import beginDrafting
from plone.app.drafts.utils import getCurrentDraft

from plone.app.z3cformdrafts.interfaces import IZ3cFormDraft, IDraftableField

import plone.app.drafts.proxy
from plone.app.drafts.interfaces import IDraftProxy
from plone.dexterity.content import FTIAwareSpecification

from zope.interface import implementer
from zope.component import adapter

from plone.app.z3cformdrafts.interfaces import IZ3cFormDataContext
from plone.app.drafts.interfaces import IDrafting

from plone.app.drafts.proxy import DraftProxy

from zope.interface import implements
from zope.interface.declarations import getObjectSpecification
from zope.interface import implementedBy
from zope.interface import providedBy
from zope.interface.declarations import ObjectSpecificationDescriptor

from Acquisition import aq_base


class DraftingZ3cFormDataContext(object):

    zope.interface.implements(IZ3cFormDataContext)

    _create = False

    # XXX: REMOVE; change to default z3cform provider
    #cacheProvider = FTIAwareSpecification

    def __init__(self, content, request, form):
        self.content = content
        self.request = request
        self.form = form

    def create(self):
        """Indicates if creating a new draft is allowed.  Default is False
        and will not create an new draft, but will use an existing draft,
        if available
        """
        return self._create

    def adapt(self):
        """If we are drafting a content item, record form data information to the
        draft, but read existing data from the underlying object.
        """

        draft = getCurrentDraft(self.request, create=self.create())
        if draft is None:
            return self.content

        # TODO: Adapt this
        proxy = Z3cFormDraftProxy(draft, self.content)

        # Make sure cache is created fresh incase context changed from last visit
        # (empty draft)
        if (not IZ3cDraft.providedBy(draft)
            and self.content.portal_type != self.form.portal_type
            ):
            setDefaults = False
            for field in self.form.fields.values():
                # Mark draft interface provided by field so it can be adapted
                if not field.field.interface.providedBy(proxy):
                    # Mark draft (add form)
                    zope.interface.alsoProvides(proxy, field.field.interface)
                    setDefaults = True

                # Provide default value on draft
                if setDefaults == True:
                    setattr(draft, field.field.getName(), field.field.default)

        if not IZ3cDraft.providedBy(proxy):
            zope.interface.alsoProvides(proxy, IZ3cDraft)

        # TODO: MODIFY INTERFACE to include DRAFT field; not just marker
        self.request['DRAFT'] = proxy
        zope.interface.alsoProvides(self.request, IZ3cDraft)

        return proxy


class ProxySpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the draft and the proxy

    TODO:  Implement a cache, but remember that it needs to work with ++add++
           form, which may not contain a dexterity/zc3form type as its context.

           I could just set _v__providedBy__ here if I could make sure it gets
           invalidated if an interface was added since last time
    """

    def __get__(self, inst, cls=None):

        # We're looking at a class - fall back on default
        if inst is None:
            return getObjectSpecification(cls)

        # Find the cached value and return it if possible
        # Only want it is its stored on draft otherwise it will not contain
        # any draft values
        #cached = getattr(inst._DraftProxy__draft, '_v__providedBy__', None)
        #if cached is not None:
        #    return cached

        # Get the interfaces implied by the class as a starting point.
        provided = implementedBy(cls)

        # Get interfaces directly provided by the draft proxy
        provided += getattr(inst, '__provides__', provided)

        # Add the interfaces provided by the target
        target = aq_base(inst._Z3cFormDraftProxy__target)
        if target is None:
            return provided

        provided += providedBy(target)

        #inst._v__providedBy__ = provided
        return provided


class Z3cFormDraftProxy(DraftProxy):

    __providedBy__ = ProxySpecification()

    def __init__(self, draft, target):
        self.__dict__['_Z3cFormDraftProxy__draft'] = draft
        self.__dict__['_Z3cFormDraftProxy__target'] = target
