from collections import namedtuple
from functools import partial

from conversation.domain import actions
from conversation.ui.manifest import *
from conversation.ui import widgets
from conversation.ui.events import Events
from conversation.ui import resources


class _Widgette(widgets.ClosablePanel):
    """Properties widget super class -- this sets min size & adds a node-change listener
    """

    _MIN_WIDTH = 300
    _MIN_HEIGHT = 300
    _TITLE = ""
    _TIP = ""

    def __init__(self, parent):
        super(_Widgette, self).__init__(parent)
        self.setMinimumSize(self._MIN_WIDTH, self._MIN_HEIGHT)

        self.set_title(self._TITLE)
        if self._TIP:
            self.setToolTip(self._TIP)

        self._current_node = None

        Events.Refresh.connect(self.repaint)
        Events.NodeSelected.connect(self.__set_node)
        Events.Flush.connect(self._flush)

    def __set_node(self, n):
        self._set_node(self._current_node, n)
        self._current_node = n
        self.repaint()

    def _flush(self):
        self._set_node(self._current_node, self._current_node)

    def _set_node(self, old, new):
        pass


class _GridWidgette(_Widgette):
    """A subclass of widget that expects it's fields to be laid out in a grid.
    """

    def __init__(self, parent):
        super(_GridWidgette, self).__init__(parent)

        grid = QWidget(self)
        self.layout = QGridLayout()

        grid.setLayout(self.layout)
        self.setWidget(grid)

    def _add_widget_row(self, text, row, widget, tip=""):
        """Adds a widget with a label beside it.

        :param text:
        :param row:
        :return: QCheckBox
        """
        label = QLabel(text)
        if tip:
            label.setToolTip(tip)
            widget.setToolTip(tip)
        self.layout.addWidget(label, row, 1)
        self.layout.addWidget(widget, row, 2)
        return widget


class Properties(_GridWidgette):
    """Simple widget to show properties panel for a node
    """

    _TITLE = "Properties Editor"
    _TIP = "Use this to set misc properties of this conversation node"

    def __init__(self, parent):
        super(Properties, self).__init__(parent)

        self.is_root_node = self._add_widget_row(
            "Is root node",
            1,
            QCheckBox(),
            tip="Set if this is the (or a) entry point for this conversation"
        )

    def _set_node(self, old, new):
        """We've been handed a new node - we should update our displayed text

        :param old:
        :param new:

        """
        # save current state to node
        if old:
            old.root_node = self.is_root_node.isChecked()

        # reset our fields
        self.is_root_node.setChecked(False)

        # set fields to the state(s) of the new node
        if new:
            self.is_root_node.setChecked(new.root_node)


class Actions(_GridWidgette):
    """Simple widget to show actions panel for a node
    """

    _TITLE = "Actions"
    _TIP = "Use this to trigger actions when this node is reached"

    _ACT = namedtuple("Act", "action widget read write reset id")

    _ADD = "add.png"

    def __init__(self, parent):
        super(Actions, self).__init__(parent)

        self._widgets = []
        self._add_action_row(actions.ClearState)
        self._add_action_row(actions.AddFlag)
        self._add_action_row(actions.SetState)

    def _add_toolbar_actions(self):
        self._toolbar.addAction(QIcon(resources.get(self._ADD)), "Add", self.__add_setstate_action)
        super(Actions, self)._add_toolbar_actions()

    def __add_setstate_action(self):
        """

        :return:
        """
        self._add_action_row(actions.SetState)
        self.repaint()

    def _set_node(self, old, new):
        """We've been handed a new node - we should update our displayed text

        :param old:
        :param new:

        """
        # save current state to node
        if old:
            old.actions = []  # reset node actions
            for act in self._widgets:
                old.actions.append((act.action, act.read()))

        # reset our fields
        for w in self._widgets:
            w.reset()

        # set fields to the state(s) of the new node
        if not new:
            return

        if not new.actions:
            return

        done = []

        def find(name):
            """Find the first non unused widget for the given action.

            :param name:
            :return: namedTuple
            """
            for w in self._widgets:
                if w.action.Name == name and w.id not in done:
                    return w
            return None

        for (action, value) in new.actions:
            m = find(action.Name)
            if not m:
                # if we don't find one, we'll just whack in another row -> boom
                m = self._add_action_row(action)
            m.write(value)
            done.append(m.id)

    def _add_action_row(self, action):
        """A higher level abstraction over the '_add_widget_row' func,
        this does the same thing, but keeps the widget & it's related action
        together, as well as simplifying the

        :param action:
        :return: namedTuple

        """
        if action.Field == bool:
            widget = QCheckBox()
            read = widget.isChecked
            write = widget.setChecked
            reset = partial(widget.setChecked, False)
        else:
            widget = QLineEdit()
            read = widget.text
            write = widget.setText
            reset = partial(widget.setText, "")

        index = len(self._widgets)
        self._add_widget_row(
            action.Text,
            index + 1,  # needs to be the row, starts at 1
            widget,
            tip=action.Tip,
        )

        act = self._ACT(action, widget, read, write, reset, index)
        self._widgets.append(act)
        return act


class Conditions(_GridWidgette):
    """Simple widget to show conditions panel for a node
    """

    _TITLE = "Conditions"
    _TIP = "Use this to set conditions that must be met for the conversation to reach this node"
    _ADD = "add.png"

    def __init__(self, parent):
        super(Conditions, self).__init__(parent)

        self.requires_user = self._add_widget_row(
            "Requires user",
            1,
            QCheckBox(),
            tip="Requires a logged in user. You probably almost always want this set .."
        )
        self.requires_flag = self._add_widget_row(
            "Requires flag",
            2,
            QLineEdit(),
            tip="Requires the user have the given flag."
        )
        self.required_states = []
        self.__add_reqstate_field()

    def _add_toolbar_actions(self):
        self._toolbar.addAction(QIcon(resources.get(self._ADD)), "Add", self.__add_reqstate_field)
        super(Conditions, self)._add_toolbar_actions()

    def __add_reqstate_field(self):
        """

        :return:
        """
        widget = QLineEdit()
        self._add_widget_row(
            "Require State",
            len(self.required_states) + 3,  # needs to be the row, starts at 1
            widget,
            tip="Require a particular chat state set to reach here",
        )
        self.required_states.append(widget)
        self.repaint()

    def _current_state(self) -> dict:
        """Parse widget state into internal model state

        :return: dict

        """
        state = {}
        for w in self.required_states:
            line = w.text()
            if not line:
                continue

            if "=" not in line:
                continue

            k, v = line.split("=", 2)
            state[k] = v
        return state

    def _set_node(self, old, new):
        """We've been handed a new node - we should update our displayed text

        :param old:
        :param new:

        """
        # save current state to node
        if old:
            old.requires_user = self.requires_user.isChecked()
            old.requires_flag = self.requires_flag.text()

            x = self._current_state()
            old.requires_state = x

        # reset fields
        self.requires_user.setChecked(True)  # default this to True
        self.requires_flag.setText("")
        for w in self.required_states:
            w.setText("")

        # set fields to state of new node
        if new:
            self.requires_user.setChecked(new.requires_user)
            self.requires_flag.setText(new.requires_flag)

            idx = 0
            for k, v in new.requires_state.items():
                while len(self.required_states) < idx:
                    self.__add_reqstate_field()

                w = self.required_states[idx]
                w.setText("%s=%s" % (k, v))
                idx += 1


class Editor(_Widgette):
    """Simple widget to show editor panel for a node's text field
    """

    _TITLE = "Copy Editor"
    _TIP = "Here is where you can write user visible content :)"

    def __init__(self, parent):
        super(Editor, self).__init__(parent)
        self._editor = QTextEdit(self)
        self.setWidget(self._editor)

    def _set_node(self, old, new):
        """We've been handed a new node - we should update our displayed text

        :param old:
        :param new:

        """
        if old:
            old.text = self._editor.toPlainText()

        self._editor.setText("")

        if new:
            self._editor.setText(new.text)

    @property
    def default_dock_widget_area(self):
        """Return where this widget should be placed by default, relative to
        the dock widget it belongs to.

        Returns:
            int
        """
        return Qt.TopDockWidgetArea
