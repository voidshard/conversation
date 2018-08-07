from functools import partial

from conversation.ui import widgets
from conversation.ui.widgets import internal
from conversation.ui.manifest import *
from conversation.ui.undo import Undo
from conversation.ui.widgets import utils
from conversation.ui import constants as consts
from conversation.ui.events import Events


class Canvas(widgets.Panel):
    """Simple widget to draw a bar chart given a GraphData object.
    """
    def __init__(self, parent):
        super(Canvas, self).__init__(parent)
        self._model = internal.NodeGraph()
        self.mouseReleaseEvent = self.__mouse_release
        self.mouseDoubleClickEvent = self.__on_dbl_click
        self.mousePressEvent = self.__on_click

        self._dragging = None

        Events.Refresh.connect(self.repaint)

    def get_graph(self):
        """
        """
        return self._model.to_domain_graph()

    def set_graph(self, graph):
        """
        """
        self._model.set_domain_graph(graph)
        self.repaint()

    def __mouse_release(self, evt):
        """

        :param evt:

        """
        x, y = self._click_coords(evt)

        if self._dragging and utils.shift_held():
            px = self._dragging.x
            py = self._dragging.y

            self._dragging.move_to(
                x - self._dragging.size/2,
                y - self._dragging.size/2
            )

            Undo.add_undo("move node", [
                partial(self._dragging.move_to, px, py),
                self.repaint,
            ])

            self.repaint()

        self._dragging = None

    def __on_dbl_click(self, evt):
        """

        :param evt:

        """
        pass

    def _on_right_click(self, evt):
        """

        :param evt:
        :param x:
        :param y:

        """
        selected = self._model.selected
        if not selected:
            return

        x, y = self._click_coords(evt)
        target = self._model.object_at(x, y)
        if not target:
            return
        elif target.id == selected.id:
            return
        elif target.shape == selected.shape:
            return

        self._model.add_edge(target, selected)
        Undo.add_undo("add edge", [
            partial(self._model.remove_edge, target, selected),
            partial(self.repaint),
        ])
        self.repaint()

    def _on_left_click(self, evt):
        """

        :param evt:

        """
        x, y = self._click_coords(evt)

        target = self._model.object_at(x, y)
        if target:
            if utils.shift_held():
                self._dragging = target
            else:
                self._model.select(target)

            self.repaint()
            return

        n = internal.Node(x - internal.Node.DefaultSize / 2, y - internal.Node.DefaultSize / 2)
        self._model.add_nodes(n)

        selected = self._model.selected
        if selected:
            self._model.add_edge(selected, n)
            if selected.shape == internal.Node.ShapeSquare:
                n.shape = internal.Node.ShapeCircle

        if not utils.control_held():
            self._model.select(n)

        Undo.add_undo("create node", [
            partial(self._model.remove_nodes, [n]),
            partial(self._model.select, selected),
            partial(self.repaint),
        ])

        self.repaint()

    def _click_coords(self, evt):
        """

        :param evt: mouse click event
        :return: int, int
        """
        p = evt.pos()
        return p.x(), p.y()

    def __on_click(self, evt):
        """Handle when the widget is clicked

        :param evt:

        """
        if evt.button() == Qt.LeftButton:
            return self._on_left_click(evt)
        if evt.button() == Qt.RightButton:
            return self._on_right_click(evt)

    def paint(self, p):
        """

        :param p:

        """
        # draw background
        utils.set_pen(p, consts.COLOUR_ANTI_DEFAULT)
        p.drawRect(
            0, self._toolbar.height(),
            self.width(), self.height() - self._toolbar.height()
        )

        # order the model to draw itself & pass it the painter
        self._model.paint(p)

    def paintEvent(self, evt):
        """Called by Qt when we need to draw this widget

        Args:
            evt:

        """
        paint = QPainter()
        paint.begin(self)
        self.paint(paint)
        paint.end()
