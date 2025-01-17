# -*- coding: UTF-8 -*-
from tinyscript.helpers import lazy_load_object

from .__common__ import *


__all__ = ["MachO"]


def __init_macho():
    MachOSection = get_section_class("MachOSection")
    
    class MachO(Binary):
        checksum = None
        
        def __iter__(self):
            for s in self.sections:
                yield MachOSection(s)
        
        def _get_builder(self):
            return lief.MachO.Builder(self._parsed)
        
        @property
        def entrypoint(self):
            return self.virtual_address_to_offset(self.entrypoint)
        
        @property
        def entrypoint_section(self):
            return self.section_from_offset(self.entrypoint)
    
    MachO.__name__ = "MachO"
    return MachO
lazy_load_object("MachO", __init_macho)

