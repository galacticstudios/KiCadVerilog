import logging
from functools import total_ordering
import re

# Take a reference (e.g. R1, U20, etc.) and split it into the letters and
# number. Allow it to be sorted by the letters first, then the integer
@total_ordering
class SortableReference:
    def __init__(self, ref):
        trailing_digit_count = re.search('[0-9]*', ref[::-1]).end()
        self.ref = ref[0 : -trailing_digit_count]
        if trailing_digit_count > 0:
            self.number = int(ref[-trailing_digit_count:])
        else:
            self.number = None

    def __eq__(self, other):
        return self.ref == other.ref and self.number == other.number

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        if self.ref < other.ref:
            return True
        elif self.ref == other.ref and self.number < other.number:
            return True
        else:
            return False

class Part:
    
    def __init__(self, part, libparts):
        self._part = part
        self.pins = {}
        self.name = part.name
        self.ref = part.ref

        # Save a reference to our libpart
        for libpart in libparts:
            duplicates = set()
            if (part.lib == libpart.lib and part.name == libpart.name):
                self._libpart = libpart
                seen = set()
                self.buses = {}
                for pin in libpart.pins:
                    # Build a list of the pins on this part.
                    self.pins[pin.num] = pincopy = pin.copy()
                    # Look for duplicate names. We'll need to mangle them later to make them unique
                    if pincopy.name in seen:
                        duplicates.add(pincopy.name)
                    else:
                        seen.add(pincopy.name)

                    # Split out any number at the end of the name.
                    # e.g. A0, A1, A2... will get split into A and the number
                    # We do this to identify buses
                    pincopy.split = split = SortableReference(pincopy.name)
                    # If the name has a number at the end and text at the beginning
                    if split.number != None and split.ref != '':
                        # Build a list of pins whose names start with the same letter(s) and have
                        # numbers at the end. I.e. buses
                        bus = self.buses.get(split.ref)
                        if bus == None:
                            self.buses[split.ref] = [(int(pincopy.num), pincopy)]
                        else:
                            bus.append((int(pincopy.num), pincopy))

                break

        # Go through the pins and give them unique names
        for pin in self.pins.values():
            if pin.name in duplicates:
                pin.unique_name = pin.name + '_' + pin.num
            else:
                pin.unique_name = pin.name

    def add_net(self, pin_number, net):
        pin = self.pins.get(pin_number)
        if (pin != None):
            pin['net'] = net

    def nets(self):
        nets = []
        for pin in self.pins.values():
            net = pin.get('net')
            if net != None:
                nets.append(net)
        return nets

    def generate_module(self) -> str:
        pass

    def generate_invocation(self) -> str:
        pass

    def is_pulldown_resistor(self) -> bool:
        gndCount = 0
        if len(self.pins) == 2 and self._libpart.desc.lower().find('resistor') != -1:
            for pin in self.pins.values():
                net = pin.get('net')
                if net != None and net.is_ground_net():
                    gndCount += 1
        return gndCount == 1

    def _mark_pulldown_net(self):
        for pin in self.pins.values():
            net = pin.get('net')
            if net != None and not net.is_ground_net():
                net.set_pulled_down()
                break

    def is_pullup_resistor(self) -> bool:
        pwrCount = 0
        if len(self.pins) == 2 and self._libpart.desc.lower().find('resistor') != -1:
            for pin in self.pins.values():
                net = pin.get('net')
                if net != None and net.is_power_net():
                    pwrCount += 1
        return pwrCount == 1

    def _mark_pullup_net(self):
        for pin in self.pins.values():
            net = pin.get('net')
            if net != None and not pin.net.is_power_net():
                net.set_pulled_up()
                break

    def is_bypass_cap(self) -> bool:
        pwrCount = 0
        gndCount = 0
        if len(self.pins) == 2 and self._libpart.desc.lower().find('capacitor') != -1:
            for pin in self.pins.values():
                net = pin.get('net')
                if net.is_power_net():
                    pwrCount += 1
                if net.is_ground_net():
                    gndCount += 1
        return pwrCount == 1 and gndCount == 1

    def _verilog_include(self) -> str:
        for field in self._part.fields:
            # If this field specifies an include file
            if field.name.lower() == 'veriloginclude':
                return field.value

        return None;


    def verilog_code(self) -> str:
        for field in self._part.fields:
            # If this field specifies an include file
            if field.name.lower() == 'verilogcode':
                return field.value.encode('raw_unicode_escape').decode('unicode_escape')

        return None;

    # Return a dictionary of net names that are connected to this part, and which should be used
    # as top-level module ports (as determined by the VerilogModulePort field). They are mapped
    # to the Verilog pin type (input, output, inout)
    def _verilog_module_ports(self):
        ports = {}
        for field in self._part.fields:
            # If this field specifies an include file
            if field.name.lower() == 'verilogmoduleport':
                # Split apart a comma-separated list
                pin_list = field.value.split(',')
                # Go through each pin number in the list
                for pin_str in pin_list:
                    pin_num = pin_str.strip()

                    pin = self.pins.get(pin_num)
                    if pin == None:
                        logging.error('Error: in part ' + self._part.ref + ', the VerilogModulePort field has the invalid pin number "' + pin + '"')

                    else:
                        ports[pin.net.net.name] = pin.type

        return ports


class Net:

    def __init__(self, net):
        self.net = net
        self.name = net.name
        self.pulled = None

    def is_power_net(self) -> bool:
        return self.net.name[0] == '+' or self.net.name.lower() in ['vdd', 'vcc']

    def is_ground_net(self) -> bool:
        return self.net.name[0:3].lower() in ['gnd', 'vss']

    def set_pulled_down(self):
        self.pulled = 0

    def set_pulled_up(self):
        self.pulled = 1

class Netlist:
    def __init__(self, nlst):
        # Build a dictionary mapping part refs to Parts
        self.parts = {}
        for part in nlst.parts:
            self.parts[part.ref] = Part(part, nlst.libparts)

        # Build a dictionary mapping net names to Nets
        self.nets = {}
        for net in nlst.nets:
            obj_net = Net(net)
            self.nets[net.name] = obj_net

            # Go through each pin connected to the net
            for pin in net.pins:
                # Tell the Part about the net its pin is connected to
                part = self.parts.get(pin.ref)
                if (part != None):
                    part.add_net(pin.num, obj_net)

            # Go through all the parts
            for part in self.parts.values():
                # If it's a pullup resistor
                if part.is_pullup_resistor():
                    part._mark_pullup_net()
                elif part.is_pulldown_resistor():
                    part._mark_pulldown_net()

    def verilog_includes(self) -> set[str]:
        includes = set()
        for part in self.parts.values():
            part_include = part._verilog_include()
            if part_include != None:
                includes.add(part_include)
        return includes

    # Return a dictionary of net names which should be used as top-level module ports 
    # (as determined by the VerilogModulePort field in each part). They are mapped
    # to the Verilog pin type (input, output, inout)
    def verilog_module_ports(self):
        nets = {}
        for part in self.parts.values():
            n = part._verilog_module_ports()
            nets = dict(nets, **n)

        return nets
