# MIT license
# 
# Copyright (C) 2023 by Bob Alexander
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

from getopt import getopt
import os
import sys

from builtins import open

try:
    from . import kinparse
    from . import NetlistObjects
except:
    import kinparse
    import NetlistObjects

libparts = {}

class Log:
    def __init__(self):
        self.messages = []
        self.errors = 0
        self.warnings = 0
        self.infos = 0

    def error(self, s):
        self.messages.append('ERROR: ' + s)
        self.errors += 1

    def warning(self, s):
        self.messages.append('WARNING: ' + s)
        self.warnings += 1

    def info(self, s):
        self.messages.append('INFO: ' + s)
        self.infos += 1

    def get_messages(self):
        return self.messages + \
            ['{} errors, {} warnings'.format(self.errors, self.warnings), \
             'Verilog generation ' + ('succeeded!' if self.errors == 0 else 'failed.')]


# Modify a KiCad name so that it's a valid Verilog identifier
def legal_verilog_name(name):
    legal_name = ''
    # If the name doesn't start with a letter, start it with an underscore
    for char in name:
        # Legal Verilog identifier characters get copied
        if char.isalnum() or char == '$' or char == '_':
            legal_name += char
        # *, ~, and / often mean inverse logic. Replace them with an 'n'
        elif char in ['*', '~']:
            legal_name += 'n'
        # Curly braces are used for inverse logic. Discard them.
        elif char == '{' or char == '}':
            pass
        # Change certain characters to underscores
        elif char in ['(', ')', '-', ' ', '.', '/']:
            legal_name += '_'
        elif char == '+':
            legal_name += 'plus'
        # Convert illegal characters to hex codes
        else:
            legal_name += hex(ord(char))[1:]

    # Make sure the name isn't starting with a digit
    if len(legal_name) == 0 or legal_name[0].isdigit():
        legal_name = '_' + legal_name

    return legal_name

# Convert the KiCad pin type into a Verilog type
def verilog_pin_type(type):
    verilog_type = {
        'input' : 'input', 'output' : 'output', 'bidirectional' : 'inout'
        }.get(type)
    if verilog_type == None:
        return 'inout'
    else:
        return verilog_type

# Generate a module name for a part
def verilog_module_name(part):
    return legal_verilog_name(part.ref)

# Wrap long lines of code
def wrap(text):
    out = []
    while len(text) > 70:
        break_pos = text.rfind(',', 0, 80)
        if break_pos == -1:
            out.append(text)
            text = ''
        else:
            out.append(text[0:break_pos + 1])
            text = text[break_pos + 1:]
    if len(text):
        out.append(text)
    return '\n   '.join(out)

###########################################################################
# Main program
def main(argv):

    logging = Log()

    input_file = None
    output_file = None
    print_help = False

    try:
        options, args = getopt(argv, "i:o:h")
    except:
        options = {'-h' : ''}

    for option, arg in options:
        if option == '-i':
            input_file = arg
        elif option == '-o':
            output_file = arg
        elif option == '-h':
            print_help = True

    if print_help or input_file == None:
        print('Converts a KiCad 6 netlist file into Verilog code.\n')
        print('Usage: KiCadVerilog.py -i <input file> [-o <output file>] [-h]\n')
        print('options:')
        print(' -h                Show this help message and exit.')
        print(' -i <input file>   Specify the name of the KiCad netlist input file. Required.')
        print(' -o <output file>  Specify the name of the Verilog output file. Optional.')
        print('                   If not specified, output will go to stdout.\n')
        print('See https://github.com/galacticstudios/KiCadVerilog for documentation.')
        return logging.get_messages()

    if output_file != None:
        try:
            out = open(output_file, 'w')
        except:
            logging.error('Unable to open', output_file, 'for writing.')
            return logging.get_messages()
    else:
        out = sys.stdout

    try:
        input = open(input_file, 'r', encoding='latin_1')
        nlst = kinparse.parse_netlist(input)

    except IOError:
        logging.error('Unable to open ' + input_file + ' for reading.')
        return logging.get_messages()

    except Exception as e:
        logging.error('Unable to parse ' + input_file + ' as a KiCad 6+ netlist.')
        logging.error(repr(e))
        return logging.get_messages()

    # Generate a name for the top level Verilog module
    if output_file:
        top_level_module_name = os.path.splitext(os.path.basename(output_file.replace('\\\\', '/')))[0]
    else:
        top_level_module_name = os.path.splitext(os.path.basename(nlst.source.replace('\\\\', '/')))[0]

    # Build objects for the netlist
    netlist = NetlistObjects.Netlist(nlst)

    # Get all the VerilogInclude files
    verilog_includes = netlist.verilog_includes()
    
    # Get the nets that should be specified as top-level module ports
    verilog_module_ports = netlist.verilog_module_ports()
                        
    # Generate `include directives for all the Verilog include files we found
    for include_file in verilog_includes:
        print('`include "' + include_file + '"', file = out)
    print('', file = out)

    module_signature = 'module ' + top_level_module_name

    wire_definitions = ''
    module_ports = []

    # Go through all the nets, generating wires for them
    for net_name, net in netlist.nets.items():
        # If this net is supposed to be a module port
        module_port_type = verilog_module_ports.get(net_name)
        if module_port_type != None:
            module_ports.append(verilog_pin_type(module_port_type) + ' ' + legal_verilog_name(net.name))
            
        # Else (this net is not a module port) generate a wire for it
        else:
            if net.is_power_net():
                wire_definitions += '   assign ' + legal_verilog_name(net.name) + ' = 1;\n'
            elif net.is_ground_net():
                wire_definitions += '   assign ' + legal_verilog_name(net.name) + ' = 0;\n'
            elif net.pulled == 0:
                wire_definitions += '   tri0 ' + legal_verilog_name(net.name) + ';\n'
            elif net.pulled == 1:
                wire_definitions += '   tri1 ' + legal_verilog_name(net.name) + ';\n'
            else:
                wire_definitions += '   wire ' + legal_verilog_name(net.name) + ';\n'

    print(module_signature, file = out)
    if len(module_ports):
        module_ports.sort()
        print('(\n   ' + ',\n   '.join(module_ports) + '\n);\n\n', file = out)
    else:
        print('();\n\n', file = out)
    print(wire_definitions, file = out)
    print('', file = out)

    # Generate modules for each of the parts. Also build a dictionary for each module,
    # of which pins are ports
    modules_code = []
    part_refs = list(netlist.parts.keys())
    part_refs.sort(key = lambda item : NetlistObjects.SortableReference(item))
    for part_ref in part_refs:
        part = netlist.parts[part_ref]

        # If it's a pullup or pulldown resistor, or a bypass cap, don't make a
        # module for it.
        if part.is_pullup_resistor() or part.is_pulldown_resistor() or part.is_bypass_cap():
            continue

        module_name = verilog_module_name(part)
        # invocation_args will be an array of wires corresponding to each pin
        invocation_args = [];
        pins = part.pins.values()
        if len(pins) == 0:
            logging.warning('No relevant nets connected to ' + part.ref)

        # Generate the pin declarations
        ports = []
        for pin in pins:
            # If this isn't a power pin
            if pin.type.find('power') == -1:
                # Make the pin an argument to the module
                ports.append('   ' + verilog_pin_type(pin.type) + ' ' + legal_verilog_name(pin.unique_name))
                net = pin.get('net')
                if net != None:
                    invocation_args.append(legal_verilog_name(pin['net'].name))
                else:
                    invocation_args.append(legal_verilog_name("1'bz"))
                    logging.warning('Pin ' + pin.num + ' on part ' + part.ref + ' is not connected to a net, and is not marked as \'no-connect\'')

        if len(ports):
            # Generate the module declaration
            module_code = 'module ' + module_name + '(\n' + ',\n'.join(ports) + ');\n\n'

            # Create vectors for any buses. The user can use them if he wants, or ignore them otherwise
            newline = ''
            first_macro = True
            undefs = []
            for bus_name, bus_pins in part.buses.items():
                # If this is a bus with only one pin in it, don't generate a vector for it
                if len(bus_pins) <= 1:
                    break

                # Sort the pins by their bus index (e.g. A15, A14, A13, A12...)
                args = sorted(bus_pins, key = lambda p: p[2].number, reverse = True)
                # Build a list of the ports in the vector
                arg_list = []
                for arg in args:
                    arg_list.append(legal_verilog_name(arg[1].unique_name))
                # Define a macro that collects bus pins into a vector. Undefine it later
                vbus_name = legal_verilog_name(bus_name)
                if first_macro:
                    module_code += '   // NOTE: The following symbols are MACRO definition(s)!\n'
                    module_code += '   // To use them, precede them with a `\n'
                    first_macro = False
                module_code += '   `define {} {{{}}}\n'.format(vbus_name, ', '.join(arg_list))
                undefs.append('   `undef {}'.format(vbus_name))
                newline = '\n'

            module_code += newline

            # Put any Verilog code in the module
            verilog_code = part.verilog_code()
            if verilog_code != None:
                module_code += verilog_code.encode('utf-8').decode('unicode_escape')
                module_code += '\n\n'

            # else if there's no Verilog code for this module
            else:
                logging.warning('Module ' + module_name + ' has no Verilog code.')

            # End the module
            if len(undefs):
                module_code += '\n'.join(undefs) + '\n\n'

            module_code += 'endmodule\n'

            modules_code.append(module_code)

            # Generate the invocation of the module
            print(wrap('   ' + module_name + ' _' + legal_verilog_name(part.ref) + '(' + ', '.join(invocation_args) + ');\n'), file = out)

        else:
            logging.info('No module generated for ' + part.ref + ' because it has no relevant pins.')

    # Finish the main module
    print('\nendmodule\n', file = out)

    # Output the modules' code
    print('', file = out)
    for module_code in modules_code:
        print(module_code, file = out)

    out.close()

    return logging.get_messages()


if __name__ == '__main__':
    from kvgui import launch
    launch()
