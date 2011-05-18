import zope.component
import zope.interface
from z3c.form import interfaces


def MultiWidget_getWidget(self, idx):
    # This monkey patch sets the widgets ignoreContext, ignoreRequest and
    # context based on self.ignoreContext, self.ignoreRequest and self.context
    """Setup widget based on index id with or without value."""
    valueType = self.field.value_type
    widget = zope.component.getMultiAdapter((valueType, self.request),
        interfaces.IFieldWidget)
    self.setName(widget, idx)
    widget.mode = self.mode
    widget.ignoreContext = self.ignoreContext
    widget.ignoreRequest = self.ignoreRequest
    widget.context = self.context
    #set widget.form (objectwidget needs this)
    if interfaces.IFormAware.providedBy(self):
        widget.form = self.form
        zope.interface.alsoProvides(
            widget, interfaces.IFormAware)
    widget.update()
    return widget


def MultiWidget_extract(self, default=interfaces.NO_VALUE):
    # This monkey patch allows extract to be compatible with drafts by allowing
    # the counterName not to exist if self.ignoreContext = True and then will
    # use the len(self.request.get(widget.name, [])) to be the counter value
    if self.request.get(self.counterName) is None:
        # counter marker not found
        return interfaces.NO_VALUE
    counter = int(self.request.get(self.counterName, 0))
    values = []
    append = values.append
    # extract value for existing widgets
    value = zope.component.getMultiAdapter((self.context, self.field),
                                            interfaces.IDataManager).query()
    for idx in range(counter):
        widget = self.getWidget(idx)
        # Added for drafts code since its possible to have counter and no
        # request.form value; especially if ajax validation is enabled
        if (widget.value is None and widget.name not in self.request):
            if not isinstance(value, list) or idx >= len(value):
                continue
            widget.value = value[idx]
        append(widget.value)
    if len(values) == 0:
        # no multi value found
        return interfaces.NO_VALUE
    return values
