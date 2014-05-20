"""
    zbx.io.xml
    ~~~~~~~~~~

    Everything to convert config into xml, and vice versa
"""

from __future__ import absolute_import
from __future__ import print_function

__all__ = ['XmlDumper']

from copy import deepcopy
import datetime
from xml.dom import minidom
import xml.etree.ElementTree as ET

try:
    from six.moves import cStringIO as StringIO
except ImportError:
    from six.moves import StringIO as StringIO

from zbx.config import Config, Reference, Collection
from zbx.util import copied
from .defaults import rules


class XmlDumper(object):
    """
    Dump conf to xml
    """

    def __init__(self, conf):
        if not isinstance(conf, Config):
            raise ValueError('Config only')
        self.conf = conf

    @property
    def compiled(self):
        """docstring for compiled"""
        return compile(self.conf)

    def __str__(self):
        """
        Converts the configuration into xml
        """
        return dumps(self.compiled)

    def __iter__(self):
        """
        Importing a full xml document into zabbix may fails.

        This method allow to generate smaller xml files, which
        are inteded to be imported in the order their are generated.
        """

        root = self.compiled

        @copied
        def factory():
            c = document()
            root_groups = c.find("./groups")
            for child in root.findall('./groups/group'):
                root_groups.append(child)
            return c

        container = factory()
        hosts = ET.SubElement(container, 'hosts')
        for src in root.findall("./hosts/host"):
            host = deepcopy(src)

            hosts.append(host)

            for child in host:
                if child.tag in ('screens', 'items'):
                    host.remove(child)

            yield 'hosts/host', dumps(container), host.find('name').text

            host.clear()
            for child in src:
                if child.tag in ('name', 'host'):
                    host.append(child)
            items = ET.SubElement(host, 'items')

            for item in src.findall("./items/item"):
                items.append(item)

            if len(items):
                yield 'hosts/host/items', dumps(container), host.find('name').text
            hosts.remove(host)

        container = factory()
        hosts = ET.SubElement(container, 'templates')
        for src in root.findall("./templates/template"):
            host = deepcopy(src)

            hosts.append(host)

            for child in host:
                if child.tag in ('screens',):
                    host.remove(child)

            yield 'templates/template', dumps(container), host.find('name').text
            hosts.remove(host)

        container = factory()
        graphs = ET.SubElement(container, 'graphs')
        for src in root.findall("./graphs/graph"):
            graph = deepcopy(src)

            graphs.append(graph)
            yield 'graphs/graph', dumps(container), graph.find('name').text
            graphs.remove(graph)

        container = factory()
        screens = ET.SubElement(container, 'screens')
        for src in root.findall("./screens/screen"):
            screen = deepcopy(src)

            screens.append(screen)
            yield 'screens/screen', dumps(container), screen.find('name').text
            screens.remove(screen)

        container = factory()
        hosts = ET.SubElement(container, 'hosts')
        for src in root.findall("./hosts/host/screens/screen/../.."):
            host = deepcopy(src)
            for child in host:
                if child.tag not in ('name', 'host'):
                    host.remove(child)
            screens = ET.SubElement(host, 'screens')

            hosts.append(host)
            for screen in src.findall("./screens/screen"):
                screens.clear()
                screens.append(screen)

                yield 'hosts/host/screens/screen', dumps(container), screen.find('name').text
            hosts.remove(host)

        container = factory()
        hosts = ET.SubElement(container, 'templates')
        for src in root.findall("./templates/template/screens/screen/../.."):
            host = ET.SubElement(hosts, 'template')
            for child in src:
                if child.tag in ('name', 'template'):
                    host.append(child)
            screens = ET.SubElement(host, 'screens')

            for screen in src.findall("./screens/screen"):
                screens.clear()
                screens.append(screen)

                yield 'templates/template/screens/screen', dumps(container), screen.find('name').text
            hosts.clear()

        container = factory()
        hosts = ET.SubElement(container, 'triggers')
        for src in root.findall("./triggers/trigger"):
            trigger = deepcopy(src)
            hosts.append(trigger)
            yield 'triggers/trigger', dumps(container), trigger.find('name').text
            hosts.remove(trigger)



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


def _compile(obj, xml_tag=None):
    """Compile obj into an ElementTree.
    """

    if isinstance(obj, Config):
        root = document()
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

        root_triggers = root.find("./triggers")
        if root_triggers is None:
            root_triggers = ET.SubElement(root, 'triggers')

        for xpath in ("./hosts/host/triggers/..",
                      "./templates/template/triggers/.."):
            for host in root.findall(xpath):
                for triggers in host.findall("./triggers"):
                    host.remove(triggers)
                    root_triggers.extend(triggers)

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


def dumps(root):
    """Convert obj into an xml string.
    """

    if not isinstance(root, ET.Element):
        raise ValueError

    document = ET.ElementTree(root)
    flow = StringIO()
    document.write(flow, encoding='utf-8', xml_declaration=True)
    contents = flow.getvalue()
    flow.close()

    return minidom.parseString(contents).toprettyxml(indent="  ")


def document():
    root = ET.Element('zabbix_export')
    ET.SubElement(root, 'version').text = '2.0'
    ET.SubElement(root, 'date').text = datetime.datetime.now().isoformat()
    ET.SubElement(root, 'groups')

    return root
