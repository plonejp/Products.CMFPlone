# -*- coding: utf-8 -*-
from plone.app.layout.navigation.root import getNavigationRootObject
from plone.app.theming.utils import theming_policy
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import ITinyMCESchema
from Products.CMFPlone.utils import get_portal
from zope.component import getUtility

import json


class TinyMCESettingsGenerator(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.settings = getUtility(IRegistry).forInterface(
            ITinyMCESchema,
            prefix="plone",
            check=False
        )
        self.nav_root = getNavigationRootObject(
            self.context,
            get_portal(),
        )
        self.nav_root_url = self.nav_root.absolute_url()

    def get_theme(self):
        return theming_policy().get_theme()

    def get_content_css(self, style_css=''):
        files = [
            '{0}/++plone++static/plone-compiled.css'.format(self.nav_root_url)
        ]
        if style_css:
            files.extend(style_css.split(','))
        content_css = self.settings.content_css or []
        for url in content_css:
            if url and url.strip():
                files.append('/'.join([self.nav_root_url, url.strip()]))
        theme = self.get_theme()
        tinymce_content_css = getattr(theme, 'tinymce_content_css', None)
        if tinymce_content_css is not None:
            files.append(self.nav_root_url + theme.tinymce_content_css)

        return ','.join(files)

    def get_style_format(self, txt, _type='format', base=None):
        parts = txt.strip().split('|')
        if len(parts) < 2:
            return
        if base is None:
            val = {}
        else:
            val = base
        val.update({
            'title': parts[0],
            _type: parts[1]
        })
        if len(parts) > 2:
            val['icon'] = parts[2]
        return val

    def get_all_style_formats(self):
        header_styles = self.settings.header_styles or []
        block_styles = self.settings.block_styles or []
        inline_styles = self.settings.inline_styles or []
        alignment_styles = self.settings.alignment_styles or []
        table_styles = self.settings.table_styles or []
        return [{
            'title': 'Headers',
            'items': [self.get_style_format(t) for t in header_styles]
        }, {
            'title': 'Block',
            'items': [self.get_style_format(t) for t in block_styles]
        }, {
            'title': 'Inline',
            'items': [self.get_style_format(t) for t in inline_styles]
        }, {
            'title': 'Alignment',
            'items': [self.get_style_format(t) for t in alignment_styles]
        }, {
            'title': 'Tables',
            'items': [
                self.get_style_format(t, 'classes', {'selector': 'table'})
                for t in table_styles
            ]
        }]

    def get_tiny_config(self):
        settings = self.settings
        importcss_file_filter = '%s/++plone++static/tinymce-styles.css' % (
            self.nav_root_url
        )

        theme = self.get_theme()
        if theme and getattr(theme, 'tinymce_styles_css', None):
            importcss_file_filter += ',%s/%s' % (
                self.nav_root_url,
                theme.tinymce_styles_css.lstrip('/'))

        tiny_config = {
            'resize': 'both' if settings.resizing else False,
            'content_css': self.get_content_css(importcss_file_filter),
            'plugins': [
                'plonelink',
                'ploneimage',
                'importcss'
            ] + settings.plugins,
            'external_plugins': {},
            'toolbar': settings.toolbar,
            'entity_encoding': settings.entity_encoding,
            'importcss_append': True,
            'importcss_file_filter': importcss_file_filter,
            'browser_spellcheck': True
        }
        toolbar_additions = settings.custom_buttons or []

        if settings.editor_height:
            tiny_config['height'] = settings.editor_height
        if settings.autoresize:
            tiny_config['plugins'].append('autoresize')
            tiny_config['autoresize_max_height'] = 1000  # hard coded?
        if settings.editor_width:
            tiny_config['width'] = settings.editor_width

        # specific plugin options
        if 'contextmenu' in settings.plugins:
            tiny_config['contextmenu'] = "plonelink ploneimage inserttable |"\
                " cell row column deletetable"

        if settings.libraries_spellchecker_choice == 'AtD':
            mtool = getToolByName(self.context, 'portal_membership')
            member = mtool.getAuthenticatedMember()
            member_id = member.getId()
            if member_id:
                if 'compat3x' not in tiny_config['plugins']:
                    tiny_config['plugins'].append('compat3x')
                tiny_config['external_plugins']['AtD'] = (
                    '{0}/++plone++static/tinymce-AtD-plugin/'
                    'editor_plugin.js'.format(self.nav_root_url)
                )
                # None when Anonymous User
                tiny_config['atd_rpc_id'] = 'plone-' + member_id
                tiny_config['atd_rpc_url'] = self.nav_root_url
                tiny_config['atd_show_types'] = ','.join(
                    settings.libraries_atd_show_types
                )
                tiny_config['atd_ignore_strings'] = ','.join(
                    settings.libraries_atd_ignore_strings
                )
                toolbar_additions.append('AtD')
        elif settings.libraries_spellchecker_choice == 'AtD':
            tiny_config['browser_spellcheck'] = True

        if toolbar_additions:
            tiny_config['toolbar'] += ' | {0}'.format(
                ' '.join(toolbar_additions)
            )

        for plugin in settings.custom_plugins or []:
            parts = plugin.split('|')
            if len(parts) != 2:
                continue
            tiny_config['external_plugins'][parts[0]] = parts[1]

        tiny_config['style_formats'] = self.get_all_style_formats()
        if settings.formats:
            try:
                tiny_config['formats'] = json.loads(settings.formats)
            except ValueError:
                pass

        if settings.menubar:
            tiny_config['menubar'] = settings.menubar
        if settings.menu:
            try:
                tiny_config['menu'] = json.loads(settings.menu)
            except ValueError:
                pass

        if hasattr(settings, 'templates') and settings.templates:
            try:
                tiny_config['templates'] = json.loads(settings.templates)
            except ValueError:
                pass

        if settings.other_settings:
            try:
                tiny_config.update(json.loads(settings.other_settings))
            except ValueError:
                pass

        return tiny_config
