#! /usr/bin/env python
#
#	Copyright (C) 2008 Fishhookweb.com
#
#	ExpoSong is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
import pygtk
import gtk
import gtk.gdk
import imp
import os.path

GRADIENT_DIRS = ('Top Left to Bottom Right', 'Top to Bottom',
				'Top Right to Bottom Left', 'Left to Right')
class Prefs:
	def __init__(self):
		self.cfg = {'general.ccli': '',
				'pres.max_font_size': 56,
				'pres.bg': ((0, 13107, 19660), (0, 26214, 39321)),
				'pres.bg_angle': GRADIENT_DIRS[0],
				'pres.text_color': (65535, 65535, 65535),
				'pres.text_shadow': (0, 0, 0, 26214)}
		self.load()
	def __getitem__(self, key):
		if key in self.cfg:
			return self.cfg[key]
		raise KeyError, 'Could not find key: '+key
	def __setitem__(self, key, value):
		if value == None:
			self.__delitem__(key, value)
		else:
			self.cfg[key] = value
	def __delitem__(self, key):
		del self.cfg[key]
	
	def load(self):
		try:
			config = imp.load_source('config', 'config.py')
		except IOError:
			return False
		for k,v in self.cfg.iteritems():
			ksp = k.split(".")
			if hasattr(config, ksp[0]) and hasattr(getattr(config, ksp[0]), ksp[1]):
				self.cfg[k] = getattr(getattr(config, ksp[0]), ksp[1])
			
	def save(self):
		cfile = open('config.py', 'r+')
		cnt = 0
		for line in cfile:
			cnt += len(line)
			if line.startswith('# @START_WRITE'):
				break
		cfile.seek(cnt)
		cfile.write("\n\n")
		cnt += 1
		
		for key, value in self.cfg.iteritems():
			ln = key+' = '+repr(value)+'\n'
			cfile.write(ln)
			cnt += len(ln)
		
		cfile.truncate(cnt)
		cfile.close()
	
	def dialog(self, parent):
		PrefsDialog(parent, self)

LABEL_SPACING = 12
WIDGET_SPACING = 4

class PrefsDialog(gtk.Dialog):
	def __init__(self, parent, config):
		self.widgets = {}
		gtk.Dialog.__init__(self, "Preferences", parent, 0,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		notebook = gtk.Notebook()
		self.vbox.pack_start(notebook, True, True, 5)
		
		#General Page
		self.table = gtk.Table(2, 8)
		self.table.set_row_spacings(10)
		self.table.set_border_width(10)
		
		self.section_title("Legal", 0)
		g_ccli = self.text_pref("CCLI #", config['general.ccli'], 1)
		
		notebook.append_page(self.table, gtk.Label("General"))
		
		#Presentation Page
		self.table = gtk.Table(4, 15)
		self.table.set_row_spacings(10)
		self.table.set_border_width(10)
		
		if isinstance(config['pres.bg'], tuple):
			if isinstance(config['pres.bg'][0], tuple):
				bg_type = 'g' #Gradiant
				bg_grad = config['pres.bg']
				bg_solid = config['pres.bg'][0]
				bg_img = ''
			else:
				bg_type = 's' #Solid
				bg_grad = (config['pres.bg'], config['pres.bg'])
				bg_solid = config['pres.bg']
				bg_img = ''
		else:
			bg_type = 'i'
			bg_grad = ((0,0,0), (0,0,0))
			bg_solid = (0,0,0)
			bg_img = config['pres.bg']
			
		
		self.section_title("Background", 0)
		p_r_solid = self.radio_pref("_Solid", bg_type=='s', 1)
		self.p_bgsol = self.color_pref(None, bg_solid, 1)
		self.p_bgsol.set_sensitive(bg_type=='s')
		p_r_solid.connect('toggled', self._on_toggle, self.p_bgsol)
		p_r_gr = self.radio_pref("_Gradiant", bg_type=='g', 2, group=p_r_solid)
		self.p_bggr = self.color_pref(None, bg_grad, 2)
		self.p_bggr[0].set_sensitive(bg_type=='g')
		self.p_bggr[1].set_sensitive(bg_type=='g')
		self.p_bggrang = self.combo_pref("Gradiant Angle\n(Clockwise From Up)", GRADIENT_DIRS, config['pres.bg_angle'], 3)
		p_r_gr.connect('toggled', self._on_toggle, self.p_bggr+[self.p_bggrang])
		
		p_r_img = self.radio_pref("_Image", bg_type=='i', 4, group=p_r_solid)
		p_r_img.set_sensitive(False) #Disabled until the feature is added
		self.p_bgimg = self.file_pref(None, bg_img, 4)
		self.p_bgimg.set_sensitive(bg_type=='i')
		self.p_bgimg.set_size_request(180, -1)
		p_r_img.connect('toggled', self._on_toggle, self.p_bgimg)
		
		self.section_title("Font", 6)
		p_txt = self.color_pref("Text Color", config['pres.text_color'], 7)
		p_shad = self.color_pref("Text Shadow", config['pres.text_shadow'], 8, True)
		p_maxsize = self.spinner_pref("Max Font Size", gtk.Adjustment(config['pres.max_font_size'], 0, 96, 1), 9)
		
		notebook.append_page(self.table, gtk.Label("Presentation"))
		
		self.show_all()
		if(self.run() == gtk.RESPONSE_ACCEPT):
			if p_r_gr.get_active():
				tlf = self.p_bggr[0].get_color()
				brt = self.p_bggr[1].get_color()
				config['pres.bg'] = ((tlf.red, tlf.green, tlf.blue),
						(brt.red, brt.green, brt.blue))
				config['pres.bg_angle'] = self.p_bggrang.get_active_text()
			elif p_r_solid.get_active():
				bgcol = self.p_bgsol.get_color()
				config['pres.bg'] = (bgcol.red, bgcol.green, bgcol.blue)
			elif p_r_img.get_active():
				img = self.p_bgimg.get_uri()
				#TODO Process the file
			txtc = p_txt.get_color()
			config['pres.text_color'] = (txtc.red, txtc.green, txtc.blue)
			txts = p_shad.get_color()
			config['pres.text_shadow'] = (txts.red, txts.green, txts.blue, p_shad.get_alpha())
			config['pres.max_font_size'] = p_maxsize.get_value()
			config['general.ccli'] = g_ccli.get_text()
			
			config.save()
			parent.presentation.draw()
		
		self.hide()
	
	def section_title(self, title, top):
		hbox = gtk.HBox()
		label = gtk.Label()
		label.set_markup("<b>"+title+"</b>")
		label.set_alignment(0.0, 0.5)
		self.table.attach(label, 0, 4, top, top+1, gtk.FILL, 0, 0)
	
	def text_pref(self, label, value, top):
		self.label(label, top)
		
		entry = gtk.Entry(10)
		entry.set_text(value)
		self.table.attach(entry, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
		return entry
	
	def file_pref(self, label, value, top):
		self.label(label, top)
		
		filech = gtk.FileChooserButton("Choose File")
		filech.set_filename(value)
		filech.set_current_folder(os.path.expanduser('~'))
		self.table.attach(filech, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
		return filech
	
	def color_pref(self, label, value, top, alpha=False):
		self.label(label, top)
		
		if(isinstance(value[0], tuple)):
			buttons = []
			cnt = 2
			for v in value:
				button = gtk.ColorButton(gtk.gdk.Color(int(v[0]), int(v[1]), int(v[2])))
				self.table.attach(button, cnt, cnt+1, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
				cnt += 1
				buttons.append(button)
			return buttons
		else:
			button = gtk.ColorButton(gtk.gdk.Color(int(value[0]), int(value[1]), int(value[2])))
			self.table.attach(button, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
			if(alpha):
				button.set_alpha(int(value[3]))
				button.set_use_alpha(True)
			return button
	
	def spinner_pref(self, label, adjustment, top):
		self.label(label, top)
		
		spinner = gtk.SpinButton(adjustment, 2.0)
		self.table.attach(spinner, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
		return spinner
	
	def combo_pref(self, label, options, value, top):
		self.label(label, top)
		
		combo = gtk.combo_box_new_text()
		for i in range(len(options)):
			combo.append_text(options[i])
			if isinstance(value, str) and options[i] == value:
				combo.set_active(i)
		self.table.attach(combo, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
		return combo
	
	def radio_pref(self, label, active, top, group = None):
		radio = gtk.RadioButton(group, label)
		radio.set_alignment(0.0, 0.5)
		radio.set_active(active)
		self.table.attach(radio, 1, 2, top, top+1, gtk.FILL, 0, LABEL_SPACING)
		return radio
	
	def label(self, label, top):
		if isinstance(label, str) and len(label):
			label = gtk.Label(label)
			label.set_alignment(0.0, 0.5)
		if isinstance(label, gtk.Widget):
			self.table.attach(label, 1, 2, top, top+1, gtk.FILL, 0, LABEL_SPACING)
	
	def _on_toggle(self, button, target):
		if isinstance(target, gtk.Widget):
			target.set_sensitive(button.get_active())
		elif isinstance(target, (tuple, list)):
			for t in target:
				self._on_toggle(button, t)

