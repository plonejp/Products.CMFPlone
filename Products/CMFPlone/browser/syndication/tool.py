from zope.component import getMultiAdapter
from Acquisition import aq_parent
from DateTime import DateTime
from zope.interface import implements
from Products.CMFPlone.interfaces.syndication import ISiteSyndicationSettings
from Products.CMFPlone.interfaces.syndication import IFeedSettings
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ISyndicationTool
from Products.CMFCore.utils import registerToolInterface
from Products.CMFDefault.permissions import ModifyPortalContent
from Products.CMFDefault.permissions import ManagePortal
from AccessControl import Unauthorized
from Products.CMFCore.utils import _checkPermission


class SyndicationTool(object):
    implements(ISyndicationTool)

    def editProperties(self, updatePeriod=None, updateFrequency=None,
                       updateBase=None, isAllowed=None, max_items=None):
        """
        Edit the properties for the SystemWide defaults on the
        SyndicationTool.
        """
        registry = getUtility(IRegistry)
        if not _checkPermission(ManagePortal, aq_parent(registry)):
            raise Unauthorized
        settings = registry.forInterface(ISiteSyndicationSettings)
        if isAllowed is not None:
            settings.enabled = isAllowed

        if updatePeriod is not None:
            settings.update_period = updatePeriod

        if updateFrequency is not None:
            settings.update_frequency = int(updateFrequency)

        if updateBase is not None:
            if isinstance(updateBase, basestring):
                updateBase = DateTime(updateBase)
            settings.update_base = updateBase.asdatetime()

        if max_items is not None:
            settings.max_items = int(max_items)

    def getSyndicatableContent(self, obj):
        """
        An interface for allowing folderish items to implement an
        equivalent of PortalFolderBase.contentValues()
        """
        util = getMultiAdapter((obj, obj.REQUEST), name="syndication-util")
        return util.adapter()._items()

    def isSiteSyndicationAllowed(self):
        """
        Return sitewide syndication policy
        """
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISiteSyndicationSettings)
        return settings.enabled

    def isSyndicationAllowed(self, obj=None):
        """
        Check whether syndication is enabled for the site.  This
        provides for extending the method to check for whether a
        particular obj is enabled, allowing for turning on only
        specific folders for syndication.
        """
        settings = IFeedSettings(obj)
        return settings.enabled

    def enableSyndication(self, obj):
        """
        Enable syndication for the obj
        """
        if not _checkPermission(ModifyPortalContent, obj):
            raise Unauthorized
        settings = IFeedSettings(obj)
        settings.enabled = True

    def disableSyndication(self, obj):
        if not _checkPermission(ModifyPortalContent, obj):
            raise Unauthorized
        settings = IFeedSettings(obj)
        settings.enabled = False

registerToolInterface('portal_syndication', ISyndicationTool)
