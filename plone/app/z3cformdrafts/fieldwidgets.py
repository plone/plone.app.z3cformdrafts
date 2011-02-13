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

from plone.app.z3cformdrafts.interfaces import IZ3cFormDataContext
from plone.app.drafts.interfaces import IDraftable

class FieldWidgets(z3c.form.field.FieldWidgets):
    """Widget manager for IFieldWidget."""

    #portal_type = None
    allowKssValidation = False
    ignoreContext = False
    createDraft = False
    draftWritable = True
    draftable = False

    def __init__(self, form, request, content):
        super(FieldWidgets, self).__init__(form, request, content)

        # Check to see if we were called by kss validation
        isKssValidation = ('kss_z3cform_inline_validation' in request.getURL().split('/'))
        if isKssValidation == True and self.allowKssValidation == False:
            self.draftWritable = False

        proxy = zope.component.getMultiAdapter((self.content,
                                                self.request,
                                                self.form), IZ3cFormDataContext)
        proxy.createDraft = self.createDraft
        self.content = proxy.adapt()
        if IZ3cDraft.providedBy(self.content):
            self.draftable = True

    def update(self):
        """See interfaces.IWidgets"""

        # Create a unique prefix.
        prefix = util.expandPrefix(self.form.prefix)
        prefix += util.expandPrefix(self.prefix)
        # Walk through each field, making a widget out of it.
        uniqueOrderedKeys = []
        for field in self.form.fields.values():

            #-------------------------------------------------------------------
            # Indicates field is draftable
##            if (proxy is not None and
##                not IDraftableField.providedBy(field)):
##                zope.interface.alsoProvides(field.field, IDraftableField)
            #-------------------------------------------------------------------

            # Step 0. Determine whether the context should be ignored.
            #-------------------------------------------------------------------
            if self.draftable:
                ignoreContext = False
            else:
                ignoreContext = self.ignoreContext
                if field.ignoreContext is not None:
                    ignoreContext = field.ignoreContext
            #-------------------------------------------------------------------

            # Step 1: Determine the mode of the widget.
            mode = self.mode
            if field.mode is not None:
                mode = field.mode
            elif field.field.readonly and not self.ignoreReadonly:
                mode = interfaces.DISPLAY_MODE
            elif not ignoreContext:
                # If we do not have enough permissions to write to the
                # attribute, then switch to display mode.
                #dm = zope.component.getMultiAdapter(
                #    (self.content, field.field), interfaces.IDataManager)
                dm = zope.component.getMultiAdapter(
                    (self.content, field.field), interfaces.IDataManager)
                if not dm.canWrite():
                    mode = interfaces.DISPLAY_MODE
            # Step 2: Get the widget for the given field.
            shortName = field.__name__
            newWidget = True
            if shortName in self._data:
                # reuse existing widget
                widget = self._data[shortName]
                newWidget = False
            elif field.widgetFactory.get(mode) is not None:
                factory = field.widgetFactory.get(mode)
                widget = factory(field.field, self.request)
            else:
                widget = zope.component.getMultiAdapter(
                    (field.field, self.request), interfaces.IFieldWidget)
            # Step 2.5:  If widget is draftable and no widget exists, create draft
            if self.draftable == False and IDraftable.providedBy(widget):
                proxy = zope.component.getMultiAdapter((self.content,
                                                        self.request,
                                                        self.form), IZ3cFormDataContext)
                proxy.createDraft = True
                self.content = proxy.adapt()
                if IZ3cDraft.providedBy(self.content):
                    self.draftable = True
                    ignoreContext = False

            # Step 3: Set the prefix for the widget
            widget.name = prefix + shortName
            widget.id = (prefix + shortName).replace('.', '-')
            # Step 4: Set the context
            widget.context = self.content
            # Step 5: Set the form
            widget.form = self.form
            # Optimization: Set both interfaces here, rather in step 4 and 5:
            # ``alsoProvides`` is quite slow
            zope.interface.alsoProvides(
                widget, interfaces.IContextAware, interfaces.IFormAware)
            # Step 6: Set some variables
            widget.ignoreContext = ignoreContext
            widget.ignoreRequest = self.ignoreRequest
            # Step 7: Set the mode of the widget
            widget.mode = mode
            # Step 8: Update the widget
            widget.update()

            #-------------------------------------------------------------------
            # Save converted widget value on draft if it different from what is
            # already stored on draft
            if self.draftable and self.draftWritable == True:
                dm = zope.component.getMultiAdapter(
                    (self.content, field.field), interfaces.IDataManager)
                value = interfaces.IDataConverter(widget).toFieldValue(widget.value)
                if getattr(self.content, field.field.getName()) != value:
                    dm.set(value)
            #-------------------------------------------------------------------

            zope.event.notify(AfterWidgetUpdateEvent(widget))
            # Step 9: Add the widget to the manager
            if widget.required:
                self.hasRequiredFields = True
            uniqueOrderedKeys.append(shortName)
            if newWidget:
                self._data_values.append(widget)
                self._data[shortName] = widget
                zope.location.locate(widget, self, shortName)
            # allways ensure that we add all keys and keep the order given from
            # button items
            self._data_keys = uniqueOrderedKeys
