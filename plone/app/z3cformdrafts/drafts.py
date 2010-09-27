"""drafts.py
   Implements drafts behavior for dexterity types"""

import re

from types import InstanceType

import zope.interface
import zope.component

from z3c.form import interfaces
from z3c.form.interfaces import NO_VALUE

from plone.z3cform.interfaces import IWidgetInputConverter

from plone.app.z3cformdrafts.interfaces import IZ3cDraft, IZ3cDrafting
from plone.app.drafts.dexterity import beginDrafting
from plone.app.drafts.utils import getCurrentDraft

from plone.app.z3cformdrafts.interfaces import IZ3cFormDraft


# Event Handlers
def begunUpdate(form, event):
    """Event subscriber listening for plone.z3cform.layout.FormWrapper.update
    notify that it has started.
    A draft will not be created at this point, but if one exists it will be used.
    It is up to a widget or other behavior, etc to actually create a draft
    (see plone.app.drafts.behaviors.drafts behavior
    or plone.formwidget.multifile.widget for examples)
    """
    portal_type = getattr(form, 'portal_type', form.context.portal_type)

    # Get draft object
    z3cFormDraft = zope.component.queryMultiAdapter((form, form.request), IZ3cFormDraft)

    if z3cFormDraft is not None:
        z3cFormDraft.update(portal_type=portal_type, create=False, allowKssValidation=False)


# Request.form draft creation
class Z3cFormDraft(object):
    """Z3cFormDraft will populate newRequestForm with values from the
    widgets and draft and then can reset request.form to newly created values.
    """
    zope.interface.implements(IZ3cFormDraft)

    zope.component.adapts(interfaces.IForm, zope.interface.Interface)

    portal_type = None
    allowKssValidation = False
    automaticallyCreateDraft = False
    isDraftable = True

    def __init__(self, form, request):
        """
        """
        self.form = form
        self.request = request

        self.formDataNotToSave = {}
        self.draftRequestForm = {}
        self.validWidgetItems = []

        self.ORIGINAL_FORM = None
        self.ORIGINAL_OTHER = None

        self.draft = None

        # Check to see if we were called by kss validation
        self.isKssValidation = ('kss_z3cform_inline_validation' in self.request.getURL().split('/')
                           and 'validate_input' in self.request.getURL().split('/'))

        if self.portal_type is None:
            self.portal_type = getattr(self.form, 'portal_type', self.form.context.portal_type)

    def getDraft(self, content, request, portal_type, create=False):
        """Tries to get or set the draft for form content object
        """
        beginDrafting(content, request, portal_type)
        draft = getCurrentDraft(request, create=create)
        return draft

    def updateRequest(self, key, value):
        """Update the request.form and .other with supplied value pairs
        """
        self.request.form[key] = value
        self.request.other[key] = value

    def removeFromRequest(self, key):
        """Remove item entries form the request.form and .other
        """
        self.request.form.pop(key, None)
        self.request.other.pop(key, None)

    def restoreRequest(self):
        """Restores draft to its original state before drafting was applied
        incase there were drafting errors and we need to revert
        """
        self.request.form = self.ORIGINAL_FORM
        self.request.other = self.ORIGINAL_OTHER

    def setupDraftRequest(self):
        """Sets up the request to make it work with drafting
        """
        # Mark request as IDraft so other modules will know a draft is available
        zope.interface.alsoProvides(self.request, IZ3cDraft, IZ3cDrafting)

        # Need to process form, update widgets, etc
##        self.form.update()

        self.ORIGINAL_FORM = self.request.form.copy()
        self.ORIGINAL_OTHER = self.request.other.copy()
        self.request['DRAFT'] = self.draft

        # Don't want any dirty values around; so delete them now
        for key in self.request.form:
            #if key in self.request.other:
            self.request.other.pop(key, None)

        # Copy a copy of the draft and update it with original form
        self.request.form = getattr(self.draft, '_form', {}).copy()
        self.request.form.update(self.ORIGINAL_FORM)
        #if '-C' in self.request.form:
        self.request.form.pop('-C', None)
        self.request.other.pop('-C', None)

##    def mergeDraftWithRequest(self):
##        """Loop through all the widgets to an set values for newRequestForm so
##        it can be used to replace existing request.form
##        """
##        #if self.draft is None:
##        #    return

        # Initially populate the request from EditForm context
        # Draft will be saved with this data for future visits to page
        # TODO:  no need for '-C' reference any more??
        if (('-C' in self.request.form or len(self.request.form) == 0)
            and len(self.draftRequestForm) == 0
            and interfaces.IEditForm.providedBy(self.form)):

            # Sets up draft and widgets
##            self.setupDraftRequest()

            # Populate request from content object (initial load)
            for widget in self.form.widgets.values():
                value = IWidgetInputConverter(widget).toWidgetInputValue(widget.value)
                self.updateRequest(widget.name, value)
                self.validWidgetItems.append(widget.name)

                # If widgets contains the attribute 'widgets', there is another
                # list of widgets to deal with; more than likely from an IList
                if getattr(widget, 'widgets', None) is not None:
                    for subWidget in widget.widgets:
                        value = IWidgetInputConverter(subWidget).toWidgetInputValue(subWidget.value)
                        self.updateRequest(subWidget.name, value)
                        self.validWidgetItems.append(subWidget.name)
        else:
##            # Don't save anything on draft that is button action related or
##            # not directly releated to a widget since data may be InstanceType
##            # and / or not needed in future request (like ajax validation values)
##            widgetItems = {}
##            buttonsPattern = re.compile('form.[\d\w.]*buttons[\d\w.]+')
##            for key, value in self.request.form.items():
##                # Don't keep empty '-C' indicator form indicator since we are
##                # going to populate the form with draft
##                if key == '-C':
##                    pass
##                elif buttonsPattern.match(key):
##                    self.formDataNotToSave[key] = value
##                    self.removeFromRequest(key)
##                elif key.startswith('form.widgets'):
##                    self.request.other.pop(key, None)
##                    widgetItems[key] = value

            # Make sure everything coming from request.  Otherwise things
            # may be pulled from context
            self.form.ignoreContext = True

            # Sets up draft and widgets
##            self.setupDraftRequest()

##            # update request.form with items removed
##            self.request.form.update(widgetItems)
##            self.request.form.update(self.formDataNotToSave)

            # loop through the widgets to get values to populate draft
            for widget in self.form.widgets.values():
                self.updateWidget(widget)

    def updateWidget(self, widget):
        """Updates the widget with draft data if available
        """
        # Store the orginal sub-widgets names before we update
        # and any related form items together
        if getattr(widget, 'widgets', None) is not None:
            originalSubWidgetsLength = len(widget.widgets)
            widget.update()

            # Clear all related widget form items and replace with
            # updated values from running widget.update() if subWidgets
            # have been removed
            if len(widget.widgets) < originalSubWidgetsLength:
                for key, value in self.request.form.copy().items():
                    if key.startswith(widget.name):
                        self.removeFromRequest(key)

                # Add back updated widget.value and invalidate draft
                self.updateRequest(widget.name, widget.value)
                self.draftRequestForm.pop(widget.name, None)

                # Add back updated subWidget values
                for subWidget in widget.widgets:
                    self.updateRequest(subWidget.name, subWidget.value)

            # Check sub widgets first, since they can effect values on
            # parent widget..
            for subWidget in widget.widgets:
                self.setRequestFormItems(subWidget)

        # set newRequestForm value from widget value
        self.setRequestFormItems(widget)

    def setRequestFormItems(self, widget):
        """Sets request.form value either from the widget.value or
        directly from the draft
        """
        widget.update()
        value = widget.value

        # Check to see if there is a copy of the widget in draft
        if widget.extract() == NO_VALUE:
            value = self.draftRequestForm.get(widget.name, None)

        if value is not None:
            value = IWidgetInputConverter(widget).toWidgetInputValue(value)

            if value == NO_VALUE:
                value = self.draftRequestForm.get(widget.name, None)

        if value is not None:
            # Store a list of valid widget names so when we go to save the draft,
            # we will only store actual widget items
            if widget.name not in self.validWidgetItems:
                self.validWidgetItems.append(widget.name)
            self.updateRequest(widget.name, value)
        else:
            # value is None; therefore it is meant to be removed; don't save on
            # draft
            for key in self.validWidgetItems:
                if key.startswith(widget.name):
                    if key in self.validWidgetItems:
                        self.validWidgetItems.remove(key)

        # TODO:  Reintroduce ajax validation again
        #
        # Ajax validation sends a string sometimes, and we don't want to
        # overwrite draft if its not a NamedFile type
        #if self.isKssValidation == True and INamed.providedBy(widget.field):
        #    value = self.draftRequestForm.get(widget.name, None)

    def saveDraft(self):
        """Saves a copy of the newly created newRequestForm in the draft
           Returns True if successful
        """
        _form = {}
        for key in self.validWidgetItems:
            value = self.request.form.get(key, None)
            if type(value) == InstanceType:
                self.formDataNotToSave[key] = value
            else:
                _form[key] = value

        # Re-wrtie the form from draft incase anything was changed since last request
        # unless its identical
        if self.draftRequestForm != self.request.form:
            setattr(self.draft, '_form', _form)

    def setFormType(self):
        """Store _form_type on draft with hint on what form view created
        the draft so we can adapt it and such
        """
        formType = getattr(self.draft, '_form_type', None)
        if not formType:
            if interfaces.IAddForm.providedBy(self.form):
                setattr(self.draft, '_form_type', 'add')
            elif interfaces.IEditForm.providedBy(self.form):
                setattr(self.draft, '_form_type', 'edit')
        return

    def update(self, portal_type=None, create=False, allowKssValidation=False, force=False):
        """updates request.form with data from draft
        - portal_type:  portal_type of the context; provide if possible
        - create: will create a draft if none exists if True, otherwise will only
        use an existing draft if it exists or will return
        - allowKssValidation:  Will return if kss validation is detected and this
        value is False.  If it is true, it will update draft every time a user
        presses tab in the browser; could be load intensive but would allow auto
        saving of drafts
        - force:  Normally a draft is not recreated if force is False.  Widgets
        may set force to True to force a new draft to be created incase they
        updated something in the request.form since it was created.
        """
        # TODO:
        # -----
        # - get rid of force
        # - reintroduce kss validate checks
        # -

        # Only allow 1 notify.  form.update() could trigger another
        if IZ3cDrafting.providedBy(self.request):
            return

        # Already created draft; return
        # TODO:  move to calling function begunUpdate both here and in dexterity
        # (will allow quicker return if a draft already exists, and will eliminate
        #  need for froce=True)
        if IZ3cDraft.providedBy(self.request) and force == False:
            return

        if self.portal_type is None:
            return

        if self.isKssValidation == True and self.allowKssValidation == False:
            return

        # Get draft data
        # Request will also be marked with IZ3cDrafting at this point
        self.draft = self.getDraft(self.form.getContent(), self.request, self.portal_type, create=self.automaticallyCreateDraft)
        if self.draft is None:
            return

        # Store draft in request and draft._form in draftRequestForm
        self.draftRequestForm = getattr(self.draft, '_form', {}).copy()

        # Merge data from draft with request.form
        #self.mergeDraftWithRequest()
        self.setupDraftRequest()

        self.save()

    def save(self):
        """Save draft; cleanup; etc
        """
        # Save draft
        self.saveDraft()

        # Append any data that was not or could not be saved in draft
        # (button actions, items not directly related to widgets, InstanceTypes)
        self.request.form.update(self.formDataNotToSave)

        # Save the form type (add, edit) on draft
        self.setFormType()

        # We are done drafting; so get rid of marker
        zope.interface.noLongerProvides(self.form.request, IZ3cDrafting)
