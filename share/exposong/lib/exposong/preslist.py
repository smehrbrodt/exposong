#! /usr/bin/env python
#
# Copyright (C) 2008 Fishhookweb.com
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
import gtk.gdk
import gobject

import exposong.slidelist
import exposong.application
import exposong.schedlist

preslist = None #will hold the PresList instance
presfilter = None #will hold PresFilter instance

class PresList(gtk.TreeView):
  '''
  Manage the presentation list.
  '''
  def __init__(self):
    gtk.TreeView.__init__(self)
    self.set_size_request(-1, 250)
    self.prev_selection = None
    
    pixbufrend = gtk.CellRendererPixbuf()
    textrend = gtk.CellRendererText()
    column = gtk.TreeViewColumn( _("Presentation") )
    column.pack_start(pixbufrend, False)
    column.set_cell_data_func(pixbufrend, self._get_row_icon)
    column.pack_start(textrend, True)
    column.set_attributes(textrend, text=1)
    column.set_sort_column_id(1)
    column.set_resizable(False)
    column.set_property('spacing', 4)
    self.append_column(column)
    self.set_headers_clickable(False)
    self.get_selection().connect("changed", self._on_pres_activate)
    self.connect("drag-data-get", self._on_drag_get)
    self.connect("drag-data-received", self._on_pres_drag_received)
    self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
        exposong.application.DRAGDROP_SCHEDULE, gtk.gdk.ACTION_COPY)
  
  def get_active_item(self):
    'Return the presentation of the currently selected item.'
    (model, s_iter) = self.get_selection().get_selected()
    if s_iter:
      return model.get_value(s_iter, 0)
    else:
      return False
  
  def append(self, item):
    'Add a presentation to the list.'
    self.get_model().append((item, item.title, item.type))
  
  def remove(self, item):
    'Delete a presentation from the list.'
    model = self.get_model()
    iter1 = model.get_iter_first()
    while model.get_value(iter1, 0).filename != item.filename:
      iter1 = model.iter_next(iter1)
    self.get_model().remove(iter1)
  
  def has_selection(self):
    'Return true if an item is selected.'
    return bool(self.get_selection().count_selected_rows())
  
  def get_model(self):
    model = gtk.TreeView.get_model(self)
    if isinstance(model, (gtk.TreeModelFilter, gtk.TreeModelSort)):
      return model.get_model()
    return model
  
  def next_pres(self, *args):
    'Go to the next presentation.'
    selection = self.get_selection()
    (model, itr) = selection.get_selected()
    if itr:
      itr2 = model.iter_next(itr)
      if itr2:
        selection.select_iter(itr2)
        self.scroll_to_cell(model.get_path(itr2))
      else: #The last presentation is active.
        return False
    elif model.get_iter_first():
      selection.select_iter(model.get_iter_first())
      self.scroll_to_point(0,0)
    else: #No presentations available.
      return False
    self._on_pres_activate()
  
  def prev_pres(self, *args):
    'Go to the previous presentation.'
    (model, s_iter) = self.get_selection().get_selected()
    if s_iter:
      path = model.get_path(s_iter)
      if path[0] > 0:
        path = (path[0]-1,)
        self.set_cursor(path)
        self.scroll_to_cell(path)
  
  def _on_pres_activate(self, *args):
    'Change the slides to the current presentation.'
    if self.prev_selection != None:
      self.prev_selection.presentation.on_deselect()
    if self.has_selection():
      exposong.slidelist.slidelist.set_presentation(
          self.get_active_item().presentation)
      self.prev_selection = self.get_active_item()
      self.get_active_item().on_select()
    else:
      exposong.slidelist.slidelist.set_presentation(None)
      self.prev_selection = None
    exposong.slidelist.slide_scroll.get_vadjustment().set_value(0)
    #TODO This is not working, may need to change the signal
    exposong.application.main.main_actions.get_action("pres-edit")\
        .set_sensitive(self.has_selection())
    exposong.application.main.main_actions.get_action("pres-delete")\
        .set_sensitive(self.has_selection())
    exposong.application.main.main_actions.get_action("pres-delete-from-schedule")\
        .set_sensitive(self.has_selection() and not self.get_model().builtin)
  
  def _on_pres_edit(self, *args):
    'Edit the presentation.'
    field = exposong.slidelist.slidelist.pres
    if not field:
      return False
    if field.edit():
      self.get_model().refresh_model()
      self._on_pres_activate()
  
  def _on_drag_get(self, treeview, context, selection, info, timestamp):
    'A presentation was dragged.'
    model, iter1 = treeview.get_selection().get_selected()
    selection.set('text/treeview-path', info, model.get_string_from_iter(iter1))
  
  def _on_pres_drag_received(self, treeview, context, x, y, selection, info,
      timestamp):
    'A presentation was reordered.'
    drop_info = treeview.get_dest_row_at_pos(x, y)
    model = treeview.get_model()
    sched = self.get_model() #Gets the current schedule
    path_mv = int(selection.data)
    
    if drop_info:
      path_to, position = drop_info
      itr_to = sched.get_iter(path_to)
    else: #Assumes that if there's no drop info, it's at the end of the list
      path_to = path_mv + 1
      position = gtk.TREE_VIEW_DROP_BEFORE
      itr_to = None
    itr_mv = sched.get_iter(path_mv)
    
    if position is gtk.TREE_VIEW_DROP_AFTER or\
        position is gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
      sched.move_after(itr_mv, itr_to)
    elif position is gtk.TREE_VIEW_DROP_BEFORE or\
        position is gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
      sched.move_before(itr_mv, itr_to)
    
    context.finish(True, False)
  
  def _on_pres_delete_from_schedule(self, *args):
    'Remove the schedule from the current schedule.'
    sched, itr = self.get_selection().get_selected()
    if not itr or sched.builtin:
      return False
    sched.remove(itr)
  
  def _get_row_icon(self, column, cell, model, titer):
    'Returns the icon of the current presentation.'
    pres = model.get_value(titer, 0)
    cell.set_property('pixbuf', pres.get_icon())
  
  @staticmethod
  def get_model_args():
    'Get the arguments to pass to `gtk.ListStore`.'
    return (gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)


class PresFilter(gtk.Entry):
  def __init__(self):
    gtk.Entry.__init__(self, 50)
    
    self.set_width_chars(12)
    self.connect("changed", self._filter)
    self.connect("focus-in-event", exposong.application.main.disable_shortcuts)
    self.connect("focus-out-event", exposong.application.main.enable_shortcuts)
  
  def _filter(self, *args):
    'Filters schedlist by the keywords.'
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
