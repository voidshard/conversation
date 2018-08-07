import abc
import copy
import enum
import uuid

from conversation.domain import actions


class _NodeType(enum.Enum):
    Message = "message"
    Reply = "reply"


class _Encodable(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def encode(self) -> dict:
        pass

    @abc.abstractclassmethod
    def decode(self, data: dict):
        pass


class Graph(_Encodable):

    def __init__(self, **kwargs):
        self._nodes = {}
        self._edges = {}
        self.metadata = kwargs

    def encode(self) -> dict:
        return {
            "nodes": [
                n.encode() for n in self._nodes.values()
            ],
            "edges": list(self._edges.values()),
            "metadata": copy.copy(self.metadata),
        }

    def get_node(self, id_):
        return self._nodes.get(id_)

    @property
    def roots(self) -> list:
        return [n for n in self.nodes if n.is_root]

    def node_edges(self, n):
        for a, b in self.edges:
            if n.id in [a.id, b.id]:
                if a == n:
                    yield b
                else:
                    yield a

    def next_nodes(self, n):
        for edge_node in self.node_edges(n):
            if edge_node.number > n.number:
                yield edge_node

    @classmethod
    def decode(cls, data: dict):
        me = cls(**data.get("metadata", {}))

        for node_value in data.get("nodes", []):
            node = Node.decode(node_value)
            me.add_node(node)

        for ea, eb in data.get("edges", []):
            na = me._nodes.get(ea)
            nb = me._nodes.get(eb)

            if not all([na, nb]):
                raise ValueError("Edge found with no matching node")

            me.add_edge(na, nb)
        return me

    @property
    def nodes(self):
        for n in self._nodes.values():
            yield n

    @property
    def edges(self):
        trimmed = {}
        for key, (a, b) in self._edges.items():
            nodea = self._nodes.get(a)
            nodeb = self._nodes.get(b)

            if not all([nodea, nodeb]):
                continue  # edge is now invalid -> don't return it

            trimmed[key] = (a, b)  # still a valid edge, so we wont remove it
            yield nodea, nodeb
        self._edges = trimmed

    def add_node(self, n):
        self._nodes[n.id] = n

    def add_edge(self, n1, n2):
        ids = sorted([n1.id, n2.id])
        key = ":".join(ids)
        self._edges[key] = ids


class _Conditions(_Encodable):
    def __init__(self):
        self._user = True
        self._flag = None
        self._state = {}

    @property
    def state_required(self) -> dict:
        return copy.copy(self._state)

    @state_required.setter
    def state_required(self, value: dict):
        self._state = value

    @property
    def user_required(self) -> bool:
        return self._user

    @user_required.setter
    def user_required(self, value: bool):
        self._user = value

    @property
    def flag_required(self) -> str:
        return self._flag

    @flag_required.setter
    def flag_required(self, value):
        self._flag = value

    def encode(self) -> dict:
        return {
            "user": self._user,
            "flag": self._flag,
            "state": self._state,
        }

    @classmethod
    def decode(cls, data: dict):
        cnd = cls()
        cnd._user = data.get("user", True)
        cnd._flag = data.get("flag")
        cnd._state = data.get("state", {})
        return cnd


class Node(_Encodable):
    Type = _NodeType

    def __init__(self, **kwargs):
        self.id = uuid.uuid4().hex
        self.number = None
        self.root_node = False
        self._type = None
        self.metadata = copy.copy(kwargs)
        self.conditions = _Conditions()
        self.text = ""
        self._actions = []

    @property
    def is_root(self):
        return self.root_node

    def encode(self) -> dict:
        return {
            "id": self.id,
            "type": self._type.value,
            "properties": {
                "is_root": self.root_node,
                "number": self.number,
            },
            "conditions": self.conditions.encode(),
            "copy": {
                "text": self.text,
            },
            "metadata": self.metadata,
            "actions": [
                [a.Name, v] for (a, v) in self.actions
            ],
        }

    @classmethod
    def decode(cls, data: dict):
        me = cls(**data.get("metadata", {}))

        me.id = data.get("id")
        me.type = data.get("type")

        props = data.get("properties", {})
        me.root_node = props.get("is_root", False)
        me.number = props.get("number", 0)

        me.conditions = _Conditions.decode(data.get("conditions", {}))
        me.text = data.get("copy", {}).get("text", "")

        for (aname, value) in data.get("actions", []):
            action = actions.get_action_by_name(aname)
            if not action:
                raise ValueError(f"unknown action {aname}")

            me.add_action(action, value)

        return me

    def remove_action(self, action, value):
        """Remove action by it's Action & value

        :param action:
        :param value:

        """
        tmp = []
        for (a, v) in self.actions:
            if not(action.Name == a.Name and v == value):
                tmp.append((a, v))
        self._actions = tmp

    def add_action(self, action_identifier, value):
        """Add action with the given value

        :param action_isedentifier:
        :param value:

        """
        all_actions = [actions.AddFlag, actions.SetState, actions.ClearState]
        action = None

        if issubclass(action_identifier, actions.Action):
            if action_identifier not in all_actions:
                raise ValueError(f"invalid action {action}")
            action = action_identifier
        else:
            for a in all_actions:
                if a.Name == action_identifier:
                    action = a
                    break

        if not action:
            raise ValueError(f"invalid action {action}")

        if isinstance(action.Field, str) and value == "":
            return

        if not isinstance(value, action.Field):
            raise ValueError(f"invalid field for action {action}: {value}")

        self._actions.append((action, value))

    @property
    def actions(self):
        return self._actions

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, v):
        all_types = [_NodeType.Reply, _NodeType.Message]

        value = None
        if isinstance(v, str):
            for e in all_types:
                if e.value == v:
                    value = e
                    break
        else:
            if v in all_types:
                value = v

        if not value:
            raise ValueError("unknown type %s" % v)

        self._type = value
