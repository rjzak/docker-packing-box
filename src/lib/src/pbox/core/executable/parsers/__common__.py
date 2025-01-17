# -*- coding: UTF-8 -*-
from tinyscript import functools

__all__ = ["get_section_class", "supported_parsers", "AbstractParsedExecutable"]

DEFAULT_SECTION_SLOTS = ["name", "size", "offset", "content", "virtual_address"]


def supported_parsers(*parsers):
    def _wrapper(f):
        @functools.wraps(f)
        def _subwrapper(parsed, *args, **kwargs):
            if parsed.parser not in parsers:
                raise ParserError("parser '%s' is not supported alteration '%s'" % f.__name__.lstrip("_"))
            return f(parsed, *args, **kwargs)
        return _subwrapper
    return _wrapper


class AbstractBase:
    # this allows to call e.g. section['name'] instead of section.name (blocked in eval2(...) when evaluating
    #  expressions from YAML configurations)
    def __getitem__(self, name):
        if not name.startswith("_"):
            return getattr(self, name)
        raise KeyNotAllowedError(name)
    
    def __repr__(self):
        name = "" if not hasattr(self, "name") else " (%s)" % self.name
        return "<%s%s object at 0x%x>" % (self.__class__.__name__, name, id(self))


class AbstractParsedExecutable(AbstractBase):
    def __getitem__(self, name):
        v = super().__getitem__(name)
        if "header" in name.lower() and not hasattr(v, "__getitem__"):
            try:
                setattr(v, "__getitem__", AbstractBase.__getitem__.__get__(v, v.__class__))
            except AttributeError:
                pass
        return v
    
    def __iter__(self):
        raise NotImplementedError("__iter__")
    
    def build(self, **kw):
        raise NotImplementedError("build")
    
    @property
    def checksum(self):
        raise NotImplementedError("checksum")
    
    def modify(self, modifier, **kw):
        modifier(self.parsed, **kw)
        self.build()
    
    @property
    def real_section_names(self):
        """ This only applies to PE as section names are limited to 8 characters for image files ; when using longer
             names, they are mapped into a string table that 'objdump' can read to recover the real section names. """
        if self.executable.group != "PE":
            raise AttributeError("'%s' object has no attribute 'real_section_names'" % self.__class__.__name__)
        if not hasattr(self, "_real_section_names"):
            names = [s.name for s in self]
            from re import match
            if all(match(r"/\d+$", n) is None for n in names):
                self._real_section_names = {}
                return self._real_section_names
            from subprocess import check_output
            real_names, out = [], check_output(["objdump", "-h", str(self.executable)]).decode("latin-1")
            for l in out.split("\n"):
                m = match(r"\s+\d+\s(.*?)\s+", l)
                if m:
                    real_names.append(m.group(1))
            self._real_section_names = {n: rn for n, rn in zip(names, real_names) if match(r"/\d+$", n)}
        return self._real_section_names
    
    def section(self, section, original=False):
        if isinstance(section, str):
            if original:
                for s1, s2 in zip(self, self.sections):
                    if s1.name == section:
                        return s2                    
            else:
                for s in self:
                    real_name = getattr(self, "real_section_names", {}).get(s.name, s.name)
                    if s.name == section or real_name == section:
                        if hasattr(s, "real_name"):
                            s.real_name = real_name
                        return s
            raise ValueError("no section named '%s'" % name)
        elif isinstance(section, AbstractBase):
            if original:
                for s1, s2 in zip(self, self.sections):
                    if s1.name == section.name:
                        return s2
                # should not happen ; this would mean that the input section does not come from the current executable
                raise ValueError("no section named '%s'" % section.name)
            else:
                if hasattr(section, "real_name"):
                    section.real_name = self.real_section_names.get(section.name, section.name)
                return section
        raise ValueError(".section(...) only supports a section name or a parsed section object as input")


def get_section_class(name, **mapping):
    slots = DEFAULT_SECTION_SLOTS
    for attr in mapping.keys():
        if attr not in slots:
            slots.append(attr)
    
    class AbstractSection(AbstractBase):
        """ Abstract representation of a binary's section, .
        
        NB: Simple namespace to hold section information. Referencing a lief.PE.Section directly is dangerous, because it
             can be modified by alterations, which will break things. Also, if different parsers are used in susequent
             alterations, a common format is required.
        """
        __slots__ = slots
        
        def __init__(self, section):
            for attr in self.__slots__:
                value = mapping.get(attr, attr)
                if isinstance(value, (type(lambda: 0), cached_property)):
                    continue
                if isinstance(value, str):
                    tmp = section
                    for token in value.split("."):
                        tmp = getattr(tmp, token)
                    value = tmp
                setattr(self, attr, value)
    
    for attr, value in mapping.items():
        if isinstance(value, cached_property):
            setattr(AbstractSection, attr, value)
            getattr(AbstractSection, attr).__set_name__(AbstractSection, attr)
        elif isinstance(value, type(lambda: 0)):
            setattr(AbstractSection, attr, value)
    AbstractSection.__name__ = name
    return AbstractSection

