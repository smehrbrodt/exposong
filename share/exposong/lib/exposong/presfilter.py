# coding: utf-8
#
# SearchEntry - An enhanced search entry with alternating background colouring 
#         and timeout support
#
# Copyright (C) 2007 Sebastian Heinlein
#               2007-2009 Canonical Ltd.
#               2010 ExpoSong.org
#
# Authors:
#  Sebastian Heinlein <glatzor@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA

import gtk
import gobject

import exposong.application
import exposong.preslist

class PresFilter(gtk.Entry):

  __gsignals__ = {'terms-changed':(gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE,
                   (gobject.TYPE_STRING,))}

  SEARCH_TIMEOUT = 200

  def __init__(self):
    """
    Creates an enhanced IconEntry that supports a timeout when typing
    and uses a different background colour when the search is active
    """
    gtk.Entry.__init__(self)
    
    self._handler_changed = self.connect_after("changed",
                           self._on_changed)
    self.connect("icon-press", self._on_icon_pressed)
    self.connect("key-press-event", self._on_key_pressed)
    self.connect("focus-in-event", exposong.application.main.disable_shortcuts)
    self.connect("focus-out-event", exposong.application.main.enable_shortcuts)
    self.connect("terms-changed", self._filter)
    
    # Make sure icons are supported by GTK version
    self.use_icons = gtk.gtk_version[0] >= 2 and gtk.gtk_version[1] > 16
    if self.use_icons:
      self.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_FIND)
    
    # Do not draw a yellow bg if an a11y theme is used
    settings = gtk.settings_get_default()
    theme = settings.get_property("gtk-theme-name")
    self._a11y = (theme.startswith("HighContrast") or
            theme.startswith("LowContrast"))
    
    # set sensible atk name
    atk_desc = self.get_accessible()
    atk_desc.set_name(_("Search"))

    # data
    self._timeout_id = 0

  def _on_icon_pressed(self, widget, icon, mouse_button):
    """
    Emit the terms-changed signal without any time out when the clear
    button was clicked
    """
    if icon == gtk.ENTRY_ICON_SECONDARY:
      # clear with no signal and emit manually to avoid the
      # search-timeout
      self.clear_with_no_signal()
      self.grab_focus()
      self.emit("terms-changed", "")
    elif icon == gtk.ENTRY_ICON_PRIMARY:
      self.grab_focus()

  def _on_key_pressed(self, widget, event):
    if event.keyval == gtk.keysyms.Escape:
      self.clear_with_no_signal()
      self.emit("terms-changed", "")

  def clear(self):
    self.set_text("")
    self._check_style()

  def clear_with_no_signal(self):
    """Clear and do not send a term-changed signal"""
    self.handler_block(self._handler_changed)
    self.clear()
    self.handler_unblock(self._handler_changed)

  def _emit_terms_changed(self):
    text = self.get_text()
    self.emit("terms-changed", text)

  def _on_changed(self, widget):
    """
    Call the actual search method after a small timeout to allow the user
    to enter a longer search term
    """
    self._check_style()
    if self._timeout_id > 0:
      gobject.source_remove(self._timeout_id)
    self._timeout_id = gobject.timeout_add(self.SEARCH_TIMEOUT,
                         self._emit_terms_changed)

  def _check_style(self):
    """
    Use a different background colour if a search is active
    """
    # show/hide icon
    if self.use_icons:
      if self.get_text() != "":
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, gtk.STOCK_CLEAR)
      else:
        self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
    # Based on the Rhythmbox code
    yellowish = gtk.gdk.Color(63479, 63479, 48830)
    black = gtk.gdk.Color(0, 0, 0)
    if self._a11y == True:
      return
    if self.get_text() == "":
      self.modify_base(gtk.STATE_NORMAL, None)
      self.modify_text(gtk.STATE_NORMAL, None)
    else:
      self.modify_base(gtk.STATE_NORMAL, yellowish)
      self.modify_text(gtk.STATE_NORMAL, black)
      
  def _filter(self, *args):
    'Filters schedlist by the keywords.'
    preslist = exposong.preslist.preslist
    if self.get_text() == "":
      preslist.set_model(preslist.get_model())
    else:
      filt = preslist.get_model().filter_new()
      filt.set_visible_func(self._visible_func)
      preslist.set_model(filt)

  def _visible_func(self, model, itr):
    'Tests the row for visibility.'
    return model.get_value(itr, 0).matches(self.get_text())

  def focus(self, *args):
    'Sets the focus (for an menu action).'
    self.grab_focus()
