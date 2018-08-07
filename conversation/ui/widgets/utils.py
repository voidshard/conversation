"""Random QT related helper functions
"""

from conversation.ui.manifest import *


def control_held() -> bool:
    """Return if the control key is held down

    :return: bool
    """
    return QApplication.keyboardModifiers() & Qt.ControlModifier


def shift_held() -> bool:
    """Return if the shift key is held down

    :return: bool
    """
    return QApplication.keyboardModifiers() & Qt.ShiftModifier


def draw_hollow_rect(painter, x, y, width, height):
    """Draws hollow square.

    +----+
    |    |
    |    |
    +----+

    :param painter:
    :param x:
    :param y:
    :param width:
    :param height:

    """
    painter.drawLine(x, y, x + width, y)
    painter.drawLine(x + width, y, x + width, y + height)
    painter.drawLine(x + width, y + width, x, y + height)
    painter.drawLine(x, y + height, x, y)


def set_pen(painter, rgb=(255, 255, 255)):
    """Set the painter pen / brush to the given colour. Defaults to white.

    Args:
        painter:
        rgb (tuple):

    """
    painter.setPen(QColor(*rgb))
    painter.setBrush(QColor(*rgb))
    painter.setFont(painter.font())
