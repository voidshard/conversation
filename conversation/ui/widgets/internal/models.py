import uuid

from conversation.ui.widgets import utils
from conversation.ui.manifest import *
from conversation.ui import constants as consts
from conversation.ui.events import Events
from conversation.domain.models import Graph as DGraph
from conversation.domain.models import Node as DNode
from conversation.domain.actions import get_action_by_name


class NodeGraph:

    """
    A UI version of the NodeGraph.

    Note we copy some of the domain/models/ logic here, but it's thought that in future these
    could be entirely different .. so it's probably good to divorce UI models and their
    underlying models a bit.

    """

    def __init__(self):
        self._nodes = {}
        self._edges = {}

        self._last_selected = None

    def to_domain_graph(self) -> DGraph:
        g = DGraph()

        for node in self.nodes():
            g.add_node(node.to_domain_node())

        for a, b in self.edges():
            g.add_edge(a, b)

        return g

    def set_domain_graph(self, g):
        self._nodes = {}
        self._edges = {}
        self._last_selected = None

        for n in g.nodes:
            graph_node = Node.from_domain_node(n)
            self._nodes[n.id] = graph_node

            if graph_node.root_node:
                self._last_selected = graph_node

        for a, b in g.edges:
            na = self._nodes.get(a.id)
            nb = self._nodes.get(b.id)

            if not all([na, nb]):
                raise ValueError("Edge found with no matching node")

            self.add_edge(na, nb)

        if self._last_selected:
            self.select(self._last_selected)

    @property
    def selected(self):
        return self._last_selected

    def nodes(self):
        for a in self._nodes.values():
            yield a

    def select(self, node):
        """Mark a node as 'selected'

        :param node:

        """
        print(len(self._edges), len(self._nodes))
        if self._last_selected:
            self._last_selected.selected = False

        self._last_selected = node
        if node:
            node.selected = True
            Events.NodeSelected.emit(node)

    def edges(self):
        """Return edges as a list of (node, node) tuple(s)

        :return: generator

        """
        trimmed = {}
        for key, (a, b) in self._edges.items():
            nodea = self._nodes.get(a)
            nodeb = self._nodes.get(b)

            if not all([nodea, nodeb]):
                continue  # edge is now invalid -> don't return it

            trimmed[key] = (a, b)  # still a valid edge, so we wont remove it
            yield nodea, nodeb
        self._edges = trimmed

    def object_at(self, x, y):
        for node in self._nodes.values():
            if node.contains(x, y):
                return node
        return None

    def add_nodes(self, value):
        if not isinstance(value, list):
            value = [value]

        for n in value:
            if len(self._nodes) == 0:
                n.root_node = True

            n.parent = self
            n.number = len(self._nodes)
            self._nodes[n.id] = n

    def remove_nodes(self, value):
        if not isinstance(value, list):
            value = [value]

        selected_id = None
        if self.selected:
            selected_id = self.selected.id

        for n in value:
            if n.id == selected_id:
                self.select(None)

            try:
                del self._nodes[n.id]
            except KeyError:
                pass

    @staticmethod
    def _edge_key(a, b):
        return ":".join(sorted([a.id, b.id]))

    def add_edge(self, a, b):
        edge_key = self._edge_key(a, b)
        self._edges[edge_key] = [a.id, b.id]

    def remove_edge(self, a, b):
        edge_key = self._edge_key(a, b)
        try:
            del self._edges[edge_key]
        except KeyError:
            pass

    def paint(self, p):
        """

        :param p: QPainter

        """
        utils.set_pen(p, consts.COLOUR_DEFAULT)
        for ea, eb in self.edges():
            p.drawLine(
                ea.x + ea.size/2, ea.y + ea.size/2,
                eb.x + eb.size/2, eb.y + eb.size/2
            )

        for node in self.nodes():
            node.paint(p)


class Node:

    """
    A UI version of the Node.

    Note we copy some of the domain/models/ logic here, but it's thought that in future these
    could be entirely different .. so it's probably good to divorce UI models and their
    underlying models a bit.

    """

    ShapeCircle = "circle"
    ShapeSquare = "square"
    DefaultSize = 20

    _TextHeight = 20
    _Buffer = 30

    def __init__(self, x=0, y=0, number=0, shape=ShapeSquare):
        self.selected = False
        self._shape = shape

        self._node = DNode(x=x, y=y, size=self.DefaultSize)
        self._node.type = self._type_for_shape(shape)
        self._node.number = number
        self._node.root_node = False

    @property
    def number(self):
        return self._node.number

    @number.setter
    def number(self, value):
        self._node.number = value

    @property
    def actions(self) -> list:
        return self._node.actions

    @actions.setter
    def actions(self, value):
        for (name, val) in value:
            if (name, val) in self._node.actions:
                continue
            else:
                self._node.add_action(name, value)

        for (name, val) in self._node.actions:
            if (name, val) not in value:
                self._node.remove_action(name, val)

    @property
    def text(self) -> str:
        return self._node.text

    @text.setter
    def text(self, value):
        self._node.text = value

    @property
    def _size(self) -> int:
        return self._node.metadata.get("size", self.DefaultSize)

    @property
    def x(self) -> int:
        return self._node.metadata.get("x", 0)

    @property
    def y(self) -> int:
        return self._node.metadata.get("y", 0)

    @x.setter
    def x(self, value):
        self._node.metadata["x"] = value

    @y.setter
    def y(self, value):
        self._node.metadata["y"] = value

    @property
    def shape(self) -> str:
        return self._shape

    @shape.setter
    def shape(self, value):
        self._node.type = self._type_for_shape(value)
        self._shape = value

    @classmethod
    def _type_for_shape(cls, shape):
        if shape == cls.ShapeCircle:
            return DNode.Type.Reply
        return DNode.Type.Message

    @classmethod
    def _shape_for_type(cls, type_):
        if type_ == DNode.Type.Reply:
            return cls.ShapeCircle
        return cls.ShapeSquare

    @classmethod
    def from_domain_node(cls, n):
        me = cls()
        me._node = n
        me._shape = cls._shape_for_type(n.type)
        return me

    @property
    def root_node(self) -> bool:
        return self._node.root_node

    @root_node.setter
    def root_node(self, value):
        self._node.root_node = value

    @property
    def requires_user(self):
        return self._node.conditions.user_required

    @requires_user.setter
    def requires_user(self, value):
        self._node.conditions.user_required = value

    @property
    def requires_flag(self):
        return self._node.conditions.flag_required

    @requires_flag.setter
    def requires_flag(self, value):
        self._node.conditions.flag_required = value

    @property
    def requires_state(self):
        return self._node.conditions.state_required

    @requires_state.setter
    def requires_state(self, value):
        self._node.conditions.state_required = value

    def to_domain_node(self) -> DNode:
        """Convert this node into a domain node

        :return: conversation.domain.Node

        """
        return self._node

    def _set_shape_colour(self, p):
        """Decide what colour this shape should be

        :param p:

        """
        utils.set_pen(p, consts.COLOUR_DEFAULT)
        if self.selected:
            utils.set_pen(p, consts.COLOUR_SELECTED)
        elif self.root_node:
            utils.set_pen(p, consts.COLOUR_BEGIN)

    def paint(self, p):
        """

        :param p: QPainter

        """
        if self.shape == self.ShapeCircle:
            self._set_shape_colour(p)
            p.drawEllipse(
                QPoint(self.x + self.size / 2, self.y + self.size / 2),
                self.size / 2,
                self.size / 2
            )

            utils.set_pen(p, consts.COLOUR_ANTI_DEFAULT)
            p.drawEllipse(
                QPoint(self.x + self.size / 2, self.y + self.size / 2),
                self.size / 2 - 1,
                self.size / 2 - 1
            )
        else:
            utils.set_pen(p, consts.COLOUR_ANTI_DEFAULT)
            p.drawRect(self.x, self.y, self.size, self.size)

            self._set_shape_colour(p)
            utils.draw_hollow_rect(p, self.x, self.y, self.size, self.size)

        if self.text:
            self._set_shape_colour(p)

            t = self.text
            if len(t) > self._Buffer:
                t = t[:self._Buffer] + ".."

            p.drawText(
                QRect(
                    self.x - self._Buffer/2,
                    self.y - self._TextHeight,
                    self._size + self._Buffer,
                    self._TextHeight
                ),
                Qt.AlignLeft,
                t
            )

    def contains(self, x, y):
        """

        :param x:
        :param y:
        :return: bool
        """
        return x - self._Buffer <= self.x <= x + self._Buffer and \
               y - self._Buffer <= self.y <= y + self._Buffer

    def move_to(self, x, y):
        self.x = x
        self.y = y

    @property
    def size(self):
        return self._size

    @shape.setter
    def shape(self, value):
        self._shape = value
        self._node.type = self._type_for_shape(self._shape)

    @property
    def id(self):
        return self._node.id
