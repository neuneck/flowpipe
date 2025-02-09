from __future__ import print_function
import json

import pytest

from flowpipe.node import INode, Node
from flowpipe.plug import InputPlug, OutputPlug


class NodeForTesting(INode):

    def compute(self):
        pass


def test_connecting_different_input_disconnects_existing_ones():

    @Node(outputs=['a_out'])
    def A(a):
        pass

    @Node(outputs=['b_out'])
    def B(b, b_compound):
        pass

    @Node(outputs=['c_out'])
    def C(c):
        pass

    @Node(outputs=['d_out_compound'])
    def D(d, d_compound):
        pass

    @Node(outputs=['e_out_compound'])
    def E(e, e_compound):
        pass

    a = A()
    b = B()
    c = C()
    d = D()
    e = E()

    a.outputs['a_out'].connect(b.inputs['b'])
    c.outputs['c_out'].connect(b.inputs['b'])

    assert not a.outputs['a_out'].connections

    b.inputs['b'].connect(a.outputs['a_out'])

    assert a.outputs['a_out'].connections

    b.inputs['b'].connect(c.outputs['c_out'])

    assert not a.outputs['a_out'].connections

    b.inputs['b_compound']['0'].connect(a.outputs['a_out'])
    assert b.inputs['b_compound']['0'].connections[0] == a.outputs['a_out']

    b.inputs['b_compound']['0'].connect(c.outputs['c_out'])
    assert b.inputs['b_compound']['0'].connections[0] == c.outputs['c_out']

    d.outputs['d_out_compound']['0'].connect(e.inputs['e_compound']['0'])
    e.inputs['e_compound']['1'].connect(d.outputs['d_out_compound']['0'])
    assert e.inputs['e_compound']['0'].connections[0] == d.outputs['d_out_compound']['0']
    assert e.inputs['e_compound']['1'].connections[0] == d.outputs['d_out_compound']['0']
    assert len(d.outputs['d_out_compound']['0'].connections) == 2


def test_connect_and_dicsonnect_nodes():
    """Connect and disconnect nodes."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug_a = OutputPlug('out', n1)
    in_plug_a = InputPlug('in_a', n2)
    in_plug_b = InputPlug('in_b', n2)
    in_plug_c = InputPlug('in_c', n2)
    in_plug_d = InputPlug('in_d', n2)
    in_plug_compound = InputPlug('in_compound', n2)
    out_plug_compound = OutputPlug('out_compound', n1)

    # Connect the out to the in
    out_plug_a >> in_plug_a
    assert 1 == len(out_plug_a.connections)
    assert 1 == len(in_plug_a.connections)
    out_plug_compound['0'] >> in_plug_c
    assert 1 == len(out_plug_compound['0'].connections)
    assert 1 == len(in_plug_c.connections)
    out_plug_compound['1'] >> in_plug_compound['1']
    assert 1 == len(out_plug_compound['1'].connections)
    assert 1 == len(in_plug_compound['1'].connections)

    # Connect the same nodes multiple times
    out_plug_a >> in_plug_a
    assert 1 == len(out_plug_a.connections)
    assert 1 == len(in_plug_a.connections)
    out_plug_compound['0'] >> in_plug_c
    assert 1 == len(out_plug_compound['0'].connections)
    assert 1 == len(in_plug_c.connections)
    out_plug_compound['1'] >> in_plug_compound['1']
    assert 1 == len(out_plug_compound['1'].connections)
    assert 1 == len(in_plug_compound['1'].connections)

    # Connect the in to the out
    in_plug_b >> out_plug_a
    assert 2 == len(out_plug_a.connections)
    assert 1 == len(in_plug_b.connections)
    in_plug_d >> out_plug_compound['0']
    assert 2 == len(out_plug_compound['0'].connections)
    assert 1 == len(in_plug_d.connections)
    in_plug_compound['2'] >> out_plug_compound['1']
    assert 2 == len(out_plug_compound['1'].connections)
    assert 1 == len(in_plug_compound['1'].connections)

    # Connect the in to the multiple times
    in_plug_b >> out_plug_a
    assert 2 == len(out_plug_a.connections)
    assert 1 == len(in_plug_b.connections)
    in_plug_d >> out_plug_compound['0']
    assert 2 == len(out_plug_compound['0'].connections)
    assert 1 == len(in_plug_d.connections)
    in_plug_compound['2'] >> out_plug_compound['1']
    assert 2 == len(out_plug_compound['1'].connections)
    assert 1 == len(in_plug_compound['1'].connections)


def test_change_connections_sets_plug_dirty():
    """Connecting and disconnecting sets the plug dirty."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug = OutputPlug('out', n1)
    in_plug = InputPlug('in', n2)
    out_compound_plug = OutputPlug('out_compound', n1)
    in_compound_plug = InputPlug('in_compound', n2)

    in_plug.is_dirty = False
    out_plug >> in_plug
    assert in_plug.is_dirty

    in_plug.is_dirty = False
    out_plug << in_plug
    assert in_plug.is_dirty

    in_compound_plug['0'].is_dirty = False
    out_compound_plug['0'] >> in_compound_plug['0']
    assert in_compound_plug['0'].is_dirty

    in_compound_plug['0'].is_dirty = False
    out_compound_plug['0'] << in_compound_plug['0']
    assert in_compound_plug['0'].is_dirty


def test_set_value_sets_plug_dirty():
    """Connecting and disconnecting sets the plug dirty."""
    n = NodeForTesting()
    in_plug = InputPlug('in', n)
    in_compound_plug = InputPlug('in_compound', n)

    in_plug.is_dirty = False
    assert not in_plug.is_dirty
    in_plug.value = 'NewValue'
    assert in_plug.is_dirty

    in_compound_plug.is_dirty = False
    assert not in_compound_plug.is_dirty
    in_compound_plug.value = 'NewValue'
    assert in_compound_plug.is_dirty


def test_set_output_pushes_value_to_connected_input():
    """OutPlugs push their values to their connected input plugs."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug = OutputPlug('out', n1)
    in_plug = InputPlug('in', n2)

    out_compound_plug = OutputPlug('out_compound', n1)
    in_compound_plug = InputPlug('in_compound', n2)

    out_plug.value = 'OldValue'
    assert in_plug.value != out_plug.value

    out_plug >> in_plug
    in_plug.is_dirty = False
    assert in_plug.value == out_plug.value
    assert not in_plug.is_dirty

    out_plug.value = 'NewValue'
    assert in_plug.is_dirty
    assert in_plug.value == out_plug.value

    out_compound_plug.value = 'OldValue'
    assert in_compound_plug.value != out_compound_plug.value

    out_compound_plug >> in_compound_plug
    in_compound_plug.is_dirty = False
    assert in_compound_plug.value == out_compound_plug.value
    assert not in_compound_plug.is_dirty

    out_compound_plug.value = 'NewValue'
    assert in_compound_plug.is_dirty
    assert in_compound_plug.value == out_compound_plug.value


def test_assign_initial_value_to_input_plug():
    """Assign an initial value to an InputPlug."""
    n = NodeForTesting()
    in_plug = InputPlug('in', n)
    assert in_plug.value is None

    in_plug = InputPlug('in', n, 123)
    assert 123 == in_plug.value


def test_serialize():
    """Serialize the Plug to json."""
    n1 = NodeForTesting()
    n2 = NodeForTesting()
    out_plug = OutputPlug('out', n1)
    out_plug.value = 'out_value'
    in1_plug = InputPlug('in1', n2)
    in2_plug = InputPlug('in2', n2)
    in_plug_with_value = InputPlug('in_value', n2, 'value')
    compound_out_plug = OutputPlug('compound_out', n1)
    compound_in_plug = InputPlug('compound_in', n2)
    out_plug >> in1_plug
    out_plug >> compound_in_plug['incoming']
    compound_out_plug['0'] >> in2_plug

    compound_in_plug['0'].value = 0
    compound_in_plug['key'].value = 'value'

    in_serialized = in1_plug.serialize()
    assert in_serialized == {
        'name': 'in1',
        'value': 'out_value',
        'connections': {
            out_plug.node.identifier: 'out'
        },
        'sub_plugs': {}
    }

    in_plug_with_value_serialized = in_plug_with_value.serialize()
    assert in_plug_with_value_serialized == {
        'name': 'in_value',
        'value': 'value',
        'connections': {},
        'sub_plugs': {}
    }

    compound_in_serialized = compound_in_plug.serialize()
    assert compound_in_serialized == {
        'name': 'compound_in',
        'value': None,
        'connections': {},
        'sub_plugs': {
            '0': {
                'connections': {},
                'name': 'compound_in.0',
                'value': 0
            },
            'incoming': {
                'connections': {
                    out_plug.node.identifier: 'out'
                },
                'name': 'compound_in.incoming',
                'value': 'out_value'
            },
            'key': {
                'connections': {},
                'name': 'compound_in.key',
                'value': 'value'
            }
        }
    }

    out_serialized = out_plug.serialize()
    assert out_serialized == {
        'name': 'out',
        'value': 'out_value',
        'connections': {
            in1_plug.node.identifier: [
                'in1',
                'compound_in.incoming'
            ]
        },
        'sub_plugs': {}
    }

    compound_out_serialized = compound_out_plug.serialize()
    assert compound_out_serialized == {
        'connections': {},
        'name': 'compound_out',
        'value': None,
        'sub_plugs': {
            '0': {
                'connections': {
                    in2_plug.node.identifier: [
                        'in2'
                    ]
                },
                'name': 'compound_out.0',
                'value': None
            }
        }
    }

    in2_plug_serialized = in2_plug.serialize()
    assert in2_plug_serialized == {
        'connections': {
            compound_out_plug.node.identifier: 'compound_out.0'
        },
        'name': 'in2',
        'value': None,
        'sub_plugs': {}
    }


def test_compound_plugs_can_only_be_strings_or_unicodes():
    @Node(outputs=['compound_out'])
    def A(compound_in):
        pass

    node = A()

    with pytest.raises(TypeError):
        node.inputs['compound_in'][0].value = 0

    with pytest.raises(TypeError):
        node.outputs['compound_out'][0].value = 0

    node.inputs['compound_in'][u"unicode"].value = "unicode"
    node.outputs['compound_out'][u"unicode"].value = "unicode"

    assert node.inputs['compound_in'][u"unicode"].value == "unicode"
    assert node.outputs['compound_out'][u"unicode"].value == "unicode"


def test_compound_input_plugs_are_accessible_by_index():

    @Node(outputs=['value'])
    def A(value):
        return {'value': value}

    @Node(outputs=['sum'])
    def B(compound_in):
        return {'sum': sum(compound_in.values())}

    a1 = A(value=1)
    a2 = A(value=2)
    a3 = A(value=3)
    b = B()

    a1.outputs['value'].connect(b.inputs['compound_in']['0'])
    a2.outputs['value'].connect(b.inputs['compound_in']['1'])
    a3.outputs['value'].connect(b.inputs['compound_in']['2'])

    a1.evaluate()
    a2.evaluate()
    a3.evaluate()

    b.evaluate()

    assert b.outputs['sum'].value == 6


def test_compound_output_plugs_are_accessible_by_index():

    @Node(outputs=['compound_out'])
    def A(values):
        return {
            'compound_out.0': values[0],
            'compound_out.1': values[1],
            'compound_out.2': values[2]
        }

    @Node(outputs=['sum'])
    def B(compound_in):
        return {'sum': sum(compound_in.values())}

    a = A(values=[1, 2, 3])
    b = B()

    a.outputs['compound_out']['0'].connect(b.inputs['compound_in']['0'])
    a.outputs['compound_out']['1'].connect(b.inputs['compound_in']['1'])
    a.outputs['compound_out']['2'].connect(b.inputs['compound_in']['2'])

    a.evaluate()
    b.evaluate()

    assert b.outputs['sum'].value == 6


def test_compound_plugs_can_be_connected_individually():

    @Node(outputs=['value', 'compound_out'])
    def A(compound_in, in1):
        pass

    a1 = A()
    a2 = A()

    a2.inputs['compound_in']['0'].connect(a1.outputs['value'])
    a1.outputs['compound_out']['0'].connect(a2.inputs['in1'])


def test_compound_plugs_are_not_dirty_if_parent_plug_is_dirty():

    @Node(outputs=['compound_out'])
    def A(compound_in):
        pass

    node = A()
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = 1

    node.inputs['compound_in'].is_dirty = False
    node.inputs['compound_in']['0'].is_dirty = False
    node.inputs['compound_in']['1'].is_dirty = False

    node.inputs['compound_in'].is_dirty = True

    assert not node.inputs['compound_in']['0'].is_dirty
    assert not node.inputs['compound_in']['1'].is_dirty

    node.outputs['compound_out']['0'].value = 0
    node.outputs['compound_out']['0'].value = 1

    node.outputs['compound_out'].is_dirty = False
    node.outputs['compound_out']['0'].is_dirty = False
    node.outputs['compound_out']['1'].is_dirty = False

    node.outputs['compound_out'].is_dirty = True

    assert not node.outputs['compound_out']['0'].is_dirty
    assert not node.outputs['compound_out']['1'].is_dirty


def test_compound_plugs_propagate_dirty_state_to_their_parent():

    @Node(outputs=['compound_out'])
    def A(compound_in):
        pass

    node = A()
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = 1

    node.inputs['compound_in'].is_dirty = False
    node.inputs['compound_in']['0'].is_dirty = False
    node.inputs['compound_in']['1'].is_dirty = False

    node.inputs['compound_in']['0'].is_dirty = True

    assert node.inputs['compound_in'].is_dirty

    node.outputs['compound_out']['0'].value = 0
    node.outputs['compound_out']['1'].value = 1

    node.outputs['compound_out']['0'].is_dirty = False
    node.outputs['compound_out']['1'].is_dirty = False
    assert not node.outputs['compound_out'].is_dirty

    node.outputs['compound_out']['0'].is_dirty = True
    assert node.outputs['compound_out'].is_dirty


def test_compound_plug_ignores_direct_value_assignment():

    @Node(outputs=['compound_out'])
    def A(compound_in):
        pass

    node = A()
    node.inputs['compound_in']['0'].value = 0
    node.inputs['compound_in']['1'].value = 1

    node.outputs['compound_out']['0'].value = 0
    node.outputs['compound_out']['1'].value = 1

    node.inputs['compound_in'].value = 2
    assert node.inputs['compound_in'].value == {'0': 0, '1': 1}

    node.outputs['compound_out'].value = 2
    assert node.outputs['compound_out'].value == {'0': 0, '1': 1}


def test_plugs_can_not_contain_dots():

    @Node()
    def A():
        pass

    with pytest.raises(ValueError):
        OutputPlug(name='name.with.dots', node=A())

    with pytest.raises(ValueError):
        InputPlug(name='name.with.dots', node=A())
