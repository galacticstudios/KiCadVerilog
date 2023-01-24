# MIT license
# 
# Copyright (C) 2017-2021 by Dave Vandenbout.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


"""
Parsers for netlist files of various formats (only KiCad, at present).
"""


from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()

from py_2_3 import *

from pyparsing import *


THIS_MODULE = locals()


def _parse_netlist_kicad(text):
    """
    Return a pyparsing object storing the contents of a KiCad netlist.
    """

    def _paren_clause(keyword, subclause):
        """
        Create a parser for a parenthesized list with an initial keyword.
        """
        lp = Literal('(').suppress()
        rp = Literal(')').suppress()
        kw = CaselessKeyword(keyword).suppress()
        clause = lp + kw + subclause + rp
        return clause

    #++++++++++++++++++++++++++++ Parser Definition +++++++++++++++++++++++++++

    # Basic elements.
    string = ZeroOrMore(White()).suppress() + CharsNotIn('()') + ZeroOrMore(White()).suppress()
    qstring = dblQuotedString() ^ sglQuotedString()
    qstring.addParseAction(removeQuotes)
    anystring = Optional(qstring ^ string) # Don't know why Optional() is necessary to make the parser work.
    word = anystring
    inum = anystring

    # Design section.
    source = _paren_clause('source', Optional(anystring)('source'))
    date = _paren_clause('date', Optional(anystring)('date'))
    tool = _paren_clause('tool', Optional(anystring)('tool'))
    number = _paren_clause('number', inum('num'))
    name = _paren_clause('name', anystring('name')) | _paren_clause('names', anystring('names'))
    value = _paren_clause('value', anystring('value'))
    tstamp = _paren_clause('tstamp', anystring('tstamp')) | _paren_clause('tstamps', anystring('tstamps'))
    title = _paren_clause('title', Optional(anystring)('title'))
    company = _paren_clause('company', Optional(anystring)('company'))
    rev = _paren_clause('rev', Optional(anystring)('rev'))
    txt = _paren_clause('value', anystring('text'))
    comment = _paren_clause('comment', Group(number & txt))
    comments = Group(OneOrMore(comment))('comments')
    title_block = _paren_clause('title_block', Optional(title) &
                        Optional(company) & Optional(rev) &
                        Optional(date) & Optional(source) & comments)
    sheet = _paren_clause('sheet', Group(number + name + tstamp + Optional(title_block)))
    sheets = OneOrMore(sheet)('sheets')
    design = (_paren_clause('design', Optional(source) & Optional(date) &
                        Optional(tool) & Optional(sheets)))

    # Components section.
    ref = _paren_clause('ref', anystring('ref'))
    datasheet = _paren_clause('datasheet', anystring('datasheet'))
    field = Group(_paren_clause('field', name & anystring('value')))
    fields = _paren_clause('fields', ZeroOrMore(field)('fields'))
    property = Group(_paren_clause('property', name & Optional(value)))
    properties = OneOrMore(property)('properties')
    lib = _paren_clause('lib', anystring('lib'))
    part = _paren_clause('part', anystring('name'))
    footprint = _paren_clause('footprint', anystring('footprint'))
    description = _paren_clause('description', anystring('desc'))  # Gets used here and in libparts.
    libsource = _paren_clause('libsource', lib & part & Optional(description))
    sheetpath = Group(_paren_clause('sheetpath', name & tstamp))('sheetpath')
    comp = Group(_paren_clause('comp', ref & value & Optional(datasheet) & 
                    Optional(fields) & Optional(libsource) & Optional(footprint) & 
                    Optional(sheetpath) & Optional(tstamp) & Optional(properties)))
    components = _paren_clause('components', ZeroOrMore(comp)('parts'))

    # Part library section.
    docs = _paren_clause('docs', anystring('docs'))
    pnum = _paren_clause('num', anystring('num'))
    ptype = _paren_clause('type', anystring('type'))
    pin = _paren_clause('pin', Group(pnum & name & ptype))
    pins = _paren_clause('pins', ZeroOrMore(pin))('pins')
    alias = _paren_clause('alias', anystring('alias'))
    aliases = _paren_clause('aliases', ZeroOrMore(alias))('aliases')
    fp = _paren_clause('fp', anystring('fp'))
    footprints = _paren_clause('footprints', ZeroOrMore(fp))('footprints')
    libpart = Group(_paren_clause('libpart', lib & part & Optional(fields) & 
                Optional(pins) & Optional(footprints) & Optional(aliases) &
                Optional(description) & Optional(docs)))
    libparts = _paren_clause('libparts', ZeroOrMore(libpart))('libparts')

    # Libraries section.
    logical = _paren_clause('logical', anystring('name'))
    uri = _paren_clause('uri', anystring('uri'))
    library = Group(_paren_clause('library', logical & uri))
    libraries = _paren_clause('libraries', ZeroOrMore(library))('libraries')

    # Nets section.
    #code = _paren_clause('code', inum('val'))('code')
    code = _paren_clause('code', inum('code'))
    part_pin = _paren_clause('pin', anystring('num'))
    pin_type = _paren_clause('pintype', anystring('type'))
    pin_func = _paren_clause('pinfunction', anystring('function'))
    node = _paren_clause('node', Group(ref & part_pin & Optional(pin_func) & Optional(pin_type)))
    nodes = Group(OneOrMore(node))('pins')
    net = _paren_clause('net', Group(code & name & nodes))
    nets = _paren_clause('nets', ZeroOrMore(net))('nets')

    # Entire netlist.
    version = _paren_clause('version', word('version'))
    end_of_file = ZeroOrMore(White()) + stringEnd
    parser = _paren_clause('export', version +
                (design & components & Optional(libparts) & Optional(libraries) & nets
                )) + end_of_file.suppress()

    return parser.parseString(text)


def parse_netlist(src, tool='kicad'):
    """
    Return a pyparsing object storing the contents of a netlist.

    Args:
        src: Either a text string, or a filename, or a file object that stores
            the netlist.

    Returns:
        A pyparsing object that stores the netlist contents.

    Exception:
        PyparsingException.
    """

    try:
        text = src.read()
    except Exception:
        try:
            text = open(src,'r',encoding='latin_1').read()
        except Exception:
            text = src

    if not isinstance(text, basestring):
        raise Exception("What is this shit you're handing me? [{}]\n".format(src))

    try:
        # Use the tool name to find the function for loading the library.
        func_name = '_parse_netlist_{}'.format(tool)
        parse_func = THIS_MODULE[func_name]
        return parse_func(text)
    except KeyError:
        # OK, that didn't work so well...
        logger.error('Unsupported ECAD tool library: {}'.format(tool))
        raise Exception
