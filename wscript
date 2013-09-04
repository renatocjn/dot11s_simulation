## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

import os

def build(bld):
	for filename in os.listdir(os.path.join('dot11s_simulations', 'src')):
		if not filename.startswith('.') and filename.endswith('.cc'):
			obj = bld.create_ns3_program(os.path.splitext(filename)[0], ['internet', 'mobility', 'wifi', 'mesh', 'flow-monitor'])
			obj.source = os.path.join('src', filename)
