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
from plone.app.drafts.proxy import DraftProxy


class FieldWidgets(z3c.form.field.FieldWidgets):
    """Widget manager for IFieldWidget."""

    #portal_type = None
    allowKssValidation = False
    automaticallyCreateDraft = False
    isDraftable = True  # NORMALLY SET TO FALSE AND OVERRIDE IN DEXTERITY BEHAVIOR

    def __init__(self, form, request, content):
        super(FieldWidgets, self).__init__(form, request, content)

    def getProxy(self):
        """Creates draft, if self.isDraftable is True, otherwise will try to
        load an existing draft if it exists
        """
    #---------------------------------------------------------------------------
        emptyDraft = True

        beginDrafting(self.content, self.request, self.form.portal_type)
        draft = getCurrentDraft(self.request, create=self.isDraftable)
        if draft is None:
            return self.content

        # Make sure cache is created fresh incase context changed from last visit
        if hasattr(draft, '_v__providedBy__'):
            emptyDraft = False
            del(draft._v__providedBy__)

        proxy = DraftProxy(draft, self.content)

        if emptyDraft == True:
            # MOVE CODE BELOW so we dont have seperate loops!!!
            setDefaults = False
            for field in self.form.fields.values():
                # Mark draft interface provided by field so it can be adapted
                # (Add form)
                # NOTE:  Not too sure if different fields may contain different
                # intefaces; so check them all so we can adapt later in datamanager
                if (not field.field.interface.providedBy(self.content) and
                    not field.field.interface.providedBy(draft)):
                    # Mark draft
                    zope.interface.alsoProvides(proxy, field.field.interface)
                    setDefaults = True

                # Provide default value on draft; since it will be empty
                # NOTE: hasattr is defensive only right now; since if draft
                # did not already have interface; it should be blank
                if (setDefaults == True and
                    not hasattr(draft, field.__name__)):
                    setattr(draft, field.__name__, field.field.default)

            zope.interface.alsoProvides(proxy, IZ3cDraft)

        zope.interface.alsoProvides(self.request, IZ3cDraft)
        self.request['DRAFT'] = proxy  # MODIFY INTERFACE to include DRAFT field; not just marker

        return proxy
    #---------------------------------------------------------------------------

    def update(self):
        """See interfaces.IWidgets"""

        #-----------------------------------------------------------------------
        adaptedContext = self.getProxy()
        #-----------------------------------------------------------------------

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
            #ignoreContext = self.ignoreContext
            #if field.ignoreContext is not None:
            #    ignoreContext = field.ignoreContext
            ignoreContext = False
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
                    (adaptedContext, field.field), interfaces.IDataManager)
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
            # Step 3: Set the prefix for the widget
            widget.name = prefix + shortName
            widget.id = (prefix + shortName).replace('.', '-')
            # Step 4: Set the context
            #-------------------------------------------------------------------
            #widget.context = self.content
            widget.context = adaptedContext
            #-------------------------------------------------------------------
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
            if adaptedContext is not None:
                #dm = zope.component.getMultiAdapter(
                #    (self.content, field.field), interfaces.IDataManager)
                dm = zope.component.getMultiAdapter(
                    (adaptedContext, field.field), interfaces.IDataManager)
                dm.set(interfaces.IDataConverter(widget).toFieldValue(widget.value))
                #adaptedContext._DraftProxy__draft[field.__name__] = interfaces.IDataConverter(widget).toFieldValue(widget.value)
                #adaptedContext.draftAnnotations[field.__name__] = interfaces.IDataConverter(widget).toFieldValue(widget.value)

                # - IDraftableField will be persistent, even in view mode if we
                #   do not remove the marker interface, so draft datamanager will
                #   be used instead of default one all the time, although that may
                #   not be so bad; since we could in theory create routines to only
                #   draft certain fields; so widgets can take advantage of that
                # - There is code to handle if a draft is not available in the
                #   draft datamanager
                #
                #zope.interface.noLongerProvides(field.field, IDraftableField)
            #-------------------------------------------------------------------

            # TODO:  Consider this as a hook??
            # ------------------------------------------------------------------
            # PROS: Would not need to adapt this; not really a pro :)
            # CONS: Expensive; would be called every request
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

        #-----------------------------------------------------------------------
        #
        # XXX: Temp Hook; just to confirm it will work here
        #
        print ''

##        from plone.app.z3cformdrafts.interfaces import IZ3cFormDraft
##        # Get draft object
##        portal_type = getattr(self.form, 'portal_type', self.form.context.portal_type)
##        z3cFormDraft = zope.component.queryMultiAdapter((self.form, self.request), IZ3cFormDraft)
##        if z3cFormDraft is not None:
##            z3cFormDraft.update(portal_type=portal_type, create=True, allowKssValidation=False)
        #-----------------------------------------------------------------------

