from conversation.domain import models


def to_facebook_message(state: dict, node: models.Node, replies: list) -> dict:
    """Transforms a node (message) and it's replies (also nodes..) to be a facebook
    message + buttons.

    :param state: conversation state information
    :param node:
    :param replies:
    :return: dict

    """
    return {
        'type': 'template',
        'payload': {
            'template_type': 'button',
            'text': node.text.format(**state),
            'buttons': [
                _fb_button(
                    n.text.format(**state),
                    n.id
                ) for n in replies
            ],
        }
    }


def _fb_button(title: str, payload: str) -> dict:
    """Return a facebook button for the given inputs.

    :param title:
    :param payload:
    :return: dict

    """
    return {
        'type': 'postback',
        'title': title,
        'payload': payload,
    }
