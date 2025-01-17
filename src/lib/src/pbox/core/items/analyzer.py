# -*- coding: UTF-8 -*-
from tinyscript.helpers import lazy_object


__all__ = ["Analyzer"]

__initialized = False


def __init():
    global __initialized
    from .__common__ import _init_base
    from ..executable import Executable
    from ...helpers import file_or_folder_or_dataset, update_logger
    Base = _init_base()
    
    class Analyzer(Base):
        """ Analyzer abstraction.
        
        Extra methods:
          .analyze(executable, **kwargs) [str]
        """
        use_output = True
        
        @update_logger
        def analyze(self, executable, **kwargs):
            """ Runs the analyzer according to its command line format. """
            e = executable if isinstance(executable, Executable) else Executable(executable)
            if not self.check(e.format, **kwargs) or \
               e.extension[1:] in getattr(self, "exclude", {}).get(e.format, []):
                return -1
            # try to analyze the input executable
            output = self.run(e, **kwargs)
            # if packer detection succeeded, we can return packer's label
            return output
        
        @file_or_folder_or_dataset
        @update_logger
        def test(self, executable, **kwargs):
            """ Tests the given item on some executable files. """
            self._test(kwargs.get('silent', False))
            out = self.analyze(executable, **kwargs)
            if out is not None:
                self.logger.info("Output:\n" + out)
    # ensure it initializes only once (otherwise, this loops forever)
    if not __initialized:
        __initialized = True
        # dynamically makes Analyzer's registry of child classes from the default dictionary of analyzers
        #  (~/.packing-box/conf/analyzers.yml)
        Analyzer.source = None
    return Analyzer
Analyzer = lazy_object(__init)

