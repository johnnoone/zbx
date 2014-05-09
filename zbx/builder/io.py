__all__ = ['compile', 'dumps']

import sys
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from zbx.config.models import Document, Reference, Collection


def compile(obj, xml_tag=None):
    """Compile obj into an ElementTree.
    """

    root = ET.Element(xml_tag or obj.xml_tag)

    if isinstance(obj, Document):
        ET.SubElement(root, 'version').text = '2.0'
        ET.SubElement(root, 'date').text = datetime.datetime.now().isoformat()

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
                    node.append(compile(element, sub_xml_tag))
        elif value is not None or getattr(value, 'allow_empty', False):
            node = ET.SubElement(root, key)
            node.text = str(value)

    if isinstance(obj, Document):
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
        if root_groups is None:
            root_groups = ET.SubElement(root, 'groups')
        else:
            root_groups.clear()
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


def dumps(obj):
    """Convert obj into an xml string.
    """

    root = compile(obj)
    document = ET.ElementTree(root)
    flow = StringIO()
    document.write(flow, encoding='utf-8', xml_declaration=True)
    contents = flow.getvalue()
    flow.close()

    return minidom.parseString(contents).toprettyxml(indent="  ")
