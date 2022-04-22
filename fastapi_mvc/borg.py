"""Borg design pattern (or monostate if you will) implementation."""
import os
import logging
import subprocess

from fastapi_mvc.commands import Invoker
from fastapi_mvc.parsers import IniParser
from fastapi_mvc.generators import builtins, load_generators
from fastapi_mvc.utils import ShellUtils
from fastapi_mvc.version import __version__


class Borg(object):
    """We are the Borg.

    Borg design pattern (or monostate if you will) implementation.

    It is a way to implement singleton behavior, but instead of having only one
    instance of a class, there are multiple instances that share the same state.
    In other words, the focus is on sharing state instead of sharing instance
    identity.

    Note:
        I am aware that singleton and monostate do not have a good reputation
        and are often considered an anty pattern. However, a little experiment
        never killed nobody :); I'm genuinely curious how this plays out.

        Besides, it has a cool name.

    Resources:
        1. http://www.aleax.it/5ep.html
        2. https://code.activestate.com/recipes/66531/

    Attributes:
        _log (logging.Logger): Logger class object instance.

    """

    __shared_state = dict()

    def __init__(self):
        """I am the beginning, the end, the one who is many. I am the Borg."""
        self.__dict__ = self.__shared_state

        if not getattr(self, "__borg_assimilated", False):
            setattr(self, "__borg_assimilated", True)
            self._log = logging.getLogger(self.__class__.__name__)
            self._log.debug("Initialize first Borg class object instance.")
            self._invoker = Invoker()
            self._parser = None
            self._project_installed = None
            self._generators_loaded = False
            self._generators = builtins

    def __str__(self):
        """Class custom __str__ method implementation."""
        return "We are the Borg. You will be assimilated. Resistance is futile."

    @property
    def generators(self):
        """Get loaded fastapi-mvc generators.

        Returns:
            dict: Loaded fastapi-mvc generators.

        """
        return self._generators

    @property
    def parser(self):
        """Get IniParser class object instance.

        Returns:
            IniParser: IniParser class object instance if set otherwise None.

        """
        return self._parser

    @property
    def version(self):
        """Get fastapi-mvc version..

        Returns:
            str: Fastapi-mvc version.

        """
        return __version__

    def require_project(self):
        """Verify if fastapi-mvc project is valid."""
        if self._parser:
            return

        try:
            parser = IniParser()
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            self._log.error(
                "Not a fastapi-mvc project. Try 'fastapi-mvc new --help' for "
                "details how to create one."
            )
            raise SystemExit(1)

        pkg_path = os.path.join(parser.project_root, parser.package_name)

        if not os.path.isdir(pkg_path):
            self._log.debug("{0:s} is not a directory.".format(pkg_path))
            self._log.error(
                "Could not find required project files. Most likely project or "
                "fastapi-mvc.ini is corrupted."
            )
            raise SystemExit(1)

        self._parser = parser

    def require_installed(self):
        """Verify if fastapi-mvc project is installed."""
        if not self._parser:
            self.require_project()

        if not self._project_installed:
            self._log.debug("Verifying if fastapi-mvc project is installed.")
            cmd = [
                "poetry",
                "run",
                self._parser.script_name,
                "--help",
            ]

            try:
                ShellUtils.run_shell(
                    cmd=cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    cwd=self._parser.project_root,
                )
            except subprocess.CalledProcessError:
                self._log.error(
                    "Project is not installed. To install run: $ make install"
                )
                raise SystemExit(1)

            self._project_installed = True

    def load_generators(self):
        """Load local fastapi-mvc generators."""
        if not self._parser:
            self.require_project()

        if not self._generators_loaded:
            generators = load_generators(self._parser.project_root)
            # Updating in the reversed way to override local generators
            # that shadows built-in ones.
            generators.update(self._generators)
            self._generators = generators
            self._generators_loaded = True

    def enqueue_command(self, command):
        """Enqueue command for Invoker to execute.

        Args:
            command (Command): Command subclass object instance.

        """
        self._invoker.enqueue(command)

    def execute(self):
        """Execute enqueued Invoker commands."""
        self._invoker.execute()