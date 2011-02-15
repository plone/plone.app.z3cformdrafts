"""Z3cFormDrafts FieldWidgits Implementation
"""
__docformat__ = "reStructuredText"
import zope.component
import zope.interface
import zope.location
import zope.schema.interfaces

from z3c.form import interfaces

from plone.app.drafts.dexterity import beginDrafting
from plone.app.drafts.utils import getCurrentDraft
from plone.app.drafts.interfaces import IDraftProxy

from plone.app.z3cformdrafts.interfaces import IZ3cFormDataContext, IZ3cDraft
from plone.app.drafts.interfaces import IDrafting

from zope.interface import implements
from zope.interface.declarations import getObjectSpecification
from zope.interface import implementedBy
from zope.interface import providedBy
from zope.interface.declarations import ObjectSpecificationDescriptor

from Acquisition import aq_base


class Z3cFormDataContext(object):

    zope.interface.implements(IZ3cFormDataContext)

    createDraft = False

    def __init__(self, content, request, form):
        self.content = content
        self.request = request
        self.form = form
        from Acquisition import aq_inner
        self.context = aq_inner(self.form.context)

    def adapt(self):
        """If we are drafting a content item, record form data information to the
        draft, but read existing data from the underlying object.
        """
        # Set up the draft (sets cookies, markers, etc)
        portal_type = getattr(self.form, 'portal_type', None)
        draft = getCurrentDraft(self.request, create=False)
        if not draft and not self.createDraft:
            return self.content

        if not draft:
            beginDrafting(self.context, self.form)
            draft = getCurrentDraft(self.request, create=self.createDraft)

        if draft is None:
            return self.content  # return contnet, not context

        # Make sure cache is created fresh incase context changed from last visit
        # (empty draft)
        # Draft has to be 'marked' with additional interfaces before the proxy
        # is created since the proxy caches __providedBy__ and therefore anything
        # added after proxy is created will not exist in cache
            #and self.content.portal_type != portal_type
        if (IZ3cDraft.providedBy(draft) == False and self.context.portal_type != portal_type):
            setDefaults = False
            for field in self.form.fields.values():
                # Mark draft interface provided by field so it can be adapted
                #
                # TODO:  Note that it will adapt, but not properly, but enuogh
                # to work for now; still need more interfaces added to draft I
                # would think.  Example field has interface type:
                # <InterfaceClass plone.app.dexterity.behaviors.metadata.IBasic>
                # and you adapt it, you will get:
                # <plone.app.drafts.draft.Draft object at 0xe7310ec>, therefore
                # special get/set handlers will not be accessed in ++add++ form.
                if not field.field.interface.providedBy(draft):
                    # Mark draft (add form)
                    zope.interface.alsoProvides(draft, field.field.interface)
                    setDefaults = True

                # Provide default value on draft
                # (uses standard datamanager since proxy is not yet created)
                if setDefaults == True:
                    dm = zope.component.getMultiAdapter(
                        (draft, field.field), interfaces.IDataManager)
                    value = field.field.default or field.field.missing_value
                    dm.set(value)

        if not IZ3cDraft.providedBy(draft):
            zope.interface.alsoProvides(draft, IZ3cDraft)

        if not IDrafting.providedBy(draft):
            zope.interface.alsoProvides(draft, IDrafting)

        proxy = Z3cFormDraftProxy(draft, self.context)

        # TODO: MODIFY INTERFACE to include DRAFT field; not just marker
        self.request['DRAFT'] = proxy
        zope.interface.alsoProvides(self.request, IZ3cDraft)

        return proxy


class ProxySpecification(ObjectSpecificationDescriptor):
    """A __providedBy__ decorator that returns the interfaces provided by
    the draft and the proxy
    """

    def __get__(self, inst, cls=None):

        # We're looking at a class - fall back on default
        if inst is None:
            return getObjectSpecification(cls)

        # Get the interfaces implied by the class as a starting point.
        provided = implementedBy(cls)

        # Get interfaces directly provided by the draft proxy
        provided += getattr(inst._Z3cFormDraftProxy__draft, '__provides__', provided)

        # Add the interfaces provided by the target
        target = aq_base(inst._Z3cFormDraftProxy__target)
        if target is None:
            return provided

        provided += providedBy(target)

        return provided


class Z3cFormDraftProxy(object):
    """Ripped from plone.app.drafts.proxy.DraftProxy to provide a custom
    __providedBy__ ProxySpecification.

    A simple proxy object that is initialised with a draft object and the
    underlying target. All attribute and annotation writes are performed
    against the draft; all reads are performed against the draft unless the
    specified attribute or key is not not found, in which case the they are
    read from the target object instead.

    Attribute deletions are saved in a set ``draft._proxyDeleted``. Annotation
    key deletions are saved in a set ``deaft._proxyAnnotationsDeleted``.
    """

    __providedBy__ = ProxySpecification()

    implements(IDraftProxy)

    def __init__(self, draft, target):
        self.__dict__['_Z3cFormDraftProxy__draft'] = draft
        self.__dict__['_Z3cFormDraftProxy__target'] = target

    def __getattr__(self, name):
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name in deleted:
            raise AttributeError(name)

        if hasattr(self.__draft, name):
            return getattr(self.__draft, name)

        #return getattr(self.__target, name)
        try:
            return getattr(self.__target, name)
        except AttributeError:
            pass

    def __setattr__(self, name, value):
        setattr(self.__draft, name, value)

        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name in deleted:
            deleted.remove(name)
            self.__draft._p_changed

    def __delattr__(self, name):
        getattr(self, name)  # allow attribute error to be raised

        # record deletion
        deleted = getattr(self.__draft, '_proxyDeleted', set())
        if name not in deleted:
            deleted.add(name)
            setattr(self.__draft, '_proxyDeleted', deleted)

        # only delete on draft
        if hasattr(self.__draft, name):
            delattr(self.__draft, name)
