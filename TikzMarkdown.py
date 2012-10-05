#!/usr/bin/env python

from markdown import *
from markdown.extensions import *
from markdown.blockprocessors import BlockProcessor
from markdown.util import AtomicString, etree
import re
from tempfile import mkdtemp
from os import path
from subprocess import check_call
from shutil import rmtree
import glob

def default_prefix(r, uri):
	'''Remove the prefix for namespace `uri`.'''
	r.set('xmlns', uri)
	prefix = '{' + uri + '}'
	for e in r.getiterator():
		if e.tag.startswith(prefix):
			_, e.tag = e.tag.split('}')

def strip_whitespace(r):
	'''Strip all whitespace (bit too agressive)'''
	for e in r.getiterator():
		e.text = e.text and e.text.strip()
		e.tail = e.tail and e.tail.strip()

def collapse_groups(r):
	'''TikZ SVG sets only one attribute per group. Collapse groups with disjoint attributes.'''
	if len(list(r)) == 1 and r.tag == r[0].tag and set(r.attrib.keys()).isdisjoint(set(r[0].attrib.keys())):
		r.attrib.update(r[0].attrib)
		for x in r[0]:
			r.append(x)
		r.remove(r[0])
		collapse_groups(r)
	else:
		for x in r:
			collapse_groups(x)

def process(r):
	default_prefix(r, 'http://www.w3.org/2000/svg')
	strip_whitespace(r)
	collapse_groups(r)

class TikzBlockProcessor(BlockProcessor):
	'''Compile tikzpicture-blocks to SVG.'''
	cache = {}
	BEGIN = r'\begin{tikzpicture}'
	END = r'\end{tikzpicture}'

	def test(self, parent, block):
		return self.BEGIN in block and self.END in block

	def compile(self, tikz):
		print 'compile', tikz
		'''Compile previously unseen TikZ blocks'''
		if tikz not in self.cache:
			tmp = mkdtemp()
			tex = path.join(tmp, 'job.tex')
			with open(tex, 'w') as f:
				print >>f, r'''\batchmode
					\documentclass{standalone}
					\def\pgfsysdriver{pgfsys-tex4ht.def}
					\usepackage{tikz}
					\begin{document}\large'''
				print >>f, tikz
				print >>f, r'\end{document}'
			# Run Tex4Ht, creates SVG file(s).
			check_call('cd {0} && mk4ht xhmlatex job >/dev/null 2>/dev/null'.format(tmp), shell=True)
			# SVGs:
			results = list(glob.glob(path.join(tmp, '*.svg')))
			if results:
				self.cache[tikz] = etree.parse(results[0])
			# Cleanup
			rmtree(tmp)
		return self.cache.get(tikz)

	def run(self, parent, blocks):
		tikz = blocks.pop(0)
		svg = self.compile(tikz)
		if svg: # success
			svg = svg.getroot()
			process(svg)
			parent.append(svg)
		else: # error
			pre = etree.SubElement(parent, 'pre')
			code = etree.SubElement(pre, 'code')
			code.text = AtomicString(tikz)

class TikzExtension(Extension):
	def extendMarkdown(self, md, md_globals):
		md.registerExtension(self)
		md.parser.blockprocessors.add('tikz', TikzBlockProcessor(md.parser), '>empty')



import subprocess
import sys
import pyinotify

class OnWriteHandler(pyinotify.ProcessEvent):
    def my_init(self, cwd, extension, cmd):
        self.cwd = cwd
        self.extensions = extension.split(',')
        self.cmd = cmd

    def _run_cmd(self):
        print '==> Modification detected'
        subprocess.call(self.cmd.split(' '), cwd=self.cwd)

    def process_IN_MODIFY(self, event):
        if all(not event.pathname.endswith(ext) for ext in self.extensions):
            return
        self._run_cmd()


if __name__ == '__main__':
	# Watch folder, compile all.
	import sys
	from pyinotify import *
	md = Markdown(output_format='xhtml5', extensions=[TikzExtension()])
	class CompileHandler(ProcessEvent):
		def process_IN_MODIFY(self, event):
			base, ext = path.splitext(event.pathname)
			if ext in ['.md', '.markdown']:
				print event.pathname
				outfile = base + '.html'
				md.convertFile(input=event.pathname, output=outfile)
				print '  =>', outfile
	wm = WatchManager()
	handler = CompileHandler()
	notifier = Notifier(wm, default_proc_fun=handler)
	wm.add_watch('.', ALL_EVENTS, rec=True, auto_add=True)
	print 'Monitoring. Press ^C to exit.'
	notifier.loop()
