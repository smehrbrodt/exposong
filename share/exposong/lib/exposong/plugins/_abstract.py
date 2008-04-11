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
import gtk
import gtk.gdk
import gobject
import xml.dom
import xml.dom.minidom
from os.path import join

from exposong.glob import *
from exposong import DATA_PATH, schedule
from exposong.plugins import Plugin

'''
Abstract classes that create plugin functionality.

These classes should not be referrenced, with the exception of `Slide`.
'''

# Abstract functions should use the following:
#	`raise NotImplementedError`


class Presentation:
	'''
	A presentation type to store the text or data for a presentation.
	
	Requires at minimum	a title and slides.
	'''
	def __init__(self, dom = None, filename = None):
		if self.__class__ is Presentation:
			raise NotImplementedError("This class cannot be instantiated.")
		self.type = ""
		self.title = ''
		self.author = {}
		self.copyright = ''
		self.slides = []
		self.filename = filename
		if isinstance(dom, xml.dom.Node):
			self.title = get_node_text(dom.getElementsByTagName("title")[0])
			for el in dom.getElementsByTagName("author"):
				atype = dom.getAttribute("type")
				self.author[atype] = get_node_text(el)
			
			self._set_slides(dom)
	
	def _set_slides(self, dom):
		'Set the slides from xml.'
		slides = dom.getElementsByTagName("slide")
		for sl in slides:
			self.slides.append(Slide(sl))
	
	def get_row(self):
		'Gets the data to add to the presentation list.'
		return (self, self.title)
	
	def set_text_buffer(self, tbuf):
		'Sets the value of a text buffer.'
		rval = ''
		for sl in self.slides:
			rval += sl.get_text() + "\n\n"
		tbuf.set_text(rval[:-2])
	
	def edit(self, parent):
		'Run the edit dialog for the presentation.'
		dialog = gtk.Dialog(_("New Presentation"), parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		if(self.title):
			dialog.set_title(_("Editing %s") % self.title)
		else:
			dialog.set_title(_("New %s Presentation") % self.type.title())
		notebook = gtk.Notebook()
		dialog.vbox.pack_start(notebook, True, True, 6)
		
		vbox = gtk.VBox()
		vbox.set_border_width(4)
		vbox.set_spacing(7)
		hbox = gtk.HBox()
		
		label = gtk.Label(_("Title:"))
		label.set_alignment(0.5, 0.5)
		hbox.pack_start(label, False, True, 5)
		title = gtk.Entry(45)
		title.set_text(self.title)
		hbox.pack_start(title, True, True)
		
		vbox.pack_start(hbox, False, True)
		
		text = gtk.TextView()
		text.set_wrap_mode(gtk.WRAP_WORD)
		self.set_text_buffer(text.get_buffer())
		text_scroll = gtk.ScrolledWindow()
		text_scroll.add(text)
		text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		text_scroll.set_size_request(300, 200)
		vbox.pack_start(text_scroll, True, True)
		notebook.append_page(vbox, gtk.Label(_("Edit")))
		
		notebook.show_all()
		rval = False
		if(dialog.run() == gtk.RESPONSE_ACCEPT):
			bounds = text.get_buffer().get_bounds()
			rval = (title.get_text(), text.get_buffer().get_text(bounds[0], bounds[1]))
		dialog.hide()
		
		if(rval):
			self.title = rval[0]
			self.slides = []
			for sl in rval[1].split("\n\n"):
				self.slides.append(Slide(sl))
			self.to_xml()
			return True
	
	def to_xml(self):
		'Save the data to disk.'
		directory = join(DATA_PATH, 'pres')
		self.filename = check_filename(self.title, directory, self.filename)
		
		doc = xml.dom.getDOMImplementation().createDocument(None, None, None)
		root = doc.createElement("presentation")
		root.setAttribute("type", self.type)
		tNode = doc.createElement("title")
		tNode.appendChild(doc.createTextNode(self.title))
		root.appendChild(tNode)
		for s in self.slides:
			sNode = doc.createElement("slide")
			s.to_node(doc, sNode)
			root.appendChild(sNode)
		doc.appendChild(root)
		outfile = open(join(directory, self.filename), 'w')
		doc.writexml(outfile)
		doc.unlink()
	
	def _on_pres_new(self, *args):
		pres = self.__class__()
		if pres.edit(self):
			sched = schedlist.schedlist.get_active_item()
			if sched and not sched.builtin:
				sched.append(pres)
			#Add presentation to appropriate builtin schedules
			model = schedlist.schedlist.get_model()
			itr = model.get_iter_first()
			while itr:
				sched = model.get_value(itr, 0)
				if sched:
					sched.append(pres)
				itr = model.iter_next(itr)


class Slide:
	'''
	A plain text slide.
	
	Reimplementing this class is optional.
	'''
	def __init__(self, value):
		if isinstance(value, xml.dom.Node):
			self.text = get_node_text(value)
			self.title = value.getAttribute("title")
		elif isinstance(value, str):
			self.text = value
			self.title = None
	
	def get_text(self):
		'Get the text for the presentation.'
		return self.text
	
	def get_markup(self):
		'Get the text for the slide selection.'
		if(self.title):
			return "<b>" + self.title + "</b>\n" + self.text
		else:
			return self.text
	
	def to_node(self, document, node):
		'Populate the node element'
		if(self.title):
			node.setAttribute("title", self.title)
		node.appendChild( document.createTextNode(self.text) )


class Menu:
	'''
	Subclasses can modify the menu using uimanager.
	'''
	def merge_menu(self, uimanager):
		'Merge new values with the uimanager.'
		raise NotImplementedError
	def unmerge_menu(self, uimanager):
		'Remove merged items from the menu.'
		raise NotImplementedError


class Schedule:
	'''
	Hooks to add built-in schedules.
	'''
	def schedule_name(self):
		'Return the string schedule name.'
		raise NotImplementedError
	
	def filter_pres(self, pres):
		'Called on each presentation, and return True if it can be added.'
		raise NotImplementedError


class Screen:
	'''
	Hooks into the presentation screen.
	'''
	def draw(self, surface):
		'Draw anywhere on the screen.'
		return NotImplemented
	
	def header_text(self, text, priority=1):
		'Draw on the header.'
		return NotImplemented
	
	def footer_text(self, text, priority=1):
		'Draw text on the footer.'
		return NotImplemented

