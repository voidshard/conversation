"""Actions represent some nebulous thing that should happen, without defining how.
"""


class Action:
    Name = ""
    Text = ""
    Tip = ""

    Field = None


class ClearState(Action):
    Name = "ClearState"
    Text = "Clear all chat state"
    Tip = "Useful if ending the conversation .. or starting over"

    Field = bool

    @classmethod
    def parse(cls):
        pass


class SetState(Action):
    Name = "SetState"
    Text = "Set chat state"
    Tip = "Set some value in the chat state using key=value"

    Field = str  # key=value

    @classmethod
    def parse(cls, value) -> tuple:
        if '=' not in value:
            return value, True

        a, b = value.split('=', 2)
        return a, b


class AddFlag(Action):
    Name = "AddFeature"
    Text = "Give feature flag"
    Tip = "Gives the user some feature flag"

    Field = str  # flag name

    @classmethod
    def parse(cls, value) -> str:
        return value.strip()


_map = {
    a.Name: a for a in [ClearState, SetState, AddFlag]
}


def get_action_by_name(name):
    return _map.get(name)
