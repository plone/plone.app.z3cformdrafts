"""Z3cFormDrafts FieldWidgits Implementation
"""

from Acquisition import aq_inner
from persistent.dict import PersistentDict

import zope.component
import zope.interface
import zope.location
import zope.schema.interfaces

from z3c.form import interfaces

from plone.app.drafts.interfaces import IDrafting
from plone.app.drafts.dexterity import beginDrafting
from plone.app.drafts.utils import getCurrentDraft

from plone.app.z3cformdrafts.interfaces import IZ3cFormDataContext, IZ3cDraft


class Z3cFormDataContext(object):

    zope.interface.implements(IZ3cFormDataContext)

    createDraft = False

    def __init__(self, content, request, form):
        self.content = content
        self.request = request
        self.form = form
        self.context = aq_inner(self.form.context)

    def adapt(self):
        """If we are drafting a content item, record form data information to the
        draft, but read existing data from the underlying object.
        """
        # Set up the draft (sets cookies, markers, etc)
        draft = getCurrentDraft(self.request, create=False)
        if not draft and not self.createDraft:
            return self.content

        if not draft:
            beginDrafting(self.content, self.form)
            draft = getCurrentDraft(self.request, create=self.createDraft)

        if draft is None:
            return self.content  # return contnet, not context

        context = getattr(draft, 'context', None)

        # Initial draft; populate initial values
        if context is None:
            context = PersistentDict()

            # Get all fields from from, including groups so we can store them
            # on draft
            _fields = []
            for field in self.form.fields.items():
                _fields.append(field)
            if hasattr(self.form, 'groups'):
                for group in self.form.groups:
                    for field in group.fields.items():
                        _fields.append(field)
            for name, field in _fields:
                # Provide default value on draft
                dm = zope.component.getMultiAdapter(
                    (self.content, field.field), interfaces.IDataManager)
                try:
                    value = dm.query(field)
                except TypeError:
                    value = field.field.default or field.field.missing_value

                context[field.field.__name__] = value

            zope.interface.alsoProvides(context, IZ3cDraft)
            zope.interface.alsoProvides(context, IDrafting)
            setattr(draft, 'context', context)

        # Cache draft
        self.request['DRAFT'] = context
        zope.interface.alsoProvides(self.request, IZ3cDraft)

        return context
