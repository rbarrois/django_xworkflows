import os
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import models
from django_xworkflows.models import WorkflowEnabledMeta

from xworkflows.base import HOOK_CHECK, HOOK_BEFORE, HOOK_ON_LEAVE, HOOK_AFTER, HOOK_ON_ENTER, noop

try:
    import pygraphviz as pgv
except:
    pgv = None


HOOKS = ((HOOK_CHECK, HOOK_BEFORE, HOOK_ON_LEAVE,), (HOOK_AFTER, HOOK_ON_ENTER))


def state_name_template(workflow):
    return '%s_st_%%s' % workflow.__class__.__name__


def transition_name_template(workflow):
    return '%s_tr_%%s' % workflow.__class__.__name__


class Command(BaseCommand):
    args = '<app[.Model[.state]]> <app[.Model[.state]]> ...'
    help = """Render the workflow by using graphviz."""
    option_list = BaseCommand.option_list + (
        make_option('-f','--filepath', action='store', dest='filepath', default=None,
                    help='Filepath to store the rendered graph at.'),
        make_option('-d', '--detail', action="store", dest='detail', default='simple',
                    help='How detailed should the output be? (minimal, simple, hooks)'),
        make_option('-o','--output-format', action='store', dest='output_format', default=None,
                    help='Set the output file format.)'),
        make_option('-l','--layout-method', action='store', dest='layout', default='dot',
                    help='Set the layout method of graphviz. (default=dot)'),
    )

    @property
    def graph(self):
        if not hasattr(self, '_graph'):
            self._graph = G = pgv.AGraph(
                strict=False, 
                directed=True, 
                label="Workflow", 
                name='Workflow',
            )
            G.node_attr.update({
                'shape': 'record',
                'fontname': 'Arial',
                'fontsize': 12,
            })
        return self._graph

    @property
    def cluster_counter(self):
        if not hasattr(self, '_cluster_counter'):
            self._cluster_counter = 1
        else:
            self._cluster_counter += 1
        return self._cluster_counter

    def draw_transition_table(self, tr_implem):
        hooks = tr_implem.hooks
        rows = ""
        row_tmpl = """<TR><TD ALIGN="LEFT">%s</TD><TD ALIGN="LEFT">%s</TD></TR>"""
        for hook_position in HOOKS[0]:
            if hook_position in hooks:
                rows += row_tmpl % (hook_position, "<br/>".join([x.function.func_name for x in hooks[hook_position]])) 
        if tr_implem.implementation != noop:
            rows += """<TR><TD ALIGN="LEFT">implementation</TD><TD ALIGN="LEFT">%s(%s)</TD></TR>""" % \
                    (tr_implem.implementation.func_name, ' ,'.join(tr_implem.implementation.__code__.co_varnames))

        for hook_position in HOOKS[1]:
            if hook_position in hooks:
                rows += row_tmpl % (hook_position, "<br/>".join([x.function.func_name for x in hooks[hook_position]])) 

        tbl = """<<TABLE ALIGN="LEFT" CELLSPACING="0" BORDER="0">
                 <TR><TD COLSPAN="2"><FONT POINT-SIZE="12" >%s</FONT></TD></TR>%s</TABLE>>""" % \
                 (tr_implem.transition.name, rows)
        return tbl

    def get_workflow_implementation_for(self, model_class, field_name):
        return model_class._xworkflows_implems[field_name]

    def get_workflow_for(self, model_class, field_name):
        return model_class._xworkflows_implems[field_name].workflow

    def draw_workflow_subgraph(self, model_class, field_name, **kwargs):
        wf = self.get_workflow_for(model_class, field_name)
        label = '%s used for %s.%s.%s' % (wf.__class__.__name__, model_class.__module__, 
                                          model_class.__name__, field_name)

        return self.graph.add_subgraph(name='cluster_%s' % self.cluster_counter, label=label)

    def render_minimal(self, model_class, field_name, options):
        """Draw the states as nodes and transitions as edges."""
        graph = self.draw_workflow_subgraph(model_class, field_name)
        workflow = self.get_workflow_for(model_class, field_name)
        st_tmpl = state_name_template(workflow)

        for state in workflow.states:
            graph.add_node(st_tmpl % state.name, label=state.title, shape='diamond')

        for transition in workflow.transitions:
             target_name = st_tmpl % transition.target.name
             for source in transition.source:
                 graph.add_edge(st_tmpl % source.name, target_name, label=transition.name)

    def render_simple(self, model_class, field_name, options):
        """Draw states and transitions and nodes."""
        graph = self.draw_workflow_subgraph(model_class, field_name)
        workflow = self.get_workflow_for(model_class, field_name)
        st_tmpl = state_name_template(workflow)
        tr_tmpl = transition_name_template(workflow)

        for state in workflow.states:
            graph.add_node(st_tmpl % state.name, label=state.title, shape='diamond')

        for transition in workflow.transitions:
            transition_name = tr_tmpl % transition.name
            graph.add_node(transition_name, label=transition.name, shape="record", fontsize=10, height=0.3)
            target_name = st_tmpl % transition.target.name
            graph.add_edge(transition_name, target_name)
            for source in transition.source:
                graph.add_edge(st_tmpl % source.name, transition_name)

    def render_hooks(self, model_class, field_name, options):
        """Draw states as nodes and transitions as nodes. 
        Add hook function names to the transitions.
        """
        graph = self.draw_workflow_subgraph(model_class, field_name)
        workflow = self.get_workflow_for(model_class, field_name)
        implementation = self.get_workflow_implementation_for(model_class, field_name)

        st_tmpl = state_name_template(workflow)
        tr_tmpl = transition_name_template(workflow)

        for state in workflow.states:
            graph.add_node(st_tmpl % state.name, label=state.title, shape='diamond')

        for transition in workflow.transitions:
            transition_name = tr_tmpl % transition.name
            label = self.draw_transition_table(implementation.implementations[transition.name])
            graph.add_node(transition_name, label=label, shape="record", fontsize=10, height=0.3)
            target_name = st_tmpl % transition.target.name
            graph.add_edge(transition_name, target_name)
            for source in transition.source:
                graph.add_edge(st_tmpl % source.name, transition_name)

    def handle(self, *args, **options):

        if not pgv:
            return "You need to install pygraphviz in order to use this command."
        detail = options['detail']
        if detail == 'minimal':
            render_method = self.render_minimal
        elif detail == 'hooks':
            render_method = self.render_hooks
        else:
            render_method = self.render_simple

        for arg in args:
            arg_parts = arg.split('.')
            app_label = arg_parts.pop(0)
            if arg_parts:
                model_class = models.get_model(app_label,arg_parts.pop(0))
                if arg_parts:
                    field = arg_parts.pop(0)
                    render_method(model_class, field, options)
                else:
                    for field in model_class._xworkflows_implems.keys():
                        render_method(model_class, field, option)
            else:
                for model_class in models.get_models(models.get_app(app_label)):
                    if isinstance(model_class, WorkflowEnabledMeta):
                        for field in model_class._xworkflows_implems.keys():
                            render_method(model_class, field, options)

        if options['filepath']:
            path = os.path.abspath(os.path.normpath(options['filepath']))
        else:
            path = None
        if path:
            draw_format = options['output_format'] or os.path.splitext(path)[1][1:] or None
            self.graph.draw(path=path, prog=options['layout'], format=draw_format)
        else:
            output = self.graph.draw(prog=options['layout'], format=options['output_format'] or 'dot')
            print output
