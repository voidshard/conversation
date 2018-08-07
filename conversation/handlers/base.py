import abc
import copy
import random

from conversation.handlers import encoders
from conversation.domain import models, actions


class ConversationHandler(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def conversation_graph(self):
        pass

    @property
    @abc.abstractmethod
    def current_node(self) -> str:
        pass

    @current_node.setter
    @abc.abstractmethod
    def current_node(self, node):
        pass

    @abc.abstractmethod
    def state(self) -> dict:
        pass

    @abc.abstractmethod
    def set_state(self, key, value):
        pass

    @abc.abstractmethod
    def check_state(self, key, value) -> bool:
        pass

    @abc.abstractmethod
    def clear_state(self):
        pass

    @abc.abstractmethod
    def set_flag(self, value):
        pass

    @abc.abstractmethod
    def has_flag(self, value) -> bool:
        pass

    @abc.abstractmethod
    def authenticated_user(self) -> bool:
        pass

    def _can_move_to(self, node) -> bool:
        """Determine if the given node can be moved to with our current
        conversation state.

        :param node:
        :return: bool

        """
        if node.conditions.user_required and not self.authenticated_user():
            return False

        flag = node.conditions.flag_required
        if flag and not self.has_flag(flag):
            return False

        state = self.state()
        for k, v in node.conditions.state_required.items():
            if k not in state:
                return False

            if v != state.get(k):
                return False

        return True

    def _apply_node(self, node):
        """Set the state / flags / clear state according to the node settings.

        :param node:

        """
        for action, value in node.actions:
            if action == actions.ClearState and value:
                self.clear_state()  # clear first
                break

        for action, value in node.actions:
            if action == actions.SetState:
                k, v = actions.SetState.parse(value)
                self.set_state(k, v)
            elif action == actions.AddFlag:
                self.set_flag(actions.AddFlag.parse(value))

    def next_nodes(self):
        graph = self.conversation_graph

        options = []
        for n in graph.next_nodes(self.current_node):
            if self._can_move_to(n):
                options.append(n)

        return options


class InMemoryHandler(ConversationHandler):
    """Example handler for a conversation

    """

    def __init__(self, graph: models.Graph, current: str=None, apply=False):
        self._graph = graph
        self._state = {}
        self._flags = {}
        self._current = None

        if current:
            self._current = graph.get_node(current)
            if not self._current:
                raise ValueError(f"node with id {current} not found in graph")
        else:
            # Nb. we want to apply the node here
            self._current = random.choice([
                n for n in graph.roots if self._can_move_to(n)]
            )

        if apply:
            self._apply_node(self._current)

    @property
    def conversation_graph(self):
        return self._graph

    @property
    def current_node(self) -> str:
        return self._current

    @current_node.setter
    def current_node(self, node):
        self._apply_node(node)
        self._current = node

    def state(self) -> dict:
        return copy.copy(self._state)

    def set_state(self, key, value):
        self._state[key] = value

    def check_state(self, key, value) -> bool:
        stored_value = self._state.get(key)
        if stored_value is None:
            return False

        return stored_value == value

    def clear_state(self):
        self._state = {}

    def set_flag(self, value):
        self._flags[value] = True

    def has_flag(self, value) -> bool:
        return self._flags.get(value, False)

    def authenticated_user(self) -> bool:
        return True
