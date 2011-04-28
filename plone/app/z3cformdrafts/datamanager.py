##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Widget Framework Implementation
"""
__docformat__ = "reStructuredText"

import zope.interface
import zope.component
import zope.schema

import persistent.mapping
import persistent.dict

from zope.interface.common import mapping
from zope.security.interfaces import ForbiddenAttribute
from zope.security.checker import canAccess, canWrite, Proxy

from z3c.form import interfaces

from z3c.form.datamanager import DataManager

from plone.app.drafts.interfaces import IDraftProxy

from plone.app.z3cformdrafts.drafting import Z3cFormAttributeDraftProxy


class AttributeField(DataManager):
    """Attribute field."""

    zope.component.adapts(
        IDraftProxy,
        zope.schema.interfaces.IField)

    def __init__(self, context, field):
        self.context = context
        self.field = field

    @property
    def adapted_context(self):
        # get the right adapter or context
        # If a draft exists use its context
        context = self.context
        if self.field.interface is not None:
            context = self.field.interface(context)
        return context

    def get(self):
        """See z3c.form.interfaces.IDataManager"""
        # Need to create a temporary DraftProxy to get proper value back
        # from adapted_context since it may handle getattr in a custom way like
        # dexterity metadata.  Without a DraftProxy we would be getting the
        # value directly from the content object, which we dont want
        draftProxy = Z3cFormAttributeDraftProxy(self.context._Z3cFormAttributeDraftProxy__draft, self.adapted_context)
        return getattr(draftProxy, self.field.getName())

    def query(self, default=interfaces.NO_VALUE):
        """See z3c.form.interfaces.IDataManager"""
        try:
            return self.get()
        except ForbiddenAttribute, e:
            raise e
        except AttributeError:
            return default

    def set(self, value):
        """See z3c.form.interfaces.IDataManager"""
        if self.field.readonly:
            raise TypeError("Can't set values on read-only fields "
                            "(name=%s, class=%s.%s)"
                            % (self.field.__name__,
                               self.context.__class__.__module__,
                               self.context.__class__.__name__))
        # Need to create a temporary DraftProxy to set proper value back
        # from adapted_context since it may handle getattr in a custom way like
        # dexterity metadata.  Without a DraftProxy we would be updating the
        # Content object, which we dont want
        draftProxy = Z3cFormAttributeDraftProxy(self.context._Z3cFormAttributeDraftProxy__draft, self.adapted_context)
        setattr(draftProxy, self.field.getName(), value)

    def canAccess(self):
        """See z3c.form.interfaces.IDataManager"""
        context = self.adapted_context
        if isinstance(context, Proxy):
            return canAccess(context, self.field.__name__)
        return True

    def canWrite(self):
        """See z3c.form.interfaces.IDataManager"""
        context = self.adapted_context
        if isinstance(context, Proxy):
            return canWrite(context, self.field.__name__)
        return True


from plone.app.z3cformdrafts.interfaces import IDictDraftProxy
class DictionaryField(DataManager):
    """Dictionary field.

    NOTE: Even though, this data manager allows nearly all kinds of
    mappings, by default it is only registered for dict, because it
    would otherwise get picked up in undesired scenarios. If you want
    to it use for another mapping, register the appropriate adapter in
    your application.

    """

    zope.component.adapts(
        IDictDraftProxy, zope.schema.interfaces.IField)

    #_allowed_data_classes = (
    #    dict,
    #    persistent.mapping.PersistentMapping,
    #    persistent.dict.PersistentDict,
    #    )

    def __init__(self, data, field):
        #if (not isinstance(data, self._allowed_data_classes) and
        #    not mapping.IMapping.providedBy(data)):
        #    raise ValueError("Data are not a dictionary: %s" %type(data))
        self.data = data
        self.field = field

    def get(self):
        """See z3c.form.interfaces.IDataManager"""
        #return self.data.get(self.field.__name__, self.field.missing_value)
        return getattr(self.data, self.field.__name__, self.field.missing_value)

    def query(self, default=interfaces.NO_VALUE):
        """See z3c.form.interfaces.IDataManager"""
        #return self.data.get(self.field.__name__, default)
        return getattr(self.data, self.field.__name__, default)

    def set(self, value):
        """See z3c.form.interfaces.IDataManager"""
        if self.field.readonly:
            raise TypeError("Can't set values on read-only fields name=%s"
                            % self.field.__name__)
        #self.data[self.field.__name__] = value
        setattr(self.data, self.field.__name__, value)

    def canAccess(self):
        """See z3c.form.interfaces.IDataManager"""
        return True

    def canWrite(self):
        """See z3c.form.interfaces.IDataManager"""
        return True
