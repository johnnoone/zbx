import logging
from zbx.builder import *
from zbx.config import *


def discovery(tpl):
    rule = tpl.discovery_rules.new('Circus discovery', key='circus.discovery')

    proto1 = rule.item_prototypes.new(**{
        'key': 'circus.worker.sum.numprocesses[{#WORKER}]',
        'name': 'Processes count for $1',
        'units': '',
        'description': 'Processes count for all worker processes',
        'applications': ['Circus server usage']
    })

    proto2 = rule.item_prototypes.new(**{
        'key': 'circus.worker.sum.mem[{#WORKER}]',
        'name': 'Memory usage for $1',
        'value_type': 'numeric_float',
        'units': '%',
        'description': 'Percentage of worker processes memory usage',
        'applications': ['Circus server usage']
    })

    proto3 = rule.item_prototypes.new(**{
        'key': 'circus.worker.sum.mem_info1[{#WORKER}]',
        'name': 'RSS Memory usage for $1',
        'value_type': 'numeric_float',
        'units': 'M',
        'description': 'Resident Set Size Memory in bytes (RSS) for all worker processes',
        'applications': ['Circus server usage']
    })

    proto4 = rule.item_prototypes.new(**{
        'key': 'circus.worker.sum.mem_info2[{#WORKER}]',
        'name': 'VMS Memory usage for $1',
        'value_type': 'numeric_float',
        'units': 'M',
        'description': 'Resident Set Size Memory in bytes (VMS) for all worker processes',
        'applications': ['Circus server usage']
    })

    proto5 = rule.item_prototypes.new(**{
        'key': 'circus.worker.sum.cpu[{#WORKER}]',
        'name': 'CPU usage for $1',
        'value_type': 'numeric_float',
        'units': '%',
        'description': 'Percentage of CPU usage of a worker',
        'applications': ['Circus server usage']
    })

    graph1 = rule.graph_prototypes.new('Circus - Processes count for {#WORKER}')
    graph1.graph_items.new(proto1)

    graph2 = rule.graph_prototypes.new('Circus - Memory usage for {#WORKER}')
    graph2.graph_items.new(proto2)

    graph3 = rule.graph_prototypes.new('Circus - RSS Memory usage for {#WORKER}')
    graph3.graph_items.new(proto3)

    graph4 = rule.graph_prototypes.new('Circus - VMS Memory usage for {#WORKER}')
    graph4.graph_items.new(proto4)

    graph5 = rule.graph_prototypes.new('Circus - CPU usage for {#WORKER}')
    graph5.graph_items.new(proto5)


def generate():
    doc = Config()

    tpl = doc.templates.new('Template - Generic - Circus Process Manager',
        groups=['Templates - Services'], applications=['Circus server usage'])


    item1 = tpl.items.new(**{
        'name': 'Circus - Number of processes',
        'key': 'circus.numprocesses',
        'units': '',
        'description': 'Total number of circusd processes',
        'applications': ['Circus server usage']
    })


    item2 = tpl.items.new(**{
        'name': 'Circus - Number of children',
        'key': 'circus.dstats.children',
        'units': '',
        'description': 'Total number of circusd children',
        'applications': ['Circus server usage']
    })

    item3 = tpl.items.new(**{
        'name': 'Circus - Memory usage',
        'key': 'circus.dstats.mem',
        'value_type': 'numeric_float',
        'units': '%',
        'description': 'Percentage of circusd process memory usage',
        'applications': ['Circus server usage']
    })

    item4 = tpl.items.new(**{
        'name': 'Circus - RSS Memory',
        'key': 'circus.dstats.mem_info1',
        'value_type': 'numeric_float',
        'units': 'M',
        'description': 'Resident Set Size Memory in bytes (RSS)',
        'applications': ['Circus server usage']
    })

    item5 = tpl.items.new(**{
        'name': 'Circus - VMS Memory',
        'key': 'circus.dstats.mem_info2',
        'value_type': 'numeric_float',
        'units': 'M',
        'description': 'Resident Set Size Memory in bytes (VMS)',
        'applications': ['Circus server usage']
    })

    item6 = tpl.items.new(**{
        'name': 'Circus - CPU usage',
        'key': 'circus.dstats.cpu',
        'value_type': 'numeric_float',
        'units': '%',
        'description': 'Percentage of circusd process CPU usage',
        'applications': ['Circus server usage']
    })

    item7 = tpl.items.new(**{
        'name': 'Circus - Nice',
        'key': 'circus.dstats.nice',
        'units': '',
        'description': 'Niceness of the circusd process (between -20 and 20)',
        'applications': ['Circus server usage']
    })

    graph1 = tpl.graphs.new('Circus - Number of processes')
    graph1.graph_items.new(item1)

    graph2 = tpl.graphs.new('Circus - Number of children')
    graph2.graph_items.new(item2)

    graph3 = tpl.graphs.new('Circus - Memory usage')
    graph3.graph_items.new(item3)

    graph4 = tpl.graphs.new('Circus - RSS Memory')
    graph4.graph_items.new(item4)

    graph5 = tpl.graphs.new('Circus - VMS Memory')
    graph5.graph_items.new(item5)

    graph6 = tpl.graphs.new('Circus - CPU usage')
    graph6.graph_items.new(item6)

    graph7 = tpl.graphs.new('Circus - Nice')
    graph7.graph_items.new(item7)

    screen1 = tpl.screens.new('Generic Screen - Circus')
    screen1.screen_items.new(graph1)
    screen1.screen_items.new(graph2)
    screen1.screen_items.new(graph3)
    screen1.screen_items.new(graph4)
    screen1.screen_items.new(graph5)
    screen1.screen_items.new(graph6)
    screen1.screen_items.new(graph7)

    # discovery rules
    discovery(tpl)
    return doc


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='zbx stuff for circus')
    parser.add_argument('--show-template', action='store_true', help='show generated template')
    parser.add_argument('--split-template', action='store_true', help='split configuration into small xml files')
    args = parser.parse_args()

    conf = generate()

    if args.show_template:
        print dumps(conf)

    if args.split_template:
        for kind, fragment, name in divide_xml(conf):
            print 'xml for:', kind, name
            print dumps(fragment)
