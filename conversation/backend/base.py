import abc
import os
import json

from conversation.domain import models


class Storage(metaclass=abc.ABCMeta):

    _SUFFIX = '.cnv'

    @abc.abstractmethod
    def write(self, name: str, location: str, graph: models.Graph):
        pass

    @abc.abstractmethod
    def read(self, name: str, location: str) -> models.Graph:
        pass

    @abc.abstractmethod
    def list(self, location: str) -> list:
        pass


class FilesystemStorage(Storage):

    def list(self, location: str) -> list:
        """List all conversation files in the given folder.

        :param location:
        :return: list

        """
        if not os.path.exists(location):
            return []

        return [i for i in os.listdir(location) if i.endswith(self._SUFFIX)]

    def write(self, name, location, graph):
        """Write file to disk as .json file with our suffix

        :param name:
        :param location:
        :param graph:
        """
        if not os.path.exists(location):
            os.makedirs(location)

        if not name.endswith(self._SUFFIX):
            name += self._SUFFIX

        encoded = graph.encode()
        data = json.dumps(encoded)
        fpath = os.path.join(location, name)

        with open(fpath, "w") as f:
            f.write(data)

        return fpath

    def read(self, name, location):
        """Read data from json file on disk

        :param name:
        :param location:
        :return: Graph

        """
        with open(os.path.join(location, name), "r") as f:
            line = f.read().strip()

        data = json.loads(line)
        return models.Graph.decode(data)
