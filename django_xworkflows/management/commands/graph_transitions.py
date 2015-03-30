# -*- coding: utf-8; mode: django -*-
"""
A Django management command to display the transition graph of a Workflow.

Heavily inspired by django-fsm's similar management command, see

https://github.com/kmmbvnr/django-fsm
"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand
import graphviz
import importlib
from optparse import make_option

from xworkflows.base import WorkflowMeta


def generate_dot(workflows):
    result = graphviz.Digraph()

    for name, workflow in workflows:
        sources, targets, edges = set(), set(), set()

        # dump nodes and edges
        for transition in workflow.transitions._transitions.values():
            for source in transition.source:
                source_name = '%s.%s' % (name, source)
                target_name = '%s.%s' % (name, transition.target)
                sources.add((source_name, str(source)))
                targets.add((target_name, str(transition.target)))
                edges.add((source_name, target_name, (('label', str(transition.name)),)))

        # construct subgraph
        subgraph = graphviz.Digraph(
            name="cluster_%s" % (name, ),
            graph_attr={
                'label': "%s" % (name, ),
            },
        )

        final_states = targets - sources
        for name, label in final_states:
            subgraph.node(name, label=label, shape='doublecircle')
        for name, label in (sources | targets) - final_states:
            subgraph.node(name, label=label, shape='circle')
            if workflow.initial_state:  # Adding initial state notation
                if label == workflow.initial_state:
                    subgraph.node('.', shape='point')
                    subgraph.edge('.', name)
        for source_name, target_name, attrs in edges:
            subgraph.edge(source_name, target_name, **dict(attrs))

        result.subgraph(subgraph)

    return result


class Command(BaseCommand):
    requires_model_validation = True

    option_list = BaseCommand.option_list + (
        make_option('--output', '-o', action='store', dest='outputfile',
            help='Render output file. Type of output dependent on file extensions. Use png or jpg to render graph to image.'),  # NOQA
        make_option('--layout', '-l', action='store', dest='layout', default='dot',
            help='Layout to be used by GraphViz for visualization. Layouts: circo dot fdp neato nop nop1 nop2 twopi'),
    )

    help = ("Creates a GraphViz dot file with transitions for selected modules")
    args = "[path.to.module]"

    def render_output(self, graph, **options):
        filename, fmt = options['outputfile'].rsplit('.', 1)
        graph.engine = options['layout']
        graph.format = fmt
        graph.render(filename)

    def handle(self, *args, **options):

        if len(args) == 0:
            self.stderr.write("Please specify at least one module as argument\n")
            return

        workflows = dict()
        for arg in args:
            try:
                mod = importlib.import_module(arg)
            except ImportError as e:
                raise ImportError("Unable to import module '%s'" % (arg))

            for s in dir(mod):
                symbol = getattr(mod, s)
                if isinstance(symbol, WorkflowMeta):
                    workflows['%s.%s' % (arg, s)] = symbol

        if not workflows:
            self.stderr.write("No workflow detected in the specified module(s), exiting.\n")
            return

        dotdata = generate_dot(workflows.items())
        if options['outputfile']:
            self.render_output(dotdata, **options)
        else:
            self.stdout.write(str(dotdata))
