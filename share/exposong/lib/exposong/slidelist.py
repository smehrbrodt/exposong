#! /usr/bin/env python
#
# Copyright (C) 2008-2010 Exposong.org
#
# ExpoSong is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import gtk
import gobject
import pango
import random

import exposong.screen

slidelist = None #will hold instance of SlideList
slide_scroll = None

class SlideList(gtk.TreeView):
  '''
  Class to manipulate the text_area in the presentation program.
  '''
  def __init__(self):
    self.pres = None
    self.slide_order = ()
    self.slide_order_index = -1
    self.__timer = 0 #Used to stop or reset the timer if the presentation or slide changes.

    gtk.TreeView.__init__(self)
    self.set_size_request(280, 200)
    self.set_enable_search(False)
    
    self.column1 = gtk.TreeViewColumn( _("Slide"))
    self.column1.set_resizable(False)
    self.append_column(self.column1)
    #self.set_column()
    
    self.set_model(gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))
    #self.set_headers_visible(False)
    self.get_selection().connect("changed", self._on_slide_activate)
  
  def set_presentation(self, pres):
    'Set the active presentation.'
    self.pres = pres
    slist = self.get_model()
    if pres is None:
      slist.clear()
    else:
      slist.clear()
      if not hasattr(self, 'pres_type') or self.pres_type is not pres.get_type():
        self.pres_type = pres.get_type()
        pres.slide_column(self.column1, exposong.slidelist.slidelist)
      slist = self.get_model()
      for slide in pres.get_slide_list():
        slist.append(slide)
      self.slide_order = pres.get_order()
      self.slide_order_index = -1
    self.__timer += 1
    men = slist.get_iter_first() is not None
    exposong.application.main.main_actions.get_action("pres-slide-next")\
        .set_sensitive(men)
    exposong.application.main.main_actions.get_action("pres-slide-prev")\
        .set_sensitive(men)
  
  def get_active_item(self):
    'Return the selected `Slide` object.'
    (model, s_iter) = self.get_selection().get_selected()
    if s_iter:
      return model.get_value(s_iter, 0)
    else:
      return False
  
  def _move_to_slide(self, widget, mv):
    'Move to the slide at mv. This ignores slide_order_index.'
    order_index = self.slide_order_index
    if self.slide_order_index == -1 and self.get_selection().count_selected_rows() > 0:
      (model,itr) = self.get_selection().get_selected()
      cur = model.get_string_from_iter(itr)
      cnt = 0
      for o in self.slide_order:
        if o == int(cur):
          if len(self.slide_order) > cnt+mv and cnt+mv > 0:
            self.to_slide(self.slide_order[cnt+mv])
            self.slide_order_index = cnt+mv
            return True
          else:
            return False
        cnt += 1
    if order_index == self.slide_order_index and \
        len(self.slide_order) > order_index+mv and order_index+mv >= 0:
      self.to_slide(self.slide_order[order_index + mv])
      self.slide_order_index = order_index + mv
      return True
  
  def prev_slide(self, widget):
    'Move to the previous slide.'
    self._move_to_slide(widget, -1)
  
  def next_slide(self, widget):
    'Move to the next slide.'
    self._move_to_slide(widget,  1)

  def to_slide(self, slide_num):
    model = self.get_model()
    itr = model.iter_nth_child(None, slide_num)
    if itr:
      selection = self.get_selection()
      selection.select_iter(itr)
      self.scroll_to_cell(model.get_path(itr))
  
  def _on_slide_activate(self, *args):
    'Present the selected slide to the screen.'
    exposong.screen.screen.draw()
    self.slide_order_index = -1
    
    #Reset the time
    self.__timer += 1
    if self.pres and self.pres.timer:
      gobject.timeout_add(self.pres.timer*1000, self._set_timer, self.__timer)
  
  def _set_timer(self, t):
    'Starts the timer, or continues a current timer.'
    if t <> self.__timer:
      return False
    self.next_slide(None)
    return True

