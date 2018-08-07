import pytest

from conversation.domain.models import Node, _Conditions


class TestConditions:

    def test_decode(self):
        # arrange
        data = {
            "user": False,
            "flag": "fooflag",
            "state": {
               "a": "b",
               "c": "d",
            },
        }

        # act
        con = _Conditions.decode(data)

        # assert
        assert con.encode() == data

    def test_encode(self):
        # arrange
        user = True
        flag = "fooflag"
        state = {
            "a": "b",
            "c": "d",
        }

        con = _Conditions()
        con.state_required = state
        con.user_required = user
        con.flag_required = flag

        # act
        data = con.encode()

        # assert
        assert data == {
            "user": user,
            "flag": flag,
            "state": state,
        }


class TestNode:

    def test_decode(self):
        # arrange
        given = {
            "id": "34567890",
            "type": 'message',
            "properties": {
                "is_root": False,
                "number": 12,
            },
            "copy": {
                "text": "this is some text",
            },
            "metadata": {"ab": "bdad", "x": 1, "y": 14},
            "actions": [
                ["ClearState", True],
            ],
            "conditions": {
                "user": False,
                "flag": "hithere",
                "state": {
                    "a": "b",
                    "foo": "bar",
                },
            },
        }

        # act
        n = Node.decode(given)

        # assert
        assert n.encode() == given

    def test_encode(self):
        # arrange
        metadata = {
            "a": "b",
            "c": True,
            "d": 1,
        }
        num = 12
        root = True
        type_ = Node.Type.Message
        text = "here is some text"

        n = Node(**metadata)
        n.number = num
        n.root_node = root
        n.type = type_
        n.text = text

        expected = {
            "type": type_.value,
            "properties": {
                "is_root": root,
                "number": num,
            },
            "copy": {
                "text": text,
            },
            "metadata": metadata,
            "actions": [],
        }

        # act
        data = n.encode()

        # assert
        assert "id" in data
        assert "conditions" in data

        del data["id"]
        del data["conditions"]

        assert data == expected

