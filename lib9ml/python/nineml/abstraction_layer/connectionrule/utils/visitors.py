"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from ...componentclass.utils import ComponentVisitor


class ConnectionRuleVisitor(ComponentVisitor):

    def visit(self, obj, **kwargs):
        return obj.accept_visitor(self, **kwargs)
