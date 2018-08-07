"""These are models specific to the widgets, and should not leave the area
unsupervised.
"""

from conversation.ui.widgets.internal.models import NodeGraph
from conversation.ui.widgets.internal.models import Node


__all__ = [
    "Node",
    "NodeGraph",
]
