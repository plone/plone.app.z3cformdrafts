"""drafts.py
   Implements drafts behavior for dexterity types"""

import re

from types import InstanceType

import zope.interface
import zope.component

from z3c.form import interfaces
from z3c.form.interfaces import NO_VALUE

from plone.z3cform.interfaces import IWidgetInputConverter

from plone.namedfile.interfaces import INamed
from plone.app.textfield.interfaces import IRichText

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.interfaces import IAddBegunEvent, IEditBegunEvent

from plone.app.drafts.interfaces import IDraft, IDrafting
from plone.app.drafts.dexterity import beginDrafting
from plone.app.drafts.utils import getCurrentDraft

from plone.app.z3cformdrafts.interfaces import IZ3cFormDraft


# Request.form draft creation
class Z3cFormDraft(object):
    """Z3cFormDraft will populate newRequestForm with values from the
    widgets and draft and then can reset request.form to newly created values.
    """
    zope.interface.implements(IZ3cFormDraft)

    zope.component.adapts(interfaces.IForm, zope.interface.Interface)

    def __init__(self, form, request):
        """
        """
        self.form = form
        self.request = request

        self.formDataNotToSave = {}
        self.draftRequestForm = {}

        self.draft = None
        self.isKssValidation = False

    def setupDraftRequest(self):
        """Sets up the request to make it work with drafting
        """
        self.request['ORIGINAL_FORM'] = self.request.form.copy()
        self.request['ORIGINAL_OTHER'] = self.request.other.copy()
        self.request.form = {}

    def restoreRequest(self):
        """Restores draft to its original state before drafting was applied
        incase there were drafting errors and we need to revert
        """
        self.request.form = self.request.ORIGINAL_FORM
        self.request.other = self.request.ORIGINAL_OTHER

    def updateRequest(self, key, value):
        """Update the request.form and .other with supplied value pairs
        """
        self.request.form[key] = value
        self.request.other[key] = value

    def getDraft(self, content, request, portal_type):
        """Tries to get or set the draft for form content object
        """
        beginDrafting(content, request, portal_type)
        draft = getCurrentDraft(request, create=True)
        return draft

    def mergeDraftWithRequest(self):
        """Loop through all the widgets to an set values for newRequestForm so
        it can be used to replace existing request.form
        """
        if self.draft is None:
            return

        # Initially populate the request from EditForm context
        # Draft will be saved with this data for future visits to page
        if (('-C' in self.request.ORIGINAL_FORM or len(self.request.ORIGINAL_FORM) == 0)
            and len(self.draftRequestForm) == 0
            and interfaces.IEditForm.providedBy(self.form)):

            # Need to update widgets, etc
            self.form.update()

            # Populate request from content object (initial load)
            for widget in self.form.widgets.values():
                value = IWidgetInputConverter(widget).toWidgetInputValue(widget.value)
                self.updateRequest(widget.name, value)

                # If widgets contains the attribute 'widgets', there is another
                # list of widgets to deal with; more than likely from an IList
                if getattr(widget, 'widgets', None) is not None:
                    for widgetWidgets in widget.widgets:
                        value = IWidgetInputConverter(widget).toWidgetInputValue(widget.value)
                        self.updateRequest(widgetWidgets.name, value)
        else:
            # Don't save anything on draft that is button action related or
            # not directly releated to a widget since data may be InstanceType
            # and / or not needed in future request (like ajax validation values)
            buttonsPattern = re.compile('form.[\d\w.]*buttons[\d\w.]+')
            for key, value in self.request.ORIGINAL_FORM.items():
                # Don't keep empty '-C' indicator form indicator since we are
                # going to populate the form with draft
                if key == '-C':
                    pass
                elif buttonsPattern.match(key):
                    self.formDataNotToSave[key] = value
                    self.request.other.pop(key, None)
                elif key.startswith('form.widgets'):
                    self.request.form[key] = value
                    self.request.other.pop(key, None)

            # Make sure everything coming from request.  Otherwise things
            # may be pulled from context
            self.form.ignoreContext = True

            # Need to update widgets, etc
            self.form.update()

            # loop through the widgets to get values to populate draft
            for widget in self.form.widgets.values():

                # Check sub widgets first, since they can effect values on
                # parent widget..
                if getattr(widget, 'widgets', None) is not None:
                    for widgetWidgets in widget.widgets:
                        self.setRequestFormValues(widgetWidgets)

                # set newRequestForm value from widget value
                self.setRequestFormValues(widget)

                # Update widget with newRequestForm, since widget.value may change
                # based on sub-wigets being set up from draft
                if getattr(widget, 'widgets', None) is not None:
                    widget.update()
                    self.setRequestFormValues(widget, temporaryRequestForm=True)

            # Loop though draft and add anything missing to newRequestForm
            for key, value in self.draftRequestForm.items():
                if key not in self.request.form:
                    self.updateRequest(key, value)

    def setRequestFormValues(self, widget, temporaryRequestForm=False):
        """Sets request.form value either from the widget.value or
        directly from the draft
        """
        value = None

        if widget.value is not None:
            value = IWidgetInputConverter(widget).toWidgetInputValue(widget.value)

        # Ajax validation sends a string sometimes, and we don't want to
        # overwrite draft if its not a NamedFile type
        if self.isKssValidation == True and INamed.providedBy(widget.field):
            value = self.draftRequestForm.get(widget.name, None)

        # If value is None; see if its availble in draft
        if (not bool(widget.value) and widget.extract() == NO_VALUE):
            value = self.draftRequestForm.get(widget.name, None)

        # TODO:  Test to see if I need to do a check before writing since
        # newRequestForm could have already been set after running
        # widget.widgets and the draft copy will be gone
        # so something like:
        # ->> if widget.name in self.newRequestForm and not widget.extract() != NO_VALUE:
        self.updateRequest(widget.name, value)

        if temporaryRequestForm == False:
            # Remove entry from request.form
            self.request.other.pop(widget.name, None)
            self.draftRequestForm.pop(widget.name, None)

            # Need to create dictionary of items to add into request.form,
            # since we need to add them after the conditional check below,
            # otherwise widget.extract == NO_VALUE could end up being false on
            # the second match
            values = {}

            # Store any related widget key/value paris in newRequest
            # Note: any buttons already got striped from request earlier so they
            # won't mess things up
            for key, value in self.request.other.items():
                if key.startswith(widget.name) and bool(widget.extract()):
                    values[key] = value
                    self.request.other.pop(key, None)

            # Grab any widget related key/value pairs from draft and put in
            # newRequestForm, only if it does not exist in newRequestForm, otherwise
            # remove it from draft copy so it will not get re-added later
            for key, value in self.draftRequestForm.items():
                if key.startswith(widget.name):
                    # Only allow names starting with letters, so we don't end up
                    # grabbing an old list value that was deleted
                    widgetPattern = re.compile('%s.[\\w.]+' % widget.name)
                    if (widgetPattern.match(key)
                        and widget.extract() == NO_VALUE
                        and key not in self.request.form
                        and key not in values):
                        values[key] = value
                    self.draftRequestForm.pop(key, None)

            self.request.form.update(values)

    def saveDraft(self):
        """Saves a copy of the newly created newRequestForm in the draft
           Returns True if successful
        """
        # Final check to make sure there are no InstanceTypes in newRequestForm
        for key, value in self.request.form.items():
            if type(value) == InstanceType:
                self.formDataNotToSave[key] = value
                self.request.form.pop(key, None)

        # Re-wrtie the form from draft incase anything was changed since last request
        # unless its identical
        if self.draftRequestForm != self.request.form:
            setattr(self.draft, '_form', self.request.form.copy())

    def markRequest(self):
        """Mark request with hints on what form view created
        the draft so we can adapt it and such
        """
        # Mark request so we can tell if add or edit notifier created it
        # (only ever set it once)
        notifier = getattr(self.draft, '_notifier', None)
        if not notifier:
            if interfaces.IAddForm.providedBy(self.form):
                setattr(self.draft, '_notifier', 'add')
            elif interfaces.IEditForm.providedBy(self.form):
                setattr(self.draft, '_notifier', 'edit')
            notifier = getattr(self.draft, '_notifier', None)

        # Mark request interface based on stored value
        if notifier == 'add':
            zope.interface.alsoProvides(self.request, IAddBegunEvent)
        elif notifier == 'edit':
            zope.interface.alsoProvides(self.request, IEditBegunEvent)

        return

    def update(self, portal_type=None, autoEnableDraftBehavior=False):
        """updates request.form with data from draft
        """
        # Only allow 1 notify.  form.update() will trigger another
        if IDrafting.providedBy(self.request):
            return

        if portal_type is None:
            portal_type = getattr(self.form, 'portal_type', None)
            if portal_type is None:
                return

        fti = zope.component.queryUtility(IDexterityFTI, name=portal_type)
        if not 'plone.app.drafts.interfaces.IDraftable' in fti.behaviors:
            if autoEnableDraftBehavior == False:
                return
            # Auto-enable behavior for content type if autoEnableDraftBehavior
            # is True
            # provided by request
            else:
                behaviors = list(fti.behaviors)
                behaviors.append('plone.app.drafts.interfaces.IDraftable')
                fti.behaviors = behaviors

        # Check to see if we were called by kss validation
        self.isKssValidation = ('kss_z3cform_inline_validation' in self.request.getURL().split('/')
                           and 'validate_input' in self.request.getURL().split('/'))

        # Don't allow autosave if IDraftAutoSaveBehavior is not enabled
        if self.isKssValidation == True and not 'plone.app.z3cformdrafts.interfaces.IDraftAutoSaveBehavior' in fti.behaviors:
            return

        # Mark request as IDraft so other modules will know a draft is available
        zope.interface.alsoProvides(self.request, IDraft)

        # Add draft to request, and backs up request.form and request.other
        # incase we need to revert back to 'almost' original state
        self.setupDraftRequest()

        # Get draft data
        # Request will also be marked with IDrafting at this point
        self.draft = self.getDraft(self.form.getContent(), self.request, portal_type)
        if self.draft is None:
            self.restoreRequest()
            zope.interface.noLongerProvides(self.form.request, IDraft, IDrafting)
            return

        # Store draft in request and draft._form in draftRequestForm
        self.request['DRAFT'] = self.draft
        self.draftRequestForm = getattr(self.draft, '_form', {}).copy()

        # Merge data from draft with request.form
        self.mergeDraftWithRequest()

        # Save draft
        self.saveDraft()

        # Append any data that was not or could not be saved in draft
        # (button actions, items not directly related to widgets, InstanceTypes)
        self.request.form.update(self.formDataNotToSave)

        # Mark request with addition markers
        self.markRequest()

        # We are done drafting; so get rid of marker
        zope.interface.noLongerProvides(self.form.request, IDrafting)
