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
from exposong.plugins import _abstract, Plugin
from exposong import DATA_PATH, schedlist
from exposong.glob import *
import exposong.application
import tarfile, tempfile, os, os.path, shutil

"""
Adds functionality to move schedules, or a full library to another exposong
instance.
"""

information = {
  'name': _("Export/Import Functions"),
  'description': __doc__,
  'required': False,
}

FILE_EXT = ".expo"
_FILTER = gtk.FileFilter()
_FILTER.set_name("Exposong Archive")
_FILTER.add_pattern("*.expo")

class ExportImport(Plugin, _abstract.Menu):
  '''
  Export or Import from file.
  
  A .expo file is a tar.gz file, with the following format:
    sched/ - folder contains all schedule xml files.
    pres/ - folder containing all presentation files.
    image/ - contains files for image presentations.
  '''
  def __init__(self):
    pass
  
  def export_sched(self, *args):
    'Export a single schedule list to file.'
    sched = schedlist.schedlist.get_active_item()
    if not sched:
      return False
    if not sched.filename:
      sched.save()
    dlg = gtk.FileChooserDialog("Export Schedule", exposong.application.main,
        gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dlg.add_filter(_FILTER)
    dlg.set_do_overwrite_confirmation(True)
    dlg.set_current_name(sched.filename.partition(".")[0]+".expo")
    if dlg.run() == gtk.RESPONSE_ACCEPT:
      exposong.application.main._save_schedules() #Make sure schedules are up to date.
      oldpath = os.getcwd()
      os.chdir(DATA_PATH)
      fname = dlg.get_filename()
      if not fname.endswith(".expo"):
        fname += ".expo"
      tar = tarfile.open(fname, "w:gz")
      tar.add("sched/"+sched.filename)
      itr = sched.get_iter_first()
      while itr:
        tar.add("pres/"+sched.get_value(itr, 0).filename)
        if sched.get_value(itr, 0).type == 'image':
          for slide in sched.get_value(itr, 0).slides:
            tar.add("image/"+slide.image.rpartition('/')[2])
        itr = sched.iter_next(itr)
      os.chdir(oldpath)
      tar.close()
    dlg.hide()
  
  def export_lib(self, *args):
    'Export the full library to file.'
    dlg = gtk.FileChooserDialog("Export Schedule", exposong.application.main,
        gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dlg.add_filter(_FILTER)
    dlg.set_do_overwrite_confirmation(True)
    dlg.set_current_name("exposong_library.expo")
    if dlg.run() == gtk.RESPONSE_ACCEPT:
      exposong.application.main._save_schedules() #Make sure schedules are up to date.
      oldpath = os.getcwd()
      os.chdir(DATA_PATH)
      fname = dlg.get_filename()
      if not fname.endswith(".expo"):
        fname += ".expo"
      tar = tarfile.open(fname, "w:gz")
      library = exposong.application.main.library
      itr = library.get_iter_first()
      while itr:
        tar.add("pres/"+library.get_value(itr, 0).filename)
        if library.get_value(itr, 0).type == 'image':
          for slide in library.get_value(itr, 0).slides:
            tar.add("image/"+slide.image.rpartition('/')[2])
        itr = library.iter_next(itr)
      model = schedlist.schedlist.get_model()
      itr = model.iter_children(schedlist.schedlist.custom_schedules)
      while itr:
        tar.add("sched/"+model.get_value(itr, 0).filename)
        itr = model.iter_next(itr)
      os.chdir(oldpath)
      tar.close()
    dlg.hide()
  
  def import_file(self, *args):
    'Import a schedule or library.'
    dlg = gtk.FileChooserDialog("Export Schedule", exposong.application.main,
        gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dlg.add_filter(_FILTER)
    if dlg.run() == gtk.RESPONSE_ACCEPT:
      tar = tarfile.open(dlg.get_filename(), "r:gz")
      # Make a temporary directory so that no files are overwritten.
      tmpdir = tempfile.mkdtemp(
          dlg.get_filename().rpartition(os.sep)[2].partition(".")[0])
      tar.extractall(tmpdir)
      tar.close()
      # TODO: On renaming a presentation, it needs to be updated in a
      # schedule. Do it for images in presentations as well.
      if os.path.isdir(os.path.join(tmpdir, "image")):
        imgs2rename = []
        for nm in os.listdir(tmpdir):
          if not os.path.exists(os.path.join(DATA_PATH, "image", nm)):
            os.rename(os.path.join(tmpdir, "image", nm),
                os.path.join(DATA_PATH, "image", nm))
          else:
            nm2 = find_freefile(os.path.join(DATA_PATH, "image", nm))
            os.rename(os.path.join(tmpdir, "image", nm), 
                os.path.join(DATA_PATH, "image", nm2))
            imgs2rename.append( (nm,nm2) )
      if os.path.isdir(os.path.join(tmpdir, "pres")):
        pres2rename = []
        for nm in os.listdir(tmpdir):
          #TODO Replace image names
          if not os.path.exists(os.path.join(DATA_PATH, "pres", nm)):
            os.rename(os.path.join(tmpdir, "pres", nm),
                os.path.join(DATA_PATH, "pres", nm))
          else:
            nm2 = find_freefile(os.path.join(DATA_PATH, "pres", nm))
            os.rename(os.path.join(tmpdir, "pres", nm), 
                os.path.join(DATA_PATH, "pres", nm2))
            pres2rename.append( (nm,nm2) )
      if os.path.isdir(os.path.join(tmpdir, "sched")):
        for nm in os.listdir(tmpdir):
          #TODO Replace presentation names
          if not os.path.exists(os.path.join(DATA_PATH, "sched", nm)):
            os.rename(os.path.join(tmpdir, "sched", nm),
                os.path.join(DATA_PATH, "sched", nm))
          else:
            nm2 = find_freefile(os.path.join(DATA_PATH, "sched", nm))
            os.rename(os.path.join(tmpdir, "sched", nm),
                os.path.join(DATA_PATH, "sched", nm2))
      if os.path.isdir(os.path.join(tmpdir, "bg")):
        for nm in os.listdir(tmpdir):
          if not os.path.exists(os.path.join(DATA_PATH, "bg", nm)):
            os.rename(os.path.join(tmpdir, "bg", nm),
                os.path.join(DATA_PATH, "bg", nm))
          else:
            nm2 = find_freefile(os.path.join(DATA_PATH, "bg", nm))
            os.rename(os.path.join(tmpdir, "bg", nm),
                os.path.join(DATA_PATH, "bg", nm2))
      #for p1 in os.listdir(tmpdir):
      #  p1abs = os.path.join(tmpdir, p1)
      #  if os.path.isdir(p1abs):
      #    for p2 in os.listdir(p1abs):
      #      flname = find_freefile(os.path.join(DATA_PATH,p1,p2))
      #      os.rename(os.path.join(tmpdir,p1,p2), flname)
      #  else:
      #    print "Error: Not a directory ("+p1abs+")"
      #shutil.rmtree(tmpdir)
    dlg.hide()
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    actiongroup = gtk.ActionGroup('export-import')
    actiongroup.add_actions([('import', None, _("_Import"), None,
            _("Import a schedule or full library."), self.import_file),
        ('export-sched', None, _("_Export Schedule"), None,
            None, self.export_sched),
        ('export-lib', None, _("Export _Library"), None,
            None, self.export_lib)])
    uimanager.insert_action_group(actiongroup, -1)
    
    #Had to use position='top' to put them above "Quit"
    self.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name="MenuBar">
        <menu action="File">
          <separator position="top" />
          <menuitem action="export-sched" position="top" />
          <menuitem action="export-lib" position="top" />
          <menuitem action="import" position="top" />
        </menu>
      </menubar>
      """)
  
  def unmerge_menu(self, uimanager):
    'Remove merged items from the menu.'
    uimanager.remove_ui(self.menu_merge_id)

