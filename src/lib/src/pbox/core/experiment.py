# -*- coding: UTF-8 -*-
from tinyscript import logging
from tinyscript.helpers import confirm, lazy_object, user_input, Path
from tinyscript.report import *

from .dataset import *
from .model import *
from ..helpers import *


__all__ = ["Experiment"]


COMMIT_VALID_COMMANDS = [
    # OS commands
    "cd", "cp", "mkdir", "mv",
    # packing-box commands
    "dataset", "detector", "model", "packer", "unpacker", "visualizer",
]


def __init():
    class Experiment(AbstractEntity):
        """ Folder structure:
        
        [name]
          +-- conf          custom YAML configuration files
          +-- (data)        custom executable format related data (e.g. common standard/packer section names)
          +-- datasets      datasets specific to the experiment
          +-- models        models specific to the experiment
          +-- (figures)     figures generated with visualization tools
          +-- (scripts)     additional scripts
          +-- README.md     notes for explaining the experiment
        """
        FOLDERS = {'mandatory': ["conf", "datasets", "models"], 'optional':  ["data", "figures", "scripts"]}
        
        @logging.bindLogger
        def __init__(self, name="experiment", load=True, **kw):
            name = config.check(Path(name).basename)
            self.path = Path(config['experiments'].joinpath(name), create=True).absolute()
            if load:
                for folder in ["conf", "datasets", "models"]:
                    folder = self.path.joinpath(folder)
                    if not folder.exists():
                        folder.mkdir()
                self['README'].touch()
                config['experiment'] = config['workspace'] = self.path
        
        def __getitem__(self, name):
            """ Get something from the experiment folder, either a config file, a dataset or a model.
            
            NB: In the case of YAML configuration files, this method aims to return the actually used YAML, not specifically
                 the one from the experiment (if exists) ; therefore, when a YAML has not been edited within the scope of
                 the experiment yet, this method will return the YAML from the main workspace.
            """
            # case 1: 'name' is README(.md) or commands(.rc) ; return a Path instance
            if name in ["README", "README.md"]:
                return self.path.joinpath("README.md")
            if name in ["commands", "commands.rc"]:
                return self.path.joinpath("commands.rc")
            # case 2: 'name' matches a reserved word for a YAML configuration file ; return a Path instance
            #          get it either from the main workspace or, if existing, from the experiment
            if name in config._defaults['definitions'].keys():
                conf = self.path.joinpath("conf").joinpath(name + ".yml")
                if not conf.exists():
                    conf = config[name]
                return conf
            # case 3: 'name' matches a dataset from the experiment ; return a (Fileless)Dataset instance
            for ds in self.path.joinpath("datasets").listdir():
                if name == ds.stem:
                    return open_dataset(ds)
            # case 4: 'name' matches a model from the experiment ; return a (Dumped)Model instance
            for ds in self.path.joinpath("models").listdir():
                if name == ds.stem:
                    return open_model(ds)
            raise KeyError(name)
        
        def __len__(self):
            """ Get dataset's length. """
            return Dataset.count() + Model.count()
        
        def _import(self, source=None, **kw):
            """ Import a custom YAML configuration file or set of YAML configuration files. """
            p_src = Path(source)
            p_exp = self.path.joinpath("conf").joinpath(p_src.basename)
            try:
                if not p_src.extension == ".yml":
                    raise KeyError
                config.get(p_src.stem, sections="definitions", error=True)
                if not p_src.is_samepath(p_exp):
                    l.debug("copying configuration file%s from '%s'..." % (["", "s"][p_src.is_dir()], p_src))
                    p_src.copy(p_exp)
            except KeyError:
                if kw.get('error', True):
                    l.error("'%s' is not a valid configuration name" % p_scr.basename)
                    raise KeyError
        
        def close(self, **kw):
            """ Close the currently open experiment. """
            del config['experiment']
        
        def commit(self, force=False, **kw):
            """ Commit the latest executed OS command to the resource file (.rc). """
            l = self.logger
            rc = self['commands']
            rc.touch()
            rc_last_line = ""
            for rc_last_line in rc.read_lines():
                pass
            hist = list(Path("~/.bash_history", expand=True).read_lines())
            while len(hist) > 0 and all(not hist[-1].startswith(cmd + " ") for cmd in COMMIT_VALID_COMMANDS):
                hist.pop()
            if len(hist) == 0 or hist[-1].strip() == rc_last_line.strip():
                l.warning("Nothing to commit")
            elif force or confirm("Do you really want to commit this command: %s ?" % hist[-1]):
                l.debug("writing command '%s' to commands.rc..." % hist[-1])
                with rc.open('a') as f:
                    f.write(hist[-1].strip())
        
        def compress(self, **kw):
            """ Compress the experiment by converting all datasets to fileless datasets. """
            l, done = self.logger, False
            for dset in Path(config['datasets']).listdir(Dataset.check):
                l.info("Dataset: %s" % dset)
                open_dataset(dset).convert()
                done = True
            if not done:
                l.warning("No dataset to be converted")
        
        def edit(self, **kw):
            """ Edit the README or a YAML configuration file. """
            l, conf = self.logger, kw.get('config')
            p = self[conf] # can be README.md, commands.rc or YAML config files
            try:
                p_main, p_exp = config[conf], self.path.joinpath("conf").joinpath(conf + ".yml")
                self._import(p_main, error=True)
                if p_exp.is_file():
                    l.debug("editing experiment's %s configuration..." % conf)
                    edit_file(p_exp, text=True, logger=l)
                elif p_exp.is_dir():
                    choices = [p.stem for p in p_exp.listdir(lambda x: x.extension == ".yml")]
                    stem = user_input(choices=choices, default=choices[0], required=True)
                    edit_file(p_exp.joinpath(stem + ".yml"), text=True, logger=l)
            except KeyError:
                l.debug("editing experiment's %s..." % p.basename)
                edit_file(p, text=True, logger=l)
        
        def list(self, raw=False, **kw):
            """ List all valid experiment folders. """
            data, headers = [], ["Name", "#Datasets", "#Models", "Custom configs"]
            for folder in config['experiments'].listdir(Experiment.check):
                exp = Experiment(folder, False)
                cfg = [f.stem for f in exp.path.joinpath("conf").listdir(Path.is_file) if f.extension == ".yml"]
                data.append([folder.basename, Dataset.count(), Model.count(), ", ".join(cfg)])
            if len(data) > 0:
                render(*[Section("Experiments (%d)" % len(data)), Table(data, column_headers=headers)])
            else:
                self.logger.warning("No experiment found in the workspace (%s)" % config['experiments'])
        
        def open(self, **kw):
            """ Open the current experiment, validating its structure. """
            self.load(self.path)
        
        def purge(self, **kw):
            """ Purge the current experiment. """
            self.logger.debug("purging experiment...")
            self.path.remove(error=False)
        
        def show(self, **kw):
            """ Show an overview of the experiment. """
            Dataset(load=False).list()
            Model(load=False).list()
        
        @classmethod
        def validate(cls, folder, warn=False, logger=None, **kw):
            f = config['experiments'].joinpath(folder)
            if not f.exists():
                raise ValueError("Does not exist")
            if not f.is_dir():
                raise ValueError("Not a folder")
            for fn in Experiment.FOLDERS['mandatory']:
                if not f.joinpath(fn).exists():
                    raise ValueError("Does not have %s" % fn)
            for cfg in f.joinpath("conf").listdir():
                if cfg.stem not in config._defaults['definitions'].keys() or cfg.extension != ".yml":
                    raise ValueError("Unknown configuration file '%s'" % cfg)
            for fn in f.listdir(Path.is_dir):
                if fn not in Experiment.FOLDERS['mandatory'] + Experiment.FOLDERS['optional'] and warn and \
                   logger is not None:
                    logger.warning("Unknown subfolder '%s'" % fn)
            for fn in f.listdir(Path.is_file):
                if fn not in ["commands.rc", "README.md"] and warn and logger is not None:
                    logger.warning("Unknown file '%s'" % fn)
            return f
    
    return Experiment
Experiment = lazy_object(__init)

