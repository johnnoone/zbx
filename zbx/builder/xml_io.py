__all__ = ['compile', 'dumps', 'divide_xml']

import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from zbx.config.models import Config, Reference, Collection
from .defaults import rules


def _compile(obj, xml_tag=None):
    """Compile obj into an ElementTree.
    """

    if isinstance(obj, Config):
        root = new_root()
    else:
        root = ET.Element(xml_tag or obj.xml_tag)

    for key, value in obj.children():
        if isinstance(value, Reference):
            node = ET.SubElement(root, key)
            for k, v in value.get_reference().items():
                ET.SubElement(node, k).text = str(v)
        elif isinstance(value, (Collection, set, list, tuple)):
            if len(value) or getattr(value, 'allow_empty', False):
                node = ET.SubElement(root, key)
                try:
                    sub_xml_tag = obj._fields[key].xml_tag
                except KeyError:
                    sub_xml_tag = None
                for element in value:
                    node.append(_compile(element, sub_xml_tag))
        elif value is not None or getattr(value, 'allow_empty', False):
            node = ET.SubElement(root, key)
            node.text = str(value)

    return root


def compile(obj, xml_tag=None):
    root = _compile(obj, xml_tag)

    clean(root)

    if isinstance(obj, Config):
        # let's do some fun
        # move every root/graphs to root

        root_graphs = root.find("./graphs")
        if root_graphs is None:
            root_graphs = ET.SubElement(root, 'graphs')

        for xpath in ("./hosts/host/graphs/..",
                      "./templates/template/graphs/.."):
            for host in root.findall(xpath):
                for graphs in host.findall("./graphs"):
                    host.remove(graphs)
                    root_graphs.extend(graphs)

        # copy every root/hosts/**/application to root/hosts

        groupnames = set()
        for group in root.findall("*//groups/group/name"):
            groupnames.add(group.text)

        root_groups = root.find("./groups")
        for name in groupnames:
            group = ET.SubElement(root_groups, 'group')
            ET.SubElement(group, 'name').text = name

        # applications
        for xpath in ("./hosts/host",
                      "./templates/template"):
            applicationnames = set()
            for host in root.findall(xpath):
                for name in host.findall("*//applications/application/name"):
                    applicationnames.add(name.text)

                host_apps = host.find("./applications")
                if host_apps is None:
                    host_apps = ET.SubElement(host, 'applications')
                else:
                    host_apps.clear()
                for name in applicationnames:
                    group = ET.SubElement(host_apps, 'application')
                    ET.SubElement(group, 'name').text = name

    return root


def clean(root):
    """clear unrelevant nodes"""

    document = ET.ElementTree(root)
    for path, value in rules:
        _, _, node = path.rpartition('/')
        xpath = './/{}/..'.format(path)
        for parent in document.findall(xpath):
            for child in parent.findall(node):
                if child.text == str(value):
                    parent.remove(child)


def dumps(obj):
    """Convert obj into an xml string.
    """

    if isinstance(obj, Config):
        root = compile(obj)
    else:
        root = obj

    document = ET.ElementTree(root)
    flow = StringIO()
    document.write(flow, encoding='utf-8', xml_declaration=True)
    contents = flow.getvalue()
    flow.close()

    return minidom.parseString(contents).toprettyxml(indent="  ")


def divide_xml(conf):
    """divide xml  into smaller nodes"""
    root = compile(conf)

    def new_container():
        container = new_root()
        root_groups = container.find("./groups")
        for child in root.findall('./groups/group'):
            root_groups.append(child)
        return container

    def dumps(root):
        document = ET.ElementTree(root)
        flow = StringIO()
        document.write(flow, encoding='utf-8', xml_declaration=True)
        contents = flow.getvalue()
        flow.close()

        return minidom.parseString(contents).toprettyxml(indent="  ")

    postponed_screens = set()

    # import hosts, then templates, then graphs ... then screens
    for host in root.findall("./hosts/host"):
        host = host.copy()
        container = new_container()
        hosts = ET.SubElement(container, 'hosts')
        hosts.append(host)

        for node in host.findall("./screens/screen/.."):
            # post pone screen
            host.remove(node)
            postponed_screens.add(('./hosts/host', './screens/screen/..'))

        yield 'hosts/host', container, host.find('name').text

    for host in root.findall("./templates/template"):
        host = host.copy()
        container = new_container()
        hosts = ET.SubElement(container, 'templates')
        hosts.append(host)

        for node in host.findall("./screens/screen/.."):
            # post pone screen
            host.remove(node)
            postponed_screens.add(('./templates/template', './screens/screen/..'))

        yield 'templates/template', container, host.find('name').text

    for graph in root.findall("./graphs/graph"):
        graph = graph.copy()
        container = new_container()
        graphs = ET.SubElement(container, 'graphs')
        graphs.append(graph)
        yield 'graphs/graph', container, graph.find('name').text

    for screen in root.findall("./screens/screen"):
        screen = screen.copy()
        container = new_container()
        hosts = ET.SubElement(container, 'screens')
        hosts.append(screen)
        yield 'screens/screen', container, screen.find('name').text

    for host in root.findall("./hosts/host/screens/screen/../.."):
        host = host.copy()

        container = new_container()
        hosts = ET.SubElement(container, 'hosts')
        hosts.append(host)
        for child in host:
            if child.tag not in ('screens', 'name', 'host'):
                host.remove(child)

        for screens in host.findall("./screens/screen/.."):
            for screen in screens:
                screens.clear()
                screens.append(screen)

                yield 'templates/template/screens/screen', container, screen.find('name').text

    for host in root.findall("./templates/template/screens/screen/../.."):
        host = host.copy()

        container = new_container()
        hosts = ET.SubElement(container, 'templates')
        hosts.append(host)
        for child in host:
            if child.tag not in ('screens', 'name', 'template'):
                host.remove(child)

        for screens in host.findall("./screens/screen/.."):
            for screen in screens:
                screens.clear()
                screens.append(screen)

                yield 'templates/template/screens/screen', container, screen.find('name').text


def new_root():
    root = ET.Element('zabbix_export')
    ET.SubElement(root, 'version').text = '2.0'
    ET.SubElement(root, 'date').text = datetime.datetime.now().isoformat()
    ET.SubElement(root, 'groups')

    return root


def import_conf():
    """docstring for import_conf"""
    pass
