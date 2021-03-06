"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from ...componentclass.validators.types import TypesComponentValidator
from ..base import ConnectionRuleBlock
from ..utils.visitors import ConnectionRuleActionVisitor


class TypesConnectionRuleValidator(ConnectionRuleActionVisitor,
                                   TypesComponentValidator):

    def action_connectionruleblock(self, connectionruleblock):
        assert isinstance(connectionruleblock, ConnectionRuleBlock)
