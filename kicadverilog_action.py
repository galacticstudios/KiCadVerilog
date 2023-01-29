import pcbnew
import os

class KiCadVerilogAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "KiCadVerilog"
        self.category = "Utility"
        self.description = "Convert KiCad netlists to Verilog code."
        self.show_toolbar_button = True # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')

    def Run(self):
        # The entry function of the plugin that is executed on user action
        import kvgui
        kvgui.launch()
