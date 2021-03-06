"""
This file contains the main classes for defining dynamics

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
import re
from nineml.utils import (filter_discrete_types, ensure_valid_identifier,
                            normalise_parameter_as_list, assert_no_duplicates)
from nineml.exceptions import NineMLRuntimeError
from ..expressions import ODE
from .. import BaseALObject
from ..units import dimensionless


class Regime(BaseALObject):

    """
    A Regime is something that contains |TimeDerivatives|, has temporal extent,
    defines a set of |Transitions| which occur based on |Conditions|, and can
    be join the Regimes to other Regimes.
    """

    defining_attributes = ('_time_derivatives', '_on_events', '_on_conditions',
                           'name')

    _n = 0

    @classmethod
    def get_next_name(cls):
        """Return the next distinct autogenerated name
        """
        Regime._n = Regime._n + 1
        return 'Regime%d' % Regime._n

    # Visitation:
    # -------------
    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_regime(self, **kwargs)

    def __init__(self, *args, **kwargs):
        """Regime constructor

            :param name: The name of the constructor. If none, then a name will
                be automatically generated.
            :param time_derivatives: A list of time derivatives, as
                either ``string``s (e.g 'dg/dt = g/gtau') or as
                |TimeDerivative| objects.
            :param transitions: A list containing either |OnEvent| or
                |OnCondition| objects, which will automatically be sorted into
                the appropriate classes automatically.
            :param *args: Any non-keyword arguments will be treated as
                time_derivatives.


        """
        valid_kwargs = ('name', 'transitions', 'time_derivatives')
        for arg in kwargs:
            if arg not in valid_kwargs:
                err = 'Unexpected Arg: %s' % arg
                raise NineMLRuntimeError(err)

        name = kwargs.get('name', None)
        if name is None:
            self._name = 'default'
        else:
            self._name = name.strip()
            ensure_valid_identifier(self._name)
        transitions = kwargs.get('transitions', None)
        kw_tds = normalise_parameter_as_list(kwargs.get('time_derivatives',
                                                        None))
        time_derivatives = list(args) + kw_tds

        # Un-named arguments are time_derivatives:
        time_derivatives = normalise_parameter_as_list(time_derivatives)
        # time_derivatives.extend( args )

        td_types = (basestring, TimeDerivative)
        td_type_dict = filter_discrete_types(time_derivatives, td_types)
        td_from_str = [TimeDerivative.from_str(o)
                       for o in td_type_dict[basestring]]
        time_derivatives = td_type_dict[TimeDerivative] + td_from_str

        # Check for double definitions:
        td_dep_vars = [td.dependent_variable for td in time_derivatives]
        assert_no_duplicates(td_dep_vars)

        # Store as a dictionary
        self._time_derivatives = dict((td.dependent_variable, td)
                                      for td in time_derivatives)

        # We support passing in 'transitions', which is a list of both OnEvents
        # and OnConditions. So, lets filter this by type and add them
        # appropriately:
        transitions = normalise_parameter_as_list(transitions)
        f_dict = filter_discrete_types(transitions, (OnEvent, OnCondition))
        self._on_events = []
        self._on_conditions = []

        # Add all the OnEvents and OnConditions:
        for event in f_dict[OnEvent]:
            self.add_on_event(event)
        for condition in f_dict[OnCondition]:
            self.add_on_condition(condition)

        # Sort for equality checking
        self._on_events = sorted(self._on_events,
                                 key=lambda x: x.src_port_name)
        self._on_conditions = sorted(self._on_conditions,
                                     key=lambda x: x.trigger)

    def _resolve_references_on_transition(self, transition):
        if transition.target_regime_name is None:
            transition.set_target_regime(self)

        assert not transition._source_regime_name
        transition.set_source_regime(self)

    def add_on_event(self, on_event):
        """Add an |OnEvent| transition which leaves this regime

        If the on_event object has not had its target regime name
        set in the constructor, or by calling its ``set_target_regime_name()``,
        then the target is assumed to be this regime, and will be set
        appropriately.

        The source regime for this transition will be set as this regime.

        """

        if not isinstance(on_event, OnEvent):
            err = "Expected 'OnEvent' Obj, but got %s" % (type(on_event))
            raise NineMLRuntimeError(err)

        self._resolve_references_on_transition(on_event)
        self._on_events.append(on_event)

    def add_on_condition(self, on_condition):
        """Add an |OnCondition| transition which leaves this regime

        If the on_condition object has not had its target regime name
        set in the constructor, or by calling its ``set_target_regime_name()``,
        then the target is assumed to be this regime, and will be set
        appropriately.

        The source regime for this transition will be set as this regime.

        """
        if not isinstance(on_condition, OnCondition):
            err = ("Expected 'OnCondition' Obj, but got %s" %
                   (type(on_condition)))
            raise NineMLRuntimeError(err)
        self._resolve_references_on_transition(on_condition)
        self._on_conditions.append(on_condition)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    # Regime Properties:
    # ------------------
    @property
    def time_derivatives(self):
        """Returns the state-variable time-derivatives in this regime.

        .. note::

            This is not guaranteed to contain the time derivatives for all the
            state-variables specified in the component. If they are not
            defined, they are assumed to be zero in this regime.

        """
        return self._time_derivatives.itervalues()

    @property
    def time_derivatives_map(self):
        return self._time_derivatives

    @property
    def transitions(self):
        """Returns all the transitions leaving this regime.

        Returns an iterator over both the on_events and on_conditions of this
        regime"""

        return chain(self._on_events, self._on_conditions)

    @property
    def on_events(self):
        """Returns all the transitions out of this regime trigger by events"""
        return iter(self._on_events)

    @property
    def on_conditions(self):
        """Returns all the transitions out of this regime trigger by
        conditions"""
        return iter(self._on_conditions)

    @property
    def name(self):
        return self._name


class StateVariable(BaseALObject):

    """A class representing a state-variable in a ``DynamicsClass``.

    This was originally a string, but if we intend to support units in the
    future, wrapping in into its own object may make the transition easier
    """

    defining_attributes = ('name', 'dimension')

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_statevariable(self, **kwargs)

    def __init__(self, name, dimension=None):
        """StateVariable Constructor

        :param name:  The name of the state variable.
        """
        self._name = name.strip()
        self._dimension = dimension if dimension is not None else dimensionless
        ensure_valid_identifier(self._name)

    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dimension

    def set_dimension(self, dimension):
        self._dimension = dimension

    def __repr__(self):
        return ("StateVariable({}{})"
                .format(self.name,
                        ', dimension={}'.format(self.dimension.name)))


class TimeDerivative(ODE):

    """Represents a first-order, ordinary differential equation with respect to
    time.

    """

    def __init__(self, dependent_variable, rhs):
        """Time Derivative Constructor

            :param dependent_variable: A `string` containing a single symbol,
                which is the dependent_variable.
            :param rhs: A `string` containing the right-hand-side of the
                equation.


            For example, if our time derivative was:

            .. math::

                \\frac{dg}{dt} = \\frac{g}{gtau}

            Then this would be constructed as::

                TimeDerivative( dependent_variable='g', rhs='g/gtau' )

            Note that although initially the time variable
            (independent_variable) is ``t``, this can be changed using the
            methods: ``td.lhs_name_transform_inplace({'t':'T'} )`` for example.



            """
        ODE.__init__(self,
                     dependent_variable=dependent_variable,
                     independent_variable='t',
                     rhs=rhs)

    def __repr__(self):
        return "TimeDerivative( d%s/dt = %s )" % \
            (self.dependent_variable, self.rhs)

    def accept_visitor(self, visitor, **kwargs):
        """ |VISITATION| """
        return visitor.visit_timederivative(self, **kwargs)

    @classmethod
    def from_str(cls, time_derivative_string):
        """Creates an TimeDerivative object from a string"""
        # Note: \w = [a-zA-Z0-9_]
        tdre = re.compile(r"""\s* d(?P<dependent_var>[a-zA-Z][a-zA-Z0-9_]*)/dt
                           \s* = \s*
                           (?P<rhs> .*) """, re.VERBOSE)

        match = tdre.match(time_derivative_string)
        if not match:
            err = "Unable to load time derivative: %s" % time_derivative_string
            raise NineMLRuntimeError(err)
        dependent_variable = match.groupdict()['dependent_var']
        rhs = match.groupdict()['rhs']
        return TimeDerivative(dependent_variable=dependent_variable, rhs=rhs)


from .transitions import OnEvent, OnCondition
